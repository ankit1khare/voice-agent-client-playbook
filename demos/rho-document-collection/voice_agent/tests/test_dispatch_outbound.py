"""Tests for explicit outbound agent dispatch construction."""

import json
import sys
from pathlib import Path

import pytest

from rho_document_collection_voice_agent import dispatch_outbound
from rho_document_collection_voice_agent.demo_context import DEMO_CALL_RECORD
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
        "call_record": DEMO_CALL_RECORD.to_dict(),
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
    assert '"call_record_id": "rho-demo-sep10-001"' in output
    assert "August 2026 bank statements" in output
    assert "+14155550123" not in output


def test_cli_accepts_a_validated_synthetic_record_file(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    payload = DEMO_CALL_RECORD.to_dict()
    payload["business_name"] = "Demo Bakery, Inc."
    record_path = tmp_path / "record.json"
    record_path.write_text(json.dumps(payload), encoding="utf-8")
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "rho-outbound-dispatch",
            "--phone-number",
            "+14155550123",
            "--record-file",
            str(record_path),
        ],
    )

    dispatch_outbound.main()

    output = capsys.readouterr().out
    assert '"business_name": "Demo Bakery, Inc."' in output
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


def test_cli_never_dispatches_to_client_service(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    dispatched = False

    async def fail_if_dispatched(
        call: OutboundCallRequest,
        agent_name: str,
    ) -> str:
        del call, agent_name
        nonlocal dispatched
        dispatched = True
        return "should-not-run"

    monkeypatch.setenv("RHO_ENABLE_OUTBOUND_CALLS", "true")
    monkeypatch.setattr(dispatch_outbound, "_dispatch", fail_if_dispatched)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "rho-outbound-dispatch",
            "--phone-number",
            "+18557438746",
            "--execute",
            "--authorized-test-call",
        ],
    )

    with pytest.raises(SystemExit, match="Client Service"):
        dispatch_outbound.main()

    assert dispatched is False
