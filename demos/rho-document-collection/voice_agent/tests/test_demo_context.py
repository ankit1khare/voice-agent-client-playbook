"""Tests for the synthetic Rho demo record."""

from datetime import date

from rho_document_collection_voice_agent.demo_context import (
    DEMO_BUSINESS,
    render_demo_record,
)


def test_demo_record_uses_a_business_day_deadline() -> None:
    assert DEMO_BUSINESS.upload_deadline == date(2026, 9, 14)
    assert DEMO_BUSINESS.upload_deadline.weekday() == 0
    assert DEMO_BUSINESS.spoken_deadline == "Monday, September 14, 2026"


def test_render_demo_record_contains_complete_synthetic_context() -> None:
    rendered = render_demo_record()

    assert "Northstar Labs, Inc." in rendered
    assert "Maya Chen" in rendered
    assert "August 2026 bank statement" in rendered
    assert "Monday, September 14, 2026" in rendered
    assert "Rho Demo Portal, then Required Documents, then Upload" in rendered
