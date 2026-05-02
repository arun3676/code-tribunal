from __future__ import annotations

import re
from typing import Any

import requests


class GitHubAnalyzer:
    def __init__(self) -> None:
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "Code-Council/1.0"})

    def parse_github_url(self, url: str) -> dict[str, str | None]:
        cleaned = url.rstrip("/")
        patterns = [
            r"https?://github\.com/([^/]+)/([^/]+)/blob/([^/]+)/(.+)",
            r"https?://github\.com/([^/]+)/([^/]+)$",
        ]
        for pattern in patterns:
            match = re.match(pattern, cleaned)
            if not match:
                continue
            if len(match.groups()) == 4:
                return {
                    "owner": match.group(1),
                    "repo": match.group(2),
                    "branch": match.group(3),
                    "file_path": match.group(4),
                }
            return {
                "owner": match.group(1),
                "repo": match.group(2),
                "branch": "main",
                "file_path": None,
            }
        raise ValueError(f"Invalid GitHub URL: {url}")

    def get_file_content(self, owner: str, repo: str, branch: str, file_path: str) -> str:
        raw_url = f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{file_path}"
        response = self.session.get(raw_url, timeout=30)
        response.raise_for_status()
        return response.text

    def get_repo_files(self, owner: str, repo: str, branch: str = "main", max_files: int = 10) -> list[dict[str, Any]]:
        api_url = f"https://api.github.com/repos/{owner}/{repo}/git/trees/{branch}?recursive=1"
        response = self.session.get(api_url, timeout=30)
        response.raise_for_status()
        data = response.json()
        files: list[dict[str, Any]] = []
        for item in data.get("tree", []):
            if item.get("type") == "blob" and self._is_code_file(item.get("path", "")):
                files.append({"path": item["path"], "size": item.get("size", 0), "sha": item.get("sha", "")})
                if len(files) >= max_files:
                    break
        return files

    def _is_code_file(self, file_path: str) -> bool:
        code_extensions = {
            ".py", ".js", ".ts", ".tsx", ".java", ".go", ".rs", ".php", ".rb", ".kt", ".swift", ".sql", ".json", ".yaml", ".yml", ".md",
        }
        return any(file_path.lower().endswith(ext) for ext in code_extensions)
