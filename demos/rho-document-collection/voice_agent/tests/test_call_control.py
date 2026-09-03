"""Tests for the ordered goodbye and disconnect sequence."""

import asyncio
from typing import cast

import pytest
from livekit.agents import RunContext

from rho_document_collection_voice_agent.call_control import (
    GOODBYE_DISCONNECT_GRACE_SECONDS,
    GracefulEndCallTool,
)


class FakeSession:
    def __init__(self) -> None:
        self.shutdown_called = False

    def shutdown(self) -> None:
        self.shutdown_called = True


class FakeRunContext:
    def __init__(self) -> None:
        self.session = FakeSession()


def test_disconnect_waits_for_carrier_grace(monkeypatch: pytest.MonkeyPatch) -> None:
    delays: list[float] = []

    async def record_sleep(delay: float) -> None:
        delays.append(delay)

    monkeypatch.setattr(asyncio, "sleep", record_sleep)
    ctx = FakeRunContext()

    asyncio.run(GracefulEndCallTool()._shutdown_after_grace(cast("RunContext", ctx)))

    assert delays == [GOODBYE_DISCONNECT_GRACE_SECONDS]
    assert ctx.session.shutdown_called is True
