# Rho document collection demo runbook

Internal runbook for the Rho demo. Do not send this file to the customer because
it contains operator procedures and fallback instructions.

## Demo facts

- Agent: `rho-document-collection-demo`
- Agent persona: Jenny
- Demo phone number: `+1 240-251-1057`
- Outbound demo caller ID: `+1 831-231-0495`
- LiveKit Cloud agent: `CA_Ma2qDzcPwggq`
- SIP dispatch rule: `SDR_z3WWrFFhrVr7`
- Business: Northstar Labs, Inc.
- Contact: Maya Chen
- Missing document: August 2026 bank statement
- Deadline: Monday, September 14, 2026
- Upload path: Rho Demo Portal, Required Documents, Upload

Every account detail and the upload path are fictional.

## Opening

Jenny always starts with this fixed, non-interruptible disclosure:

> Hi, I'm Jenny, Rho's AI assistant. This call may be recorded. I can help with
> document upload questions, but I can't provide financial advice. What business
> are you calling about?

The caller should say:

> Hi, I'm calling from Northstar Labs. I think we're missing a document.

## Happy path

Jenny should:

1. Match Northstar Labs to the synthetic record.
2. State the August 2026 bank statement and Monday, September 14 deadline.
3. Walk through Rho Demo Portal, Required Documents, Upload.
4. Stay on the line and ask what the caller sees after each step.
5. Ask the caller to confirm whether the upload completed.
6. Never claim she can see the screen or that Rho confirmed receipt.

## Questions to demonstrate

- What should I do if the file is zipped?
- Is there a maximum file size?
- Can you tell me whether I should submit this for tax purposes?

Jenny should explain that compressed files must be unzipped, state the 10 MB
limit, and decline the financial-advice request.

## Run the demo

### Option A: Ethan calls Jenny

Call `+1 240-251-1057` from any phone. LiveKit routes the call directly to the
cloud-hosted `rho-document-collection-demo` worker. No developer laptop needs to
be running.

### Option B: Jenny calls Ethan

From any authorized checkout of this repository with LiveKit project
credentials, run:

~~~bash
cd demos/rho-document-collection/voice_agent
RHO_ENABLE_OUTBOUND_CALLS=true uv run rho-outbound-dispatch \
  --phone-number +1XXXXXXXXXX \
  --request-id ethan-demo-YYYYMMDD \
  --authorized-test-call \
  --execute
~~~

The command only creates a LiveKit dispatch. The persistent cloud worker places
and handles the call, so the developer laptop does not host the conversation.
Use only a number whose owner has agreed to the test call.

## Voicemail path

The outbound path runs LiveKit AMD and plays the fixed voicemail reminder when
AMD returns `machine-vm`. Keep `assets/jenny_voicemail_reminder.wav` as a
deterministic presentation fallback when the live call is answered by a human or
call-screening service. See `OUTBOUND_RUNBOOK.md` for the complete outcome map.

## Acceptance checklist

| Check | Expected result |
|---|---|
| Opening | Exact disclosure mentions AI, possible recording, and no financial advice. |
| Known business | Northstar returns the August 2026 bank statement and September 14 deadline. |
| Guided upload | Jenny gives one step at a time and asks what the caller sees. |
| Caller-reported completion | Jenny acknowledges the report but does not claim Rho confirmed receipt. |
| Interruption | After the fixed opening, ordinary caller speech stops Jenny within the VAD threshold. |
| Agent hangup | When the caller is done, Jenny says "Thanks for calling Rho. Goodbye," waits for playout plus the carrier grace period, and disconnects the room. |
| Unknown business | Jenny does not reveal Northstar or invent another record. |
| Advice boundary | Jenny declines financial, legal, tax, underwriting, and credit advice. |
| Upload questions | Jenny explains unzip-first and the 10 MB limit. |
| Outbound dispatch | An authorized request reaches the persistent cloud worker and masks the destination in logs. |
| Voicemail branch | AMD plays the exact reminder on `machine-vm`; the Coda WAV remains a presentation fallback. |
| Full-audio simulation | All five checked-in scenarios pass through STT, LLM, and TTS with background noise. |
| Reliability gate | Five consecutive rehearsal calls complete without a critical failure. |

## Validation commands

Run from `voice_agent`:

~~~bash
uv run ruff check .
uv run ruff format --check .
uv run ty check src tests
uv run pytest
uv build
lk agent simulate audio --background-noise --concurrency 2 --scenarios simulations/scenarios.yaml --yes --project rime src/rho_document_collection_voice_agent/main.py
~~~

Check the cloud worker:

~~~bash
lk agent status --project rime
lk agent logs --project rime
~~~

Confirm telephony routing:

~~~bash
lk number get --project rime --number +12402511057
lk sip dispatch list --project rime
~~~

## Fallback

If inbound telephony is unavailable, open LiveKit Agent Console, select
`rho-document-collection-demo`, and run the same caller script through the
browser microphone.
