"""Coordination backend factory — Band kept, swappable to NullBackend."""

from __future__ import annotations

from code_council.tribunal.band_adapter import BandAdapter
from code_council.tribunal.coordination import NullBackend, get_coordination_backend


def test_null_backend_selected(monkeypatch):
    monkeypatch.setenv("COORDINATION_BACKEND", "null")
    backend = get_coordination_backend()
    assert isinstance(backend, NullBackend)
    assert backend.enabled is False
    assert backend.mode == "demo"


def test_band_backend_is_default(monkeypatch):
    monkeypatch.delenv("COORDINATION_BACKEND", raising=False)
    monkeypatch.setenv("BAND_ENABLED", "false")
    backend = get_coordination_backend()
    assert isinstance(backend, BandAdapter)
