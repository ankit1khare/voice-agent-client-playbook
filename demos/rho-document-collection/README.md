# Rho document collection demo

Cloud-hosted voice-agent demo for Rho's missing-document workflow. Ethan can
either call the inbound demo number or dispatch an explicitly authorized
outbound call to a test number. Both paths run in the same LiveKit Cloud worker
and remain available when the developer laptop is off.

The solution contains:

- `voice_agent`: Python LiveKit worker using Rime Coda through LiveKit Inference.
- `voice_agent/simulations`: deterministic full-audio behavioral checks.
- `assets`: fixed demo scripts and generated audio used during the presentation.
- `telephony`: reproducible inbound dispatch configuration for the demo number.
- `DEMO_RUNBOOK.md`: internal operating and rehearsal instructions.
- `OUTBOUND_RUNBOOK.md`: outbound dispatch instructions, AMD outcomes, and
  safety gates.

The demo uses a validated synthetic call record and ships with a fictional
Northstar Labs example containing several required documents. Live conversations
can produce structured Zendesk ticket previews for commitments, extension
requests, disputed deadlines, claimed prior uploads, existing Rho contacts,
requirement reviews, secure-link requests, and human-transfer requests. Every
preview says that no external write or transfer occurred.

The demo does not access Rho customer data, independently confirm uploads, write
to Zendesk, or transfer a caller. Outbound dialing requires an authorized-test
flag, explicit outbound metadata, and the cloud safety switch. The current shared
test trunk is for internal synthetic demos only; use a dedicated Rho trunk before
any customer or production call.
