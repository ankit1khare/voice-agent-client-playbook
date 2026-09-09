"""Tests for the standalone Zendesk preview command."""

import json
import sys

import pytest

from rho_document_collection_voice_agent import preview_workflow


def test_preview_cli_prints_an_extension_without_writing(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "rho-zendesk-preview",
            "--disposition",
            "extension_requested",
            "--request-id",
            "demo-extension",
            "--requested-submission-date",
            "2026-09-25",
        ],
    )

    preview_workflow.main()

    payload = json.loads(capsys.readouterr().out)
    assert payload["request_id"] == "demo-extension"
    assert payload["conversation_disposition"] == "extension_requested"
    assert payload["details"] == {"requested_submission_date": "2026-09-25"}
    assert payload["zendesk_action"] == "preview"
    assert payload["write_performed"] is False
