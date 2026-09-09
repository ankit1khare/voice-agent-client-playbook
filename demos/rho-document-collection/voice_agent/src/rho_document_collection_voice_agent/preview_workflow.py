"""Print a demo-only Zendesk ticket preview without external writes."""

import argparse
import json

from rho_document_collection_voice_agent.demo_context import DEMO_CALL_RECORD
from rho_document_collection_voice_agent.workflow import (
    ConversationDisposition,
    build_zendesk_ticket_preview,
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Print a synthetic Zendesk ticket preview."
    )
    parser.add_argument(
        "--disposition",
        required=True,
        choices=[disposition.value for disposition in ConversationDisposition],
    )
    parser.add_argument("--request-id", default="rho-demo-preview")
    parser.add_argument("--promised-upload-date", default="")
    parser.add_argument("--requested-submission-date", default="")
    parser.add_argument("--client-expected-deadline", default="")
    parser.add_argument("--preferred-callback-time", default="")
    parser.add_argument("--rho-contact-name", default="")
    parser.add_argument("--status-update", default="")
    parser.add_argument("--reason", default="")
    return parser


def main() -> None:
    """Print one preview JSON object and make no external request."""
    args = _parser().parse_args()
    details = {
        "promised_upload_date": args.promised_upload_date,
        "requested_submission_date": args.requested_submission_date,
        "client_expected_deadline": args.client_expected_deadline,
        "preferred_callback_time": args.preferred_callback_time,
        "rho_contact_name": args.rho_contact_name,
        "status_update": args.status_update,
        "reason": args.reason,
    }
    preview = build_zendesk_ticket_preview(
        record=DEMO_CALL_RECORD,
        request_id=args.request_id,
        disposition=ConversationDisposition(args.disposition),
        details=details,
    )
    print(json.dumps(preview, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
