from __future__ import annotations

import ast
import re
from datetime import datetime
from pathlib import Path

from ..models import SecurityReport, SecurityVulnerability


class SecurityAnalyzer:
    def __init__(self) -> None:
        self.patterns = {
            "sql_injection": {
                "severity": "critical",
                "cwe_id": "CWE-89",
                "description": "Potential SQL injection vulnerability detected",
                "patterns": [
                    r"execute\s*\(\s*f?[\"'][^\"']*\{",
                    r"execute\s*\(\s*[^\n]*\+[^\n]*\)",
                    r"SELECT .*\+.*FROM",
                ],
            },
            "command_injection": {
                "severity": "critical",
                "cwe_id": "CWE-78",
                "description": "Potential command injection vulnerability",
                "patterns": [
                    r"os\.system\s*\(",
                    r"subprocess\.(run|call|Popen)\s*\([^\)]*shell\s*=\s*True",
                    r"exec\s*\(",
                ],
            },
            "hardcoded_secrets": {
                "severity": "high",
                "cwe_id": "CWE-259",
                "description": "Hardcoded secret detected",
                "patterns": [
                    r"(api_?key|token|secret|password)\s*=\s*[\"'][^\"']{8,}[\"']",
                ],
            },
            "xss": {
                "severity": "high",
                "cwe_id": "CWE-79",
                "description": "Potential XSS vulnerability",
                "patterns": [
                    r"innerHTML\s*=",
                    r"document\.write\s*\(",
                ],
            },
            "weak_crypto": {
                "severity": "medium",
                "cwe_id": "CWE-327",
                "description": "Weak cryptographic primitive detected",
                "patterns": [
                    r"hashlib\.md5\s*\(",
                    r"hashlib\.sha1\s*\(",
                ],
            },
        }

    def analyze_code_security(self, code: str, language: str = "python", file_path: str = "") -> SecurityReport:
        findings = self._pattern_findings(code, file_path)
        if language.lower() == "python":
            findings.extend(self._python_ast_findings(code, file_path))
        findings = self._deduplicate(findings)
        summary = {
            "total": len(findings),
            "critical": sum(1 for item in findings if item.severity == "critical"),
            "high": sum(1 for item in findings if item.severity == "high"),
            "medium": sum(1 for item in findings if item.severity == "medium"),
            "low": sum(1 for item in findings if item.severity == "low"),
        }
        risk_score = min(100.0, summary["critical"] * 35 + summary["high"] * 20 + summary["medium"] * 10 + summary["low"] * 4)
        recommendations = []
        if summary["critical"] or summary["high"]:
            recommendations.append("Prioritize eliminating injection risks and moving secrets out of source code.")
        if any(item.vulnerability_type == "weak_crypto" for item in findings):
            recommendations.append("Replace deprecated hashing algorithms with modern alternatives such as SHA-256 or better.")
        if not recommendations:
            recommendations.append("No high-confidence security issues detected by the static ruleset.")
        return SecurityReport(
            vulnerabilities=findings,
            summary=summary,
            risk_score=risk_score,
            recommendations=recommendations,
            scan_timestamp=datetime.utcnow().isoformat(),
        )

    def _pattern_findings(self, code: str, file_path: str) -> list[SecurityVulnerability]:
        findings: list[SecurityVulnerability] = []
        lines = code.splitlines()
        for issue_type, meta in self.patterns.items():
            for pattern in meta["patterns"]:
                regex = re.compile(pattern, re.IGNORECASE)
                for index, line in enumerate(lines, start=1):
                    if regex.search(line):
                        findings.append(
                            SecurityVulnerability(
                                vulnerability_type=issue_type,
                                severity=meta["severity"],
                                description=meta["description"],
                                line_number=index,
                                code_snippet=line.strip(),
                                file_path=file_path,
                                cwe_id=meta["cwe_id"],
                                remediation="Refactor this code path to use a safer API or sanitize untrusted input.",
                                confidence=0.82,
                            )
                        )
        return findings

    def _python_ast_findings(self, code: str, file_path: str) -> list[SecurityVulnerability]:
        findings: list[SecurityVulnerability] = []
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return findings
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                if node.func.id == "eval":
                    findings.append(
                        SecurityVulnerability(
                            vulnerability_type="eval_injection",
                            severity="critical",
                            description="Use of eval introduces arbitrary code execution risk",
                            line_number=getattr(node, "lineno", 0),
                            code_snippet="eval(...)",
                            file_path=file_path,
                            cwe_id="CWE-95",
                            remediation="Avoid eval on untrusted input and use structured parsing instead.",
                            confidence=0.95,
                        )
                    )
                if node.func.id == "exec":
                    findings.append(
                        SecurityVulnerability(
                            vulnerability_type="exec_usage",
                            severity="critical",
                            description="Use of exec introduces arbitrary code execution risk",
                            line_number=getattr(node, "lineno", 0),
                            code_snippet="exec(...)",
                            file_path=file_path,
                            cwe_id="CWE-78",
                            remediation="Avoid exec and dispatch behavior explicitly instead.",
                            confidence=0.95,
                        )
                    )
        return findings

    def _deduplicate(self, findings: list[SecurityVulnerability]) -> list[SecurityVulnerability]:
        seen: set[tuple[str, int, str]] = set()
        unique: list[SecurityVulnerability] = []
        for item in findings:
            key = (item.vulnerability_type, item.line_number, item.code_snippet)
            if key in seen:
                continue
            seen.add(key)
            unique.append(item)
        return unique

    def scan_file(self, file_path: str) -> SecurityReport:
        path = Path(file_path)
        return self.analyze_code_security(path.read_text(encoding="utf-8"), file_path=str(path), language=path.suffix.lstrip("."))
