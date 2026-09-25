"""Regression for an interrupted result being bypassed by ordinary replies."""

import asyncio
from collections.abc import AsyncIterator
from typing import Any, cast

import pytest
from livekit.agents import Agent, ModelSettings, RunContext, llm
from pytest import MonkeyPatch

from nudge_voice_agent import workflow
from nudge_voice_agent.assistant import NudgeDocumentCollectionAssistant
from nudge_voice_agent.outbound_assistant import (
    NudgeOutboundDocumentCollectionAssistant,
)


@pytest.mark.parametrize("outbound", [False, True])
def test_pending_result_restricts_model_until_recovery_finishes(
    monkeypatch: MonkeyPatch, outbound: bool
) -> None:
    assistant = (
        NudgeOutboundDocumentCollectionAssistant()
        if outbound
        else NudgeDocumentCollectionAssistant()
    )
    captured: list[tuple[set[str], ModelSettings]] = []
    playback_completed = False

    async def playback(ctx: RunContext, message: str) -> bool:
        del ctx, message
        return playback_completed

    async def model(
        agent: Agent,
        chat_ctx: llm.ChatContext,
        tools: list[llm.Tool],
        model_settings: ModelSettings,
    ) -> AsyncIterator[str]:
        del agent, chat_ctx
        captured.append(({tool.id for tool in tools}, model_settings))
        yield ""

    monkeypatch.setattr(workflow, "_speak_tool_result", playback)
    monkeypatch.setattr(Agent.default, "llm_node", model)

    async def run() -> None:
        nonlocal playback_completed
        tool = assistant.follow_up_tool
        context = cast("RunContext", None)
        if outbound:
            await cast(Any, tool.confirm_authorized_listener)(context, True)
        else:
            await cast(Any, tool.verify_business_name)(
                context, "Northstar Labs Incorporated"
            )
        await cast(Any, tool.record_extension_request)(context, "September 25, 2026")
        original_tools = [
            entry
            for group in assistant.tools
            if isinstance(group, llm.Toolset)
            for entry in group.tools
        ]
        settings = ModelSettings(tool_choice="auto")

        async def invoke() -> None:
            async for _ in assistant.llm_node(
                llm.ChatContext(), original_tools, settings
            ):
                pass

        await invoke()
        assert captured[-1][0] == {"finish_interrupted_result", "end_call"}
        assert captured[-1][1].tool_choice == "required"
        assert settings.tool_choice == "auto"

        # Another interruption must leave the same restriction in place.
        await cast(Any, tool.finish_interrupted_result)(context)
        await invoke()
        assert captured[-1][0] == {"finish_interrupted_result", "end_call"}
        assert captured[-1][1].tool_choice == "required"
        assert len(tool.previews) == 1

        playback_completed = True
        await cast(Any, tool.finish_interrupted_result)(context)
        await invoke()
        assert captured[-1][0] == {entry.id for entry in original_tools}
        assert captured[-1][1].tool_choice == "auto"
        assert not tool.has_pending_spoken_result
        assert len(tool.previews) == 1

    asyncio.run(run())
