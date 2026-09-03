"""Tests for environment-backed agent settings."""

from pathlib import Path

from pytest import MonkeyPatch

from client_voice_agent.settings import (
    DEFAULT_AGENT_NAME,
    DEFAULT_LLM_MODEL,
    DEFAULT_STT_MODEL,
    DEFAULT_TTS_MODEL,
    DEFAULT_TTS_VOICE,
    load_settings,
)


def test_settings_use_documented_defaults(
    monkeypatch: MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.chdir(tmp_path)
    _clear_settings_env(monkeypatch)

    settings = load_settings()

    assert settings.agent_name == DEFAULT_AGENT_NAME
    assert settings.stt_model == DEFAULT_STT_MODEL
    assert settings.llm_model == DEFAULT_LLM_MODEL
    assert settings.tts_model == DEFAULT_TTS_MODEL
    assert settings.tts_voice == DEFAULT_TTS_VOICE


def test_settings_read_dotenv_and_ignore_blank_values(
    monkeypatch: MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.chdir(tmp_path)
    _clear_settings_env(monkeypatch)
    tmp_path.joinpath(".env").write_text(
        "LIVEKIT_AGENT_NAME=custom-client-demo\n"
        "LIVEKIT_INFERENCE_STT_MODEL=deepgram/nova-3\n"
        "LIVEKIT_INFERENCE_LLM_MODEL=\n"
        "LIVEKIT_INFERENCE_TTS_MODEL=rime/coda\n"
        "RIME_CODA_SPEAKER=astra\n",
        encoding="utf-8",
    )

    settings = load_settings()

    assert settings.agent_name == "custom-client-demo"
    assert settings.stt_model == "deepgram/nova-3"
    assert settings.llm_model == DEFAULT_LLM_MODEL
    assert settings.tts_model == "rime/coda"
    assert settings.tts_voice == "astra"


def _clear_settings_env(monkeypatch: MonkeyPatch) -> None:
    for name in (
        "LIVEKIT_AGENT_NAME",
        "LIVEKIT_INFERENCE_STT_MODEL",
        "LIVEKIT_INFERENCE_STT_LANGUAGE",
        "LIVEKIT_INFERENCE_LLM_MODEL",
        "LIVEKIT_INFERENCE_TTS_MODEL",
        "LIVEKIT_INFERENCE_TTS_LANGUAGE",
        "RIME_CODA_SPEAKER",
    ):
        monkeypatch.delenv(name, raising=False)
