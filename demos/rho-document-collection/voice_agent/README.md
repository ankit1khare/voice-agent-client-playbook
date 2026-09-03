# Rho document collection voice agents

A LiveKit Cloud worker for the Rho inbound demo and its guarded outbound path.
Inbound calls and explicitly authorized outbound dispatches share the
`rho-document-collection-demo` deployment.

After the fixed disclosure, VAD barge-in stops Jenny after 0.3 seconds of caller
speech. When the caller is done, LiveKit's end-call tool plays the final goodbye
and deletes the room so the agent disconnects the phone call.

The agent uses LiveKit Inference for the voice pipeline:

- STT: Deepgram Flux (`deepgram/flux-general`)
- LLM: Gemma (`google/gemma-4-31b-it`)
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

The checked-in `livekit.toml` points to cloud agent `CA_Ma2qDzcPwggq`. Deploy a
clean committed snapshot from the repository root with the repository's release
adapter:

~~~bash
./scripts/deploy-livekit-agent \
  --source customers/rho/document_collection_demo/voice_agent \
  -- \
  --project rime
~~~

The runtime is LiveKit Cloud, not the machine that runs the deploy command.

## Guarded outbound path

`outbound_main.py` implements explicit outbound dispatch, stored-trunk dialing,
LiveKit AMD, human and voicemail branches, and structured outcomes. It uses only
the fictional Northstar Labs record. Source defaults remain disabled; the cloud
deployment holds its runtime switch and test-trunk ID as LiveKit secrets.

Previewing a request masks the destination and does not write to LiveKit:

~~~bash
uv run rho-outbound-dispatch \
  --phone-number +14155550123 \
  --request-id demo-preview
~~~

See `../OUTBOUND_RUNBOOK.md` for the safety gates and test-call procedure. The
current shared trunk is limited to authorized internal synthetic tests; replace
it with a dedicated Rho trunk before customer or production use.

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

The checked-in suite exercises the complete STT, LLM, and TTS pipeline with
background noise:

~~~bash
lk agent simulate audio \
  --background-noise \
  --concurrency 2 \
  --scenarios simulations/scenarios.yaml \
  --yes \
  --project rime \
  src/rho_document_collection_voice_agent/main.py
~~~

See `SIMULATION_RESULTS.md` for the latest run.
