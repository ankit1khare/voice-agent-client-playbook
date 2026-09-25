"""Tests for Nudge voice-agent settings."""

from pathlib import Path

from pytest import MonkeyPatch

from nudge_voice_agent.settings import (
    DEFAULT_AGENT_NAME,
    DEFAULT_LLM_MODEL,
    DEFAULT_STT_MODEL,
    DEFAULT_TTS_VOICE,
    load_settings,
)


def test_load_settings_uses_nudge_and_coda_defaults(
    monkeypatch: MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.chdir(tmp_path)
    _clear_settings_env(monkeypatch)

    settings = load_settings()

    assert settings.agent_name == DEFAULT_AGENT_NAME
    assert settings.stt_model == DEFAULT_STT_MODEL
    assert settings.llm_model == DEFAULT_LLM_MODEL
    assert settings.tts_voice == DEFAULT_TTS_VOICE


def test_load_settings_reads_dotenv_and_ignores_blank_values(
    monkeypatch: MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.chdir(tmp_path)
    _clear_settings_env(monkeypatch)
    tmp_path.joinpath(".env").write_text(
        "LIVEKIT_AGENT_NAME=custom-nudge-demo\n"
        "LIVEKIT_INFERENCE_STT_MODEL=deepgram/nova-3\n"
        "LIVEKIT_INFERENCE_LLM_MODEL=\n"
        "RIME_CODA_LANGUAGE=es\n"
        "RIME_CODA_SPEAKER=astra\n",
        encoding="utf-8",
    )

    settings = load_settings()

    assert settings.agent_name == "custom-nudge-demo"
    assert settings.stt_model == "deepgram/nova-3"
    assert settings.llm_model == DEFAULT_LLM_MODEL
    assert settings.tts_language == "es"
    assert settings.tts_voice == "astra"


def _clear_settings_env(monkeypatch: MonkeyPatch) -> None:
    for name in (
        "LIVEKIT_AGENT_NAME",
        "LIVEKIT_INFERENCE_STT_MODEL",
        "LIVEKIT_INFERENCE_STT_LANGUAGE",
        "LIVEKIT_INFERENCE_LLM_MODEL",
        "RIME_CODA_LANGUAGE",
        "RIME_CODA_SPEAKER",
    ):
        monkeypatch.delenv(name, raising=False)
