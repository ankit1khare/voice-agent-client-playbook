"""Tests for Jenny's instructions and exact disclosure."""

from rho_document_collection_voice_agent.assistant import (
    INITIAL_DISCLOSURE,
    RhoDocumentCollectionAssistant,
    assistant_instructions,
)
from rho_document_collection_voice_agent.call_control import (
    FINAL_GOODBYE,
    GOODBYE_DISCONNECT_GRACE_SECONDS,
    GracefulEndCallTool,
)


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
    assert "August 2026 bank statement" in instructions
    assert "Monday, September 14, 2026" in instructions


def test_instructions_ground_upload_help_and_walkthrough() -> None:
    instructions = assistant_instructions()

    assert "10 MB" in instructions
    assert "unzip it before uploading" in instructions
    assert "guide the caller one step at a time" in instructions
    assert "ask the caller what they see" in instructions
    assert "acknowledge what" in instructions
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

    assert len(assistant.tools) == 1
    assert isinstance(assistant.tools[0], GracefulEndCallTool)
    assert "call the end_call tool immediately" in instructions
    assert "Never say goodbye without calling end_call" in instructions
    assert FINAL_GOODBYE == "Thanks for calling Rho. Goodbye."
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
