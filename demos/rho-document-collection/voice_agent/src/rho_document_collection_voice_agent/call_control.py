"""Shared call-ending behavior for the Rho demo agents."""

import asyncio

from livekit.agents import RunContext, function_tool, get_job_context
from livekit.agents.llm import ToolFlag, Toolset
from livekit.agents.voice.events import CloseEvent

INBOUND_FINAL_GOODBYE = "Thank you for calling Rho. Have a great day."
OUTBOUND_FINAL_GOODBYE = "Thanks, goodbye for now. Have a great day."
GOODBYE_DISCONNECT_GRACE_SECONDS = 1.0

END_CALL_DESCRIPTION = """
Finish the current call after the caller clearly indicates they are done.

Call when the caller says goodbye, says that is all, confirms they need no more
help, or asks to end the call. Also call after the document workflow is complete
and the caller confirms there are no more questions.

Do not call when the caller asks to pause, hold, or transfer, or when their intent
is unclear. Never merely say goodbye without using this tool.
"""


class GracefulEndCallTool(Toolset):
    """End a call only after the final spoken audio has cleared the phone line."""

    def __init__(self, final_goodbye: str = INBOUND_FINAL_GOODBYE) -> None:
        super().__init__(id="end_call")
        self._final_goodbye = final_goodbye

    @function_tool(
        name="end_call",
        description=END_CALL_DESCRIPTION,
        flags=ToolFlag.IGNORE_ON_ENTER,
    )
    async def end_call(self, ctx: RunContext) -> None:
        """Speak the final goodbye, allow carrier playout, then end the call."""
        await self._speak_goodbye_and_shutdown(ctx)

    async def _speak_goodbye_and_shutdown(self, ctx: RunContext) -> None:
        ctx.disallow_interruptions()
        ctx.session.once("close", self._on_session_close)
        await ctx.wait_for_playout()
        goodbye = ctx.session.say(self._final_goodbye, allow_interruptions=False)
        await goodbye.wait_for_playout()
        await asyncio.sleep(GOODBYE_DISCONNECT_GRACE_SECONDS)
        ctx.session.shutdown()

    def _on_session_close(self, ev: CloseEvent) -> None:
        job_ctx = get_job_context()

        async def delete_call_room() -> None:
            await job_ctx.delete_room()

        job_ctx.add_shutdown_callback(delete_call_room)
        job_ctx.shutdown(reason=ev.reason.value)


def build_end_call_tool(
    final_goodbye: str = INBOUND_FINAL_GOODBYE,
) -> GracefulEndCallTool:
    """Return the Rho call-ending tool."""
    return GracefulEndCallTool(final_goodbye)
