"""Tests for the outbound prompt and fixed messages."""

from pathlib import Path

from rho_document_collection_voice_agent.call_control import (
    FINAL_GOODBYE,
    GOODBYE_DISCONNECT_GRACE_SECONDS,
    GracefulEndCallTool,
)
from rho_document_collection_voice_agent.outbound_assistant import (
    OUTBOUND_DISCLOSURE,
    RhoOutboundDocumentCollectionAssistant,
    outbound_assistant_instructions,
    voicemail_message,
)


def test_outbound_disclosure_is_fixed_and_complete() -> None:
    assert OUTBOUND_DISCLOSURE == (
        "Hi, this is Jenny, Rho's AI assistant. This call may be recorded. I'm "
        "calling for Maya Chen at Northstar Labs about a document reminder. I can "
        "help with upload questions, but I can't provide financial advice. Am I "
        "speaking with Maya or someone authorized to help with this business?"
    )


def test_outbound_prompt_requires_authorization_before_document_details() -> None:
    instructions = outbound_assistant_instructions()

    assert "synthetic outbound demonstration" in instructions
    assert "Do not share the missing document" in instructions
    assert "Maya Chen" in instructions
    assert "wrong person" in instructions
    assert "cannot discuss the request" in instructions
    assert "cannot see the screen" in instructions
    assert "cannot" in instructions and "confirm receipt" in instructions
    assert "financial, legal, tax, underwriting, or credit advice" in instructions


def test_runtime_voicemail_matches_rendered_demo_asset_text() -> None:
    asset = (
        Path(__file__).parents[2] / "assets" / "jenny_voicemail_reminder.txt"
    ).read_text(encoding="utf-8")

    assert voicemail_message() == asset.strip()


def test_outbound_agent_ends_completed_calls() -> None:
    assistant = RhoOutboundDocumentCollectionAssistant()
    instructions = outbound_assistant_instructions()

    assert len(assistant.tools) == 1
    assert isinstance(assistant.tools[0], GracefulEndCallTool)
    assert "call the end_call tool immediately" in instructions
    assert "Never say goodbye without calling end_call" in instructions
    assert FINAL_GOODBYE == "Thanks for calling Rho. Goodbye."
    assert GOODBYE_DISCONNECT_GRACE_SECONDS == 1.0
