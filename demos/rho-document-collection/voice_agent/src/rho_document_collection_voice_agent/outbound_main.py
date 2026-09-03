"""LiveKit worker entrypoint for the guarded Rho outbound demo path."""

import asyncio
import logging
import os

from livekit import api
from livekit.agents import AMD, AgentServer, JobContext

from rho_document_collection_voice_agent.outbound import (
    OUTBOUND_AGENT_NAME,
    AMDAction,
    CallOutcome,
    CallResult,
    OutboundCallRequest,
    amd_action_for_category,
    build_sip_participant_request,
    call_outcome_for_sip_status,
)
from rho_document_collection_voice_agent.outbound_assistant import (
    OUTBOUND_DISCLOSURE,
    RhoOutboundDocumentCollectionAssistant,
    voicemail_message,
)
from rho_document_collection_voice_agent.runtime import (
    build_room_options,
    create_agent_session,
)
from rho_document_collection_voice_agent.session_reporting import (
    log_session_transcript,
)
from rho_document_collection_voice_agent.settings import load_settings

logger = logging.getLogger("rho-outbound-demo")
settings = load_settings()
server = AgentServer()

DIAL_TIMEOUT_SECONDS = 45.0
PARTICIPANT_JOIN_TIMEOUT_SECONDS = 10.0


@server.rtc_session(
    agent_name=os.getenv("RHO_OUTBOUND_AGENT_NAME", OUTBOUND_AGENT_NAME).strip(),
    on_session_end=log_session_transcript,
)
async def rho_outbound_document_collection_demo(ctx: JobContext) -> None:
    """Place one explicitly authorized synthetic outbound call."""

    async def delete_call_room() -> None:
        await ctx.delete_room()

    ctx.add_shutdown_callback(delete_call_room)

    try:
        call = OutboundCallRequest.from_metadata(ctx.job.metadata)
    except ValueError as exc:
        _log_result(
            CallResult(
                request_id="unknown",
                outcome=CallOutcome.INVALID_REQUEST,
                detail=str(exc),
            )
        )
        ctx.shutdown("invalid outbound request")
        return

    trunk_id = os.getenv("RHO_OUTBOUND_TRUNK_ID", "").strip()
    if not _outbound_calls_enabled() or trunk_id == "":
        _log_result(
            CallResult(
                request_id=call.request_id,
                outcome=CallOutcome.OUTBOUND_DISABLED,
                detail="outbound calls are disabled or the Rho trunk is missing",
            )
        )
        ctx.shutdown("outbound calls disabled")
        return

    logger.info(
        "starting authorized synthetic outbound call",
        extra={
            "request_id": call.request_id,
            "destination": call.masked_phone_number,
        },
    )

    session = create_agent_session(settings)
    await session.start(
        room=ctx.room,
        agent=RhoOutboundDocumentCollectionAssistant(),
        room_options=build_room_options(),
    )
    if session.room_io is None:
        _log_result(
            CallResult(
                request_id=call.request_id,
                outcome=CallOutcome.DIAL_FAILED,
                detail="session room I/O is unavailable",
            )
        )
        ctx.shutdown("session room I/O unavailable")
        return

    session.room_io.set_participant(call.participant_identity)

    async with AMD(
        session,
        participant_identity=call.participant_identity,
        ivr_detection=False,
    ) as detector:
        try:
            await ctx.api.sip.create_sip_participant(
                build_sip_participant_request(
                    call,
                    room_name=ctx.room.name,
                    trunk_id=trunk_id,
                ),
                timeout=DIAL_TIMEOUT_SECONDS,
            )
        except api.SipCallError as exc:
            _log_result(
                CallResult(
                    request_id=call.request_id,
                    outcome=call_outcome_for_sip_status(exc.sip_status_code),
                    sip_status_code=exc.sip_status_code,
                    detail=exc.sip_status,
                )
            )
            ctx.shutdown("outbound dial failed")
            return
        except TimeoutError:
            _log_result(
                CallResult(
                    request_id=call.request_id,
                    outcome=CallOutcome.NO_ANSWER,
                    detail="dial timed out",
                )
            )
            ctx.shutdown("outbound dial timed out")
            return

        try:
            await asyncio.wait_for(
                ctx.wait_for_participant(identity=call.participant_identity),
                timeout=PARTICIPANT_JOIN_TIMEOUT_SECONDS,
            )
        except TimeoutError:
            _log_result(
                CallResult(
                    request_id=call.request_id,
                    outcome=CallOutcome.PARTICIPANT_MISSING,
                    detail="answered SIP participant did not join the room",
                )
            )
            ctx.shutdown("SIP participant missing")
            return

        disclosure = session.say(OUTBOUND_DISCLOSURE, allow_interruptions=False)
        detection = await detector.execute()
        category = _amd_category_value(detection.category)
        action = amd_action_for_category(
            category,
            allow_ivr_screening=_ivr_screening_enabled(),
        )

        if action is AMDAction.START_CONVERSATION:
            await disclosure.wait_for_playout()
            _log_result(
                CallResult(
                    request_id=call.request_id,
                    outcome=CallOutcome.HUMAN_ANSWERED,
                    amd_category=category,
                )
            )
            return

        await session.interrupt(force=True)

        if action is AMDAction.LEAVE_VOICEMAIL:
            message = session.say(voicemail_message(), allow_interruptions=False)
            await message.wait_for_playout()
            _log_result(
                CallResult(
                    request_id=call.request_id,
                    outcome=CallOutcome.VOICEMAIL_LEFT,
                    amd_category=category,
                )
            )
            ctx.shutdown("voicemail left")
            return

        if action is AMDAction.CONTINUE_IVR_SCREENING:
            screening_message = session.say(
                OUTBOUND_DISCLOSURE,
                allow_interruptions=False,
            )
            await screening_message.wait_for_playout()
            _log_result(
                CallResult(
                    request_id=call.request_id,
                    outcome=CallOutcome.IVR_SCREENING_CONTINUED,
                    amd_category=category,
                )
            )
            return

        if action is AMDAction.END_IVR:
            outcome = CallOutcome.IVR_DETECTED
            reason = "IVR detected"
        else:
            outcome = CallOutcome.MAILBOX_UNAVAILABLE
            reason = "mailbox unavailable"

        _log_result(
            CallResult(
                request_id=call.request_id,
                outcome=outcome,
                amd_category=category,
            )
        )
        ctx.shutdown(reason)


def _outbound_calls_enabled() -> bool:
    return os.getenv("RHO_ENABLE_OUTBOUND_CALLS", "false").strip().lower() == "true"


def _ivr_screening_enabled() -> bool:
    return os.getenv("RHO_ALLOW_IVR_SCREENING", "false").strip().lower() == "true"


def _amd_category_value(category: object) -> str:
    value = getattr(category, "value", category)
    return str(value)


def _log_result(result: CallResult) -> None:
    logger.info("outbound_call_result", extra={"call_result": result.to_log_record()})


def main() -> None:
    """Run the guarded outbound LiveKit agent server."""
    from livekit import agents

    agents.cli.run_app(server)


if __name__ == "__main__":
    main()
