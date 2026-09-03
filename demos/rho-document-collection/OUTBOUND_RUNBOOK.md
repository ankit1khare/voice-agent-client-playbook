# Rho outbound demo runbook

The Phase 1.5 outbound path runs inside the persistent
`rho-document-collection-demo` LiveKit Cloud worker. It uses only the fictional
Northstar Labs record. Every call still requires an explicit dispatch and an
authorized-test flag.

## What it does

The worker creates an outbound SIP participant through a stored third-party trunk.
LiveKit AMD listens before Jenny speaks and classifies the answer:

| AMD result | Rho outcome | Action |
|---|---|---|
| `human` or `uncertain` | `human_answered` | Play the fixed disclosure and start the document-reminder conversation. |
| `machine-vm` | `voicemail_left` | Play the exact Coda voicemail message and end the call. |
| `machine-ivr` | `ivr_detected` or `ivr_screening_continued` | End by default. For an authorized call-screening test, play the disclosure and keep the call open. |
| `machine-unavailable` | `mailbox_unavailable` | End without leaving a message. |

Pre-answer SIP failures map to `busy_or_rejected`, `no_answer`, or `dial_failed`.
Every attempt writes a structured `outbound_call_result` record to the worker log.
The record omits the destination number.

## Safety controls

- The metadata must say `demo_only=true` and `authorized_test_call=true`.
- `RHO_ENABLE_OUTBOUND_CALLS` defaults to `false` in source and must be enabled
  explicitly by the dispatcher. The cloud worker holds its runtime switch as a
  LiveKit secret.
- `RHO_OUTBOUND_TRUNK_ID` has no source default. The cloud demo currently uses
  the existing VoiceLab trunk for authorized internal synthetic tests only.
- `RHO_ALLOW_IVR_SCREENING` defaults to `false`. Enable it only for an
  authorized test number with a known call-screening service. Jenny then plays
  the approved disclosure into the screening prompt and keeps the call open.
- The dispatcher previews a masked destination unless `--execute` is present.
- Replace the shared test trunk with a dedicated Rho trunk before any customer
  or production call.
- The current inbound deployment and number are unchanged.

The outbound disclosure is a draft for the synthetic demo. Rho must approve the
production wording, consent rules, voicemail content, and retention policy before
any customer call.

## Preview a call

This command performs no LiveKit write and places no call:

~~~bash
uv run rho-outbound-dispatch --phone-number +14155550123
~~~

## Cloud worker

Inbound and outbound requests share agent `rho-document-collection-demo`.
Ordinary jobs follow the inbound path. Only metadata with
`mode=rho_outbound_test` can select the outbound path. The current cloud secrets
enable outbound dialing, provide the test trunk ID, and allow the known phone
screening flow. Secret values are not stored in the repository.

Check availability from any authorized checkout:

~~~bash
lk agent status --project rime
lk agent secrets --project rime
~~~

## Place an authorized test call

Run this only with a number whose owner agreed to receive the call:

~~~bash
RHO_ENABLE_OUTBOUND_CALLS=true uv run rho-outbound-dispatch \
  --phone-number +14155550123 \
  --request-id ethan-demo-YYYYMMDD \
  --authorized-test-call \
  --execute
~~~

The command creates the dispatch and can exit immediately. LiveKit Cloud places
and runs the call; no local worker must remain active.

## Deploy from the repository

Deploy from a clean repository commit so LiveKit records the source revision:

~~~bash
cd demos/rho-document-collection/voice_agent
lk agent deploy --project rime .
~~~

Existing cloud secrets remain attached to the agent. If a trunk or safety switch
changes, update the values through LiveKit's secret controls rather than putting
them in Git.

## Disabled-path integration check

On 2026-09-02, a local outbound worker registered as
`rho-document-collection-outbound-demo`. Explicit dispatch `AD_iGKbzZcmw3wa`
used an authorized synthetic request while the worker's outbound switch remained
off and no Rho trunk was configured. The worker logged `outbound_disabled`, did
not create a SIP participant, deleted the temporary room, and shut down cleanly.
No phone call was placed.

## Authorized cell test

On 2026-09-03, Ankit authorized two test attempts to his cell. Both used the
existing `voicelab-twilio` trunk for this test only. No trunk configuration was
changed, and this does not make that trunk the Rho trunk.

The first dispatch, `AD_5cygX2tT4dtz`, reached the phone's call-screening
assistant. AMD returned `machine-ivr`, so the default policy ended the call.

The second dispatch, `AD_4czbbrVDggKL`, ran with
`RHO_ALLOW_IVR_SCREENING=true`. Jenny played the exact outbound disclosure into
the screening prompt and remained connected. After Ankit accepted the call, the
test completed the synthetic Northstar Labs flow:

1. The caller confirmed they were Maya.
2. Jenny stated the August 2026 bank statement and September 14 deadline.
3. Jenny walked through the demo portal one step at a time.
4. When the caller said the upload was finished, Jenny said she could not see
   the screen or independently confirm receipt.
5. The caller ended the call.

The temporary worker stopped immediately after the test. The source defaults
remain `RHO_ENABLE_OUTBOUND_CALLS=false` and
`RHO_ALLOW_IVR_SCREENING=false`. The LiveKit session report indicates that
recording was enabled for the test call.

## Persistent cloud test

On 2026-09-03, the cloud worker registered as
`rho-document-collection-demo` with no local worker running. Dispatch
`AD_FAAqqJotMt9X` reached the authorized cell through the configured test trunk.
AMD classified the phone screening prompt as `machine-ivr`, Jenny played the
fixed disclosure, and the worker logged `ivr_screening_continued`. This confirms
that explicit outbound dispatch reaches the persistent cloud worker. The inbound
number continued to target the same agent through `SDR_z3WWrFFhrVr7`.

## Turn-taking and hangup

Jenny uses VAD barge-in with a 0.3-second minimum. Once the disclosure finishes,
ordinary caller speech stops the current response. The fixed disclosure and
voicemail message remain non-interruptible.

Both inbound and outbound assistants have an end-call tool. When the caller says
goodbye, says they need nothing else, or asks to end the call, Jenny says
"Thanks, goodbye for now. Have a great day." The tool waits for speech playout and gives
the carrier one additional second before it deletes the room and disconnects the
SIP call from the agent side.

After the session closes, the worker builds a LiveKit session report and writes
the complete timestamped chat history and tool calls to the private agent logs as
`session_end_transcript`. The hook applies only to calls handled after its
deployment and cannot recover an earlier transcript.

## Validate without dialing

~~~bash
uv run ruff check .
uv run ruff format --check .
uv run ty check src tests
uv run pytest
uv build
~~~
