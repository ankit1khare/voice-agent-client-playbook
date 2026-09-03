"""Validated requests and outcomes for the Rho outbound demo path."""

import json
import re
from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any

from livekit import api

OUTBOUND_AGENT_NAME = "rho-document-collection-demo"
OUTBOUND_JOB_MODE = "rho_outbound_test"

_E164_PATTERN = re.compile(r"^\+[1-9][0-9]{7,14}$")
_REQUEST_ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9-]{0,47}$")


class CallOutcome(str, Enum):
    """Canonical terminal or handoff outcomes for an outbound attempt."""

    OUTBOUND_DISABLED = "outbound_disabled"
    INVALID_REQUEST = "invalid_request"
    HUMAN_ANSWERED = "human_answered"
    VOICEMAIL_LEFT = "voicemail_left"
    IVR_SCREENING_CONTINUED = "ivr_screening_continued"
    IVR_DETECTED = "ivr_detected"
    MAILBOX_UNAVAILABLE = "mailbox_unavailable"
    BUSY_OR_REJECTED = "busy_or_rejected"
    NO_ANSWER = "no_answer"
    DIAL_FAILED = "dial_failed"
    PARTICIPANT_MISSING = "participant_missing"


class AMDAction(str, Enum):
    """Action selected from a LiveKit AMD category."""

    START_CONVERSATION = "start_conversation"
    LEAVE_VOICEMAIL = "leave_voicemail"
    CONTINUE_IVR_SCREENING = "continue_ivr_screening"
    END_IVR = "end_ivr"
    END_UNAVAILABLE = "end_unavailable"


@dataclass(frozen=True, slots=True)
class OutboundCallRequest:
    """A single authorized call to synthetic demo data."""

    phone_number: str
    request_id: str
    demo_only: bool
    authorized_test_call: bool

    @classmethod
    def from_metadata(cls, raw_metadata: str) -> "OutboundCallRequest":
        """Parse and validate LiveKit job metadata."""
        try:
            payload = json.loads(raw_metadata)
        except json.JSONDecodeError as exc:
            raise ValueError("job metadata must be valid JSON") from exc

        if not isinstance(payload, dict):
            raise ValueError("job metadata must be a JSON object")
        if payload.get("mode") != OUTBOUND_JOB_MODE:
            raise ValueError(f"mode must be {OUTBOUND_JOB_MODE}")

        request = cls(
            phone_number=_required_string(payload, "phone_number"),
            request_id=_required_string(payload, "request_id"),
            demo_only=payload.get("demo_only") is True,
            authorized_test_call=payload.get("authorized_test_call") is True,
        )
        request.validate()
        return request

    def validate(self) -> None:
        """Reject unsafe or malformed dial requests."""
        self.validate_structure()
        if not self.demo_only:
            raise ValueError("only synthetic demo calls are enabled")
        if not self.authorized_test_call:
            raise ValueError("authorized_test_call must be true")

    def validate_structure(self) -> None:
        """Validate identifiers without treating a preview as authorization."""
        if not _E164_PATTERN.fullmatch(self.phone_number):
            raise ValueError("phone_number must use E.164 format")
        if not _REQUEST_ID_PATTERN.fullmatch(self.request_id):
            raise ValueError(
                "request_id must contain lowercase letters, digits, or dashes"
            )

    @property
    def participant_identity(self) -> str:
        """Return a stable identity that does not expose the destination number."""
        return f"rho-outbound-{self.request_id}"

    @property
    def masked_phone_number(self) -> str:
        """Return a log-safe form of the destination number."""
        return f"+********{self.phone_number[-4:]}"

    def to_metadata(self) -> str:
        """Serialize the request for an explicit LiveKit dispatch."""
        payload = {"mode": OUTBOUND_JOB_MODE, **asdict(self)}
        return json.dumps(payload, separators=(",", ":"), sort_keys=True)


def is_outbound_job_metadata(raw_metadata: str) -> bool:
    """Return whether job metadata explicitly selects the outbound path."""
    try:
        payload = json.loads(raw_metadata)
    except json.JSONDecodeError:
        return False
    return isinstance(payload, dict) and payload.get("mode") == OUTBOUND_JOB_MODE


@dataclass(frozen=True, slots=True)
class CallResult:
    """Structured, log-safe result for one outbound attempt."""

    request_id: str
    outcome: CallOutcome
    amd_category: str | None = None
    sip_status_code: int | None = None
    detail: str | None = None

    def to_log_record(self) -> dict[str, str | int | None]:
        """Return a structured record suitable for cloud logs."""
        return {
            "request_id": self.request_id,
            "outcome": self.outcome.value,
            "amd_category": self.amd_category,
            "sip_status_code": self.sip_status_code,
            "detail": self.detail,
        }


def build_sip_participant_request(
    request: OutboundCallRequest,
    *,
    room_name: str,
    trunk_id: str,
) -> api.CreateSIPParticipantRequest:
    """Build the stored-trunk dial request expected by LiveKit."""
    if trunk_id.strip() == "":
        raise ValueError("a dedicated Rho outbound trunk ID is required")
    if room_name.strip() == "":
        raise ValueError("room_name is required")

    return api.CreateSIPParticipantRequest(
        room_name=room_name,
        sip_trunk_id=trunk_id,
        sip_call_to=request.phone_number,
        participant_identity=request.participant_identity,
        participant_name="Rho document contact",
        hide_phone_number=True,
        krisp_enabled=True,
        wait_until_answered=True,
    )


def call_outcome_for_sip_status(status_code: int | None) -> CallOutcome:
    """Map documented SIP dial failures to Rho call outcomes."""
    if status_code in {486, 603}:
        return CallOutcome.BUSY_OR_REJECTED
    if status_code in {408, 480}:
        return CallOutcome.NO_ANSWER
    return CallOutcome.DIAL_FAILED


def amd_action_for_category(
    category: str,
    *,
    allow_ivr_screening: bool = False,
) -> AMDAction:
    """Map a LiveKit AMD category to the next outbound action."""
    if category in {"human", "uncertain"}:
        return AMDAction.START_CONVERSATION
    if category == "machine-vm":
        return AMDAction.LEAVE_VOICEMAIL
    if category == "machine-ivr":
        if allow_ivr_screening:
            return AMDAction.CONTINUE_IVR_SCREENING
        return AMDAction.END_IVR
    if category == "machine-unavailable":
        return AMDAction.END_UNAVAILABLE
    raise ValueError(f"unsupported AMD category: {category}")


def _required_string(payload: dict[str, Any], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or value.strip() == "":
        raise ValueError(f"{key} must be a non-empty string")
    return value.strip()
