---
name: ship-audit
description: Audit a whole codebase or product for production readiness. Use when the user asks whether a project is ready to ship, launch or go live, asks for a production readiness review or pre-launch checklist, asks what is missing or what they forgot, or wants a SaaS or app checked end to end before a first deploy, launch or demo. Walks twelve gates: correctness, tests, secrets and configuration, authentication and authorisation, input handling and web security, data and backups, failure and recovery, performance and cost, observability, accessibility, dependencies and licences, operations and legal. Reports findings by severity with file and line evidence and a ship or do not ship verdict set by a fixed severity rule. Covers a whole release only; a single concern audit (security, performance, accessibility) goes to the specialist skill. Triggers on is this production ready, ready to launch, pre-launch audit, go live checklist, what am I missing, review my whole project, ship it or not.
license: MIT
metadata:
  version: 1.1.0
  suite: ai-skill
---

# Ship audit

The failure this corrects: a release decision made from a generic checklist, or from an audit padded
with invented findings. "Add tests, handle errors, check security" is identical for every project and
helps nobody, and filler findings (style nits, hypothetical edge cases, advice to extract a helper)
bury the one defect that loses data. The output here is a verdict backed by specific defects in specific
files, and a short report when the project is in good shape.

## When to use and when to stay off

Run when the user wants a ship or do not ship decision on a whole release, product or codebase.

Stay off, or hand over, when the request covers one concern. This skill covers a whole release; a single
concern audit goes to the specialist:

- Security only: `security-hardening`.
- Schema, migrations or backups only: `data-layer`.
- Logging, metrics or alerting only: `observability-setup`.
- Accessibility or front end quality only: `frontend-build`.
- Test coverage or test design only: `test-strategy`.
- Hosting, infrastructure or deploy pipeline only: `infra-deploy`.
- Release process, staging or rollback only: `release-manage`.
- Speed or cost only: `performance-tuning`.
- One diff or pull request: `code-review`.

Off switch: the user says "stop", "I've decided", or "just execute". Comply at once and stay off for
the rest of the session unless asked again.

## Non-negotiables

These override everything else in this file.

1. Read the code before judging it. No finding for a file that was not opened. Partial coverage is stated.
2. Every finding carries a path, a line or symbol, the trigger, the consequence and a fix. Without a trigger it is an observation.
3. Never invent a benchmark, a vulnerability identifier or a compliance requirement. Retrieve it or mark it as needing verification.
4. Severity follows consequence, not effort.
5. The verdict follows the severity rule in step 5, with no exceptions for launch pressure.
6. No filler. A gate that passes gets one line.

## Procedure

### Step 1, establish what shipping means here

Ask, or infer from the repository, and state the assumption. An internal tool with five users, a public
signup product taking payments, and a library published to a registry have different bars.

Four facts change almost every conclusion: does it handle personal data, does it handle money, can a
failure lose data, and how many users does an outage affect. Get those first.

### Step 2, map before reading

Find the entry points, data stores, external calls, auth boundary, build and deploy path, and test suite.
Note what is absent as well as what exists.

Run the tooling the project already has and report what it said. A command that fails to run is itself a
finding.

```
# examples, adapt to the stack actually present
npm audit --omit=dev ; npx tsc --noEmit ; npm test
pip-audit -r requirements.txt ; mypy . ; pytest -q
cargo audit ; cargo clippy -- -D warnings
go vet ./... ; govulncheck ./...
gitleaks git -v .
```

### Step 3, walk the twelve gates

Details and the questions that catch real defects are in `references/gates.md`. Work them in order,
because later gates assume earlier ones. The specialist skill named for each gate holds the deeper
method if a gate needs more than the audit covers.

1. Correctness, `code-review`
2. Tests, `test-strategy`
3. Secrets and configuration, `security-hardening`
4. Authentication and authorisation, `security-hardening`
5. Input handling and web security, `security-hardening`
6. Data, migrations and backups, `data-layer`
7. Failure and recovery, `infra-deploy`
8. Performance and cost, `performance-tuning`
9. Observability, `observability-setup`
10. Accessibility and client quality, `frontend-build`
11. Dependencies and licences, `security-hardening`
12. Operations and legal, `release-manage`

For each gate record one state: pass, with what was checked; finding, with evidence; not applicable,
with the reason; or not reviewed, with what would be needed.

### Step 4, verify each finding

Answer two questions: what exact sequence triggers it, and what does the user or business lose when it
does? If either answer is vague, dig until it is concrete or downgrade it to an observation. Observations
go in their own section and never affect the verdict.

### Step 5, apply the severity rule and report

Severity definitions are in `references/report-format.md`. The verdict is mechanical:

- DO NOT SHIP if any Critical finding is open. A Critical fixed during the audit counts as closed only after the fix is re-verified with the original trigger.
- DO NOT SHIP if any High finding lacks a listed fix and a named verification step.
- SHIP WITH FIXES if there is no open Critical and one or more High findings, each listed with its fix and the verification (test, reproduction or command) that must pass before release. Nothing else goes on that list.
- SHIP if there is no open Critical or High. Medium and Low findings are tracked with an owner and do not block.
- NOT ENOUGH ACCESS if a gate that could hold a Critical for this product (for example secrets, authorisation, or backups for a product that stores user data) was not reviewed. This overrides SHIP and SHIP WITH FIXES, never DO NOT SHIP. Name exactly what access is needed.

Format in `references/report-format.md`. Verdict first, then blockers, then everything else.

## Self-audit

- Every finding names a file and a line or symbol, a trigger and a consequence.
- No finding cites code that was not read.
- All twelve gates appear in the report with a state.
- The verdict matches the step 5 rule when checked against the finding list.
- Every High on a SHIP WITH FIXES list has a fix and a verification step.
- Observations are separate and did not change the verdict.
- Commands run are listed with their real output.
- Every legal item ends with "ask a lawyer:" (or the named professional) and an exact question.
- The report would be shorter if the project were in better shape.

## What this cannot do

A static review finds a subset of problems. It does not find race conditions that appear only under
real concurrency, logic errors that match the author's intent, or defects that depend on production data
shape or production configuration it was not shown. State what the audit could not cover and recommend
the test that would, such as a load test, a restore drill or a penetration test.

It cannot give legal advice. Legal items in gate 12 end with the exact question for a lawyer. Card data
scope needs a PCI Qualified Security Assessor; ask: "Given this payment flow (describe where card data is
entered and whether it touches our servers), which PCI DSS self-assessment questionnaire applies, and
which requirements are in scope?"
