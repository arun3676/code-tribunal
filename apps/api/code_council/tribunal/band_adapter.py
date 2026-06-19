"""Band coordination adapter.

When ``BAND_ENABLED=true`` and ``BAND_API_KEY`` is present, the runner mirrors
the deliberation into a real Band room (messages with @mentions, structured
events, mid-trial participant recruitment). When disabled or unconfigured,
every method is a safe no-op so the SSE trial still streams locally.

Implements the official Band Agent API:
https://docs.band.ai/api/agent-api
"""

from __future__ import annotations

import logging
import os
from typing import Any

import httpx

logger = logging.getLogger("code_council.tribunal.band")

# Band handles (without leading @) — see docs/hackathon/band-agents.md
AGENT_HANDLES: dict[str, str] = {
    "CLERK": "arunn9694/tribunal-clerk",
    "ADVOCATE": "arunn9694/intent-advocate",
    "SURVEYOR": "arunn9694/diff-surveyor",
    "GHOST": "arunn9694/omission-ghost",
    "DRIFT": "arunn9694/scope-drift",
    "WARDEN": "arunn9694/security-warden",
    "ARBITER": "arunn9694/merge-arbiter",
}


class BandError(Exception):
    """Raised when a Band API call fails and ``BAND_STRICT=true``."""

    def __init__(self, operation: str, detail: str) -> None:
        self.operation = operation
        self.detail = detail
        super().__init__(f"Band {operation} failed: {detail}")


class BandAdapter:
    def __init__(self) -> None:
        self.api_key = os.getenv("BAND_API_KEY", "").strip()
        self.base_url = self._normalize_base_url(
            os.getenv("BAND_BASE_URL", "https://app.band.ai/api/v1")
        )
        self.strict = os.getenv("BAND_STRICT", "").lower() == "true"
        self.enabled = os.getenv("BAND_ENABLED", "").lower() == "true" and bool(self.api_key)
        self.chat_id: str | None = None
        self._agent_ids = {
            "CLERK": os.getenv("BAND_CLERK_ID", "").strip(),
            "ADVOCATE": os.getenv("BAND_ADVOCATE_ID", "").strip(),
            "SURVEYOR": os.getenv("BAND_SURVEYOR_ID", "").strip(),
            "GHOST": os.getenv("BAND_GHOST_ID", "").strip(),
            "DRIFT": os.getenv("BAND_DRIFT_ID", "").strip(),
            "WARDEN": os.getenv("BAND_WARDEN_ID", "").strip(),
            "ARBITER": os.getenv("BAND_ARBITER_ID", "").strip(),
        }
        self._agent_keys = {
            agent: os.getenv(f"BAND_{agent}_API_KEY", "").strip() or self.api_key
            for agent in self._agent_ids
        }

    @staticmethod
    def _normalize_base_url(raw: str) -> str:
        url = raw.rstrip("/")
        if url.endswith("/agent"):
            url = url[: -len("/agent")]
        return url

    def _agent_url(self, path: str) -> str:
        return f"{self.base_url}/agent{path}"

    def _headers(self, agent: str = "CLERK") -> dict[str, str]:
        key = self._agent_keys.get(agent, self.api_key)
        return {
            "X-API-Key": key,
            "Content-Type": "application/json",
        }

    @property
    def mode(self) -> str:
        return "live" if self.enabled else "demo"

    def band_meta(self, *, mirrored: bool = True) -> dict[str, Any]:
        return {
            "enabled": self.enabled,
            "strict": self.strict,
            "chat_id": self.chat_id,
            "mirrored": mirrored,
            "mode": self.mode,
        }

    def _handle_failure(self, operation: str, exc: Exception) -> None:
        msg = str(exc)
        logger.warning("BAND FAILURE [%s]: %s", operation, msg)
        if self.strict:
            raise BandError(operation, msg) from exc

    def _maybe_prefix(self, agent: str, text: str) -> str:
        per_agent_key = os.getenv(f"BAND_{agent}_API_KEY", "").strip()
        if per_agent_key:
            return text
        if agent != "CLERK":
            return f"[{agent}] {text}"
        return text

    def _mentions(self, targets: list[str]) -> list[dict[str, str]]:
        mentions: list[dict[str, str]] = []
        for agent in targets:
            agent_id = self._agent_ids.get(agent, "")
            handle = AGENT_HANDLES.get(agent, "")
            if agent_id and handle:
                mentions.append({"id": agent_id, "name": agent, "handle": handle})
        return mentions

    def _inject_mentions(self, text: str, targets: list[str]) -> str:
        if not targets:
            return text
        prefix = " ".join(f"@{AGENT_HANDLES[t]}" for t in targets if t in AGENT_HANDLES)
        if prefix and not any(f"@{AGENT_HANDLES.get(t, '')}" in text for t in targets):
            return f"{prefix} {text}".strip()
        return text

    @staticmethod
    def _extract_id(data: dict[str, Any], *keys: str) -> str | None:
        nested = data.get("data")
        if isinstance(nested, dict):
            inner = nested.get("id")
            if isinstance(inner, str) and inner:
                return inner
        for key in keys:
            val = data.get(key)
            if isinstance(val, str) and val:
                return val
            if isinstance(val, dict):
                inner = val.get("id")
                if isinstance(inner, str) and inner:
                    return inner
        return None

    async def verify_me(self, agent: str = "CLERK") -> dict[str, Any]:
        if not self.enabled:
            return {}
        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.get(
                self._agent_url("/me"),
                headers=self._headers(agent),
            )
            resp.raise_for_status()
            return resp.json()

    async def create_room(self, title: str) -> str | None:
        if not self.enabled:
            return None
        try:
            async with httpx.AsyncClient(timeout=20) as client:
                resp = await client.post(
                    self._agent_url("/chats"),
                    headers=self._headers("CLERK"),
                    json={"chat": {}},
                )
                resp.raise_for_status()
                data = resp.json()
                chat_id = self._extract_id(data, "id", "chat")
                self.chat_id = chat_id
                if chat_id and title:
                    logger.info("Band room created: %s (%s)", chat_id, title)
                return chat_id
        except Exception as exc:  # pragma: no cover - network path
            self._handle_failure("create_room", exc)
            return None

    async def add_participant(self, room_id: str | None, agent: str) -> None:
        if not self.enabled or not room_id:
            return
        participant_id = self._agent_ids.get(agent, "")
        if not participant_id:
            self._handle_failure("add_participant", ValueError(f"missing BAND_{agent}_ID"))
            return
        try:
            async with httpx.AsyncClient(timeout=20) as client:
                resp = await client.post(
                    self._agent_url(f"/chats/{room_id}/participants"),
                    headers=self._headers("CLERK"),
                    json={"participant": {"participant_id": participant_id}},
                )
                resp.raise_for_status()
                logger.info("Band participant added: %s → %s", agent, room_id)
        except Exception as exc:  # pragma: no cover - network path
            self._handle_failure(f"add_participant({agent})", exc)

    async def send_message(
        self,
        room_id: str | None,
        from_agent: str,
        text: str,
        *,
        targets: list[str] | None = None,
    ) -> None:
        """Post a human-legible @mention message into the Band transcript."""

        if not self.enabled or not room_id:
            return
        mention_targets = targets or []
        if not mention_targets:
            mention_targets = ["CLERK"] if from_agent != "CLERK" else ["ADVOCATE"]
        # Band API key must match the posting agent identity.
        api_agent = from_agent if os.getenv(f"BAND_{from_agent}_API_KEY", "").strip() else "CLERK"
        content = self._inject_mentions(self._maybe_prefix(from_agent, text), mention_targets)
        mentions = self._mentions(mention_targets)
        if not mentions:
            self._handle_failure("send_message", ValueError(f"no valid mentions for {from_agent}"))
            return
        try:
            async with httpx.AsyncClient(timeout=20) as client:
                resp = await client.post(
                    self._agent_url(f"/chats/{room_id}/messages"),
                    headers=self._headers(api_agent),
                    json={"message": {"content": content, "mentions": mentions}},
                )
                resp.raise_for_status()
        except Exception as exc:  # pragma: no cover - network path
            self._handle_failure(f"send_message({from_agent})", exc)

    async def post_event(
        self,
        room_id: str | None,
        agent: str,
        kind: str,
        payload: dict,
        *,
        text: str = "",
    ) -> None:
        """Post a structured (machine) event to the Band audit channel."""

        if not self.enabled or not room_id:
            return
        content = text or payload.get("kind", kind) or "tribunal event"
        content = self._maybe_prefix(agent, content)
        metadata = {**payload, "kind": kind, "agent": agent}
        try:
            async with httpx.AsyncClient(timeout=20) as client:
                resp = await client.post(
                    self._agent_url(f"/chats/{room_id}/events"),
                    headers=self._headers(agent),
                    json={
                        "event": {
                            "content": content,
                            "message_type": "tool_result",
                            "metadata": metadata,
                        }
                    },
                )
                resp.raise_for_status()
        except Exception as exc:  # pragma: no cover - network path
            self._handle_failure(f"post_event({agent},{kind})", exc)
