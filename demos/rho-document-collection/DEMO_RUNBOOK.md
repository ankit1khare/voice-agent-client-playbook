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
- Required documents: August 2026 bank statements and Q2 2026 interim financials
- Spoken document wording: "second quarter 2026 interim financials" to avoid
  pronouncing the `Q2` abbreviation incorrectly
- Deadline: Tuesday, September 22, 2026
- Upload path: Settings, Business Documents

Every business and contact detail is fictional. The upload path and support
contact information follow Rho's September 9 direction: `clientservice@rho.co`
and `1-855-743-8746`.

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
2. State both required documents and the Tuesday, September 22 deadline.
3. Walk through Settings, Business Documents.
4. Stay on the line and ask what the caller sees after each step.
5. Record any commitment, extension request, disputed deadline, claimed prior
   upload, requirement-change request, existing Rho contact, secure-link request,
   or human-transfer request as a demo-only Zendesk ticket preview.
6. Never claim she can see the screen, confirm receipt, update Zendesk, approve
   an extension, or complete a human transfer.

## Questions to demonstrate

- I need an extension until September 25.
- I thought the deadline was September 24.
- I already uploaded the documents.
- I am already working with Lucas at Rho.
- The file is too large. Can you send a secure link?
- Can you transfer me to Client Service?
- Can you tell me whether I should submit this for tax purposes?

Jenny should record the applicable preview, state the limits of the demo, and
decline the financial-advice request. She must not invent a secure link or say an
external system changed.

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
  --record-file ../assets/demo_call_record.json \
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

## Show the Zendesk preview without calling

This command performs no network request and writes nothing to Zendesk:

~~~bash
cd demos/rho-document-collection/voice_agent
uv run rho-zendesk-preview \
  --disposition extension_requested \
  --request-id rho-demo-sep10 \
  --requested-submission-date 2026-09-25
~~~

## Acceptance checklist

| Check | Expected result |
|---|---|
| Opening | Exact disclosure mentions AI, possible recording, and no financial advice. |
| Known business | Northstar returns both required documents and the September 22 deadline. |
| Guided upload | Jenny gives one step at a time and asks what the caller sees. |
| Caller-reported completion | Jenny acknowledges the report but does not claim Rho confirmed receipt. |
| Extension request | Jenny captures the requested date, routes the preview to Underwriting, and does not promise approval. |
| Deadline dispute | Jenny records the expected date and does not guess which deadline is correct. |
| Existing Rho contact | Jenny records the person's name and status without claiming an existing case changed. |
| Human request | Jenny records a transfer preview, says live transfer is disabled, and does not dial Client Service. |
| Zendesk preview | The payload says `demo_only=true`, `write_performed=false`, and `zendesk_action=preview`. |
| Interruption | After the fixed opening, ordinary caller speech stops Jenny within the VAD threshold. |
| False interruption | If noise stops an interruptible response without producing a caller turn, Jenny resumes after two seconds. |
| Interrupted workflow result | If a caller talks over a required status or boundary, Jenny finishes the material result before continuing. |
| Inbound agent hangup | When the caller is done, Jenny says "Thank you for calling Rho. Have a great day.", waits for playout plus the carrier grace period, and disconnects the room. |
| Outbound agent hangup | When Jenny's outbound call is done, she says "Thanks, goodbye for now. Have a great day.", waits for playout plus the carrier grace period, and disconnects the room. |
| Session transcript | After the session closes, private cloud logs contain one structured `session_end_transcript` record with the timestamped chat history, tool calls, and complete follow-up preview payloads. |
| Unknown business | Jenny does not reveal Northstar or invent another record. |
| Access gate | No account-specific follow-up tool runs before inbound business or outbound listener verification succeeds. |
| Advice boundary | Jenny declines financial, legal, tax, underwriting, and credit advice. |
| Large file | Jenny records a secure-link request and does not invent or send a link. |
| Outbound dispatch | An authorized request reaches the persistent cloud worker and masks the destination in logs. |
| Support-number denylist | The dispatcher rejects `+1 855-743-8746` as a test destination, even with execution enabled. |
| Screened human | If call screening connects a person, that person hears the fixed disclosure and good-time question before account authorization begins. |
| Voicemail branch | AMD plays the exact reminder on `machine-vm`; the Coda WAV remains a presentation fallback. |
| Full-audio simulation | All eleven checked-in scenarios pass through STT, LLM, and TTS without injected noise; noise is a separate fail-closed ASR stress test. |
| Reliability gate | Five consecutive rehearsal calls complete without a critical failure. |

## Validation commands

Run from `voice_agent`:

~~~bash
uv run ruff check .
uv run ruff format --check .
uv run ty check src tests
uv run pytest
uv build
lk agent simulate audio --concurrency 4 --scenarios simulations/scenarios.yaml --yes --project rime src/rho_document_collection_voice_agent/main.py
~~~

Add `--background-noise` only for the optional ASR stress test.

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
