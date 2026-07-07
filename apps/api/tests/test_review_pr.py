"""Offline unit tests for parse_pr_url — no network calls."""

from __future__ import annotations

import pytest

from code_council.github_webhook import parse_pr_url


@pytest.mark.parametrize(
    "url,expected",
    [
        # Standard https URL
        (
            "https://github.com/owner/repo/pull/42",
            ("owner", "repo", 42),
        ),
        # http (no s)
        (
            "http://github.com/owner/repo/pull/1",
            ("owner", "repo", 1),
        ),
        # Trailing path segment (e.g. /files, /commits)
        (
            "https://github.com/owner/repo/pull/99/files",
            ("owner", "repo", 99),
        ),
        # Fragment (e.g. #discussion_r123)
        (
            "https://github.com/owner/repo/pull/7#discussion_r456789",
            ("owner", "repo", 7),
        ),
        # .git suffix in the URL (rare but valid)
        (
            "https://github.com/owner/repo.git/pull/3",
            ("owner", "repo", 3),
        ),
        # Hyphenated repo and org names
        (
            "https://github.com/my-org/my-repo/pull/100",
            ("my-org", "my-repo", 100),
        ),
        # Dots in repo name
        (
            "https://github.com/owner/my.repo/pull/5",
            ("owner", "my.repo", 5),
        ),
    ],
)
def test_parse_pr_url_valid(url: str, expected: tuple) -> None:
    assert parse_pr_url(url) == expected


@pytest.mark.parametrize(
    "url",
    [
        # Not a PR URL — issues path
        "https://github.com/owner/repo/issues/42",
        # Plain repo homepage
        "https://github.com/owner/repo",
        # Completely unrelated URL
        "https://example.com/pull/1",
        # Missing pull number
        "https://github.com/owner/repo/pull/",
        # Empty string
        "",
    ],
)
def test_parse_pr_url_invalid_raises(url: str) -> None:
    with pytest.raises(ValueError):
        parse_pr_url(url)
