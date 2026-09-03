# Voice agent client playbook

A runnable reference for turning a nontechnical customer's workflow into a
small, testable voice agent. The example handles one inbound document-reminder
call with LiveKit and Rime Coda.

The code is intentionally narrow. It uses one fictional organization, one
document request, and one approved help answer. That keeps the first demo easy
to review with the customer before anyone connects production data or telephony.

Start with the [build article](ARTICLE.md), use the
[customer worksheet](CUSTOMER_WORKSHEET.md) in discovery, and track delivery
with the [implementation plan](IMPLEMENTATION_PLAN.md).

## What the reference demonstrates

- A deterministic AI and recording disclosure spoken outside the LLM
- A synthetic record that can be inspected with the customer
- Identity gating before the agent shares document details
- A guided upload walkthrough without false back-end confirmation
- Short spoken turns and caller interruption handling
- Environment-configurable STT, LLM, and Rime Coda voice settings
- Unit tests for the conversation contract and runtime configuration

The example is an educational starting point. It is not a compliance program,
and it should not be connected to real customer data without review by the
people responsible for security, privacy, consent, and the underlying business
process.

## Architecture

```text
Caller or console
      |
      v
LiveKit room
      |
      +--> Deepgram Flux speech-to-text
      +--> Gemma language model
      +--> Rime Coda text-to-speech
      |
      v
Spoken response
```

LiveKit Inference supplies the model connections used in this reference. The
agent does not require separate Deepgram, Google, or Rime provider keys when it
runs in a compatible LiveKit Cloud project.

## Run it locally

Prerequisites:

- Python 3.11 through 3.14
- [uv](https://docs.astral.sh/uv/)
- A [LiveKit Cloud](https://cloud.livekit.io/) project

Install the project and create a local environment file:

```bash
uv sync
cp .env.example .env.local
```

Add your local LiveKit URL, API key, and API secret to `.env.local`, then start a
microphone and speaker session:

```bash
uv run python -m client_voice_agent.main console
```

Try these calls:

1. Say `Juniper Works` and ask what document is needed.
2. Ask the agent to stay on the line while you upload it.
3. Say the portal shows the upload as complete.
4. Start a new session with a different organization name.
5. Ask for legal or financial advice.

The agent should guide the upload, make clear that it cannot independently
confirm receipt, protect the fictional record in the unknown-organization case,
and decline advice.

## Deploy to LiveKit Cloud

Authenticate the LiveKit CLI, then create the first deployment from this
directory:

```bash
lk cloud auth
lk agent create --project YOUR_PROJECT .
```

The command creates `livekit.toml` for the deployment. For later versions, run:

```bash
lk agent deploy --project YOUR_PROJECT .
lk agent status --project YOUR_PROJECT
```

Connect a phone number only after the console flow passes the acceptance tests
in `IMPLEMENTATION_PLAN.md`. Inbound and outbound telephony each need their own
operating rules. Outbound calling also needs consent controls, a dedicated
trunk, answer-machine handling, retry rules, and suppression logic.

## Change the demo for a customer

1. Replace the fictional record and approved help text in
   `src/client_voice_agent/context.py`.
2. Rewrite the disclosure and guardrails in
   `src/client_voice_agent/assistant.py`.
3. Pick the Rime speaker in `.env.local` with `RIME_CODA_SPEAKER`.
4. Update the tests before changing the prompt further.
5. Run the full check suite and complete five clean calls.

```bash
uv run ruff check .
uv run ruff format --check .
uv run ty check
uv run pytest
uv build
```

## Project boundaries

This repository uses synthetic data and has no live phone number, customer
system integration, document upload, or ability to verify receipt. The agent
only explains a fictional workflow and reflects what the caller reports.

## License

MIT
