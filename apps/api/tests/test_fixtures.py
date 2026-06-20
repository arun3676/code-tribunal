"""The 4 demo fixtures must stay byte-stable on the deterministic path."""

from __future__ import annotations

import asyncio

import pytest

from code_council.tribunal.fixtures import get_fixture
from code_council.tribunal.headless import run_trial_collect

EXPECTED = {
    "auth-login-001": "BLOCK",
    "health-check-002": "APPROVE",
    "payment-refund-003": "BLOCK",
    "user-profile-004": "APPROVE",
}


@pytest.mark.parametrize("fixture_id,merge", EXPECTED.items())
def test_fixture_verdict(fixture_id, merge):
    docket = get_fixture(fixture_id)
    assert docket is not None
    assert docket.engine == "deterministic"
    result = asyncio.run(run_trial_collect(docket))
    assert result["verdict"]["merge_decision"] == merge
