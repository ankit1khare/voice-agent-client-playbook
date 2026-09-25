# Nudge

A Python voice agent for document follow-up, built with LiveKit, Deepgram Flux,
Gemini 3.1 Flash Lite, and the Coda streaming endpoint using the Wawona voice.

Nudge explains which documents are needed, captures a request for more time,
and keeps a required acknowledgment pending if the caller interrupts it.
Workflow actions produce local previews. This tutorial does not connect a
support system, approve extensions, verify document receipt, or transfer calls.

[Read the tutorial](https://www.rime.ai/resources/build-and-deploy-voice-agents-with-livekit-and-rime)
· [Watch the video](https://www.youtube.com/watch?v=pKhtCMqb9YM)

## Run locally

Run these commands from `demos/nudge` in this repository.

Use `uv`; `.python-version` selects Python 3.14.6 for local development. Copy the environment template, then fill in your
LiveKit project URL, API key, and secret, plus `RIME_API_KEY`. Speech recognition,
the LLM, and VAD use LiveKit Inference. TTS connects directly to Rime through the
LiveKit Rime plugin. A LiveKit credential alone does not authenticate that request.

```bash
cp .env.example .env.local
uv sync --locked
uv run python -m nudge_voice_agent.main console
```

For a worker that a LiveKit browser client can reach:

```bash
uv run python -m nudge_voice_agent.main dev
```

The worker registers as `nudge-demo`. Configure your browser client or agent
playground to dispatch that name. The room and worker must use the same project.

The project excludes credentials and cloud agent IDs. Outbound calling defaults
to disabled. The video opens with an outbound call; the setup below uses inbound
calls. Reproducing the outbound direction also requires an outbound SIP trunk
and dispatch configuration.

## Coda streaming

The locked LiveKit Agents and Rime plugin versions are 1.8.3. Coda WebSocket v1
requires plugin 1.8.2 or later. This is the TTS configuration used by the session:

```python
from livekit.agents import AgentSession
from livekit.plugins import rime

session = AgentSession(
    tts=rime.TTS(
        websocket_url="wss://api.rime.ai/coda/ws",
        speaker="wawona",
        lang="en",
    ),
)
```

The complete session also configures STT, an LLM, VAD, and turn handling in
`runtime.py`. The endpoint selects Coda, so do not pass a separate model argument.
The plugin manages the connection and its protocol defaults.

For generated replies, LiveKit passes streamed LLM text into TTS. The plugin
buffers fragments into sentences and sends successive sentences in one synthesis
context. It can receive audio before all text for that reply is available. It does
not forward every individual token immediately. Do not add a sentence-by-sentence
`StreamAdapter` around this provider or force a flush after every token.

LiveKit calls the provider's prewarm hook when the session starts. The plugin
pools connections for sequential turns, and closes or cancels active synthesis
when interrupted. Local playback stops through LiveKit; application code separately
keeps required tool acknowledgments pending until their speech completes. A canceled
audio stream does not undo an action already recorded by a tool.

The fixed greeting and tool acknowledgments already have complete text. Streaming
LLM-input benefits apply to generated replies; do not attribute their benefit to a
fixed `session.say()` message. A shared context is intended to support consistent
delivery, but voice quality still needs listening checks on the actual workflow.

To run a controlled input-streaming and cancellation check, set `RIME_API_KEY` and
run `uv run python evaluations/coda_streaming_check.py --output /tmp/nudge-coda-check`.
It compares scheduled input chunks with waiting for the same whole text on the
same endpoint and voice. Its timing ends at PCM receipt, not phone playback.

## Find the implementation

1. Open `src/nudge_voice_agent/runtime.py` to see the STT, LLM, TTS, and turn-handling wiring.
2. Open `settings.py` for the endpoint and Wawona voice.
3. Open `demo_context.py` for the fictional Northstar Labs fixture.
4. Open `assistant.py` for the prompt and mandatory tool instructions.
5. Open `workflow.py` for access checks, request previews, and required-result recovery.
6. Open `call_control.py` for the spoken goodbye and disconnect sequence.

The video follows a deployed call and the main implementation choices. This
package includes the supporting modules, setup instructions, and checks.

## See a preview without a model or call

```bash
uv run nudge-zendesk-preview \
  --disposition extension_requested \
  --request-id nudge-tutorial \
  --requested-submission-date 2026-09-25
```

The preview command uses the fixture directly. The conversational tool separately
enforces its access check. `write_performed: false` means no external write took
place. The retained internal `zendesk` name identifies the preview schema, not a
live integration.

The business-name match is a demonstration gate for fictional data. A real
account integration needs its own authentication and authorization. Support
addresses use `nudge.example` and a fictional phone number. Fixed September 2026
dates are sample data; change the fixture before using a different scenario.

## Measure first audio with the configured voice

```bash
uv run python evaluations/coda_first_audio_check.py --output /tmp/nudge-first-audio
```

This check separates the first cold request from 20 sequential requests on the
warmed connection. It rotates five short replies, saves every audio sample, and
reports the median, P95, maximum, and failures. Timing starts when complete text
enters the plugin and ends at the first received PCM frame. It includes network
time, but excludes listening, LLM generation, and phone playback. The output
directory must be new so evidence from an earlier run is not overwritten.

Use `evaluations/coda_streaming_check.py` for the separate scheduled-input
comparison. Neither check measures perceived naturalness or competitor latency.

## Tests

```bash
uv run pytest --no-cov -q
uv run ruff check .
uv run ruff format --check .
uv run ty check src tests
uv build
```

Unit tests use local doubles for playback. They check workflow state and the
required spoken text. They do not establish live recognition quality, interruption
timing, phone connectivity, or response latency. Record a real call for those.

## Connect an inbound number

After a successful local rehearsal, create a Nudge worker in your chosen LiveKit
project using this directory. The Dockerfile is included. An existing demo can
also be replaced when its owner intends that change. Check the target in
`livekit.toml` before deploying.

Use LiveKit's agent deployment flow, then assign an inbound number to a dispatch
rule whose agent name is `nudge-demo`. Each call should enter a separate room.
Verify that the worker is online, then call your number and inspect the matching
session and request preview. This package does not rent a number or configure
your project automatically.

Current setup references:

- [LiveKit voice AI quickstart](https://docs.livekit.io/agents/start/voice-ai/)
- [LiveKit phone numbers](https://docs.livekit.io/telephony/start/phone-numbers/)
- [Inbound dispatch rules](https://docs.livekit.io/telephony/accepting-calls/dispatch-rule/)
- [Coda LiveKit integration](https://rimelabs-docs-coda-websocket-reference.mintlify.site/api-reference/coda/websockets-livekit)
- [Coda streaming lifecycle](https://rimelabs-docs-coda-websocket-reference.mintlify.site/api-reference/coda/websockets)

## Provenance

Adapted for this tutorial from the MIT-licensed `voice-agent-client-playbook`,
commit `07392744e41ca5062e2bd3f904b97113ddec38e1`. Product identifiers, assistant
name, support contacts, and package paths were changed for the fictional Nudge
demo. Nudge is a self-contained package under `demos/nudge`. Missing-date
placeholder validation was added
after an audio rehearsal exposed an extension request recorded with "unknown".
The experimental Jev branch was not copied. The original license is included.
