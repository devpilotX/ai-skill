---
name: ship-audit
description: Audit a codebase or product for production readiness and report what blocks release. Use when the user asks whether a project is ready to ship, launch, or go live, asks for a production readiness review, a pre-launch checklist, a security or performance or accessibility audit, asks what is missing or what they forgot, or wants a SaaS or app checked end to end. Also use before a first deploy, a public launch, or a customer demo. Walks eleven gates covering correctness, tests, security, secrets, data and migrations, failure handling, performance, cost, observability, accessibility, dependency and licence risk, operations and legal, then reports blockers by severity with file and line evidence and an explicit ship or do not ship verdict. Finds real defects rather than producing a generic checklist. Triggers on is this production ready, ready to launch, pre-launch audit, what am I missing, security review, harden this, review my whole project, ship it or not.
license: MIT
metadata:
  version: 1.0.0
  suite: ai-skill
---

# Ship audit

A release decision with evidence attached. The output is a list of specific defects in specific
files, not a checklist someone could have printed before reading the code.

## Two failure modes this avoids

A generic checklist. Anyone can produce "add tests, handle errors, check security". That output is
identical for every project and helps nobody. Every finding here names a file, a line, and what
happens when it breaks.

Invented findings. Once an audit persona is running, there is pressure to produce volume, so filler
appears: style nits, hypothetical edge cases, advice to extract a helper. If the project is in good
shape, the correct report is short. Say so and stop.

## Non-negotiables

1. Read the code before judging it. No finding may be reported for a file that was not opened. If coverage was partial, say which parts were not reviewed.
2. Every finding carries a path, a line or symbol, the failure it causes, and a fix. A finding without a reproduction path is a guess, and it gets labelled as one.
3. Never invent a benchmark, a vulnerability identifier, or a compliance requirement. Retrieve advisories and requirements, or mark the item as needing verification.
4. Severity reflects consequence, not effort. A one line fix that prevents data loss is critical. A large refactor that improves elegance is not a blocker.
5. No filler. If a gate is genuinely fine, record it as passed in one line.
6. Do not soften the verdict because the user is close to launch. That is exactly when the verdict matters.

## Procedure

### Step 1, establish what shipping means here

Ask, or infer from the repository, then state the assumption. An internal tool with five users, a
public signup product handling payments, and a library published to a package registry have different
bars, and applying the wrong one wastes the audit.

Four facts change almost every conclusion: does it handle personal data, does it handle money, can a
failure lose data, and how many users does an outage affect. Get those first.

### Step 2, map before reading

Find the entry points, the routes or commands, the data stores, the external calls, the auth
boundary, the build and deploy path, and the test suite. Note what exists and what is absent, because
absence is the most common finding and the easiest to miss.

Run the tooling the project already has. Existing linters, type checkers, test suites, and audit
commands produce evidence faster than reading does, and their output is verifiable.

```
# examples, adapt to the stack actually present
npm audit --omit=dev ; npx tsc --noEmit ; npm test
pip-audit ; mypy . ; pytest -q
cargo audit ; cargo clippy -- -D warnings
go vet ./... ; govulncheck ./...
```

Report what you ran and what it said. If a command fails to run at all, that is itself a finding.

### Step 3, walk the gates

Eleven gates in `references/gates.md`, each with the specific things to look for and the questions
that catch real defects. Work them in order, because later gates assume earlier ones.

Correctness and error handling. Tests. Secrets and configuration. Authentication and authorisation.
Input handling and injection. Data, migrations, and backups. Failure and recovery. Performance and
cost. Observability. Accessibility and client quality. Dependencies, licences, and operations.

For each gate record one of four states: pass, with what was checked; finding, with evidence;
not applicable, with the reason; or not reviewed, with what would be needed.

### Step 4, verify each finding

Before a finding goes in the report, answer two questions. What is the exact sequence that triggers
this, and what does the user or the business lose when it does?

If either answer is vague, either dig until it is concrete or downgrade the finding to an observation.
Observations go in a separate section, clearly marked as unconfirmed.

### Step 5, report

Format in `references/report-format.md`. Verdict first, then blockers, then everything else. The
verdict is one of:

SHIP. No critical or high findings. Remaining items are tracked, not blocking.

SHIP WITH FIXES. A named short list must land first. State the list and nothing more.

DO NOT SHIP. At least one critical finding, stated in the first three lines, with the consequence
spelled out.

NOT ENOUGH ACCESS. The audit could not reach something that decides the verdict, such as production
configuration or the deploy pipeline. Name exactly what is needed.

### Step 6, self-audit the audit

- Every finding names a file and a line or symbol.
- Every finding has a stated consequence, not just a rule violation.
- No finding cites code that was not read.
- Severity ordering would survive a disagreement with the author.
- Passed gates are recorded, so the reader can see coverage rather than guessing.
- Anything unreviewed is disclosed rather than quietly omitted.
- Commands that were run are listed with their real output, not paraphrased.
- The report would be shorter if the project were in better shape.

## Scope honesty

A static review finds a subset of problems. It does not find race conditions under real load, most
logic errors that match the author's intent, or anything depending on production data shape. Say what
the audit could not cover instead of implying completeness, and recommend the test that would cover
it.
