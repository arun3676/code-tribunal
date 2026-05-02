from __future__ import annotations

import ast
import re
from datetime import datetime

from ..models import PerformanceIssue, PerformanceReport


class PerformanceAnalyzer:
    def __init__(self) -> None:
        self.patterns = {
            "nested_loops": {
                "severity": "high",
                "description": "Nested loops detected - likely quadratic or worse complexity",
                "suggestion": "Consider hashing, indexing, batching, or pre-computing lookups.",
            },
            "string_concat_in_loop": {
                "severity": "medium",
                "description": "String concatenation inside loops can be expensive",
                "suggestion": "Collect parts and join once, or use buffered builders.",
            },
            "membership_on_list": {
                "severity": "medium",
                "description": "Repeated membership checks on lists can be slow",
                "suggestion": "Use a set for repeated lookups when order is not required.",
            },
        }

    def analyze_code_performance(self, code: str, language: str = "python", file_path: str = "") -> PerformanceReport:
        issues = self._regex_findings(code, file_path)
        if language.lower() == "python":
            issues.extend(self._python_ast_findings(code, file_path))
        issues = self._deduplicate(issues)
        complexity_analysis = self._complexity_summary(issues)
        overall_score = max(0.0, 100.0 - len(issues) * 12)
        summary = {
            "total_issues": len(issues),
            "high": sum(1 for item in issues if item.severity == "high"),
            "medium": sum(1 for item in issues if item.severity == "medium"),
            "low": sum(1 for item in issues if item.severity == "low"),
        }
        recommendations = [issue.suggestion for issue in issues[:5]] or ["No major performance issues detected by the static ruleset."]
        return PerformanceReport(
            issues=issues,
            summary=summary,
            overall_score=overall_score,
            recommendations=recommendations,
            complexity_analysis=complexity_analysis,
            scan_timestamp=datetime.utcnow().isoformat(),
        )

    def _regex_findings(self, code: str, file_path: str) -> list[PerformanceIssue]:
        findings: list[PerformanceIssue] = []
        lines = code.splitlines()
        nested_pattern = re.compile(r"for .*:\s*$")
        for index, line in enumerate(lines, start=1):
            if nested_pattern.search(line) and index < len(lines) and nested_pattern.search(lines[index]):
                findings.append(
                    PerformanceIssue(
                        issue_type="nested_loops",
                        severity="high",
                        description=self.patterns["nested_loops"]["description"],
                        line_number=index,
                        code_snippet=line.strip(),
                        file_path=file_path,
                        impact="Potential O(n²) or worse runtime",
                        suggestion=self.patterns["nested_loops"]["suggestion"],
                        complexity="O(n²)",
                        estimated_improvement="Large on bigger inputs",
                    )
                )
        return findings

    def _python_ast_findings(self, code: str, file_path: str) -> list[PerformanceIssue]:
        findings: list[PerformanceIssue] = []
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return findings
        parents: dict[ast.AST, ast.AST] = {}
        for parent in ast.walk(tree):
            for child in ast.iter_child_nodes(parent):
                parents[child] = parent
        for node in ast.walk(tree):
            if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
                parent = parents.get(node)
                if isinstance(parent, ast.Assign) and self._inside_loop(parent, parents):
                    findings.append(
                        PerformanceIssue(
                            issue_type="string_concat_in_loop",
                            severity="medium",
                            description=self.patterns["string_concat_in_loop"]["description"],
                            line_number=getattr(node, "lineno", 0),
                            code_snippet="string concatenation in loop",
                            file_path=file_path,
                            impact="Can lead to repeated allocations",
                            suggestion=self.patterns["string_concat_in_loop"]["suggestion"],
                            complexity="O(n²) memory churn",
                            estimated_improvement="Moderate",
                        )
                    )
            if isinstance(node, ast.Compare) and any(isinstance(op, ast.In) for op in node.ops):
                if isinstance(node.comparators[0], ast.Name) and self._inside_loop(node, parents):
                    findings.append(
                        PerformanceIssue(
                            issue_type="membership_on_list",
                            severity="medium",
                            description=self.patterns["membership_on_list"]["description"],
                            line_number=getattr(node, "lineno", 0),
                            code_snippet="membership check in loop",
                            file_path=file_path,
                            impact="Repeated linear scans can dominate runtime",
                            suggestion=self.patterns["membership_on_list"]["suggestion"],
                            complexity="Potential O(n²)",
                            estimated_improvement="Moderate to large",
                        )
                    )
        return findings

    def _inside_loop(self, node: ast.AST, parents: dict[ast.AST, ast.AST]) -> bool:
        current = node
        while current in parents:
            current = parents[current]
            if isinstance(current, (ast.For, ast.While, ast.AsyncFor)):
                return True
        return False

    def _deduplicate(self, issues: list[PerformanceIssue]) -> list[PerformanceIssue]:
        seen: set[tuple[str, int, str]] = set()
        unique: list[PerformanceIssue] = []
        for item in issues:
            key = (item.issue_type, item.line_number, item.code_snippet)
            if key in seen:
                continue
            seen.add(key)
            unique.append(item)
        return unique

    def _complexity_summary(self, issues: list[PerformanceIssue]) -> dict[str, str | int]:
        if any(item.issue_type == "nested_loops" for item in issues):
            complexity = "O(n²) risk detected"
        else:
            complexity = "No obvious super-linear hotspot detected"
        return {
            "overall_complexity": complexity,
            "issue_count": len(issues),
        }
