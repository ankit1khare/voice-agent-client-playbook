"""Tests for post-screening outbound routing."""

import asyncio
from collections.abc import Callable
from dataclasses import dataclass
from typing import cast

import pytest
from livekit.agents import AgentSession, JobContext

from rho_document_collection_voice_agent import outbound_main
from rho_document_collection_voice_agent.outbound import (
    CallOutcome,
    CallResult,
    OutboundCallRequest,
)
from rho_document_collection_voice_agent.outbound_assistant import (
    OUTBOUND_DISCLOSURE,
    voicemail_message,
)


@dataclass
class _FakeTranscriptEvent:
    transcript: str
    is_final: bool = True


class _FakeSpeech:
    def __init__(self, session: "_FakeSession", emit_transcripts: bool) -> None:
        self._session = session
        self._emit_transcripts = emit_transcripts

    async def wait_for_playout(self) -> None:
        if self._emit_transcripts:
            self._session.emit_transcripts()


class _FakeSession:
    def __init__(self, transcripts: list[str]) -> None:
        self._transcripts = transcripts
        self._callbacks: list[Callable[[_FakeTranscriptEvent], None]] = []
        self.spoken: list[tuple[str, bool]] = []
        self.interrupts: list[bool] = []

    def on(
        self,
        event: str,
        callback: Callable[[_FakeTranscriptEvent], None],
    ) -> None:
        assert event == "user_input_transcribed"
        self._callbacks.append(callback)

    def off(
        self,
        event: str,
        callback: Callable[[_FakeTranscriptEvent], None],
    ) -> None:
        assert event == "user_input_transcribed"
        self._callbacks.remove(callback)

    def say(self, message: str, *, allow_interruptions: bool) -> _FakeSpeech:
        self.spoken.append((message, allow_interruptions))
        return _FakeSpeech(self, emit_transcripts=len(self.spoken) == 1)

    async def interrupt(self, *, force: bool) -> None:
        self.interrupts.append(force)

    def emit_transcripts(self) -> None:
        for transcript in self._transcripts:
            event = _FakeTranscriptEvent(transcript)
            for callback in list(self._callbacks):
                callback(event)


class _FakeContext:
    def __init__(self) -> None:
        self.shutdown_reasons: list[str] = []

    def shutdown(self, reason: str) -> None:
        self.shutdown_reasons.append(reason)


def _call() -> OutboundCallRequest:
    return OutboundCallRequest(
        phone_number="+14155550123",
        request_id="screening-test",
        demo_only=True,
        authorized_test_call=True,
    )


def test_screening_handoff_plays_only_the_full_voicemail(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = _FakeSession(
        [
            "Thanks.",
            "Please stay on the line.",
            "This person is not available. Leave a message after the tone.",
        ]
    )
    ctx = _FakeContext()
    results: list[CallResult] = []
    monkeypatch.setattr(outbound_main, "_log_result", results.append)

    continue_live = asyncio.run(
        outbound_main._handle_ivr_screening(
            cast("JobContext", ctx),
            cast("AgentSession", session),
            _call(),
        )
    )

    assert continue_live is False
    assert session.spoken == [
        (OUTBOUND_DISCLOSURE, False),
        (voicemail_message(), False),
    ]
    assert session.interrupts == [True]
    assert ctx.shutdown_reasons == ["voicemail left after IVR screening"]
    assert [result.outcome for result in results] == [
        CallOutcome.IVR_SCREENING_CONTINUED,
        CallOutcome.VOICEMAIL_LEFT,
    ]
    assert results[-1].amd_category == "machine-vm-after-ivr"
    assert not session._callbacks


def test_screening_handoff_resumes_the_live_conversation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = _FakeSession(["Thank you.", "Hello, this is Ankit."])
    ctx = _FakeContext()
    results: list[CallResult] = []
    monkeypatch.setattr(outbound_main, "_log_result", results.append)

    continue_live = asyncio.run(
        outbound_main._handle_ivr_screening(
            cast("JobContext", ctx),
            cast("AgentSession", session),
            _call(),
        )
    )

    assert continue_live is True
    assert session.spoken == [
        (OUTBOUND_DISCLOSURE, False),
        (OUTBOUND_DISCLOSURE, False),
    ]
    assert session.interrupts == []
    assert ctx.shutdown_reasons == []
    assert [result.outcome for result in results] == [
        CallOutcome.IVR_SCREENING_CONTINUED,
        CallOutcome.HUMAN_ANSWERED,
    ]
    assert results[-1].amd_category == "human-after-ivr"
    assert not session._callbacks
