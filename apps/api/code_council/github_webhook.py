"""GitHub webhook — Tribunal as a pre-merge gatekeeper in CI.

When a coding agent opens a pull request, GitHub posts a ``pull_request`` event
here. CLERK extracts the intent (PR body + linked issue) and the diff, convenes
the court headlessly, and ARBITER posts the verdict + traceability ledger back
as a PR comment — requesting changes when the diff ``DOES_NOT_CONFORM``. That
review request is what kicks the coding agent into its next fix loop, with zero
human in the path.

This router is **dormant until configured**. Set:
    GITHUB_WEBHOOK_SECRET   shared secret for HMAC signature verification
    GITHUB_TOKEN            token with repo scope to read the diff + post comments

Without those it returns 503 and never touches the rest of the API.
"""

from __future__ import annotations

import hashlib
import hmac
import logging
import os

import httpx
from fastapi import APIRouter, BackgroundTasks, Header, HTTPException, Request

from .tribunal.headless import build_adhoc_docket, run_trial_collect

logger = logging.getLogger("code_council.github")

router = APIRouter(prefix="/webhooks", tags=["github"])

_GITHUB_API = "https://api.github.com"
_VERDICT_EMOJI = {"APPROVE": "✅", "APPROVE_WITH_CONDITIONS": "⚠️", "BLOCK": "⛔"}


def _enabled() -> bool:
    return bool(os.getenv("GITHUB_WEBHOOK_SECRET") and os.getenv("GITHUB_TOKEN"))


def verify_signature(body: bytes, signature: str | None, secret: str) -> bool:
    """Constant-time check of GitHub's ``X-Hub-Signature-256`` header."""
    if not signature or not signature.startswith("sha256="):
        return False
    expected = "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)


def format_pr_comment(result: dict) -> str:
    """Render a headless trial result as a Markdown PR review comment."""
    verdict = result.get("verdict") or {}
    state = verdict.get("state", "UNKNOWN")
    merge = verdict.get("merge_decision", "UNKNOWN")
    trust = verdict.get("trust_score", "?")
    emoji = _VERDICT_EMOJI.get(merge, "•")

    lines = [
        "## ⚖️ Code Council Tribunal — Intent-Conformance Verdict",
        "",
        f"**{emoji} {state}** · Merge: **{merge}** · Trust score: **{trust}/100**",
        "",
        f"> {verdict.get('summary', '')}",
        "",
    ]

    blockers = verdict.get("blockers") or []
    if blockers:
        lines.append("### ⛔ Blockers")
        lines += [f"- {b}" for b in blockers]
        lines.append("")

    conditions = verdict.get("conditions") or []
    if conditions:
        lines.append("### ⚠️ Conditions")
        lines += [f"- {c}" for c in conditions]
        lines.append("")

    ledger = verdict.get("ledger") or []
    if ledger:
        lines.append("### 📋 Traceability ledger")
        lines.append("| Req | Requirement | Decision |")
        lines.append("| --- | --- | --- |")
        for row in ledger:
            lines.append(
                f"| {row.get('requirement_id','')} | {row.get('requirement','')} | **{row.get('decision','')}** |"
            )
        lines.append("")

    if result.get("recruited"):
        lines.append(f"_Witnesses recruited: {', '.join(result['recruited'])}._")
    lines.append("")
    lines.append("<sub>🤖 Posted by Code Council Tribunal — intent-conformance review, not generic code review.</sub>")
    return "\n".join(lines)


def parse_pr_url(url: str) -> tuple[str, str, int]:
    """Extract (owner, repo, number) from a GitHub PR URL.

    Accepts https/http, optional .git suffix, and trailing fragments like
    #pullrequestreview-…. Raises ValueError on no match.
    """
    import re as _re
    m = _re.search(r"github\.com[:/]+([\w.-]+)/([\w.-]+?)(?:\.git)?/pull/(\d+)", url)
    if not m:
        raise ValueError(f"Cannot parse GitHub PR URL: {url!r}")
    owner, repo, number = m.group(1), m.group(2), int(m.group(3))
    return owner, repo, number


async def _fetch_pr_diff(owner: str, repo: str, number: int, token: str | None = None) -> str:
    # GitHub allows ~60 unauthenticated requests/hr/IP — sufficient for a demo.
    # Pass GITHUB_TOKEN for private repos or to raise the rate limit to 5 000/hr.
    headers: dict[str, str] = {"Accept": "application/vnd.github.v3.diff"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(
            f"{_GITHUB_API}/repos/{owner}/{repo}/pulls/{number}",
            headers=headers,
        )
        resp.raise_for_status()
        return resp.text


async def fetch_pr_meta(owner: str, repo: str, number: int, token: str | None = None) -> tuple[str, str]:
    """Return (title, body) for a GitHub pull request.

    Works unauthenticated for public repos; pass a token for private repos.
    """
    headers: dict[str, str] = {"Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(
            f"{_GITHUB_API}/repos/{owner}/{repo}/pulls/{number}",
            headers=headers,
        )
        resp.raise_for_status()
        data = resp.json()
        return data.get("title", ""), data.get("body") or ""


async def _post_pr_comment(owner: str, repo: str, number: int, token: str, body: str) -> None:
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            f"{_GITHUB_API}/repos/{owner}/{repo}/issues/{number}/comments",
            headers={"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"},
            json={"body": body},
        )
        resp.raise_for_status()


async def _request_changes(owner: str, repo: str, number: int, token: str, body: str) -> None:
    """Submit a 'changes requested' review — the signal that loops the agent."""
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            f"{_GITHUB_API}/repos/{owner}/{repo}/pulls/{number}/reviews",
            headers={"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"},
            json={"event": "REQUEST_CHANGES", "body": body},
        )
        if resp.status_code >= 400:
            # Fall back to a plain comment if review submission is not permitted.
            logger.warning("request_changes failed (%s); falling back to comment", resp.status_code)
            await _post_pr_comment(owner, repo, number, token, body)


async def _adjudicate_pr(owner: str, repo: str, number: int, title: str, intent: str) -> None:
    token = os.environ["GITHUB_TOKEN"]
    try:
        diff = await _fetch_pr_diff(owner, repo, number, token)
        docket = build_adhoc_docket(intent or title, diff, title=f"PR #{number}: {title}")
        result = await run_trial_collect(docket)
        comment = format_pr_comment(result)
        merge = (result.get("verdict") or {}).get("merge_decision")
        if merge == "BLOCK":
            await _request_changes(owner, repo, number, token, comment)
        else:
            await _post_pr_comment(owner, repo, number, token, comment)
        logger.info("tribunal posted verdict on %s/%s#%s: %s", owner, repo, number, merge)
    except Exception:  # pragma: no cover - background best-effort
        logger.exception("tribunal PR adjudication failed for %s/%s#%s", owner, repo, number)


@router.post("/github")
async def github_webhook(
    request: Request,
    background: BackgroundTasks,
    x_github_event: str | None = Header(default=None),
    x_hub_signature_256: str | None = Header(default=None),
) -> dict:
    if not _enabled():
        raise HTTPException(status_code=503, detail="GitHub integration not configured.")

    raw = await request.body()
    if not verify_signature(raw, x_hub_signature_256, os.environ["GITHUB_WEBHOOK_SECRET"]):
        raise HTTPException(status_code=401, detail="Invalid signature.")

    if x_github_event == "ping":
        return {"ok": True, "pong": True}
    if x_github_event != "pull_request":
        return {"ok": True, "ignored": x_github_event}

    payload = await request.json()
    if payload.get("action") not in {"opened", "reopened", "synchronize", "ready_for_review"}:
        return {"ok": True, "ignored_action": payload.get("action")}

    pr = payload.get("pull_request", {})
    repo = payload.get("repository", {})
    owner = repo.get("owner", {}).get("login")
    repo_name = repo.get("name")
    number = pr.get("number")
    if not (owner and repo_name and number):
        raise HTTPException(status_code=400, detail="Malformed pull_request payload.")

    background.add_task(
        _adjudicate_pr,
        owner,
        repo_name,
        number,
        pr.get("title", ""),
        pr.get("body") or "",
    )
    return {"ok": True, "queued": f"{owner}/{repo_name}#{number}"}
