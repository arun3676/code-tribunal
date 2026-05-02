from dataclasses import dataclass
from pathlib import Path


@dataclass
class LanguageInfo:
    name: str
    confidence: float = 1.0
    file_extension: str | None = None


class LanguageDetector:
    def __init__(self) -> None:
        self.extension_map = {
            ".py": "python",
            ".js": "javascript",
            ".jsx": "javascript",
            ".ts": "typescript",
            ".tsx": "typescript",
            ".java": "java",
            ".go": "go",
            ".rs": "rust",
            ".php": "php",
            ".rb": "ruby",
            ".swift": "swift",
            ".kt": "kotlin",
            ".sql": "sql",
            ".c": "c",
            ".cpp": "cpp",
            ".cc": "cpp",
            ".hpp": "cpp",
            ".cs": "csharp",
            ".html": "html",
            ".css": "css",
            ".json": "json",
            ".yaml": "yaml",
            ".yml": "yaml",
        }
        self.keyword_map = {
            "python": ["def ", "import ", "from ", "elif", "self", "__name__"],
            "javascript": ["function ", "const ", "let ", "=>", "console.log", "await "],
            "typescript": ["interface ", "type ", "enum ", ": string", ": number"],
            "java": ["public class", "private ", "public static void main", "System.out"],
            "go": ["package main", "func ", "fmt.", ":=", "defer "],
            "rust": ["fn main", "let mut", "println!", "impl ", "use "],
            "sql": ["select ", "insert ", "update ", "delete ", "where "],
            "html": ["<html", "<div", "<body", "<script", "</"],
        }

    def detect_language(self, code: str, file_path: str | None = None) -> LanguageInfo:
        if file_path:
            suffix = Path(file_path).suffix.lower()
            if suffix in self.extension_map:
                return LanguageInfo(name=self.extension_map[suffix], confidence=0.98, file_extension=suffix)
        lowered = code.lower()
        best_language = "python"
        best_score = 0
        for language, keywords in self.keyword_map.items():
            score = sum(1 for keyword in keywords if keyword in lowered)
            if score > best_score:
                best_score = score
                best_language = language
        confidence = min(0.99, 0.35 + (best_score * 0.12)) if best_score else 0.2
        return LanguageInfo(name=best_language, confidence=confidence)
