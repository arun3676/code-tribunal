from __future__ import annotations

import json
import subprocess
import time
from functools import wraps
from pathlib import Path
from typing import Any, Iterable


def timer_decorator(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        started_at = time.perf_counter()
        result = func(*args, **kwargs)
        duration = time.perf_counter() - started_at
        if hasattr(result, "execution_time"):
            result.execution_time = duration
        return result

    return wrapper


def strip_code_fences(text: str) -> str:
    stripped = text.strip()
    if stripped.startswith("```") and stripped.endswith("```"):
        lines = stripped.splitlines()
        if len(lines) >= 3:
            return "\n".join(lines[1:-1]).strip()
    return stripped


def parse_llm_response(response: str) -> dict[str, Any]:
    result: dict[str, Any] = {
        "code_quality_score": 70,
        "potential_bugs": [],
        "improvement_suggestions": [],
        "documentation": "",
    }
    cleaned = strip_code_fences(response)

    try:
        start_index = cleaned.find("{")
        end_index = cleaned.rfind("}")
        if start_index >= 0 and end_index > start_index:
            payload = json.loads(cleaned[start_index : end_index + 1])
            if isinstance(payload.get("code_quality_score"), (int, float)):
                result["code_quality_score"] = float(payload["code_quality_score"])
            if isinstance(payload.get("potential_bugs"), list):
                result["potential_bugs"] = [str(item).strip() for item in payload["potential_bugs"] if str(item).strip()]
            if isinstance(payload.get("improvement_suggestions"), list):
                result["improvement_suggestions"] = [str(item).strip() for item in payload["improvement_suggestions"] if str(item).strip()]
            if isinstance(payload.get("documentation"), str):
                result["documentation"] = payload["documentation"].strip()
            return result
    except Exception:
        pass

    current_section: str | None = None
    documentation_lines: list[str] = []
    for raw_line in cleaned.splitlines():
        line = raw_line.strip()
        lowered = line.lower()
        if not line:
            continue
        if "quality score" in lowered or "code quality" in lowered:
            for token in line.replace("/100", " ").split():
                try:
                    result["code_quality_score"] = float(token)
                    break
                except ValueError:
                    continue
            continue
        if "bug" in lowered or "issue" in lowered or "error" in lowered:
            current_section = "potential_bugs"
            continue
        if "suggestion" in lowered or "improvement" in lowered or "recommend" in lowered:
            current_section = "improvement_suggestions"
            continue
        if "documentation" in lowered or "summary" in lowered or "overview" in lowered:
            current_section = "documentation"
            continue
        clean_line = line.lstrip("-*0123456789. ")
        if current_section == "potential_bugs" and clean_line:
            result["potential_bugs"].append(clean_line)
        elif current_section == "improvement_suggestions" and clean_line:
            result["improvement_suggestions"].append(clean_line)
        else:
            documentation_lines.append(clean_line)
    if documentation_lines and not result["documentation"]:
        result["documentation"] = "\n".join(documentation_lines).strip()
    return result


def chunk_text_for_sse(text: str, chunk_size: int = 32) -> Iterable[str]:
    if len(text) <= chunk_size:
        yield text
        return
    current = ""
    for piece in text.split(" "):
        candidate = f"{current} {piece}".strip()
        if current and len(candidate) > chunk_size:
            yield current + " "
            current = piece
        else:
            current = candidate
    if current:
        yield current


def normalize_issue_text(text: str) -> str:
    normalized = "".join(ch.lower() if ch.isalnum() or ch.isspace() else " " for ch in text)
    return " ".join(normalized.split())


def jaccard_similarity(left: str, right: str) -> float:
    left_tokens = set(normalize_issue_text(left).split())
    right_tokens = set(normalize_issue_text(right).split())
    if not left_tokens and not right_tokens:
        return 1.0
    if not left_tokens or not right_tokens:
        return 0.0
    intersection = len(left_tokens & right_tokens)
    union = len(left_tokens | right_tokens)
    return intersection / union if union else 0.0


def get_git_sha(root: Path | None = None) -> str:
    try:
        base_dir = root or Path(__file__).resolve().parents[3]
        return (
            subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=base_dir)
            .decode("utf-8")
            .strip()
        )
    except Exception:
        return "dev"
