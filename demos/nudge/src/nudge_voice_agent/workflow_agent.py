"""Keep an unfinished workflow acknowledgment ahead of ordinary replies."""

from collections.abc import AsyncIterable
from dataclasses import replace

from livekit.agents import Agent, ModelSettings, llm
from livekit.agents.types import FlushSentinel

from nudge_voice_agent.workflow import FollowUpPreviewTool


class WorkflowAgent(Agent):
    """Limit the next model action while a required result remains unspoken."""

    follow_up_tool: FollowUpPreviewTool

    async def llm_node(
        self,
        chat_ctx: llm.ChatContext,
        tools: list[llm.Tool],
        model_settings: ModelSettings,
    ) -> AsyncIterable[llm.ChatChunk | str | FlushSentinel]:
        if self.follow_up_tool.has_pending_spoken_result:
            # Both tools complete the pending result. end_call also honors goodbye.
            tools = [
                tool
                for tool in tools
                if tool.id in {"finish_interrupted_result", "end_call"}
            ]
            model_settings = replace(model_settings, tool_choice="required")
        async for chunk in Agent.default.llm_node(
            self, chat_ctx, tools, model_settings
        ):
            yield chunk
