"""Tests for the synthetic Rho centralized call record."""

from datetime import date

import pytest

from rho_document_collection_voice_agent.demo_context import (
    DEMO_CALL_RECORD,
    CentralizedCallRecord,
    RequiredDocument,
    render_demo_record,
)


def test_demo_record_uses_latest_synthetic_deadline_and_upload_path() -> None:
    assert DEMO_CALL_RECORD.upload_deadline == date(2026, 9, 22)
    assert DEMO_CALL_RECORD.upload_deadline.weekday() == 1
    assert DEMO_CALL_RECORD.spoken_deadline == "Tuesday, September 22, 2026"
    assert DEMO_CALL_RECORD.upload_path == ("Settings", "Business Documents")


def test_demo_record_supports_a_natural_multi_document_list() -> None:
    assert len(DEMO_CALL_RECORD.required_documents) == 2
    assert DEMO_CALL_RECORD.spoken_required_documents == (
        "August 2026 bank statements and second quarter 2026 interim financials"
    )


def test_quarter_label_stays_canonical_while_speech_expands_it() -> None:
    document = RequiredDocument(document_type="interim financials", period="Q2 2026")

    assert document.display_name == "Q2 2026 interim financials"
    assert document.spoken_name == "second quarter 2026 interim financials"


def test_render_demo_record_contains_complete_synthetic_context() -> None:
    rendered = render_demo_record()

    assert "rho-demo-sep10-001" in rendered
    assert "Northstar Labs, Inc." in rendered
    assert "Maya Chen" in rendered
    assert "August 2026 bank statements" in rendered
    assert "second quarter 2026 interim financials" in rendered
    assert "Tuesday, September 22, 2026" in rendered
    assert "Settings, then Business Documents" in rendered


def test_call_record_round_trips_through_json_safe_data() -> None:
    restored = CentralizedCallRecord.from_dict(DEMO_CALL_RECORD.to_dict())

    assert restored == DEMO_CALL_RECORD


def test_required_document_can_omit_a_reporting_period() -> None:
    document = RequiredDocument(document_type="latest line-of-credit update")

    assert document.spoken_name == "latest line-of-credit update"


@pytest.mark.parametrize(
    ("change", "message"),
    [
        ({"record_id": "Rho demo"}, "lowercase"),
        ({"required_documents": []}, "between 1 and 10"),
        ({"upload_path": []}, "between 1 and 6"),
        ({"upload_deadline": "September 22"}, "YYYY-MM-DD"),
    ],
)
def test_call_record_rejects_invalid_input(
    change: dict[str, object], message: str
) -> None:
    payload = DEMO_CALL_RECORD.to_dict()
    payload.update(change)

    with pytest.raises(ValueError, match=message):
        CentralizedCallRecord.from_dict(payload)
