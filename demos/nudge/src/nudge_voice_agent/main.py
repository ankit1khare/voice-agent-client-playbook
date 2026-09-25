"""LiveKit worker entrypoint for the Nudge document collection demo."""

from livekit import agents
from livekit.agents import AgentServer

from nudge_voice_agent.assistant import (
    INITIAL_DISCLOSURE,
    NudgeDocumentCollectionAssistant,
)
from nudge_voice_agent.outbound import is_outbound_job_metadata
from nudge_voice_agent.outbound_main import (
    nudge_outbound_document_collection_demo,
)
from nudge_voice_agent.runtime import (
    build_room_options,
    create_agent_session,
    play_initial_disclosure,
)
from nudge_voice_agent.session_reporting import (
    log_session_transcript,
    register_follow_up_previews,
)
from nudge_voice_agent.settings import load_settings

settings = load_settings()
server = AgentServer()


@server.rtc_session(
    agent_name=settings.agent_name,
    on_session_end=log_session_transcript,
)
async def nudge_document_collection_demo(ctx: agents.JobContext) -> None:
    """Route explicit outbound jobs or handle an inbound call."""
    if is_outbound_job_metadata(ctx.job.metadata):
        await nudge_outbound_document_collection_demo(ctx)
        return

    session = create_agent_session(settings)
    assistant = NudgeDocumentCollectionAssistant()
    register_follow_up_previews(ctx.job.id, assistant.follow_up_tool.previews)

    await session.start(
        room=ctx.room,
        agent=assistant,
        room_options=build_room_options(),
    )
    await play_initial_disclosure(session, INITIAL_DISCLOSURE)


def main() -> None:
    """Run the LiveKit agent server CLI."""
    agents.cli.run_app(server)


if __name__ == "__main__":
    main()
