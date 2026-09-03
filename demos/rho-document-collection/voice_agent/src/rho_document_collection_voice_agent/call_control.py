"""Shared call-ending behavior for the Rho demo agents."""

from livekit.agents.beta.tools import EndCallTool

FINAL_GOODBYE = "Thanks for calling Rho. Goodbye."


def build_end_call_tool() -> EndCallTool:
    """Return a tool that speaks the final line, then disconnects the call."""
    return EndCallTool(
        delete_room=True,
        ignore_on_enter=True,
        end_instructions=f'Say exactly "{FINAL_GOODBYE}" and nothing else.',
        extra_description=(
            "Use this when the caller says goodbye, says that is all, confirms "
            "they need no more help, or asks to end the call. Also use it after "
            "the document workflow is complete and the caller confirms there are "
            "no more questions. Never merely say goodbye without using this tool."
        ),
    )
