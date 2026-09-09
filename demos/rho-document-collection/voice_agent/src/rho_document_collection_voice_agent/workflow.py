"""Demo-only business dispositions and Zendesk ticket previews."""

from __future__ import annotations

import logging
import re
from enum import Enum
from typing import Any, Literal

from livekit.agents import RunContext, function_tool
from livekit.agents.llm import ToolError, ToolFlag, Toolset

from rho_document_collection_voice_agent.demo_context import (
    RHO_SUPPORT_EMAIL,
    RHO_SUPPORT_PHONE_SPOKEN,
    CentralizedCallRecord,
)

ZENDESK_TICKET_PREVIEW_EVENT = "zendesk_ticket_preview"

logger = logging.getLogger("rho-workflow-preview")


class ConversationDisposition(str, Enum):
    """Business result captured during a live reminder conversation."""

    NOT_A_GOOD_TIME = "not_a_good_time"
    PROMISE_TO_UPLOAD = "promise_to_upload"
    EXTENSION_REQUESTED = "extension_requested"
    PRIOR_UPLOAD_CLAIMED = "prior_upload_claimed"
    DEADLINE_DISPUTED = "deadline_disputed"
    REQUIREMENT_CHANGE_REQUESTED = "requirement_change_requested"
    EXISTING_RHO_CONTACT = "existing_rho_contact"
    HUMAN_TRANSFER_REQUESTED = "human_transfer_requested"
    SECURE_LINK_REQUESTED = "secure_link_requested"


_SUGGESTED_ROUTES = {
    ConversationDisposition.NOT_A_GOOD_TIME: "Client Service",
    ConversationDisposition.PROMISE_TO_UPLOAD: "Document collection team",
    ConversationDisposition.EXTENSION_REQUESTED: "Underwriting",
    ConversationDisposition.PRIOR_UPLOAD_CLAIMED: "Client Service",
    ConversationDisposition.DEADLINE_DISPUTED: "Underwriting",
    ConversationDisposition.REQUIREMENT_CHANGE_REQUESTED: "Review team, owner TBD",
    ConversationDisposition.EXISTING_RHO_CONTACT: "Client Service",
    ConversationDisposition.HUMAN_TRANSFER_REQUESTED: "Client Service",
    ConversationDisposition.SECURE_LINK_REQUESTED: "Client Service",
}


def build_zendesk_ticket_preview(
    *,
    record: CentralizedCallRecord,
    request_id: str,
    disposition: ConversationDisposition,
    details: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Build the external-write payload without sending it to Zendesk."""
    clean_details = {
        key: value.strip()
        for key, value in (details or {}).items()
        if isinstance(value, str) and value.strip()
    }
    transfer_requested = disposition is ConversationDisposition.HUMAN_TRANSFER_REQUESTED
    return {
        "demo_only": True,
        "write_performed": False,
        "source": "rho_voice_agent_demo",
        "request_id": request_id,
        "call_record_id": record.record_id,
        "business_name": record.business_name,
        "contact_name": record.contact_name,
        "required_documents": [
            document.display_name for document in record.required_documents
        ],
        "deadline": record.upload_deadline.isoformat(),
        "conversation_disposition": disposition.value,
        "suggested_route": _SUGGESTED_ROUTES[disposition],
        "details": clean_details,
        "human_transfer": {
            "requested": transfer_requested,
            "performed": False,
            "destination": "Rho Client Service" if transfer_requested else None,
        },
        "zendesk_action": "preview",
    }


class FollowUpPreviewTool(Toolset):
    """Capture follow-up work while all external integrations remain disabled."""

    def __init__(
        self,
        record: CentralizedCallRecord,
        request_id: str,
        verification_mode: Literal["business_name", "authorized_listener"] = (
            "business_name"
        ),
    ) -> None:
        super().__init__(id="rho_follow_up_preview")
        unavailable_gate = (
            "confirm_authorized_listener"
            if verification_mode == "business_name"
            else "verify_business_name"
        )
        self._tools = [tool for tool in self._tools if tool.id != unavailable_gate]
        self._record = record
        self._request_id = request_id
        self._verification_mode = verification_mode
        self._access_granted = False
        self.previews: list[dict[str, Any]] = []

    @property
    def access_granted(self) -> bool:
        """Return whether this call has passed its configured access gate."""
        return self._access_granted

    @function_tool(
        name="verify_business_name",
        description=(
            "Required before sharing account details or recording any account action. "
            "Pass exactly the business name spoken by the caller. Do not infer a match."
        ),
        flags=ToolFlag.IGNORE_ON_ENTER,
    )
    async def verify_business_name(
        self,
        ctx: RunContext,
        provided_business_name: str,
    ) -> str:
        """Match the caller-provided business name without exposing the record."""
        if self._verification_mode != "business_name":
            raise ToolError("Use confirm_authorized_listener for this outbound call.")
        provided = _required_detail(provided_business_name, "provided_business_name")
        self._access_granted = _business_key(provided) == _business_key(
            self._record.business_name
        )
        if self._access_granted:
            await self._disable_verification_tool(ctx, "verify_business_name")
            return (
                "Business verified. You may now discuss this record and use its "
                "follow-up tools."
            )
        return (
            "Business not verified. Do not reveal record details or use another "
            "follow-up tool. Ask the caller to restate or spell the full business "
            "name without suggesting a customer name."
        )

    @function_tool(
        name="confirm_authorized_listener",
        description=(
            "Required on an outbound call before account details or account actions. "
            "Set authorized to true only after the listener explicitly confirms they "
            "are the named contact or authorized to help with the business."
        ),
        flags=ToolFlag.IGNORE_ON_ENTER,
    )
    async def confirm_authorized_listener(
        self,
        ctx: RunContext,
        authorized: bool,
    ) -> str:
        """Gate outbound account access on the listener's explicit confirmation."""
        if self._verification_mode != "authorized_listener":
            raise ToolError("Use verify_business_name for this inbound call.")
        self._access_granted = authorized
        if authorized:
            await self._disable_verification_tool(ctx, "confirm_authorized_listener")
            return (
                "Listener authorization confirmed. You may now discuss the outbound "
                "record and use its follow-up tools."
            )
        return (
            "Listener is not authorized. Do not reveal record details or use an "
            "account-specific follow-up tool."
        )

    def record_preview(
        self,
        disposition: ConversationDisposition,
        **details: str,
    ) -> dict[str, Any]:
        """Create and log one demo-only follow-up payload."""
        preview = build_zendesk_ticket_preview(
            record=self._record,
            request_id=self._request_id,
            disposition=disposition,
            details=details,
        )
        self.previews.append(preview)
        logger.info(
            ZENDESK_TICKET_PREVIEW_EVENT,
            extra={"zendesk_ticket_preview": preview},
        )
        return preview

    @function_tool(
        name="share_document_request_details",
        description=(
            "After access verification, speak every required document, the exact "
            "deadline, and the upload path in one complete response. Use this instead "
            "of generating those details yourself."
        ),
        flags=ToolFlag.IGNORE_ON_ENTER,
    )
    async def share_document_request_details(self, ctx: RunContext) -> None:
        """Speak the complete reminder from validated call data."""
        self._require_access()
        await _speak_tool_result(
            ctx,
            f"Rho is still awaiting {self._record.spoken_required_documents}. "
            f"The submission deadline is {self._record.spoken_deadline}. You can "
            f"upload the documents under {self._record.spoken_upload_path}. Would "
            "you like me to walk you through the upload one step at a time?",
        )

    @function_tool(
        name="record_not_a_good_time",
        description=(
            "Record that the client cannot talk now. Include a preferred callback "
            "time only if the client volunteered one. This does not schedule a call."
        ),
        flags=ToolFlag.IGNORE_ON_ENTER,
    )
    async def record_not_a_good_time(
        self,
        ctx: RunContext,
        preferred_callback_time: str = "",
    ) -> str:
        """Record an unavailable client without inventing a callback."""
        del ctx
        self.record_preview(
            ConversationDisposition.NOT_A_GOOD_TIME,
            preferred_callback_time=preferred_callback_time,
        )
        return "The demo follow-up preview is saved. No callback was scheduled."

    @function_tool(
        name="record_upload_commitment",
        description=(
            "Record the exact date the client promises to upload the documents. "
            "Ask for a calendar date before calling this tool."
        ),
        flags=ToolFlag.IGNORE_ON_ENTER,
    )
    async def record_upload_commitment(
        self,
        ctx: RunContext,
        promised_upload_date: str,
    ) -> None:
        """Record a client's promised upload date."""
        self._require_access()
        promised_date = _required_detail(promised_upload_date, "promised_upload_date")
        self.record_preview(
            ConversationDisposition.PROMISE_TO_UPLOAD,
            promised_upload_date=promised_date,
        )
        await _speak_tool_result(
            ctx,
            f"I've recorded your commitment to upload the documents on "
            f"{promised_date}. I'll pass that date to the document collection "
            "team. Do you need anything else?",
        )

    @function_tool(
        name="record_extension_request",
        description=(
            "Record the exact date requested for an extension. This creates only a "
            "demo preview and does not approve the extension."
        ),
        flags=ToolFlag.IGNORE_ON_ENTER,
    )
    async def record_extension_request(
        self,
        ctx: RunContext,
        requested_submission_date: str,
    ) -> None:
        """Record an extension request for Underwriting review."""
        self._require_access()
        requested_date = _required_detail(
            requested_submission_date, "requested_submission_date"
        )
        self.record_preview(
            ConversationDisposition.EXTENSION_REQUESTED,
            requested_submission_date=requested_date,
        )
        await _speak_tool_result(
            ctx,
            f"I've recorded your extension request through {requested_date} for "
            "Underwriting to review. It is not approved yet. Do you need anything "
            "else?",
        )

    @function_tool(
        name="record_prior_upload_claim",
        description=(
            "Record that the client says the documents were already uploaded. "
            "This tool does not check or confirm document status."
        ),
        flags=ToolFlag.IGNORE_ON_ENTER,
    )
    async def record_prior_upload_claim(self, ctx: RunContext) -> None:
        """Record the client's unverified upload report."""
        self._require_access()
        self.record_preview(ConversationDisposition.PRIOR_UPLOAD_CLAIMED)
        await _speak_tool_result(
            ctx,
            "I've recorded that you reported the upload complete for Client Service "
            "to check. I can't independently confirm receipt. Do you need anything "
            "else?",
        )

    @function_tool(
        name="record_deadline_dispute",
        description=(
            "Record the deadline the client expected. Do not guess which deadline "
            "is correct or promise that it will change."
        ),
        flags=ToolFlag.IGNORE_ON_ENTER,
    )
    async def record_deadline_dispute(
        self,
        ctx: RunContext,
        client_expected_deadline: str,
    ) -> None:
        """Record a disputed deadline for Underwriting review."""
        self._require_access()
        expected_deadline = _required_detail(
            client_expected_deadline, "client_expected_deadline"
        )
        self.record_preview(
            ConversationDisposition.DEADLINE_DISPUTED,
            client_expected_deadline=expected_deadline,
        )
        await _speak_tool_result(
            ctx,
            f"I've recorded that you expected {expected_deadline}. Underwriting "
            "will need to check the discrepancy. I can't confirm which date is "
            "correct. Do you need anything else?",
        )

    @function_tool(
        name="record_requirement_change_request",
        description=(
            "Record why the client wants Rho to review the recurring document "
            "requirement. Do not promise that the requirement will change."
        ),
        flags=ToolFlag.IGNORE_ON_ENTER,
    )
    async def record_requirement_change_request(
        self,
        ctx: RunContext,
        reason: str,
    ) -> None:
        """Record a request to review the monthly requirement."""
        self._require_access()
        change_reason = _required_detail(reason, "reason")
        self.record_preview(
            ConversationDisposition.REQUIREMENT_CHANGE_REQUESTED,
            reason=change_reason,
        )
        await _speak_tool_result(
            ctx,
            "I've recorded your reason for the appropriate team to review. No "
            "requirement has been changed. Do you need anything else?",
        )

    @function_tool(
        name="record_existing_rho_contact",
        description=(
            "Record the Rho employee the client is already working with and the "
            "client's latest status. Do not claim an existing case was updated."
        ),
        flags=ToolFlag.IGNORE_ON_ENTER,
    )
    async def record_existing_rho_contact(
        self,
        ctx: RunContext,
        rho_contact_name: str,
        status_update: str,
    ) -> None:
        """Record an existing human support relationship."""
        self._require_access()
        contact_name = _required_detail(rho_contact_name, "rho_contact_name")
        latest_status = _required_detail(status_update, "status_update")
        self.record_preview(
            ConversationDisposition.EXISTING_RHO_CONTACT,
            rho_contact_name=contact_name,
            status_update=latest_status,
        )
        await _speak_tool_result(
            ctx,
            f"I've recorded that you're working with {contact_name} and that "
            f"{latest_status}. I didn't update any existing case. Do you need "
            "anything else?",
        )

    @function_tool(
        name="request_human_transfer",
        description=(
            "Record that the client requested a human. Live transfer is disabled "
            "in this demo, so this tool must never claim that a transfer occurred."
        ),
        flags=ToolFlag.IGNORE_ON_ENTER,
    )
    async def request_human_transfer(
        self,
        ctx: RunContext,
        reason: str = "",
    ) -> None:
        """Exercise the disabled transfer branch and record the request."""
        self._require_access()
        self.record_preview(
            ConversationDisposition.HUMAN_TRANSFER_REQUESTED,
            reason=reason,
        )
        await _speak_tool_result(
            ctx,
            "I've recorded your request for Client Service. Live transfer is "
            f"unavailable in this demo. You can call {RHO_SUPPORT_PHONE_SPOKEN} or "
            f"email {RHO_SUPPORT_EMAIL}. Do you need anything else?",
        )

    @function_tool(
        name="record_secure_link_request",
        description=(
            "Record that a file is too large and the client needs an approved secure "
            "upload link. Do not invent or provide a link."
        ),
        flags=ToolFlag.IGNORE_ON_ENTER,
    )
    async def record_secure_link_request(self, ctx: RunContext) -> None:
        """Record a large-file help request for Client Service."""
        self._require_access()
        self.record_preview(ConversationDisposition.SECURE_LINK_REQUESTED)
        await _speak_tool_result(
            ctx,
            "I've recorded a secure upload link request for Client Service. Client "
            "Service must provide an approved link; no link was sent. Do you need "
            "anything else?",
        )

    def _require_access(self) -> None:
        if not self._access_granted:
            raise ToolError(
                "Access not verified. Do not say anything was recorded. Complete the "
                "configured identity or authorization check first."
            )

    async def _disable_verification_tool(
        self,
        ctx: RunContext,
        tool_name: str,
    ) -> None:
        """Remove a completed access check from later model turns."""
        self._tools = [tool for tool in self._tools if tool.id != tool_name]
        if ctx is not None:
            current_agent = ctx.session.current_agent
            await current_agent.update_tools(current_agent.tools)


def build_follow_up_preview_tool(
    record: CentralizedCallRecord,
    request_id: str,
    verification_mode: Literal["business_name", "authorized_listener"] = (
        "business_name"
    ),
) -> FollowUpPreviewTool:
    """Return a new per-call preview toolset."""
    return FollowUpPreviewTool(record, request_id, verification_mode)


def _required_detail(value: str, name: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise ToolError(f"{name} must not be empty")
    if len(normalized) > 500:
        raise ToolError(f"{name} must be at most 500 characters")
    return normalized


def _business_key(value: str) -> str:
    """Normalize ordinary legal-suffix and spacing variants for exact matching."""
    words = re.findall(r"[a-z0-9]+", value.casefold())
    suffixes = {
        "co",
        "company",
        "corp",
        "corporation",
        "inc",
        "incorporated",
        "llc",
    }
    while words and words[-1] in suffixes:
        words.pop()
    return "".join(words)


async def _speak_tool_result(ctx: RunContext, message: str) -> None:
    """Speak a required workflow outcome fully and prevent a second model reply."""
    ctx.disallow_interruptions()
    await ctx.wait_for_playout()
    speech = ctx.session.say(message, allow_interruptions=False)
    await speech.wait_for_playout()
