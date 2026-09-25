# Voice agent client playbook

Build and deploy **Nudge**, a Python voice agent for document follow-up with
LiveKit and Rime Coda. This is the code from the Rime tutorial and video.

Nudge uses Deepgram Flux for speech recognition, Gemini 3.1 Flash Lite for
conversation and tool selection, and Rime's Wawona voice through the Coda
WebSocket endpoint. Python tools validate extension requests, create local
workflow previews, and recover required acknowledgments after interruptions.

[Read the tutorial](https://www.rime.ai/resources/build-and-deploy-voice-agents-with-livekit-and-rime)
· [Watch the video](https://www.youtube.com/watch?v=pKhtCMqb9YM)
· [Browse the Nudge project](demos/nudge)

## Run Nudge

Install [uv](https://docs.astral.sh/uv/), then clone this repository:

```bash
git clone https://github.com/ankit1khare/voice-agent-client-playbook.git
cd voice-agent-client-playbook/demos/nudge
cp .env.example .env.local
uv sync --locked
```

Set `LIVEKIT_URL`, `LIVEKIT_API_KEY`, `LIVEKIT_API_SECRET`, and `RIME_API_KEY`
in `.env.local`, then start a microphone and speaker session:

```bash
uv run python -m nudge_voice_agent.main console
```

Say `Northstar Labs Incorporated`, ask which documents are missing, and request
more time through September 25, 2026. Interrupt the acknowledgment and ask whether
the extension is approved. Nudge should preserve the requested date and explain
that the request still needs review.

The fixture uses fictional account data and fixed September 2026 dates. Workflow
tools create local previews; they do not write to a support system, approve
extensions, or verify document receipt. Outbound calling is disabled by default.

The [Nudge README](demos/nudge/README.md) covers browser sessions, Coda streaming,
latency diagnostics, tests, and inbound phone deployment. Run its commands from
`demos/nudge`, which has its own dependencies, lockfile, and Dockerfile.

## Check Nudge

From `demos/nudge`:

```bash
uv run pytest --no-cov -q
uv run ruff check .
uv run ruff format --check .
uv run ty check src tests
uv build
```

Tests use local playback doubles. The included evaluation scripts measure first
audio and streamed input using your Rime key. Live calls are needed to assess
recognition, audible interruptions, and telephone latency.

## Earlier examples and customer planning

- [Original inbound starter](demos/starter.md), implemented in `src/client_voice_agent`.
- [Rho document collection](demos/rho-document-collection), with inbound and guarded
  outbound calls, voicemail handling, synthetic data, and operating runbooks.
- [Original build article](ARTICLE.md), [customer worksheet](CUSTOMER_WORKSHEET.md),
  and [implementation plan](IMPLEMENTATION_PLAN.md).

Each demo has its own setup. Nudge uses a direct Rime connection and needs a
`RIME_API_KEY`; the earlier root example uses LiveKit Inference for TTS.

## License

[MIT](LICENSE)
