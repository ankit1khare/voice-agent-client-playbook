# Rho inbound simulation results

## 2026-09-09 post-review deployment gate

- LiveKit run: `SR_hgHEXEJ8r9YC`
- Result: 10 passed, 0 failed
- Mode: full speech-to-speech without injected ambient noise
- Models: Deepgram Flux, Gemini 3.1 Flash Lite, and Rime Coda/Wawona
- Source: temporary local worker connected to the `rime` LiveKit Cloud project
- Scenarios: `simulations/scenarios.yaml`
- Dashboard: <https://cloud.livekit.io/projects/p_64a692accjl/simulations/runs/SR_hgHEXEJ8r9YC>

This is the deployment gate after the September 9 review fixes. It verifies the
TTS-safe "second quarter" wording, one-time business verification, deterministic
document/deadline/upload-path delivery, all follow-up paths, and the privacy and
advice boundaries. The simulation log contains no tool, worker, or session-report
errors.

The preceding run, `SR_s4gsSpMaqUQd`, passed 9/10. Its known-business scenario
exposed an intermittent response that acknowledged the request and stopped before
giving the documents. The new access-gated `share_document_request_details` tool
replaced that free-form response and the full rerun passed.

## 2026-09-09 initial ten-scenario run

- LiveKit run: `SR_9kJbcwMi8f5Y`
- Result: 10 passed, 0 failed
- Mode: full speech-to-speech without injected ambient noise
- Models: Deepgram Flux, Gemini 3.1 Flash Lite, and Rime Coda/Wawona
- Source: temporary local worker connected to the `rime` LiveKit Cloud project
- Scenarios: `simulations/scenarios.yaml`
- Dashboard: <https://cloud.livekit.io/projects/p_64a692accjl/simulations/runs/SR_9kJbcwMi8f5Y>

The suite covers business verification, multi-document disclosure, upload
guidance, prior-upload claims, upload commitments, extension requests, deadline
disputes, existing Rho contacts, recurring-requirement changes, large-file
requests, advice boundaries, and disabled human-transfer behavior. It performs
no Zendesk write, document-status lookup, telephone call, or live transfer.

During development, Gemma produced intermittent mid-response stalls. A focused
three-scenario reliability run passed 3/3 after changing the default LLM to
Gemini 3.1 Flash Lite and filtering the verification tool by call direction:
`SR_RoLTVpgNE3fU`. The final ten-scenario result above uses that exact local
configuration.

Generated background noise remains a separate ASR stress test. A corrupted or
ambiguous business name must fail closed rather than reveal account-specific
information; the meeting acceptance gate does not require every noisy utterance
to transcribe successfully.

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
  --concurrency 4 \
  --scenarios simulations/scenarios.yaml \
  --yes \
  --project rime \
  src/rho_document_collection_voice_agent/main.py
~~~

Add `--background-noise` when running the optional ASR stress test.
