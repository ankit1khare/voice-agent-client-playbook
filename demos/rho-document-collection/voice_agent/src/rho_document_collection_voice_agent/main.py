"""LiveKit worker entrypoint for the Rho document collection demo."""

from livekit import agents
from livekit.agents import AgentServer

from rho_document_collection_voice_agent.assistant import (
    INITIAL_DISCLOSURE,
    RhoDocumentCollectionAssistant,
)
from rho_document_collection_voice_agent.outbound import is_outbound_job_metadata
from rho_document_collection_voice_agent.outbound_main import (
    rho_outbound_document_collection_demo,
)
from rho_document_collection_voice_agent.runtime import (
    build_room_options,
    create_agent_session,
    play_initial_disclosure,
)
from rho_document_collection_voice_agent.settings import load_settings

settings = load_settings()
server = AgentServer()


@server.rtc_session(agent_name=settings.agent_name)
async def rho_document_collection_demo(ctx: agents.JobContext) -> None:
    """Route explicit outbound jobs or handle an inbound call."""
    if is_outbound_job_metadata(ctx.job.metadata):
        await rho_outbound_document_collection_demo(ctx)
        return

    session = create_agent_session(settings)

    await session.start(
        room=ctx.room,
        agent=RhoDocumentCollectionAssistant(),
        room_options=build_room_options(),
    )
    await play_initial_disclosure(session, INITIAL_DISCLOSURE)


def main() -> None:
    """Run the LiveKit agent server CLI."""
    agents.cli.run_app(server)


if __name__ == "__main__":
    main()
