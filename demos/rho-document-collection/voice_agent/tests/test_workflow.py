"""Tests for demo-only business dispositions and Zendesk previews."""

import asyncio
import logging
from typing import Any, cast

import pytest
from _pytest.logging import LogCaptureFixture
from livekit.agents.llm import ToolError

from rho_document_collection_voice_agent.demo_context import DEMO_CALL_RECORD
from rho_document_collection_voice_agent.workflow import (
    ZENDESK_TICKET_PREVIEW_EVENT,
    ConversationDisposition,
    FollowUpPreviewTool,
    build_zendesk_ticket_preview,
)


class _FakeSpeech:
    interrupted = False

    async def wait_for_playout(self) -> None:
        return None


class _InterruptedFakeSpeech(_FakeSpeech):
    interrupted = True


class _FakeAgent:
    def __init__(self) -> None:
        self.tools: list[Any] = []
        self.tool_updates: list[list[Any]] = []

    async def update_tools(self, tools: list[Any]) -> None:
        self.tool_updates.append(tools)


class _FakeSession:
    def __init__(self, *, interrupt_next_speech: bool = False) -> None:
        self.messages: list[str] = []
        self.current_agent = _FakeAgent()
        self.interrupt_next_speech = interrupt_next_speech

    def say(self, message: str, *, allow_interruptions: bool) -> _FakeSpeech:
        assert allow_interruptions is True
        self.messages.append(message)
        if self.interrupt_next_speech:
            self.interrupt_next_speech = False
            return _InterruptedFakeSpeech()
        return _FakeSpeech()


class _FakeRunContext:
    def __init__(self, *, interrupt_next_speech: bool = False) -> None:
        self.session = _FakeSession(
            interrupt_next_speech=interrupt_next_speech,
        )
        self.interruptions_disallowed = False
        self.waited_for_playout = False

    def disallow_interruptions(self) -> None:
        self.interruptions_disallowed = True

    async def wait_for_playout(self) -> None:
        self.waited_for_playout = True


def test_extension_preview_has_required_fields_and_no_external_write() -> None:
    preview = build_zendesk_ticket_preview(
        record=DEMO_CALL_RECORD,
        request_id="demo-extension",
        disposition=ConversationDisposition.EXTENSION_REQUESTED,
        details={"requested_submission_date": "2026-09-25"},
    )

    assert preview == {
        "demo_only": True,
        "write_performed": False,
        "source": "rho_voice_agent_demo",
        "request_id": "demo-extension",
        "call_record_id": "rho-demo-sep10-001",
        "business_name": "Northstar Labs, Inc.",
        "contact_name": "Maya Chen",
        "required_documents": [
            "August 2026 bank statements",
            "Q2 2026 interim financials",
        ],
        "deadline": "2026-09-22",
        "conversation_disposition": "extension_requested",
        "suggested_route": "Underwriting",
        "details": {"requested_submission_date": "2026-09-25"},
        "human_transfer": {
            "requested": False,
            "performed": False,
            "destination": None,
        },
        "zendesk_action": "preview",
    }
    assert "phone" not in preview


def test_human_transfer_preview_never_claims_transfer_performed() -> None:
    preview = build_zendesk_ticket_preview(
        record=DEMO_CALL_RECORD,
        request_id="demo-transfer",
        disposition=ConversationDisposition.HUMAN_TRANSFER_REQUESTED,
        details={"reason": "Client requested more help"},
    )

    assert preview["human_transfer"] == {
        "requested": True,
        "performed": False,
        "destination": "Rho Client Service",
    }
    assert preview["suggested_route"] == "Client Service"


@pytest.mark.parametrize("disposition", list(ConversationDisposition))
def test_every_disposition_builds_a_preview(
    disposition: ConversationDisposition,
) -> None:
    preview = build_zendesk_ticket_preview(
        record=DEMO_CALL_RECORD,
        request_id="demo-all-dispositions",
        disposition=disposition,
    )

    assert preview["conversation_disposition"] == disposition.value
    assert preview["suggested_route"]
    assert preview["write_performed"] is False


def test_preview_tool_logs_and_retains_each_payload(
    caplog: LogCaptureFixture,
) -> None:
    tool = FollowUpPreviewTool(DEMO_CALL_RECORD, "demo-log")

    with caplog.at_level(logging.INFO, logger="rho-workflow-preview"):
        preview = tool.record_preview(
            ConversationDisposition.EXISTING_RHO_CONTACT,
            rho_contact_name="Lucas",
            status_update="Client is preparing the documents",
            empty_value="   ",
        )

    assert tool.previews == [preview]
    assert preview["details"] == {
        "rho_contact_name": "Lucas",
        "status_update": "Client is preparing the documents",
    }
    record = next(
        record
        for record in caplog.records
        if record.message == ZENDESK_TICKET_PREVIEW_EVENT
    )
    assert record.__dict__["zendesk_ticket_preview"] == preview


def test_business_verification_accepts_spacing_and_legal_suffix_variants() -> None:
    tool = FollowUpPreviewTool(DEMO_CALL_RECORD, "demo-verify")
    verify_business_name = cast(Any, tool.verify_business_name)

    result = asyncio.run(verify_business_name(None, "North Star Labs Incorporated"))

    assert result.startswith("Business verified.")
    assert tool.access_granted is True
    assert "confirm_authorized_listener" not in {item.id for item in tool.tools}
    assert "verify_business_name" not in {item.id for item in tool.tools}


def test_successful_verification_updates_the_live_tool_list() -> None:
    tool = FollowUpPreviewTool(DEMO_CALL_RECORD, "demo-live-tool-removal")
    ctx = _FakeRunContext()
    ctx.session.current_agent.tools = [tool]
    verify_business_name = cast(Any, tool.verify_business_name)

    asyncio.run(verify_business_name(ctx, "Northstar Labs"))

    assert ctx.session.current_agent.tool_updates == [[tool]]
    assert "verify_business_name" not in {item.id for item in tool.tools}


def test_failed_business_verification_blocks_account_actions() -> None:
    tool = FollowUpPreviewTool(DEMO_CALL_RECORD, "demo-block")
    verify_business_name = cast(Any, tool.verify_business_name)
    record_prior_upload_claim = cast(Any, tool.record_prior_upload_claim)

    result = asyncio.run(verify_business_name(None, "Southstar Design"))

    assert result.startswith("Business not verified.")
    assert tool.access_granted is False
    with pytest.raises(ToolError, match="Access not verified"):
        asyncio.run(record_prior_upload_claim(None))
    assert tool.previews == []


def test_successful_action_speaks_deterministic_complete_acknowledgment() -> None:
    tool = FollowUpPreviewTool(DEMO_CALL_RECORD, "demo-commitment")
    ctx = _FakeRunContext()
    verify_business_name = cast(Any, tool.verify_business_name)
    record_upload_commitment = cast(Any, tool.record_upload_commitment)

    asyncio.run(verify_business_name(None, "Northstar Labs"))
    asyncio.run(record_upload_commitment(ctx, "September 21, 2026"))

    assert tool.previews[-1]["conversation_disposition"] == "promise_to_upload"
    assert tool.previews[-1]["details"] == {
        "promised_upload_date": "September 21, 2026"
    }
    assert ctx.interruptions_disallowed is False
    assert ctx.waited_for_playout is True
    assert ctx.session.messages == [
        "I've recorded your upload commitment for September 21, 2026. I'll pass "
        "that timing to the document collection team. Do you need anything else?"
    ]


def test_later_today_commitment_is_preserved_without_reprompting() -> None:
    tool = FollowUpPreviewTool(DEMO_CALL_RECORD, "demo-later-today")
    ctx = _FakeRunContext()
    verify_business_name = cast(Any, tool.verify_business_name)
    record_upload_commitment = cast(Any, tool.record_upload_commitment)

    asyncio.run(verify_business_name(None, "Northstar Labs"))
    asyncio.run(record_upload_commitment(ctx, "later today"))

    assert tool.previews[-1]["details"] == {"promised_upload_date": "later today"}
    assert ctx.session.messages == [
        "I've recorded your upload commitment for later today. I'll pass that "
        "timing to the document collection team. Do you need anything else?"
    ]


def test_document_request_details_are_spoken_as_one_grounded_response() -> None:
    tool = FollowUpPreviewTool(DEMO_CALL_RECORD, "demo-details")
    ctx = _FakeRunContext()
    verify_business_name = cast(Any, tool.verify_business_name)
    share_details = cast(Any, tool.share_document_request_details)

    asyncio.run(verify_business_name(None, "Northstar Labs"))
    asyncio.run(share_details(ctx))

    assert ctx.session.messages == [
        "Rho is still awaiting August 2026 bank statements and second quarter "
        "2026 interim financials. The submission deadline is Tuesday, September "
        "22, 2026. You can upload the documents under Settings, then Business "
        "Documents. Would you like me to walk you through the upload one step at "
        "a time?"
    ]
    assert tool.previews == []


def test_outbound_document_reminder_ends_with_rhos_submission_question() -> None:
    tool = FollowUpPreviewTool(
        DEMO_CALL_RECORD,
        "demo-outbound-details",
        verification_mode="authorized_listener",
    )
    ctx = _FakeRunContext()
    confirm_authorized_listener = cast(Any, tool.confirm_authorized_listener)
    share_details = cast(Any, tool.share_document_request_details)

    asyncio.run(confirm_authorized_listener(None, True))
    asyncio.run(share_details(ctx))

    assert ctx.session.messages[-1].endswith(
        "Do you expect to submit the documents by then, or do you need an extension "
        "or have any questions I can help with?"
    )


def test_critical_workflow_boundaries_are_spoken_first() -> None:
    tool = FollowUpPreviewTool(DEMO_CALL_RECORD, "demo-boundary-order")
    ctx = _FakeRunContext()
    verify_business_name = cast(Any, tool.verify_business_name)
    record_deadline_dispute = cast(Any, tool.record_deadline_dispute)
    request_human_transfer = cast(Any, tool.request_human_transfer)

    asyncio.run(verify_business_name(None, "Northstar Labs"))
    asyncio.run(record_deadline_dispute(ctx, "September 24, 2026"))
    asyncio.run(request_human_transfer(ctx, "More questions"))

    assert ctx.session.messages[-2].startswith(
        "Rho will need to check the deadline discrepancy. I can't confirm which "
        "date is correct."
    )
    assert ctx.session.messages[-1].startswith(
        "Live transfer is unavailable in this demo. You can call "
    )


def test_interrupted_tool_result_requests_complete_recovery() -> None:
    tool = FollowUpPreviewTool(DEMO_CALL_RECORD, "demo-interrupted-result")
    ctx = _FakeRunContext(interrupt_next_speech=True)
    verify_business_name = cast(Any, tool.verify_business_name)
    request_human_transfer = cast(Any, tool.request_human_transfer)

    asyncio.run(verify_business_name(None, "Northstar Labs"))
    result = asyncio.run(request_human_transfer(ctx, "More questions"))

    assert result is not None
    assert result.startswith("The required caller-facing result was interrupted.")
    assert "finish_interrupted_result" in result
    pending = tool.take_pending_spoken_result()
    assert pending is not None
    assert "Live transfer is unavailable in this demo" in pending
    assert "clientservice@rho.co" in pending
    assert tool.take_pending_spoken_result() is None


def test_interrupted_document_reminder_does_not_block_the_next_intent() -> None:
    tool = FollowUpPreviewTool(DEMO_CALL_RECORD, "demo-interrupted-reminder")
    interrupted_ctx = _FakeRunContext(interrupt_next_speech=True)
    completed_ctx = _FakeRunContext()
    verify_business_name = cast(Any, tool.verify_business_name)
    share_document_request_details = cast(Any, tool.share_document_request_details)
    record_prior_upload_claim = cast(Any, tool.record_prior_upload_claim)

    asyncio.run(verify_business_name(None, "Northstar Labs"))
    result = asyncio.run(share_document_request_details(interrupted_ctx))
    asyncio.run(record_prior_upload_claim(completed_ctx))

    assert result is not None
    assert result.startswith("The document reminder was interrupted.")
    assert tool.take_pending_spoken_result() is None
    assert tool.previews[-1]["conversation_disposition"] == "prior_upload_claimed"


def test_end_call_recovery_omits_optional_follow_up_question() -> None:
    tool = FollowUpPreviewTool(DEMO_CALL_RECORD, "demo-end-call-recovery")
    interrupted_ctx = _FakeRunContext(interrupt_next_speech=True)
    verify_business_name = cast(Any, tool.verify_business_name)
    request_human_transfer = cast(Any, tool.request_human_transfer)

    asyncio.run(verify_business_name(None, "Northstar Labs"))
    asyncio.run(request_human_transfer(interrupted_ctx, "More questions"))

    pending = tool.take_pending_spoken_result()
    assert pending is not None
    assert pending.endswith("I've recorded your request for Client Service.")
    assert "Do you need anything else?" not in pending


def test_finish_interrupted_result_replays_and_clears_pending_message() -> None:
    tool = FollowUpPreviewTool(DEMO_CALL_RECORD, "demo-finish-interrupted")
    interrupted_ctx = _FakeRunContext(interrupt_next_speech=True)
    completed_ctx = _FakeRunContext()
    verify_business_name = cast(Any, tool.verify_business_name)
    request_human_transfer = cast(Any, tool.request_human_transfer)
    finish_interrupted_result = cast(Any, tool.finish_interrupted_result)

    asyncio.run(verify_business_name(None, "Northstar Labs"))
    asyncio.run(request_human_transfer(interrupted_ctx, "More questions"))
    result = asyncio.run(finish_interrupted_result(completed_ctx))

    assert result is None
    assert completed_ctx.session.messages[-1].startswith(
        "Live transfer is unavailable in this demo"
    )
    assert tool.take_pending_spoken_result() is None


def test_pending_result_blocks_other_workflow_tools() -> None:
    tool = FollowUpPreviewTool(DEMO_CALL_RECORD, "demo-pending-gate")
    interrupted_ctx = _FakeRunContext(interrupt_next_speech=True)
    verify_business_name = cast(Any, tool.verify_business_name)
    request_human_transfer = cast(Any, tool.request_human_transfer)
    record_secure_link_request = cast(Any, tool.record_secure_link_request)

    asyncio.run(verify_business_name(None, "Northstar Labs"))
    asyncio.run(request_human_transfer(interrupted_ctx, "More questions"))

    with pytest.raises(ToolError, match="finish_interrupted_result"):
        asyncio.run(record_secure_link_request(_FakeRunContext()))
    assert len(tool.previews) == 1


@pytest.mark.parametrize(
    (
        "method_name",
        "arguments",
        "disposition",
        "details",
        "message_fragment",
    ),
    [
        (
            "record_extension_request",
            {"requested_submission_date": "September 25, 2026"},
            "extension_requested",
            {"requested_submission_date": "September 25, 2026"},
            "It is not approved yet",
        ),
        (
            "record_prior_upload_claim",
            {},
            "prior_upload_claimed",
            {},
            "can't independently confirm receipt",
        ),
        (
            "record_deadline_dispute",
            {"client_expected_deadline": "September 24, 2026"},
            "deadline_disputed",
            {"client_expected_deadline": "September 24, 2026"},
            "can't confirm which date is correct",
        ),
        (
            "record_requirement_change_request",
            {"reason": "Our reporting process changed"},
            "requirement_change_requested",
            {"reason": "Our reporting process changed"},
            "No requirement has been changed",
        ),
        (
            "record_existing_rho_contact",
            {
                "rho_contact_name": "Lucas",
                "status_update": "the documents are being prepared",
            },
            "existing_rho_contact",
            {
                "rho_contact_name": "Lucas",
                "status_update": "the documents are being prepared",
            },
            "I didn't update any existing case",
        ),
        (
            "request_human_transfer",
            {"reason": "More questions"},
            "human_transfer_requested",
            {"reason": "More questions"},
            "Live transfer is unavailable in this demo",
        ),
        (
            "record_secure_link_request",
            {},
            "secure_link_requested",
            {},
            "no link was sent",
        ),
    ],
)
def test_each_account_action_records_and_speaks_its_hard_boundary(
    method_name: str,
    arguments: dict[str, str],
    disposition: str,
    details: dict[str, str],
    message_fragment: str,
) -> None:
    tool = FollowUpPreviewTool(DEMO_CALL_RECORD, f"demo-{disposition}")
    ctx = _FakeRunContext()
    verify_business_name = cast(Any, tool.verify_business_name)
    action = getattr(tool, method_name)

    asyncio.run(verify_business_name(None, "Northstar Labs"))
    asyncio.run(action(ctx, **arguments))

    assert tool.previews[-1]["conversation_disposition"] == disposition
    assert tool.previews[-1]["details"] == details
    assert ctx.interruptions_disallowed is False
    assert ctx.waited_for_playout is True
    assert message_fragment in ctx.session.messages[-1]


def test_not_a_good_time_can_be_recorded_before_account_authorization() -> None:
    tool = FollowUpPreviewTool(
        DEMO_CALL_RECORD,
        "demo-not-a-good-time",
        verification_mode="authorized_listener",
    )
    action = cast(Any, tool.record_not_a_good_time)

    result = asyncio.run(action(None, "tomorrow afternoon"))

    assert result.startswith("The demo follow-up preview is saved")
    assert tool.previews[-1]["conversation_disposition"] == "not_a_good_time"
    assert tool.previews[-1]["details"] == {
        "preferred_callback_time": "tomorrow afternoon"
    }


def test_not_a_good_time_does_not_invent_a_callback_time() -> None:
    tool = FollowUpPreviewTool(
        DEMO_CALL_RECORD,
        "demo-not-a-good-time-no-callback",
        verification_mode="authorized_listener",
    )
    action = cast(Any, tool.record_not_a_good_time)

    asyncio.run(action(None))

    assert tool.previews[-1]["conversation_disposition"] == "not_a_good_time"
    assert tool.previews[-1]["details"] == {}


@pytest.mark.parametrize("invalid_date", ["", " ", "x" * 501])
def test_invalid_tool_detail_is_recoverable_for_the_llm(invalid_date: str) -> None:
    tool = FollowUpPreviewTool(DEMO_CALL_RECORD, "demo-invalid-date")
    verify_business_name = cast(Any, tool.verify_business_name)
    action = cast(Any, tool.record_extension_request)

    asyncio.run(verify_business_name(None, "Northstar Labs"))
    with pytest.raises(ToolError, match="requested_submission_date"):
        asyncio.run(action(_FakeRunContext(), invalid_date))

    assert tool.previews == []


def test_outbound_authorization_gate_requires_explicit_confirmation() -> None:
    tool = FollowUpPreviewTool(
        DEMO_CALL_RECORD,
        "demo-outbound-auth",
        verification_mode="authorized_listener",
    )
    confirm_authorized_listener = cast(Any, tool.confirm_authorized_listener)
    record_prior_upload_claim = cast(Any, tool.record_prior_upload_claim)

    assert "verify_business_name" not in {item.id for item in tool.tools}
    assert "confirm_authorized_listener" in {item.id for item in tool.tools}

    result = asyncio.run(confirm_authorized_listener(None, False))
    assert result.startswith("Listener is not authorized.")
    with pytest.raises(ToolError, match="Access not verified"):
        asyncio.run(record_prior_upload_claim(None))

    result = asyncio.run(confirm_authorized_listener(None, True))
    assert result.startswith("Listener authorization confirmed.")
    assert tool.access_granted is True
    assert "confirm_authorized_listener" not in {item.id for item in tool.tools}
