"""Tests for validated outbound requests and outcome mapping."""

import json

import pytest

from rho_document_collection_voice_agent.outbound import (
    AMDAction,
    CallOutcome,
    CallResult,
    OutboundCallRequest,
    amd_action_for_category,
    build_sip_participant_request,
    call_outcome_for_sip_status,
    is_outbound_job_metadata,
)


def _valid_request() -> OutboundCallRequest:
    return OutboundCallRequest(
        phone_number="+14155550123",
        request_id="demo-1234",
        demo_only=True,
        authorized_test_call=True,
    )


def test_outbound_request_round_trips_without_phone_identity_leak() -> None:
    request = _valid_request()

    parsed = OutboundCallRequest.from_metadata(request.to_metadata())

    assert parsed == request
    assert parsed.participant_identity == "rho-outbound-demo-1234"
    assert parsed.masked_phone_number == "+********0123"


def test_outbound_metadata_has_an_explicit_mode() -> None:
    metadata = _valid_request().to_metadata()

    assert json.loads(metadata)["mode"] == "rho_outbound_test"
    assert is_outbound_job_metadata(metadata) is True


@pytest.mark.parametrize("metadata", ["", "not-json", "{}", "[]"])
def test_inbound_metadata_does_not_select_outbound(metadata: str) -> None:
    assert is_outbound_job_metadata(metadata) is False


@pytest.mark.parametrize(
    ("change", "message"),
    [
        ({"phone_number": "4155550123"}, "E.164"),
        ({"request_id": "Demo 1234"}, "lowercase"),
        ({"demo_only": False}, "synthetic demo"),
        ({"authorized_test_call": False}, "authorized_test_call"),
    ],
)
def test_outbound_request_rejects_unsafe_metadata(
    change: dict[str, object], message: str
) -> None:
    payload: dict[str, object] = json.loads(_valid_request().to_metadata())
    payload.update(change)

    with pytest.raises(ValueError, match=message):
        OutboundCallRequest.from_metadata(json.dumps(payload))


def test_preview_structure_validation_does_not_require_call_authorization() -> None:
    request = OutboundCallRequest(
        phone_number="+14155550123",
        request_id="preview-1234",
        demo_only=True,
        authorized_test_call=False,
    )

    request.validate_structure()


def test_sip_request_uses_stored_trunk_and_privacy_controls() -> None:
    sip_request = build_sip_participant_request(
        _valid_request(),
        room_name="rho-outbound-demo-1234",
        trunk_id="ST_rho_test",
    )

    assert sip_request.sip_trunk_id == "ST_rho_test"
    assert sip_request.sip_call_to == "+14155550123"
    assert sip_request.participant_identity == "rho-outbound-demo-1234"
    assert sip_request.room_name == "rho-outbound-demo-1234"
    assert sip_request.hide_phone_number is True
    assert sip_request.krisp_enabled is True
    assert sip_request.wait_until_answered is True


@pytest.mark.parametrize(
    ("status_code", "outcome"),
    [
        (486, CallOutcome.BUSY_OR_REJECTED),
        (603, CallOutcome.BUSY_OR_REJECTED),
        (408, CallOutcome.NO_ANSWER),
        (480, CallOutcome.NO_ANSWER),
        (503, CallOutcome.DIAL_FAILED),
        (None, CallOutcome.DIAL_FAILED),
    ],
)
def test_sip_status_mapping(status_code: int | None, outcome: CallOutcome) -> None:
    assert call_outcome_for_sip_status(status_code) is outcome


@pytest.mark.parametrize(
    ("category", "action"),
    [
        ("human", AMDAction.START_CONVERSATION),
        ("uncertain", AMDAction.START_CONVERSATION),
        ("machine-vm", AMDAction.LEAVE_VOICEMAIL),
        ("machine-ivr", AMDAction.END_IVR),
        ("machine-unavailable", AMDAction.END_UNAVAILABLE),
    ],
)
def test_amd_category_mapping(category: str, action: AMDAction) -> None:
    assert amd_action_for_category(category) is action


def test_amd_can_continue_through_authorized_call_screening() -> None:
    assert (
        amd_action_for_category("machine-ivr", allow_ivr_screening=True)
        is AMDAction.CONTINUE_IVR_SCREENING
    )


def test_call_result_is_structured_and_has_no_phone_number() -> None:
    result = CallResult(
        request_id="demo-1234",
        outcome=CallOutcome.VOICEMAIL_LEFT,
        amd_category="machine-vm",
    )

    record = result.to_log_record()

    assert record["outcome"] == "voicemail_left"
    assert record["amd_category"] == "machine-vm"
    assert "phone" not in record
