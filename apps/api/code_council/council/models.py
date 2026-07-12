from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class CodeAnalysisResult:
    code_quality_score: float
    potential_bugs: list[str]
    improvement_suggestions: list[str]
    documentation: str
    model_name: str
    execution_time: float = 0.0
    fix_suggestions: list[dict[str, Any]] = field(default_factory=list)
    raw_response: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ModelEvaluationResult:
    model_name: str
    average_quality_score: float
    average_execution_time: float
    success_rate: float
    analysis_samples: list[CodeAnalysisResult]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ModelDescriptor:
    id: str
    provider: str
    display: str
    color: str
    env_var: str
    base_url: str | None = None
    vision: bool = False

    def to_dict(self, available: bool) -> dict[str, Any]:
        return {
            "id": self.id,
            "provider": self.provider,
            "available": available,
            "display": self.display,
            "color": self.color,
            "vision": self.vision,
        }


@dataclass
class SecurityVulnerability:
    vulnerability_type: str
    severity: str
    description: str
    line_number: int
    code_snippet: str
    file_path: str
    cwe_id: str | None = None
    remediation: str | None = None
    confidence: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class SecurityReport:
    vulnerabilities: list[SecurityVulnerability]
    summary: dict[str, int]
    risk_score: float
    recommendations: list[str]
    scan_timestamp: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "vulnerabilities": [item.to_dict() for item in self.vulnerabilities],
            "summary": self.summary,
            "risk_score": self.risk_score,
            "recommendations": self.recommendations,
            "scan_timestamp": self.scan_timestamp,
        }


@dataclass
class PerformanceIssue:
    issue_type: str
    severity: str
    description: str
    line_number: int
    code_snippet: str
    file_path: str
    impact: str
    suggestion: str
    complexity: str | None = None
    estimated_improvement: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class PerformanceReport:
    issues: list[PerformanceIssue]
    summary: dict[str, Any]
    overall_score: float
    recommendations: list[str]
    complexity_analysis: dict[str, Any]
    scan_timestamp: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "issues": [item.to_dict() for item in self.issues],
            "summary": self.summary,
            "overall_score": self.overall_score,
            "recommendations": self.recommendations,
            "complexity_analysis": self.complexity_analysis,
            "scan_timestamp": self.scan_timestamp,
        }


@dataclass
class FixSuggestion:
    issue_id: str
    issue_type: str
    severity: str
    title: str
    description: str
    line_number: int
    original_code: str
    fixed_code: str
    explanation: str
    confidence: float
    tags: list[str]
    related_links: list[str]
    diff: str
    can_auto_apply: bool
    plain_explanation: str = ""
    learn_more_link: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
