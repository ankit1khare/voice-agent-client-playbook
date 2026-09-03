"""Private session-end transcript logging for the Rho demo."""

import logging
from typing import Any

from livekit.agents import JobContext

SESSION_TRANSCRIPT_LOG_EVENT = "session_end_transcript"
SESSION_TRANSCRIPT_ERROR_EVENT = "session_end_transcript_failed"

logger = logging.getLogger("rho-session-report")


def build_session_transcript(ctx: JobContext) -> dict[str, Any]:
    """Build a searchable transcript record from LiveKit's finalized history."""
    report = ctx.make_session_report()
    history = report.chat_history.to_dict(
        exclude_timestamp=False,
        exclude_function_call=False,
        exclude_metrics=True,
        exclude_config_update=True,
        strip_markup=True,
    )
    return {
        "job_id": report.job_id,
        "room_id": report.room_id,
        "room": report.room,
        "ended_at": report.timestamp,
        "chat_history": history,
    }


async def log_session_transcript(ctx: JobContext) -> None:
    """Write the finalized conversation transcript to private worker logs."""
    try:
        transcript = build_session_transcript(ctx)
    except Exception:
        logger.exception(SESSION_TRANSCRIPT_ERROR_EVENT)
        return

    logger.info(
        SESSION_TRANSCRIPT_LOG_EVENT,
        extra={"session_transcript": transcript},
    )
