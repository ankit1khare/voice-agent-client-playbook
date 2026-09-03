# Rho inbound simulation results

## 2026-09-02 full-audio run

- LiveKit run: `SR_hnZY5c4LSkBR`
- Result: 5 passed, 0 failed
- Mode: speech-to-speech with generated background noise
- Source: local worker connected to the `rime` LiveKit Cloud project
- Scenarios: `simulations/scenarios.yaml`
- Dashboard: <https://cloud.livekit.io/projects/p_64a692accjl/simulations/runs/SR_hnZY5c4LSkBR>

The worker logs confirm microphone audio input, STT-based turn commits, the Rime
Coda output path, and room audio I/O. The five scenarios covered:

1. Known-business document details and upload path.
2. Unknown-business privacy and record isolation.
3. Step-by-step upload guidance and the no-false-confirmation boundary.
4. Oversized-file guidance and financial-advice refusal.
5. Unsupported-policy questions and human-support fallback.

LiveKit's evaluator reported no actionable defect. The run consistently preserved
the approved opening, synthetic record, upload walkthrough, privacy gate, and
receipt-confirmation boundary.

This run exercises the same source and model configuration as the deployed agent,
but it starts a temporary local worker. It does not replace a call to the deployed
phone number over the public telephone network.

## Reproduce

Run from `voice_agent`:

~~~bash
lk agent simulate audio \
  --background-noise \
  --concurrency 2 \
  --scenarios simulations/scenarios.yaml \
  --yes \
  --project rime \
  src/rho_document_collection_voice_agent/main.py
~~~
