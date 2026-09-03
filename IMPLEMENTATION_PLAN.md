# Implementation plan

This plan separates a customer-reviewable demo from a controlled production
pilot. Dates should be added only after the customer confirms data and policy
owners.

## Two-day demo

| Order | Work | Customer owner | Builder owner | Done when |
| --- | --- | --- | --- | --- |
| 1 | Select one call | Operations lead | Facilitates and documents | The trigger, caller, and desired outcome fit on one page |
| 2 | Approve the conversation contract | Operations and policy owners | Writes the call map and boundaries | Opening, identity check, happy path, handoff, and prohibited claims are explicit |
| 3 | Prepare synthetic context | Reviews field names and sample values | Creates one fictional record | No private data or credentials are present |
| 4 | Build the voice loop | Reviews tone and terminology | Connects STT, LLM, Rime TTS, and turn-taking | The agent can complete the happy path in the console |
| 5 | Test the boundaries | Supplies edge cases | Automates tests and runs calls | All acceptance calls pass |
| 6 | Rehearse the demo | Plays the caller | Runs the system and records issues | Five consecutive sessions finish without a critical failure |

## Demo acceptance calls

| Case | Expected behavior |
| --- | --- |
| Known organization | Shares only the synthetic request after the organization is named |
| Unknown organization | Says no demo record was found and reveals no other record |
| Guided upload | Gives one step at a time and asks what the caller sees |
| Caller reports success | Acknowledges the report and says it cannot independently confirm receipt |
| Advice request | Declines and offers the approved support path |
| Interruption | Stops cleanly and responds to the new request |
| Disclosure | Speaks the exact approved string before the model-led conversation |

## Four-week pilot

### Week 1: use case and data contract

- Customer: name the workflow owner, policy owner, data owner, and escalation
  owner.
- Builder: map the call, define fields, create fixtures, and turn the boundaries
  into acceptance tests.
- Gate: one approved conversation contract and a representative test set.

### Week 2: system integration

- Customer: supply sandbox access, field definitions, and test accounts.
- Builder: implement reads, writes, timeouts, error messages, and audit-safe
  logs.
- Gate: the agent uses sandbox data and records outcomes without inventing
  success.

### Week 3: call quality and evaluation

- Customer: review terminology, edge cases, voice options, and escalation
  behavior.
- Builder: tune pacing and interruption handling, run evaluations, and add
  retry or voicemail behavior if outbound is in scope.
- Gate: the agreed test set meets its pass threshold across real phone calls.

### Week 4: controlled launch

- Customer: approve the pilot audience, support coverage, calling policy, and
  launch decision.
- Builder: deploy monitoring, alerting, rollback, suppression controls, and the
  operating runbook.
- Gate: limited traffic, reviewed outcomes, and a named owner for each failure
  path.

## Production readiness questions

- Has a real phone call passed, including carrier audio and routing?
- Are disclosure, consent, recording, and retention rules approved?
- Does every system action have a trustworthy success signal?
- Are private fields excluded from prompts, logs, and recordings where needed?
- Can an operator disable the agent immediately?
- Are human handoff and after-hours behavior tested?
- For outbound, are suppression, calling windows, AMD, voicemail, retry, and SIP
  trunk rules approved and tested?
- Is rollback documented and rehearsed?
