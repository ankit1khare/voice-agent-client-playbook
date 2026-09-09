"""Create an explicit LiveKit dispatch for one synthetic outbound call."""

import argparse
import asyncio
import json
import os
import secrets
from pathlib import Path

from livekit import api

from rho_document_collection_voice_agent.demo_context import (
    DEMO_CALL_RECORD,
    CentralizedCallRecord,
)
from rho_document_collection_voice_agent.outbound import (
    OUTBOUND_AGENT_NAME,
    OutboundCallRequest,
)
from rho_document_collection_voice_agent.settings import load_settings


def build_dispatch_request(
    call: OutboundCallRequest,
    *,
    agent_name: str = OUTBOUND_AGENT_NAME,
) -> api.CreateAgentDispatchRequest:
    """Build an explicit agent dispatch without placing a call itself."""
    return api.CreateAgentDispatchRequest(
        agent_name=agent_name,
        room=f"rho-outbound-{call.request_id}",
        metadata=call.to_metadata(),
    )


async def _dispatch(call: OutboundCallRequest, agent_name: str) -> str:
    livekit_api = api.LiveKitAPI()
    try:
        dispatch = await livekit_api.agent_dispatch.create_dispatch(
            build_dispatch_request(call, agent_name=agent_name)
        )
        return dispatch.id
    finally:
        await livekit_api.aclose()


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Preview or dispatch one authorized synthetic Rho outbound call."
    )
    parser.add_argument("--phone-number", required=True, help="E.164 test destination")
    parser.add_argument(
        "--request-id",
        default=f"demo-{secrets.token_hex(4)}",
        help="lowercase request identifier used in room and participant names",
    )
    parser.add_argument(
        "--agent-name",
        default=os.getenv("RHO_OUTBOUND_AGENT_NAME", OUTBOUND_AGENT_NAME),
    )
    parser.add_argument(
        "--record-file",
        type=Path,
        help="JSON file containing a validated synthetic centralized call record",
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="create the dispatch; without this flag the command only previews it",
    )
    parser.add_argument(
        "--authorized-test-call",
        action="store_true",
        help="confirm that the destination owner authorized this test call",
    )
    return parser


def main() -> None:
    """Preview a call by default and dispatch only after both safety gates."""
    load_settings()
    args = _parser().parse_args()

    if args.execute and not args.authorized_test_call:
        raise SystemExit("--execute requires --authorized-test-call")
    if (
        args.execute
        and os.getenv("RHO_ENABLE_OUTBOUND_CALLS", "false").lower() != "true"
    ):
        raise SystemExit("set RHO_ENABLE_OUTBOUND_CALLS=true before using --execute")

    call_record = _load_call_record(args.record_file)
    call = OutboundCallRequest(
        phone_number=args.phone_number,
        request_id=args.request_id,
        demo_only=True,
        authorized_test_call=args.authorized_test_call,
        call_record=call_record,
    )
    try:
        call.validate_structure()
        if args.execute:
            call.validate()
    except ValueError as exc:
        raise SystemExit(f"invalid outbound request: {exc}") from exc

    request = build_dispatch_request(call, agent_name=args.agent_name)
    preview = {
        "agent_name": request.agent_name,
        "room": request.room,
        "request_id": call.request_id,
        "call_record_id": call.call_record.record_id,
        "business_name": call.call_record.business_name,
        "required_documents": [
            document.display_name for document in call.call_record.required_documents
        ],
        "deadline": call.call_record.upload_deadline.isoformat(),
        "destination": call.masked_phone_number,
        "authorized_test_call": call.authorized_test_call,
        "mode": "execute" if args.execute else "preview",
    }
    print(json.dumps(preview, indent=2, sort_keys=True))

    if args.execute:
        dispatch_id = asyncio.run(_dispatch(call, args.agent_name))
        print(json.dumps({"dispatch_id": dispatch_id}, indent=2))


def _load_call_record(path: Path | None) -> CentralizedCallRecord:
    if path is None:
        return DEMO_CALL_RECORD
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"record file must contain valid JSON: {exc}") from exc
    except OSError as exc:
        raise SystemExit(f"could not read record file: {exc}") from exc
    try:
        return CentralizedCallRecord.from_dict(payload)
    except ValueError as exc:
        raise SystemExit(f"invalid call record: {exc}") from exc


if __name__ == "__main__":
    main()
