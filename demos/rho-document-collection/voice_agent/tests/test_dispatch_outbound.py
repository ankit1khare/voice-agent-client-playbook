"""Tests for explicit outbound agent dispatch construction."""

import json
import sys

import pytest

from rho_document_collection_voice_agent import dispatch_outbound
from rho_document_collection_voice_agent.dispatch_outbound import (
    build_dispatch_request,
)
from rho_document_collection_voice_agent.outbound import OutboundCallRequest


def test_dispatch_routes_authorized_metadata_to_outbound_agent() -> None:
    call = OutboundCallRequest(
        phone_number="+14155550123",
        request_id="demo-5678",
        demo_only=True,
        authorized_test_call=True,
    )

    request = build_dispatch_request(call)
    metadata = json.loads(request.metadata)

    assert request.agent_name == "rho-document-collection-demo"
    assert request.room == "rho-outbound-demo-5678"
    assert metadata == {
        "authorized_test_call": True,
        "demo_only": True,
        "mode": "rho_outbound_test",
        "phone_number": "+14155550123",
        "request_id": "demo-5678",
    }


def test_cli_previews_masked_destination_without_dispatching(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(
        sys,
        "argv",
        ["rho-outbound-dispatch", "--phone-number", "+14155550123"],
    )

    dispatch_outbound.main()

    output = capsys.readouterr().out
    assert '"mode": "preview"' in output
    assert '"destination": "+********0123"' in output
    assert "+14155550123" not in output


def test_cli_execute_requires_per_call_authorization(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "rho-outbound-dispatch",
            "--phone-number",
            "+14155550123",
            "--execute",
        ],
    )

    with pytest.raises(SystemExit, match="--authorized-test-call"):
        dispatch_outbound.main()


def test_cli_execute_requires_environment_switch(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("RHO_ENABLE_OUTBOUND_CALLS", raising=False)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "rho-outbound-dispatch",
            "--phone-number",
            "+14155550123",
            "--execute",
            "--authorized-test-call",
        ],
    )

    with pytest.raises(SystemExit, match="RHO_ENABLE_OUTBOUND_CALLS=true"):
        dispatch_outbound.main()
