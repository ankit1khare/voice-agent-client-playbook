"""Tests for the synthetic demo context."""

from datetime import date

from client_voice_agent.context import DEMO_RECORD, render_demo_record


def test_demo_record_is_fictional_and_complete() -> None:
    assert DEMO_RECORD.organization_name == "Juniper Works, LLC"
    assert DEMO_RECORD.upload_deadline == date(2026, 9, 18)
    assert DEMO_RECORD.upload_deadline.weekday() == 4


def test_rendered_record_is_speakable() -> None:
    rendered = render_demo_record()

    assert "Friday, September 18, 2026" in rendered
    assert "Demo Portal, then Open Requests, then Upload Document" in rendered
