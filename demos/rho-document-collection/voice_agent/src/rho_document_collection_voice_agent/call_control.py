"""Shared call-ending behavior for the Rho demo agents."""

import asyncio

from livekit.agents import RunContext, function_tool, get_job_context
from livekit.agents.llm import ToolFlag, Toolset
from livekit.agents.voice.events import CloseEvent

FINAL_GOODBYE = "Thanks for calling Rho. Goodbye."
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

    def __init__(self) -> None:
        super().__init__(id="end_call")
        self._shutdown_task: asyncio.Task[None] | None = None

    @function_tool(
        name="end_call",
        description=END_CALL_DESCRIPTION,
        flags=ToolFlag.IGNORE_ON_ENTER,
    )
    async def end_call(self, ctx: RunContext) -> str:
        """Speak the final goodbye, allow carrier playout, then end the call."""
        ctx.disallow_interruptions()
        ctx.speech_handle.add_done_callback(
            lambda _: self._schedule_delayed_shutdown(ctx)
        )
        ctx.session.once("close", self._on_session_close)
        return f'Say exactly "{FINAL_GOODBYE}" and nothing else.'

    def _schedule_delayed_shutdown(self, ctx: RunContext) -> None:
        if self._shutdown_task is None:
            self._shutdown_task = asyncio.create_task(self._shutdown_after_grace(ctx))

    async def _shutdown_after_grace(self, ctx: RunContext) -> None:
        await asyncio.sleep(GOODBYE_DISCONNECT_GRACE_SECONDS)
        ctx.session.shutdown()

    def _on_session_close(self, ev: CloseEvent) -> None:
        if self._shutdown_task is not None:
            self._shutdown_task.cancel()
            self._shutdown_task = None

        job_ctx = get_job_context()

        async def delete_call_room() -> None:
            await job_ctx.delete_room()

        job_ctx.add_shutdown_callback(delete_call_room)
        job_ctx.shutdown(reason=ev.reason.value)


def build_end_call_tool() -> GracefulEndCallTool:
    """Return the Rho call-ending tool."""
    return GracefulEndCallTool()
