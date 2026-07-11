"""Tests for POST /waitlist — Resend-backed invite registrations."""

from __future__ import annotations

import httpx
import pytest
import respx
from fastapi.testclient import TestClient

from code_council.server import app

client = TestClient(app)

RESEND_URL = "https://api.resend.com/audiences/aud_123/contacts"


def _configure_resend(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RESEND_API_KEY", "re_test_key")
    monkeypatch.setenv("RESEND_AUDIENCE_ID", "aud_123")


def test_waitlist_rejects_invalid_email() -> None:
    response = client.post("/waitlist", json={"email": "not-an-email"})
    assert response.status_code == 422


def test_waitlist_rejects_missing_at_domain() -> None:
    response = client.post("/waitlist", json={"email": "user@nodot"})
    assert response.status_code == 422


def test_waitlist_logs_when_resend_unconfigured() -> None:
    # conftest clears provider env; RESEND_* are unset here.
    response = client.post("/waitlist", json={"email": "Early.Bird@example.com"})
    assert response.status_code == 200
    assert response.json() == {"ok": True, "stored": "log"}


@respx.mock
def test_waitlist_stores_contact_in_resend(monkeypatch: pytest.MonkeyPatch) -> None:
    _configure_resend(monkeypatch)
    route = respx.post(RESEND_URL).mock(
        return_value=httpx.Response(201, json={"id": "contact_1"})
    )
    response = client.post("/waitlist", json={"email": "USER@Example.com"})
    assert response.status_code == 200
    assert response.json() == {"ok": True, "stored": "resend"}
    sent = route.calls.last.request
    assert b'"email": "user@example.com"' in sent.content or b'"email":"user@example.com"' in sent.content
    assert sent.headers["authorization"] == "Bearer re_test_key"


@respx.mock
def test_waitlist_duplicate_contact_is_success(monkeypatch: pytest.MonkeyPatch) -> None:
    _configure_resend(monkeypatch)
    respx.post(RESEND_URL).mock(return_value=httpx.Response(409, json={"message": "exists"}))
    response = client.post("/waitlist", json={"email": "user@example.com"})
    assert response.status_code == 200
    assert response.json()["ok"] is True


@respx.mock
def test_waitlist_resend_failure_returns_502(monkeypatch: pytest.MonkeyPatch) -> None:
    _configure_resend(monkeypatch)
    respx.post(RESEND_URL).mock(return_value=httpx.Response(500, json={"message": "boom"}))
    response = client.post("/waitlist", json={"email": "user@example.com"})
    assert response.status_code == 502
