from __future__ import annotations

from difflib import unified_diff

from .models import FixSuggestion


class FixSuggestionGenerator:
    def generate_fix_suggestions(self, code: str, issues: list[dict], language: str = "python") -> list[dict]:
        suggestions: list[dict] = []
        for index, issue in enumerate(issues, start=1):
            suggestion = self._generate_fix(code, issue, language, index)
            if suggestion:
                suggestions.append(suggestion.to_dict())
        return suggestions

    def _generate_fix(self, code: str, issue: dict, language: str, issue_id: int) -> FixSuggestion | None:
        description = str(issue.get("description", "Potential issue"))
        lowered = description.lower()
        original_code = code
        fixed_code = code
        title = "Suggested improvement"
        explanation = description
        tags = [issue.get("type", "quality")]
        links: list[str] = []
        if "secret" in lowered or "password" in lowered or "token" in lowered:
            title = "Move secret to environment variables"
            fixed_code = code.replace("password = \"secret\"", "password = os.getenv(\"PASSWORD\")")
            explanation = "Hardcoded secrets should be moved to environment variables or a secret manager."
            tags.extend(["security", "configuration"])
        elif "eval" in lowered:
            title = "Replace eval with safe parsing"
            explanation = "Dynamic code execution should be replaced with explicit parsing or dispatch."
            tags.extend(["security", "execution"])
        elif "nested" in lowered and "loop" in lowered:
            title = "Reduce nested loop work"
            explanation = "Consider indexing one side of the loop or using a set/dictionary for lookups."
            tags.extend(["performance", "complexity"])
        elif "debug" in lowered:
            title = "Remove debug-only output"
            explanation = "Debug logging should be removed or gated before production use."
            tags.extend(["quality"])
        if fixed_code == original_code and title == "Suggested improvement":
            fixed_code = original_code
        diff = "\n".join(
            unified_diff(
                original_code.splitlines(),
                fixed_code.splitlines(),
                fromfile="before",
                tofile="after",
                lineterm="",
            )
        ) or "No automated diff available"
        return FixSuggestion(
            issue_id=f"issue-{issue_id}",
            issue_type=str(issue.get("type", "quality")),
            severity=str(issue.get("severity", "medium")),
            title=title,
            description=description,
            line_number=int(issue.get("line_number", 0) or 0),
            original_code=original_code,
            fixed_code=fixed_code,
            explanation=explanation,
            confidence=0.62,
            tags=list(dict.fromkeys(tags)),
            related_links=links,
            diff=diff,
            can_auto_apply=False,
            plain_explanation=explanation,
            learn_more_link=links[0] if links else "",
        )
