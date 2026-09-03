"""Tests for the conversation contract and exact disclosure."""

from client_voice_agent.assistant import INITIAL_DISCLOSURE, assistant_instructions


def test_disclosure_is_exact_and_complete() -> None:
    assert INITIAL_DISCLOSURE == (
        "Hi, I'm Jamie, an AI assistant for the support team. This call may be "
        "recorded. I can explain the upload steps, but I can't provide legal or "
        "financial advice. What organization are you calling about?"
    )


def test_instructions_ground_the_single_demo_record() -> None:
    instructions = assistant_instructions()

    assert "Juniper Works, LLC" in instructions
    assert "Sam Rivera" in instructions
    assert "current certificate of insurance" in instructions
    assert "Friday, September 18, 2026" in instructions


def test_instructions_define_identity_and_unknown_record_behavior() -> None:
    instructions = assistant_instructions()

    assert "only after the caller identifies Juniper Works" in instructions
    assert "For any other organization" in instructions
    assert "Do not reveal" in instructions
    assert "do not invent another record" in instructions


def test_instructions_allow_guidance_without_false_confirmation() -> None:
    instructions = assistant_instructions()

    assert "guide the caller one step at a time" in instructions
    assert "ask the caller what they see" in instructions
    assert "cannot independently confirm receipt" in instructions
    assert "Never claim you can see the caller's screen" in instructions
