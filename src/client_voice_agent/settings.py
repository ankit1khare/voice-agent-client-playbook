"""Environment-backed settings for the reference agent."""

import os
from dataclasses import dataclass

from dotenv import load_dotenv

DEFAULT_AGENT_NAME = "client-document-demo"
DEFAULT_STT_MODEL = "deepgram/flux-general"
DEFAULT_STT_LANGUAGE = "en"
DEFAULT_LLM_MODEL = "google/gemma-4-31b-it"
DEFAULT_TTS_MODEL = "rime/coda"
DEFAULT_TTS_VOICE = "wawona"
DEFAULT_TTS_LANGUAGE = "en"


@dataclass(frozen=True)
class Settings:
    """Voice pipeline settings loaded from the environment."""

    agent_name: str = DEFAULT_AGENT_NAME
    stt_model: str = DEFAULT_STT_MODEL
    stt_language: str = DEFAULT_STT_LANGUAGE
    llm_model: str = DEFAULT_LLM_MODEL
    tts_model: str = DEFAULT_TTS_MODEL
    tts_voice: str = DEFAULT_TTS_VOICE
    tts_language: str = DEFAULT_TTS_LANGUAGE


def load_settings() -> Settings:
    """Load local dotenv files, then fall back to demo-safe defaults."""
    load_dotenv(dotenv_path=".env.local")
    load_dotenv(dotenv_path=".env", override=False)

    return Settings(
        agent_name=_env("LIVEKIT_AGENT_NAME", DEFAULT_AGENT_NAME),
        stt_model=_env("LIVEKIT_INFERENCE_STT_MODEL", DEFAULT_STT_MODEL),
        stt_language=_env("LIVEKIT_INFERENCE_STT_LANGUAGE", DEFAULT_STT_LANGUAGE),
        llm_model=_env("LIVEKIT_INFERENCE_LLM_MODEL", DEFAULT_LLM_MODEL),
        tts_model=_env("LIVEKIT_INFERENCE_TTS_MODEL", DEFAULT_TTS_MODEL),
        tts_voice=_env("RIME_CODA_SPEAKER", DEFAULT_TTS_VOICE),
        tts_language=_env("LIVEKIT_INFERENCE_TTS_LANGUAGE", DEFAULT_TTS_LANGUAGE),
    )


def _env(name: str, default: str) -> str:
    value = os.getenv(name)
    if value is None or value.strip() == "":
        return default
    return value.strip()
