"""Tests for the ordered goodbye and disconnect sequence."""

import asyncio
from typing import cast

import pytest
from livekit.agents import RunContext

from rho_document_collection_voice_agent.call_control import (
    GOODBYE_DISCONNECT_GRACE_SECONDS,
    OUTBOUND_FINAL_GOODBYE,
    GracefulEndCallTool,
)


class FakeSpeechHandle:
    def __init__(self, events: list[str]) -> None:
        self.events = events

    async def wait_for_playout(self) -> None:
        self.events.append("goodbye_played")


class FakeSession:
    def __init__(self, events: list[str]) -> None:
        self.events = events

    def once(self, event: str, callback: object) -> None:
        del callback
        self.events.append(f"listen:{event}")

    def say(self, text: str, *, allow_interruptions: bool) -> FakeSpeechHandle:
        self.events.append(f"say:{text}:{allow_interruptions}")
        return FakeSpeechHandle(self.events)

    def shutdown(self) -> None:
        self.events.append("shutdown")


class FakeRunContext:
    def __init__(self) -> None:
        self.events: list[str] = []
        self.session = FakeSession(self.events)

    def disallow_interruptions(self) -> None:
        self.events.append("disallow_interruptions")

    async def wait_for_playout(self) -> None:
        self.events.append("pre_tool_speech_played")


def test_goodbye_plays_before_carrier_grace_and_shutdown(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ctx = FakeRunContext()

    async def record_sleep(delay: float) -> None:
        ctx.events.append(f"sleep:{delay}")

    monkeypatch.setattr(asyncio, "sleep", record_sleep)
    asyncio.run(
        GracefulEndCallTool()._speak_goodbye_and_shutdown(cast("RunContext", ctx))
    )

    assert ctx.events == [
        "disallow_interruptions",
        "listen:close",
        "pre_tool_speech_played",
        "say:Thank you for calling Rho. Have a great day.:False",
        "goodbye_played",
        f"sleep:{GOODBYE_DISCONNECT_GRACE_SECONDS}",
        "shutdown",
    ]


def test_outbound_tool_uses_outbound_closing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ctx = FakeRunContext()

    async def skip_sleep(delay: float) -> None:
        del delay

    monkeypatch.setattr(asyncio, "sleep", skip_sleep)
    asyncio.run(
        GracefulEndCallTool(OUTBOUND_FINAL_GOODBYE)._speak_goodbye_and_shutdown(
            cast("RunContext", ctx)
        )
    )

    assert "say:Thanks, goodbye for now. Have a great day.:False" in ctx.events
