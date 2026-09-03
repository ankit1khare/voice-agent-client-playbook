# How to build a voice agent with a nontechnical customer

The hardest part of a first voice agent is rarely speech-to-text, a prompt, or a
phone number. It is turning a familiar human process into a contract that a
customer can inspect.

That is especially true when the customer has never built a voice agent. They
know the workflow, the awkward exceptions, and what a bad call sounds like.
They should not need to know what endpointing means before they can help you
build a useful demo.

This playbook starts with a document-reminder call. The agent finds one
fictional organization, explains which document is needed, and stays on the
line while the caller navigates a fictional portal. LiveKit handles the
realtime session, and Rime Coda speaks the response.

The prototype should be honest about its limits. Its immediate job is to create
a small call that both the builder and the customer can judge.

## Begin with the call

Ask the customer to describe one real call from beginning to end. Write down
the answers to six questions:

1. Who starts the call?
2. What does the agent know before anyone speaks?
3. What must the caller confirm before the agent shares details?
4. What can the agent explain or change?
5. What must the agent never claim?
6. How does the call end when it succeeds, fails, or reaches voicemail?

These answers become the conversation contract. A vague request such as “call
customers about missing paperwork” becomes something testable:

- The agent knows one organization's name, one contact, one document, one
  deadline, and one upload path.
- It shares details only after the caller names the organization.
- It can walk through approved upload steps.
- It cannot see the caller's screen or confirm that a back-end system received
  the file.
- It sends unsupported questions to a person.

This is a better first artifact than a large prompt. A customer can correct it
in a few minutes.

## Build the smallest credible demo

Use synthetic data in the first version. One record is enough. A narrow fixture
makes grounding failures obvious and keeps private customer data out of an
unfinished system.

The reference project uses this fictional record:

```text
Organization: Juniper Works, LLC
Contact: Sam Rivera
Required document: current certificate of insurance
Upload path: Demo Portal, then Open Requests, then Upload Document
```

The demo still needs real behavior. It should let the customer interrupt, ask a
follow-up question, take the upload one step at a time, and hear a useful answer
when the agent reaches a boundary.

An inbound call is often the quickest way to test that behavior. It avoids the
extra policy and telephony work that outbound calling introduces, while giving
the customer the same conversation to review. When outbound is the eventual
workflow, say that plainly. Treat the inbound call as a rehearsal, not as proof
that outbound operations are finished.

## Keep exact language out of the model

Some words need to be identical on every call. Disclosures are the obvious
example.

Do not ask the language model to “say” required disclosure text. It may shorten
or paraphrase the wording. In this project, the application sends the exact
string to `session.say()` before the model handles the conversation:

```python
speech = session.say(disclosure, allow_interruptions=False)
await speech
```

This creates a clean test. You can assert the exact string in code and hear the
same language on every call. The customer's legal or compliance owner still
decides the wording.

## Make the architecture easy to explain

The reference uses four parts:

- LiveKit manages the realtime room and turn-taking.
- Deepgram Flux transcribes the caller.
- Gemma chooses the next response within the conversation contract.
- Rime Coda speaks that response.

The customer does not need a model tour. They need to know where their data
enters, which component decides what to say, and where a human takes over. Draw
that path on one page. If an important system is absent from the drawing, it is
probably absent from the plan.

## Give the first demo two focused days

The first demo should answer one question: can this conversation work?

### Day one: agree on the contract

The customer owns the workflow facts, approved source material, disclosure
owner, and a small set of example calls. The builder turns those inputs into a
synthetic record, explicit boundaries, and acceptance tests.

By the end of the day, everyone should agree on the opening, identity check,
happy path, unsupported question, and handoff.

### Day two: make and review calls

The builder connects the voice pipeline, tunes interruption behavior, runs
automated checks, and makes repeated calls. The customer listens for wrong
facts, awkward pacing, missing steps, and phrases their team would never use.

Five clean sessions are a useful demo gate. Include the happy path, an unknown
organization, an advice request, an interrupted response, and a claimed upload.
The fifth case matters because the agent must distinguish “the caller says it
worked” from “the system confirmed it.”

If the eventual experience begins with a real phone number, provision and test
that number early. A browser or console session does not exercise carrier audio,
routing, or telephony configuration.

## Use a four-week path from demo to pilot

A good demo can fit in two days. A responsible pilot needs time for the parts
the demo deliberately leaves out.

| Week | Shared decision | Customer owns | Builder owns | Exit check |
| --- | --- | --- | --- | --- |
| 1 | Lock the use case and data contract | Workflow, source data, consent language, escalation owners | Call map, prompt boundaries, fixtures, acceptance tests | One approved conversation contract |
| 2 | Connect systems | Sandbox access, field definitions, test accounts | Read path, outcome writes, error handling, audit-safe logs | Agent uses sandbox data without inventing facts |
| 3 | Tune and evaluate calls | Reviewers, edge cases, approved wording | Voice selection, pacing, interruptions, evals, retries | Agreed pass rate across a representative test set |
| 4 | Run a controlled pilot | Pilot audience, support coverage, launch approval | Deployment, monitoring, rollback, runbook, handoff | Limited traffic with an owner for every failure path |

Data access is usually the largest schedule variable. A clean sheet with stable
column definitions is more useful in week one than a promise of a perfect API
later. Connect the real system once the conversation and fields are understood.

## Treat voicemail and failure paths as product work

If most outbound attempts reach voicemail, voicemail is part of the main
experience. Write and review the message before the outbound worker exists. A
pre-rendered Rime clip can make the behavior concrete during an inbound demo.

Production outbound work adds more than a dial command. Plan for permission to
call, suppression lists, calling windows, a dedicated SIP trunk, answer-machine
detection, IVR handling, retries, structured outcomes, and a kill switch. Test
only with authorized numbers until the operating policy is approved.

Do the same for inbound failures. Decide what the agent says when the record is
missing, the caller cannot verify identity, an integration times out, or a
human is unavailable.

## Review behavior, then voice

Voice choice matters, but it can hide a weak workflow. Review in this order:

1. Did the agent use only approved facts?
2. Did it protect details before identity was established?
3. Did it avoid claiming actions the system did not perform?
4. Did it hand off unsupported questions cleanly?
5. Did the pacing, pronunciation, and tone fit the customer?

Once those behaviors are stable, compare voices using the same scripts and
call conditions. That gives the customer a real choice instead of a moving
target.

## Leave the customer with an operating system

The code is only one handoff. A nontechnical customer also needs:

- A one-page map of the call
- The approved facts and phrases the agent may use
- A test scorecard with pass and fail examples
- Named owners for data, policy, escalation, and deployment
- A runbook for monitoring, rollback, and changes
- A list of what the current version cannot do

Those artifacts let the customer review the agent without reading Python. They
also make the next use case faster because the team has a repeatable way to go
from workflow to call.

The reference implementation in this repository is intentionally modest. That
is its point. Start with one call everyone understands, make its boundaries
audible, and earn the right to connect the rest of the system.
