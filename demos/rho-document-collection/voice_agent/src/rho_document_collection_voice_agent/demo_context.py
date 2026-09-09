"""Synthetic call data and approved help content for the Rho demo."""

from __future__ import annotations

import re
from calendar import day_name, month_name
from dataclasses import dataclass
from datetime import date
from typing import Any

RHO_APPLYING_FAQ_URL = (
    "https://www.rho.co/help-center/general-rho-information/applying-to-rho-faqs"
)
RHO_HELP_CENTER_URL = "https://www.rho.co/help-center"

_RECORD_ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9-]{0,63}$")
_QUARTER_PATTERN = re.compile(r"^Q([1-4])(?:\s+(.+))?$", re.IGNORECASE)
_QUARTER_NAMES = {
    "1": "first quarter",
    "2": "second quarter",
    "3": "third quarter",
    "4": "fourth quarter",
}
_MAX_REQUIRED_DOCUMENTS = 10
_MAX_UPLOAD_PATH_STEPS = 6


@dataclass(frozen=True, slots=True)
class RequiredDocument:
    """One fictional document requested for a specific reporting period."""

    document_type: str
    period: str | None = None

    def __post_init__(self) -> None:
        _validate_text(self.document_type, "document_type")
        if self.period is not None:
            _validate_text(self.period, "period")

    @property
    def display_name(self) -> str:
        """Return the canonical document label for records and integrations."""
        if self.period is None:
            return self.document_type
        return f"{self.period} {self.document_type}"

    @property
    def spoken_name(self) -> str:
        """Return a TTS-safe document name without changing the stored label."""
        if self.period is None:
            return self.document_type
        match = _QUARTER_PATTERN.fullmatch(self.period)
        if match is None:
            spoken_period = self.period
        else:
            quarter, remainder = match.groups()
            spoken_period = _QUARTER_NAMES[quarter]
            if remainder is not None:
                spoken_period = f"{spoken_period} {remainder}"
        return f"{spoken_period} {self.document_type}"

    def to_dict(self) -> dict[str, str | None]:
        """Return a JSON-safe representation."""
        return {"document_type": self.document_type, "period": self.period}

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> RequiredDocument:
        """Build a validated required document from JSON data."""
        if not isinstance(payload, dict):
            raise ValueError("each required document must be an object")
        period = payload.get("period")
        if period is not None and not isinstance(period, str):
            raise ValueError("document period must be a string or null")
        return cls(
            document_type=_required_text(payload, "document_type"),
            period=period,
        )


@dataclass(frozen=True, slots=True)
class CentralizedCallRecord:
    """A fictional monthly record used to personalize one reminder call."""

    record_id: str
    business_name: str
    contact_name: str
    required_documents: tuple[RequiredDocument, ...]
    upload_deadline: date
    upload_path: tuple[str, ...]

    def __post_init__(self) -> None:
        if not _RECORD_ID_PATTERN.fullmatch(self.record_id):
            raise ValueError(
                "record_id must contain lowercase letters, digits, or dashes"
            )
        _validate_text(self.business_name, "business_name")
        _validate_text(self.contact_name, "contact_name")
        if not 1 <= len(self.required_documents) <= _MAX_REQUIRED_DOCUMENTS:
            raise ValueError("required_documents must contain between 1 and 10 items")
        if not 1 <= len(self.upload_path) <= _MAX_UPLOAD_PATH_STEPS:
            raise ValueError("upload_path must contain between 1 and 6 steps")
        for step in self.upload_path:
            _validate_text(step, "upload_path step")

    @property
    def spoken_deadline(self) -> str:
        """Return the deadline in unambiguous spoken form."""
        value = self.upload_deadline
        return (
            f"{day_name[value.weekday()]}, {month_name[value.month]} "
            f"{value.day}, {value.year}"
        )

    @property
    def spoken_upload_path(self) -> str:
        """Return the upload path in spoken form."""
        return ", then ".join(self.upload_path)

    @property
    def spoken_required_documents(self) -> str:
        """Return the required documents as a natural spoken list."""
        names = [document.spoken_name for document in self.required_documents]
        if len(names) == 1:
            return names[0]
        if len(names) == 2:
            return f"{names[0]} and {names[1]}"
        return f"{', '.join(names[:-1])}, and {names[-1]}"

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-safe representation for guarded job metadata."""
        return {
            "record_id": self.record_id,
            "business_name": self.business_name,
            "contact_name": self.contact_name,
            "required_documents": [
                document.to_dict() for document in self.required_documents
            ],
            "upload_deadline": self.upload_deadline.isoformat(),
            "upload_path": list(self.upload_path),
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> CentralizedCallRecord:
        """Build a validated call record from JSON data."""
        if not isinstance(payload, dict):
            raise ValueError("call_record must be an object")

        raw_documents = payload.get("required_documents")
        if not isinstance(raw_documents, list):
            raise ValueError("required_documents must be a list")

        raw_upload_path = payload.get("upload_path")
        if not isinstance(raw_upload_path, list) or not all(
            isinstance(step, str) for step in raw_upload_path
        ):
            raise ValueError("upload_path must be a list of strings")

        raw_deadline = _required_text(payload, "upload_deadline")
        try:
            upload_deadline = date.fromisoformat(raw_deadline)
        except ValueError as exc:
            raise ValueError("upload_deadline must use YYYY-MM-DD format") from exc

        return cls(
            record_id=_required_text(payload, "record_id"),
            business_name=_required_text(payload, "business_name"),
            contact_name=_required_text(payload, "contact_name"),
            required_documents=tuple(
                RequiredDocument.from_dict(document) for document in raw_documents
            ),
            upload_deadline=upload_deadline,
            upload_path=tuple(raw_upload_path),
        )


def _required_text(payload: dict[str, Any], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str):
        raise ValueError(f"{key} must be a string")
    return _validate_text(value, key)


def _validate_text(value: str, name: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{name} must not be empty")
    if len(normalized) > 200:
        raise ValueError(f"{name} must be at most 200 characters")
    return normalized


DEMO_CALL_RECORD = CentralizedCallRecord(
    record_id="rho-demo-sep10-001",
    business_name="Northstar Labs, Inc.",
    contact_name="Maya Chen",
    required_documents=(
        RequiredDocument(document_type="bank statements", period="August 2026"),
        RequiredDocument(document_type="interim financials", period="Q2 2026"),
    ),
    upload_deadline=date(2026, 9, 22),
    upload_path=("Settings", "Business Documents"),
)

LARGE_FILE_HELP = (
    "If a file is too large for the Rho platform, do not invent or promise a "
    "secure link. Record a secure-upload-link request so Client Service can "
    "follow up through an approved channel."
)

RHO_SUPPORT_PHONE_SPOKEN = "1-855-743-8746"
RHO_SUPPORT_PHONE_E164 = "+18557438746"
RHO_SUPPORT_EMAIL = "clientService@rho.co"


def render_demo_record(record: CentralizedCallRecord = DEMO_CALL_RECORD) -> str:
    """Render the synthetic record for use in assistant instructions."""
    documents = "\n".join(
        f"- {document.spoken_name}" for document in record.required_documents
    )
    return (
        f"Record ID: {record.record_id}\n"
        f"Business: {record.business_name}\n"
        f"Credit contact: {record.contact_name}\n"
        f"Required documents:\n{documents}\n"
        f"Upload deadline: {record.spoken_deadline}\n"
        f"Upload path: {record.spoken_upload_path}"
    )
