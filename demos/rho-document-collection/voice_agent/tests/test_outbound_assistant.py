"""Tests for the outbound prompt and fixed messages."""

from pathlib import Path

from rho_document_collection_voice_agent.call_control import (
    GOODBYE_DISCONNECT_GRACE_SECONDS,
    OUTBOUND_FINAL_GOODBYE,
    GracefulEndCallTool,
)
from rho_document_collection_voice_agent.outbound_assistant import (
    OUTBOUND_DISCLOSURE,
    RhoOutboundDocumentCollectionAssistant,
    follow_up_tool_for,
    outbound_assistant_instructions,
    voicemail_message,
)
from rho_document_collection_voice_agent.workflow import FollowUpPreviewTool


def test_outbound_disclosure_is_fixed_and_complete() -> None:
    assert OUTBOUND_DISCLOSURE == (
        "Hi, this is Jenny, Rho's AI assistant. Before we begin, please note that "
        "this call is being recorded. Would this be a good time for a call?"
    )


def test_outbound_prompt_requires_authorization_before_document_details() -> None:
    instructions = outbound_assistant_instructions()

    assert "synthetic outbound demonstration" in instructions
    assert "If it is not a good time" in instructions
    assert "only if the listener volunteers one" in instructions
    assert "Acknowledge the answer, then call end_call" in instructions
    assert "Maya Chen" in instructions
    assert "calling for Northstar Labs, Inc." in instructions
    assert "Rho has approved naming the business at this stage" in instructions
    assert "wrong person" in instructions
    assert "cannot discuss the request" in instructions
    assert "August 2026 bank statements" in instructions
    assert "second quarter 2026 interim financials" in instructions
    assert "Tuesday, September 22, 2026" in instructions
    assert "Settings, then Business Documents" in instructions
    assert "call share_document_request_details immediately" in instructions
    assert "today, later today, or tomorrow" in instructions
    assert "call record_deadline_dispute with that date immediately" in instructions
    assert "call finish_interrupted_result" in instructions
    assert "only documented navigation path" in instructions
    assert "Never guess what any other button" in instructions
    assert "cannot" in instructions and "independently confirm receipt" in instructions
    assert "financial, legal, tax, underwriting, or credit advice" in instructions


def test_outbound_prompt_defines_every_preview_workflow() -> None:
    instructions = outbound_assistant_instructions()

    for tool_name in (
        "record_not_a_good_time",
        "record_upload_commitment",
        "record_extension_request",
        "record_prior_upload_claim",
        "record_deadline_dispute",
        "record_requirement_change_request",
        "record_existing_rho_contact",
        "request_human_transfer",
        "record_secure_link_request",
        "share_document_request_details",
    ):
        assert tool_name in instructions
    assert "Never say the extension is approved" in instructions
    assert "Never guess which date is correct" in instructions
    assert (
        "Live transfer is" in instructions and "disabled for this demo" in instructions
    )
    assert "Do not claim that an external system was read or changed" in instructions


def test_runtime_voicemail_matches_rendered_demo_asset_text() -> None:
    asset = (
        Path(__file__).parents[2] / "assets" / "jenny_voicemail_reminder.txt"
    ).read_text(encoding="utf-8")

    assert voicemail_message() == asset.strip()
    assert "August 2026 bank statements" in asset
    assert "second quarter 2026 interim financials" in asset
    assert "Settings, then Business Documents" in asset
    assert "Tuesday, September 22" in asset
    assert "clientservice@rho.co" in asset
    assert "service@rho.com" not in asset
    assert "upcoming deadline to submit your financial documentation" in asset
    assert "You can securely upload the documents" in asset
    assert "fictional account information" not in asset
    assert "Rho Demo Portal" not in asset


def test_outbound_agent_ends_completed_calls() -> None:
    assistant = RhoOutboundDocumentCollectionAssistant()
    instructions = outbound_assistant_instructions()

    assert len(assistant.tools) == 2
    assert isinstance(assistant.tools[0], FollowUpPreviewTool)
    assert isinstance(assistant.tools[1], GracefulEndCallTool)
    assert follow_up_tool_for(assistant) is assistant.tools[0]
    assert follow_up_tool_for(assistant).access_granted is False
    assert "confirm_authorized_listener" in instructions
    assert "call the end_call tool immediately" in instructions
    assert "Never say goodbye without calling end_call" in instructions
    assert OUTBOUND_FINAL_GOODBYE == "Thanks, goodbye for now. Have a great day."
    assert GOODBYE_DISCONNECT_GRACE_SECONDS == 1.0
