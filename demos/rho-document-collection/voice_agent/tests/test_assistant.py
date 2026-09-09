"""Tests for Jenny's instructions and exact disclosure."""

from rho_document_collection_voice_agent.assistant import (
    INITIAL_DISCLOSURE,
    RhoDocumentCollectionAssistant,
    assistant_instructions,
    follow_up_tool_for,
)
from rho_document_collection_voice_agent.call_control import (
    GOODBYE_DISCONNECT_GRACE_SECONDS,
    INBOUND_FINAL_GOODBYE,
    GracefulEndCallTool,
)
from rho_document_collection_voice_agent.workflow import FollowUpPreviewTool


def test_disclosure_is_exact_and_complete() -> None:
    assert INITIAL_DISCLOSURE == (
        "Hi, I'm Jenny, Rho's AI assistant. This call may be recorded. I can help "
        "with document upload questions, but I can't provide financial advice. "
        "What business are you calling about?"
    )


def test_instructions_define_the_inbound_rho_demo() -> None:
    instructions = assistant_instructions()

    assert instructions.startswith(
        "You are Jenny, Rho's AI assistant in an inbound demonstration."
    )
    assert "caller contacted Rho" in instructions
    assert "Northstar Labs, Inc." in instructions
    assert "August 2026 bank statements" in instructions
    assert "second quarter 2026 interim financials" in instructions
    assert "Tuesday, September 22, 2026" in instructions
    assert "Settings, then Business Documents" in instructions
    assert "call share_document_request_details immediately" in instructions


def test_instructions_ground_upload_help_and_walkthrough() -> None:
    instructions = assistant_instructions()

    assert "secure-upload-link request" in instructions
    assert "Never invent or send" in instructions and "secure link" in instructions
    assert "Offer one upload step at a time" in instructions
    assert "ask what the caller sees" in instructions
    assert "Acknowledge the report" in instructions
    assert "independently confirm receipt" in instructions
    assert "Never claim you can see their screen" in instructions
    assert "received the upload" in instructions


def test_instructions_define_unknown_business_and_advice_boundaries() -> None:
    instructions = assistant_instructions()

    assert "For any other business" in instructions
    assert "do not invent another record" in instructions
    assert "Do not provide financial, legal, tax, underwriting, or credit advice" in (
        instructions
    )


def test_inbound_agent_ends_completed_calls() -> None:
    assistant = RhoDocumentCollectionAssistant()
    instructions = assistant_instructions()

    assert len(assistant.tools) == 2
    assert isinstance(assistant.tools[0], FollowUpPreviewTool)
    assert isinstance(assistant.tools[1], GracefulEndCallTool)
    assert follow_up_tool_for(assistant) is assistant.tools[0]
    assert follow_up_tool_for(assistant).access_granted is False
    assert "call the end_call tool immediately" in instructions
    assert "Never say goodbye without calling end_call" in instructions
    assert INBOUND_FINAL_GOODBYE == "Thank you for calling Rho. Have a great day."
    assert GOODBYE_DISCONNECT_GRACE_SECONDS == 1.0


def test_instructions_do_not_leak_reference_customer_content() -> None:
    combined = f"{INITIAL_DISCLOSURE}\n{assistant_instructions()}".lower()

    for forbidden in (
        "experian",
        "waystar",
        "riley",
        "npi",
        "tax id",
        "1234567893",
        "12-3456789",
        "ca_kbugaf9bbkdt",
        "ca_xgzb76zryimy",
    ):
        assert forbidden not in combined


def test_instructions_require_hard_business_verification() -> None:
    instructions = assistant_instructions()

    assert "verify_business_name" in instructions
    assert 'returns "Business verified."' in instructions
    assert "Never say an action" in instructions
    assert "before its tool succeeds" in instructions
