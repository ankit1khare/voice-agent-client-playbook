"""Tests for LiveKit model and turn-handling configuration."""

import asyncio
from collections.abc import Generator
from typing import cast

from livekit.agents import AgentSession

from client_voice_agent.assistant import INITIAL_DISCLOSURE
from client_voice_agent.runtime import (
    ENDPOINTING_MAX_DELAY_SECONDS,
    ENDPOINTING_MIN_DELAY_SECONDS,
    INTERRUPTION_MIN_DURATION_SECONDS,
    INTERRUPTION_MIN_WORDS,
    build_session_model_config,
    build_turn_handling_options,
    play_initial_disclosure,
)
from client_voice_agent.settings import Settings


class FakeSpeechHandle:
    def __init__(self) -> None:
        self.waited_for_playout = False

    async def wait_for_playout(self) -> None:
        self.waited_for_playout = True

    def __await__(self) -> Generator[object, None, None]:
        return self.wait_for_playout().__await__()


class FakeAgentSession:
    def __init__(self) -> None:
        self.speech_handle = FakeSpeechHandle()
        self.say_args: tuple[str, ...] | None = None
        self.say_kwargs: dict[str, object] | None = None

    def say(self, *args: str, **kwargs: object) -> FakeSpeechHandle:
        self.say_args = args
        self.say_kwargs = kwargs
        return self.speech_handle


def test_model_config_uses_livekit_inference_and_rime() -> None:
    config = build_session_model_config(Settings())

    assert config.stt_model == "deepgram/flux-general"
    assert config.llm_model == "google/gemma-4-31b-it"
    assert config.tts_model == "rime/coda"
    assert config.tts_voice == "wawona"


def test_turn_handling_is_tuned_for_conversation() -> None:
    options = build_turn_handling_options()

    assert options["turn_detection"] == "stt"
    assert options["endpointing"] == {
        "mode": "fixed",
        "min_delay": ENDPOINTING_MIN_DELAY_SECONDS,
        "max_delay": ENDPOINTING_MAX_DELAY_SECONDS,
    }
    assert options["interruption"] == {
        "mode": "adaptive",
        "min_duration": INTERRUPTION_MIN_DURATION_SECONDS,
        "min_words": INTERRUPTION_MIN_WORDS,
    }


def test_disclosure_uses_exact_noninterruptible_speech() -> None:
    session = FakeAgentSession()

    speech_handle = cast(
        "FakeSpeechHandle",
        asyncio.run(
            play_initial_disclosure(
                cast("AgentSession", session),
                INITIAL_DISCLOSURE,
            )
        ),
    )

    assert session.say_args == (INITIAL_DISCLOSURE,)
    assert session.say_kwargs == {"allow_interruptions": False}
    assert speech_handle.waited_for_playout is True
