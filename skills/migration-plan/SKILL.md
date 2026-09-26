---
name: migration-plan
description: Move a system from one technology, provider or version to another without a cutover weekend. Use when the user asks how to migrate, port or move between databases, frameworks, languages, cloud providers, authentication systems or major versions, how to escape a vendor, asks about zero downtime data migration, dual writing, change data capture, shadow traffic, backfilling, the strangler fig pattern, or whether to upgrade or replace. Plans an incremental path with both systems running, traffic moved in reversible slices, correctness checked against a stated mismatch tolerance, and the parallel running cost stated. Schema migrations inside one database go to data-layer. Rewrite or refactor of the same codebase goes to refactor-safely. Triggers on migrate from, port to, move off, move to AWS, leave Heroku, Firebase to Postgres, Python 2 to 3, switch database, upgrade major version, zero downtime migration, dual write, change data capture, CDC, shadow traffic, strangler fig, backfill, vendor lock in, cutover.
license: MIT
metadata:
  version: 1.1.0
  suite: ai-skill
---

# Migration planning

A single cutover concentrates all the risk into one irreversible moment, and incremental
plans can fail more quietly: dual writes that diverge without anyone noticing, a comparison that never
reaches zero so reads move anyway, a backfill that overwrites fresher data, and an exit bill nobody
retrieved. This skill corrects both by running the two systems in parallel, moving traffic in
reversible slices, and making every consistency mechanism say what happens when one side fails.

## When to use and when to stay off

Run when a system, datastore, provider, framework, language or authentication system is being replaced,
or when a major version jump is large enough to plan.

Stay off, and route instead, when:

- The change is a schema migration inside one database (adding a column, splitting a table, an index). Use `data-layer`.
- The code stays on the same stack and the question is whether to rewrite or restructure it. Use `refactor-safely`.
- The target has not been chosen yet. Use `arch-decide` first, and come back with the decision.
- The question is only how to roll out a release. Use `release-manage`.

The user says "stop", "I've decided", or "just execute": comply at once and stay off for the rest of
the session unless asked again.

## Non-negotiables

These override everything else in this file.

1. Every step is reversible on its own, or it is split until it is, or it is scheduled as a named point of no return with its own checklist.
2. Every mechanism that keeps two systems in step states what happens when one write succeeds and the other fails, and how the gap is found and repaired.
3. Correctness is verified by comparison against a tolerance set before comparison starts, and reads move only when every mismatch class is explained.
4. A tested restore exists before any data is moved, tested on this data.
5. The parallel running cost is stated in money and attention, and the finish date is part of the plan.
6. Never migrate and redesign at the same time. Move first, improve after.
7. Retrieve the target's real limits, behaviour, and the source's exit and egress terms. Recall is not verification.

## Procedure

Failure modes, comparison design, checklists and provider specifics are in `references/patterns.md`.

### Step 1, be honest about why

Write the reason down: cost, a required capability, an unsupported version, a limit being hit. Ask
whether an upgrade in place achieves it, since that usually costs far less. If the reason is that the
current system is unpleasant to work with, say a migration will not fix that for long.

### Step 2, inventory what depends on it

Every reader and writer, including scripts, reports, dashboards, scheduled jobs, third party
integrations, and internal tools. Search all of the organisation's code.

Every undocumented behaviour depended upon: ordering, case sensitivity, collation, precision, null
handling, timezones, identifier format and sequences, transaction isolation, error codes.

Data volume and growth, which decides whether a backfill takes hours or weeks.

For a provider move, the exit cost. Retrieve the current egress price and any export charges at the
data size measured here, and the contractual exit terms. In 2024 some large cloud providers announced
egress waivers for customers moving data off their platform, generally on request and with conditions;
retrieve the current terms from the provider's own documentation instead of assuming they apply. Check
the arithmetic with `numbers-check`.

### Step 3, prove it on a slice

Take the hardest representative piece and make it work end to end against the target. Measure
performance on real data volume. This finds the incompatibility that changes the plan while changing it
is cheap.

### Step 4, choose the pattern

For data stores, pick how writes reach both systems, and state its failure semantics:

- Application dual write, writing to both from the application, is not atomic. If the second write fails or the process dies between them, the stores diverge. Use it only with a repair path: record failed second writes durably and replay them, and run reconciliation to catch the ones that never got recorded.
- Transactional outbox: write the change and an outbox row in one transaction on the old store, and a relay applies it to the new store. At least once, so the apply is idempotent.
- Change data capture or log based replication: stream the old store's change log into the new one. No application change, and every committed write is seen.
- Primary write plus asynchronous replay: write only to the old store and replay a durable log of operations into the new one, with lag monitored.

Then shadow reads: keep serving from the old store, read from the new one in parallel, and compare
without using the result.

For services and applications, use a routing layer in front and move one route, feature or cohort at a
time (the strangler fig pattern). Shadow traffic can exercise the new service first, as long as its side
effects are blocked; see `release-manage`.

For frameworks and languages, including Python 2 to 3, run the new one alongside for new code and
migrate modules at boundaries.

For major version upgrades, move one major version at a time, and read the changelog and upgrade guide
for each one crossed. Upgrade dependencies first, fix deprecation warnings on the current version, then
move. Skipping majors hides which change broke what.

For authentication systems and provider moves, follow the specifics in `references/patterns.md`: hash
formats and lazy rehash, session continuity, identifier mapping, DNS TTL and endpoint indirection.

### Step 5, set the tolerance and run the comparison

Before comparing, write the tolerance: the unexplained mismatch rate allowed, over how many
comparisons, for how long. Base it on what a wrong read costs the business, and label it `ASSUMPTION:`
with its reasoning if nobody owns that figure.

Classify every mismatch (bug in the new path, bug in the old path, expected difference such as
precision or ordering, timing of the comparison itself). Each class is explained and either fixed or
accepted in writing. An unexplained class blocks the move regardless of its rate. Move reads only when
no unexplained class remains and the residual rate stays inside tolerance for the agreed period.

Emit the mismatch counts as metrics through `observability-setup`, so the rate is watched and not
sampled by hand.

### Step 6, backfill carefully

In batches with a pause between them, resumable, with progress recorded durably. Watch production load,
since a backfill can cause the outage the migration was meant to avoid.

Guard against the race with live writes. Once dual writing or replication has started, a backfill that
copies an old snapshot can overwrite a newer row. Make every backfill write a conditional upsert guarded
by a version number or an update timestamp from the source, so it only writes when its copy is newer
than what the target holds.

Verify counts and checksums per batch. Keep a list of failed records and resolve each one.

### Step 7, move traffic and keep the exit open

Move in increments with a wait at each, watching error rate, latency and the business metric that proves
the system works. Keep the way back open until the old system is genuinely no longer needed.

Name the point of no return, usually when writes stop going to the old system, and complete the point
of no return checklist in `references/patterns.md` before passing it.

### Step 8, finish it

Decommission on a date. Remove the dual write code, the comparison code, routing shims and flags.
Update documentation and runbooks. Record actual cost against the estimate.

## Self-audit

- The reason is written down, and upgrading in place was considered.
- Full inventory of dependants, including scripts and reports outside the main application.
- Exit and egress terms were retrieved with a date, not recalled.
- The write mechanism names its failure semantics and its repair or reconciliation path.
- A mismatch tolerance was written before comparison started, and every mismatch class is explained.
- Backfill writes are guarded by version or timestamp against overwriting newer data.
- Major version upgrades cross one major at a time, with each changelog read.
- Authentication moves cover hash format, session continuity and identifier mapping.
- Restore tested on this data.
- The point of no return is named and its checklist completed.
- Parallel running cost and a decommission date are stated.

## What this cannot do

It cannot see the data. Mismatch classes, volumes and backfill durations come from running the
comparison, not from the plan.

It cannot read the source provider's contract. Ask a technology contracts lawyer: "Under our agreement
with this provider, what notice, fees and data return obligations apply when we leave, and are we
entitled to any egress waiver they have announced?"

When personal data moves between providers or regions, ask a data protection lawyer: "Does moving this
personal data to this provider in these regions require a new transfer mechanism, an updated processor
agreement, or notice to users?"
