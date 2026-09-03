# Voice agent customer worksheet

Complete this with the people who run the workflow. Plain language is enough.
The builder will translate the answers into code and tests.

## 1. The call

- Who starts the call?
- Why is the call happening now?
- What should the person know or do when the call ends?
- What is the shortest successful version of this call?

## 2. Facts available before the call

- Which record identifies the person or organization?
- Which fields may the agent say aloud?
- Which fields must never be spoken?
- How current is the data?
- What should happen when the record is missing or ambiguous?

## 3. Identity and permission

- What must the caller confirm before details are shared?
- Can an authorized colleague act for the named contact?
- What does the agent say to the wrong person?
- Which disclosures must be spoken exactly?
- Who approves the disclosure language?

## 4. Allowed actions

- Which questions can the agent answer?
- Which systems can it read?
- Which systems can it change?
- What confirmation proves that a change succeeded?
- What may the agent acknowledge only as something the caller reported?

## 5. Boundaries and handoff

- Which advice or topics are out of scope?
- Which questions always go to a person?
- Who receives the handoff, and during which hours?
- What should happen when no person is available?

## 6. Voice and language

- Which three words describe the desired voice?
- Which words or phrases should the agent avoid?
- Which names, acronyms, and numbers need pronunciation review?
- Which languages are required for the first pilot?

## 7. Failure paths

- What should happen on silence, interruption, or a dropped call?
- For outbound calls, what should happen on voicemail, IVR, busy, or no answer?
- How many retries are allowed, and when?
- What immediately disables calling?

## 8. Acceptance calls

Write one example for each case:

- Happy path
- Unknown record
- Failed identity check
- Unsupported question
- Caller interruption
- Integration failure
- Human handoff
- Voicemail, if outbound is in scope

For each call, record the expected opening, facts, boundary, outcome, and owner
of any follow-up.
