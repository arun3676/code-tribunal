"""Coordination layer seam.

The runner deliberates the Tribunal and *mirrors* the deliberation into an
external "room" (messages, @mentions, structured events, mid-trial recruitment).
Today that room is **Band**. To keep the runner and agents independent of the
coordination provider, the runner only ever talks to a :class:`CoordinationBackend`
obtained from :func:`get_coordination_backend` — never to a concrete adapter.

Swapping coordination later (see local docs/internal/band-migration.md) is a
one-line change: implement the Protocol and register it in the factory. Nothing
in ``runner.py``, the agents, ``protocol.py``, or the web/CLI/MCP faces changes.
"""

from __future__ import annotations

import logging
import os
from typing import Any, Protocol, runtime_checkable

logger = logging.getLogger("code_council.tribunal.coordination")


@runtime_checkable
class CoordinationBackend(Protocol):
    """The surface the runner uses on whatever backend is active.

    ``BandAdapter`` (band_adapter.py) satisfies this structurally; so does
    :class:`NullBackend`. Any future backend just implements these members.
    """

    enabled: bool
    strict: bool

    @property
    def mode(self) -> str:  # "live" | "demo"
        ...

    def band_meta(self, *, mirrored: bool = True) -> dict[str, Any]:
        ...

    async def create_room(self, title: str) -> str | None:
        ...

    async def add_participant(self, room_id: str | None, agent: str) -> None:
        ...

    async def send_message(
        self,
        room_id: str | None,
        from_agent: str,
        text: str,
        *,
        targets: list[str] | None = None,
    ) -> None:
        ...

    async def post_event(
        self,
        room_id: str | None,
        agent: str,
        kind: str,
        payload: dict,
        *,
        text: str = "",
    ) -> None:
        ...


class NullBackend:
    """No-op coordination backend — the Tribunal still streams locally.

    The default once Band is retired (set ``COORDINATION_BACKEND=null``). Every
    method is inert, ``enabled`` is False, so the runner's mirror guard
    (``if mirror and band.enabled and room_id``) short-circuits every call.
    """

    def __init__(self) -> None:
        self.enabled = False
        self.strict = False

    @property
    def mode(self) -> str:
        return "demo"

    def band_meta(self, *, mirrored: bool = True) -> dict[str, Any]:
        return {"enabled": False, "strict": False, "chat_id": None, "mirrored": False, "mode": "demo"}

    async def create_room(self, title: str) -> str | None:
        return None

    async def add_participant(self, room_id: str | None, agent: str) -> None:
        return None

    async def send_message(
        self,
        room_id: str | None,
        from_agent: str,
        text: str,
        *,
        targets: list[str] | None = None,
    ) -> None:
        return None

    async def post_event(
        self,
        room_id: str | None,
        agent: str,
        kind: str,
        payload: dict,
        *,
        text: str = "",
    ) -> None:
        return None


def get_coordination_backend() -> CoordinationBackend:
    """Return the active coordination backend, selected by ``COORDINATION_BACKEND``.

    ``band`` (default) → live Band mirroring (BandAdapter, which itself no-ops
    when ``BAND_ENABLED`` is false). ``null``/``none``/``off`` → :class:`NullBackend`.
    """

    choice = os.getenv("COORDINATION_BACKEND", "band").strip().lower()
    if choice in ("null", "none", "off"):
        return NullBackend()
    if choice != "band":
        logger.warning("Unknown COORDINATION_BACKEND=%r; defaulting to band", choice)
    from .band_adapter import BandAdapter

    return BandAdapter()
