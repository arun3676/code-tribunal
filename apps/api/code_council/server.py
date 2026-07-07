from __future__ import annotations

import asyncio
import json
import logging
import os
import re
import time
from collections import defaultdict, deque
from pathlib import Path
from typing import AsyncIterator

import httpx
from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sse_starlette.sse import EventSourceResponse

from .analyzer import Analyzer
from .fixes import FixSuggestionGenerator
from .github_webhook import router as github_router, parse_pr_url, _fetch_pr_diff, fetch_pr_meta
from .multimodal import MultiModalAnalyzer
from .scanners.performance import PerformanceAnalyzer
from .scanners.security import SecurityAnalyzer
from .tribunal.fixtures import get_fixture, list_fixtures
from .tribunal.headless import build_adhoc_docket, run_trial_collect, summarize_verdict
from .tribunal.protocol import Docket, IntentSource
from .tribunal.runner import run_trial
from .utils import chunk_text_for_sse, get_git_sha, parse_llm_response

logger = logging.getLogger("code_council")
logging.basicConfig(level=logging.INFO)

app = FastAPI(title="Code Council API", version="0.1.0")
app.include_router(github_router)


def _allowed_origins() -> list[str]:
    configured = os.getenv("ALLOWED_ORIGINS", "")
    origins = [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:3002",
        "http://localhost:3003",
        "http://localhost:3004",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
        "http://127.0.0.1:3002",
        "http://127.0.0.1:3003",
        "http://127.0.0.1:3004",
    ]
    origins.extend([item.strip() for item in configured.split(",") if item.strip()])
    return list(dict.fromkeys(origins))


app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins(),
    allow_origin_regex=os.getenv("ALLOWED_ORIGIN_REGEX") or None,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "Authorization"],
)

analyzer = Analyzer()
multi_modal_analyzer = MultiModalAnalyzer()
security_analyzer = SecurityAnalyzer()
performance_analyzer = PerformanceAnalyzer()
fix_generator = FixSuggestionGenerator()
RATE_LIMIT = 30
RATE_WINDOW_SECONDS = 60
request_windows: dict[str, deque[float]] = defaultdict(deque)


class AnalyzeRequest(BaseModel):
    code: str = Field(min_length=1)
    language: str | None = None
    model: str
    mode: str = Field(default="quick", pattern="^(quick|thorough)$")


class CouncilRequest(BaseModel):
    code: str = Field(min_length=1)
    language: str | None = None
    models: list[str] = Field(min_length=1)
    mode: str = Field(default="quick", pattern="^(quick|thorough)$")


class ScanRequest(BaseModel):
    code: str = Field(min_length=1)
    language: str | None = None


class TribunalRequest(BaseModel):
    fixture_id: str | None = None
    title: str | None = None
    ticket: str | None = None
    diff: str | None = None
    touched_domains: list[str] = Field(default_factory=list)


@app.on_event("startup")
async def startup_event() -> None:
    for descriptor in analyzer.get_model_registry():
        available = bool(os.getenv(descriptor.env_var))
        logger.info("provider=%s model=%s available=%s", descriptor.provider, descriptor.id, available)


_RATE_EXEMPT_PATHS = {"/health", "/models"}

@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    # Exempt CORS preflights and cheap read-only endpoints from rate limiting
    if request.method == "OPTIONS" or request.url.path in _RATE_EXEMPT_PATHS:
        return await call_next(request)
    client_ip = request.client.host if request.client else "unknown"
    now = time.time()
    window = request_windows[client_ip]
    while window and now - window[0] > RATE_WINDOW_SECONDS:
        window.popleft()
    if len(window) >= RATE_LIMIT:
        # Return a Response (not raise) so CORSMiddleware can add headers
        return JSONResponse({"detail": "Rate limit exceeded"}, status_code=429)
    window.append(now)
    return await call_next(request)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "version": get_git_sha(Path(__file__).resolve().parents[2])}


@app.get("/models")
async def models() -> list[dict]:
    return analyzer.get_available_models()


@app.post("/scan")
async def scan(payload: ScanRequest) -> dict:
    language = analyzer.resolve_language(payload.code, payload.language)
    security = security_analyzer.analyze_code_security(payload.code, language=language)
    performance = performance_analyzer.analyze_code_performance(payload.code, language=language)
    return {
        "security": {
            "vulnerabilities": [item.to_dict() for item in security.vulnerabilities],
            "risk_score": security.risk_score,
            "summary": security.summary,
            "recommendations": security.recommendations,
        },
        "performance": {
            "issues": [item.to_dict() for item in performance.issues],
            "overall_score": performance.overall_score,
            "summary": performance.summary,
            "recommendations": performance.recommendations,
            "complexity_analysis": performance.complexity_analysis,
        },
    }


async def _run_model(code: str, model: str, language: str | None, mode: str, queue: asyncio.Queue) -> None:
    started_at = time.perf_counter()
    try:
        resolved_language, response_text = await asyncio.to_thread(
            lambda: analyzer.generate_analysis_text(code, model, language=language, mode=mode)
        )
        for delta in chunk_text_for_sse(response_text):
            await queue.put(("token", {"model": model, "delta": delta}))
            await asyncio.sleep(0.03)
        parsed = parse_llm_response(response_text)
        payload = {
            "model": model,
            "quality_score": parsed.get("code_quality_score", 70),
            "bugs": parsed.get("potential_bugs", []),
            "suggestions": parsed.get("improvement_suggestions", []),
            "documentation": parsed.get("documentation", ""),
        }
        await queue.put(("parsed", payload))
        if mode == "thorough":
            issues = [
                {"type": "bug", "description": item, "line_number": 0, "severity": "medium"}
                for item in payload["bugs"]
            ] + [
                {"type": "improvement", "description": item, "line_number": 0, "severity": "low"}
                for item in payload["suggestions"]
            ]
            fixes = await asyncio.to_thread(lambda: fix_generator.generate_fix_suggestions(code, issues, resolved_language))
            await queue.put(("fixes", {"model": model, "items": fixes}))
        duration_ms = round((time.perf_counter() - started_at) * 1000, 2)
        await queue.put(("done", {"model": model, "duration_ms": duration_ms}))
    except Exception as exc:
        await queue.put(("error", {"model": model, "message": str(exc)}))
    finally:
        await queue.put(("finished", {"model": model}))


@app.post("/analyze")
async def analyze(payload: AnalyzeRequest):
    async def event_stream() -> AsyncIterator[dict[str, str]]:
        queue: asyncio.Queue = asyncio.Queue()
        task = asyncio.create_task(_run_model(payload.code, payload.model, payload.language, payload.mode, queue))
        finished = False
        while not finished:
            event, data = await queue.get()
            if event == "finished":
                finished = True
            elif event == "parsed":
                raw = {
                    "quality_score": data["quality_score"],
                    "bugs": data["bugs"],
                    "suggestions": data["suggestions"],
                    "documentation": data["documentation"],
                }
                yield {"event": "parsed", "data": json.dumps(raw)}
            elif event == "fixes":
                yield {"event": "fixes", "data": json.dumps(data["items"])}
            elif event == "done":
                yield {"event": "done", "data": json.dumps({"duration_ms": data["duration_ms"]})}
            elif event == "error":
                yield {"event": "error", "data": json.dumps({"message": data["message"]})}
            else:
                yield {"event": "token", "data": json.dumps({"delta": data["delta"]})}
        await task

    return EventSourceResponse(event_stream())


@app.post("/council")
async def council(payload: CouncilRequest):
    async def event_stream() -> AsyncIterator[dict[str, str]]:
        queue: asyncio.Queue = asyncio.Queue()
        started_at = time.perf_counter()
        tasks = [
            asyncio.create_task(_run_model(payload.code, model, payload.language, payload.mode, queue))
            for model in payload.models
        ]
        finished = 0
        while finished < len(tasks):
            event, data = await queue.get()
            if event == "finished":
                finished += 1
            elif event == "done":
                yield {"event": "done", "data": json.dumps(data)}
            elif event == "parsed":
                yield {"event": "parsed", "data": json.dumps(data)}
            elif event == "fixes":
                yield {"event": "fixes", "data": json.dumps(data)}
            elif event == "error":
                yield {"event": "error", "data": json.dumps(data)}
            else:
                yield {"event": "token", "data": json.dumps(data)}
        await asyncio.gather(*tasks, return_exceptions=True)
        yield {"event": "all_done", "data": json.dumps({"total_duration_ms": round((time.perf_counter() - started_at) * 1000, 2)})}

    return EventSourceResponse(event_stream())


def _detect_domains(diff: str, declared: list[str]) -> list[str]:
    domains = set(d.strip().lower() for d in declared if d.strip())
    text = diff.lower()
    if any(k in text for k in ("login", "auth", "password", "token", "session")):
        domains.add("auth")
    if any(k in text for k in ("bcrypt", "crypto", "secret", "middleware", "permission")):
        domains.add("security")
    return sorted(domains)


@app.get("/tribunal/fixtures")
async def tribunal_fixtures() -> list[dict]:
    return list_fixtures()


@app.post("/tribunal/run")
async def tribunal_run(payload: TribunalRequest):
    if payload.fixture_id:
        docket = get_fixture(payload.fixture_id)
        if docket is None:
            raise HTTPException(status_code=404, detail=f"Unknown fixture: {payload.fixture_id}")
    else:
        if not payload.ticket or not payload.diff:
            raise HTTPException(status_code=400, detail="Provide fixture_id, or both ticket and diff.")
        files = sorted({m for m in re.findall(r"[+]{3}\s+b/(\S+)", payload.diff)})
        docket = Docket(
            trial_id=f"adhoc-{int(time.time())}",
            title=payload.title or "Ad-hoc tribunal",
            intent_sources=[IntentSource(source_ref="custom", title="Ticket", text=payload.ticket)],
            diff=payload.diff,
            touched_files=files,
            touched_domains=_detect_domains(payload.diff, payload.touched_domains),
        )

    async def event_stream() -> AsyncIterator[dict[str, str]]:
        try:
            async for event in run_trial(docket):
                yield {"event": event.type, "data": event.model_dump_json()}
        except Exception as exc:  # pragma: no cover - defensive
            logger.exception("tribunal run failed")
            yield {"event": "error", "data": json.dumps({"message": str(exc)})}

    return EventSourceResponse(event_stream())


@app.post("/tribunal/verdict")
async def tribunal_verdict(payload: TribunalRequest) -> dict:
    """Headless (non-streaming) trial — returns the final verdict as JSON.

    This is the programmatic entrypoint for coding agents / CI / MCP: same
    court, same Band mirroring and WARDEN recruitment as ``/tribunal/run``, but
    one JSON response instead of an SSE stream.
    """
    if payload.fixture_id:
        docket = get_fixture(payload.fixture_id)
        if docket is None:
            raise HTTPException(status_code=404, detail=f"Unknown fixture: {payload.fixture_id}")
    else:
        if not payload.ticket or not payload.diff:
            raise HTTPException(status_code=400, detail="Provide fixture_id, or both ticket and diff.")
        docket = build_adhoc_docket(payload.ticket, payload.diff, payload.touched_domains, payload.title)

    result = await run_trial_collect(docket)
    result["headline"] = summarize_verdict(result.get("verdict"))
    return result


class ReviewPrRequest(BaseModel):
    pr_url: str = Field(min_length=1)


@app.post("/tribunal/review-pr")
async def tribunal_review_pr(payload: ReviewPrRequest) -> dict:
    """Fetch a GitHub PR's diff + metadata and run the tribunal headlessly.

    Returns the same JSON verdict shape as ``POST /tribunal/verdict`` so the
    frontend can treat both endpoints identically.  Works unauthenticated for
    public PRs (GitHub allows ~60 req/hr/IP); set GITHUB_TOKEN in the
    environment to handle private repos and to raise the rate limit to 5 000/hr.
    """
    try:
        owner, repo, number = parse_pr_url(payload.pr_url)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid GitHub PR URL")

    token: str | None = os.getenv("GITHUB_TOKEN") or None

    try:
        diff, (title, body) = await asyncio.gather(
            _fetch_pr_diff(owner, repo, number, token),
            fetch_pr_meta(owner, repo, number, token),
        )
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 404:
            raise HTTPException(
                status_code=404,
                detail="PR not found or private — set GITHUB_TOKEN for private repos",
            )
        raise HTTPException(
            status_code=502,
            detail=f"GitHub API error: {exc.response.status_code}",
        )
    except httpx.RequestError as exc:
        raise HTTPException(status_code=502, detail=f"GitHub request failed: {exc}")

    intent = body or title
    docket = build_adhoc_docket(intent, diff, title=f"PR #{number}: {title}")
    result = await run_trial_collect(docket)
    result["headline"] = summarize_verdict(result.get("verdict"))
    return result


@app.post("/multimodal")
async def multimodal(
    image: UploadFile = File(...),
    prompt: str | None = Form(default=None),
    model: str | None = Form(default=None),
) -> dict:
    content = await image.read()
    return multi_modal_analyzer.analyze(content, prompt=prompt, model_id=model)
