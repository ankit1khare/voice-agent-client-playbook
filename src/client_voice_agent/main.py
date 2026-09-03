"""LiveKit worker entrypoint for the reference agent."""

from livekit import agents
from livekit.agents import AgentServer

from client_voice_agent.assistant import INITIAL_DISCLOSURE, DocumentAssistant
from client_voice_agent.runtime import create_agent_session, play_initial_disclosure
from client_voice_agent.settings import load_settings

settings = load_settings()
server = AgentServer()


@server.rtc_session(agent_name=settings.agent_name)
async def client_document_demo(ctx: agents.JobContext) -> None:
    """Handle an inbound LiveKit room dispatch."""
    session = create_agent_session(settings)

    await session.start(room=ctx.room, agent=DocumentAssistant())
    await play_initial_disclosure(session, INITIAL_DISCLOSURE)


def main() -> None:
    """Run the LiveKit agent server CLI."""
    agents.cli.run_app(server)


if __name__ == "__main__":
    main()
