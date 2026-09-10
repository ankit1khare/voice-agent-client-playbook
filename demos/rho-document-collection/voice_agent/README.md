# Rho document collection voice agents

A LiveKit Cloud worker for the Rho inbound demo and its guarded outbound path.
Inbound calls and explicitly authorized outbound dispatches share the
`rho-document-collection-demo` deployment.

The worker accepts a validated synthetic call record with several required
documents. During a conversation, tool calls can capture business dispositions
and log a `zendesk_ticket_preview`. The preview is local or private-log output
only. It always reports that no Zendesk write or live transfer occurred.

After the fixed disclosure, VAD barge-in stops Jenny after 0.3 seconds of caller
speech. When the caller is done, the end-call tool plays a fixed closing suited
to the call direction, waits for audio playout plus a one-second carrier grace
period, and deletes the room so the agent disconnects the phone call. Inbound
calls end with "Thank you for calling Rho. Have a great day." Outbound calls end
with "Thanks, goodbye for now. Have a great day."

At session end, the worker builds a LiveKit session report and writes the full
timestamped chat history, including tool calls and the complete list of
`zendesk_ticket_preview` payloads created during the call, as a structured
`session_end_transcript` record in the private cloud agent logs. This starts
with calls handled by the version that contains the hook. It cannot recover
earlier sessions.

The agent uses LiveKit Inference for the voice pipeline:

- STT: Deepgram Flux (`deepgram/flux-general`)
- LLM: Gemini 3.1 Flash Lite (`google/gemini-3.1-flash-lite`)
- TTS: Rime Coda with Wawona (`rime/coda`, `wawona`)

LiveKit Cloud supplies the worker credentials and LiveKit Inference does not
require separate Deepgram, LLM-provider, or Rime API keys. The first cloud job
verified that AI Acoustics loads without an additional agent secret.

## Local development

Copy `.env.example` to `.env.local` and provide the LiveKit project credentials.

~~~bash
uv sync
uv run python -m rho_document_collection_voice_agent.main console
~~~

Use development mode to connect the local worker to LiveKit Cloud:

~~~bash
lk agent dev \
  --project rime \
  src/rho_document_collection_voice_agent/main.py
~~~

## Persistent cloud deployment

The checked-in `livekit.toml` points to cloud agent `CA_Ma2qDzcPwggq`. Deploy
from a clean commit so LiveKit records the source revision:

~~~bash
cd demos/rho-document-collection/voice_agent
lk agent deploy --project rime .
~~~

The runtime is LiveKit Cloud, not the machine that runs the deploy command.

## Guarded outbound path

`outbound_main.py` implements explicit outbound dispatch, stored-trunk dialing,
LiveKit AMD, human and voicemail branches, and structured outcomes. It defaults
to the fictional Northstar Labs record and accepts another validated synthetic
record. Source defaults remain disabled; the cloud deployment holds its runtime
switch and test-trunk ID as LiveKit secrets.

If a phone-screening service answers first, the worker keeps normal agent replies
paused while it waits for the screening result. A human connection resumes the
conversation by replaying the fixed disclosure directly to that person and waiting
for their answer. A later voicemail invitation plays the complete fixed voicemail
and disconnects without the conversational goodbye.

Routine conversation and workflow acknowledgements allow caller interruption.
If voice activity interrupts a response but no caller turn follows, Jenny resumes
after the two-second false-interruption timeout instead of going silent.
If a real caller interrupts a required workflow status or boundary, Jenny carries
the exact result into her next reply so the caller still hears the material point.
The AI and recording disclosure, voicemail, and final goodbye remain
non-interruptible so those required messages play completely.

The dispatcher always rejects Rho Client Service (`+1 855-743-8746`) as a test
destination, including when execution is enabled.

Previewing a request masks the destination and does not write to LiveKit:

~~~bash
uv run rho-outbound-dispatch \
  --phone-number +14155550123 \
  --request-id demo-preview \
  --record-file ../assets/demo_call_record.json
~~~

See `../OUTBOUND_RUNBOOK.md` for the safety gates and test-call procedure. The
current shared trunk is limited to authorized internal synthetic tests; replace
it with a dedicated Rho trunk before customer or production use.

## Preview a Zendesk ticket

Generate the payload for an extension request without calling or writing to an
external system:

~~~bash
uv run rho-zendesk-preview \
  --disposition extension_requested \
  --request-id rho-demo-sep10 \
  --requested-submission-date 2026-09-25
~~~

The command prints `demo_only: true`, `write_performed: false`, and
`zendesk_action: preview` with the fictional call record and suggested route.

## Render the voicemail demo clip

After creating `.env.local`, run:

~~~bash
uv run python scripts/render_voicemail.py
~~~

This writes `../assets/jenny_voicemail_reminder.wav` using Rime Coda with the
same Wawona voice as the live agent.

## Checks

~~~bash
uv run ruff check .
uv run ruff format --check .
uv run ty check src tests
uv run pytest
uv build
~~~

## Voice simulation

The checked-in suite exercises the complete STT, LLM, and TTS pipeline:

~~~bash
lk agent simulate audio \
  --concurrency 4 \
  --scenarios simulations/scenarios.yaml \
  --yes \
  --project rime \
  src/rho_document_collection_voice_agent/main.py
~~~

This is the deterministic meeting gate. Add `--background-noise` separately for
an optional ASR stress test; ambiguous business names should fail closed.

See `SIMULATION_RESULTS.md` for the latest run.
