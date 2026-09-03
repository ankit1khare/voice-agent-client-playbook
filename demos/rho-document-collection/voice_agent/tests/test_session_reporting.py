"""Tests for finalized session transcript logging."""

import asyncio
import logging
from typing import cast

from _pytest.logging import LogCaptureFixture
from livekit.agents import JobContext

from rho_document_collection_voice_agent.session_reporting import (
    SESSION_TRANSCRIPT_ERROR_EVENT,
    SESSION_TRANSCRIPT_LOG_EVENT,
    log_session_transcript,
)


class FakeChatHistory:
    def __init__(self) -> None:
        self.options: dict[str, object] = {}

    def to_dict(self, **kwargs: object) -> dict[str, list[dict[str, object]]]:
        self.options = kwargs
        return {
            "items": [
                {
                    "type": "message",
                    "role": "user",
                    "content": ["That is all."],
                    "created_at": 1_788_468_000.0,
                },
                {
                    "type": "message",
                    "role": "assistant",
                    "content": ["Thank you for calling Rho. Have a great day."],
                    "created_at": 1_788_468_001.0,
                },
            ]
        }


class FakeReport:
    def __init__(self, history: FakeChatHistory) -> None:
        self.job_id = "AJ_test"
        self.room_id = "RM_test"
        self.room = "rho-test-room"
        self.timestamp = 1_788_468_002.0
        self.chat_history = history


class FakeJobContext:
    def __init__(self, history: FakeChatHistory) -> None:
        self.report = FakeReport(history)

    def make_session_report(self) -> FakeReport:
        return self.report


class FailingJobContext:
    def make_session_report(self) -> None:
        raise RuntimeError("report unavailable")


def test_session_end_logs_complete_timestamped_history(
    caplog: LogCaptureFixture,
) -> None:
    history = FakeChatHistory()
    ctx = FakeJobContext(history)

    with caplog.at_level(logging.INFO, logger="rho-session-report"):
        asyncio.run(log_session_transcript(cast("JobContext", ctx)))

    record = next(
        record
        for record in caplog.records
        if record.message == SESSION_TRANSCRIPT_LOG_EVENT
    )
    transcript = record.__dict__["session_transcript"]
    assert transcript == {
        "job_id": "AJ_test",
        "room_id": "RM_test",
        "room": "rho-test-room",
        "ended_at": 1_788_468_002.0,
        "chat_history": {
            "items": [
                {
                    "type": "message",
                    "role": "user",
                    "content": ["That is all."],
                    "created_at": 1_788_468_000.0,
                },
                {
                    "type": "message",
                    "role": "assistant",
                    "content": ["Thank you for calling Rho. Have a great day."],
                    "created_at": 1_788_468_001.0,
                },
            ]
        },
    }
    assert history.options == {
        "exclude_timestamp": False,
        "exclude_function_call": False,
        "exclude_metrics": True,
        "exclude_config_update": True,
        "strip_markup": True,
    }


def test_session_report_failure_does_not_break_shutdown(
    caplog: LogCaptureFixture,
) -> None:
    with caplog.at_level(logging.ERROR, logger="rho-session-report"):
        asyncio.run(log_session_transcript(cast("JobContext", FailingJobContext())))

    assert any(
        record.message == SESSION_TRANSCRIPT_ERROR_EVENT for record in caplog.records
    )
