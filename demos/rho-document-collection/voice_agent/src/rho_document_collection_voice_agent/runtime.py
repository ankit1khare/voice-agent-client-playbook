"""LiveKit session construction for the Rho document collection demo."""

from dataclasses import dataclass

from livekit.agents import AgentSession, TurnHandlingOptions, inference, room_io
from livekit.agents.voice import SpeechHandle
from livekit.plugins import ai_coustics

from rho_document_collection_voice_agent.settings import Settings

VAD_ACTIVATION_THRESHOLD = 0.6
VAD_MIN_SPEECH_DURATION_SECONDS = 0.1
VAD_MIN_SILENCE_DURATION_SECONDS = 0.35
ENDPOINTING_MIN_DELAY_SECONDS = 0.5
ENDPOINTING_MAX_DELAY_SECONDS = 3.0
INTERRUPTION_MIN_DURATION_SECONDS = 0.3
INTERRUPTION_MIN_WORDS = 0


@dataclass(frozen=True)
class SessionModelConfig:
    """Model identifiers used by the LiveKit voice session."""

    stt_model: str
    stt_language: str
    llm_model: str
    tts_model: str
    tts_voice: str
    tts_language: str


def build_session_model_config(settings: Settings) -> SessionModelConfig:
    """Build a testable model configuration from runtime settings."""
    return SessionModelConfig(
        stt_model=settings.stt_model,
        stt_language=settings.stt_language,
        llm_model=settings.llm_model,
        tts_model=settings.tts_model,
        tts_voice=settings.tts_voice,
        tts_language=settings.tts_language,
    )


def build_turn_handling_options() -> TurnHandlingOptions:
    """Build turn handling tuned for natural phone conversation."""
    return TurnHandlingOptions(
        turn_detection="stt",
        endpointing={
            "mode": "fixed",
            "min_delay": ENDPOINTING_MIN_DELAY_SECONDS,
            "max_delay": ENDPOINTING_MAX_DELAY_SECONDS,
        },
        interruption={
            "mode": "vad",
            "min_duration": INTERRUPTION_MIN_DURATION_SECONDS,
            "min_words": INTERRUPTION_MIN_WORDS,
            "resume_false_interruption": False,
            "false_interruption_timeout": None,
        },
        preemptive_generation={"preemptive_tts": False},
    )


def build_room_options() -> room_io.RoomOptions:
    """Build room options with voice-focused audio enhancement."""
    return room_io.RoomOptions(
        audio_input=room_io.AudioInputOptions(
            noise_cancellation=ai_coustics.audio_enhancement(
                model=ai_coustics.EnhancerModel.QUAIL_VF_L,
            ),
            pre_connect_audio=False,
        ),
    )


def create_agent_session(settings: Settings) -> AgentSession:
    """Create the LiveKit STT, LLM, and TTS session."""
    model_config = build_session_model_config(settings)

    return AgentSession(
        vad=inference.VAD(
            model="silero",
            activation_threshold=VAD_ACTIVATION_THRESHOLD,
            min_speech_duration=VAD_MIN_SPEECH_DURATION_SECONDS,
            min_silence_duration=VAD_MIN_SILENCE_DURATION_SECONDS,
        ),
        stt=inference.STT(
            model=model_config.stt_model,
            language=model_config.stt_language,
        ),
        llm=inference.LLM(model=model_config.llm_model),
        tts=inference.TTS(
            model=model_config.tts_model,
            voice=model_config.tts_voice,
            language=model_config.tts_language,
        ),
        turn_handling=build_turn_handling_options(),
    )


async def play_initial_disclosure(
    session: AgentSession,
    disclosure: str,
) -> SpeechHandle:
    """Speak the exact disclosure without passing it through the LLM."""
    speech = session.say(disclosure, allow_interruptions=False)
    await speech
    return speech
