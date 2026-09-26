---
name: arch-decide
description: Choose a technical architecture and record the decision with its reversibility and consequences. Use when the user asks how to structure a system, monolith, microservices or modular monolith, event driven or request response, which message queue or Kafka, CQRS, multi-tenant design, how services communicate, serverless or containers, build vs buy, managed or self-hosted, vendor lock-in, or asks for a design doc, RFC or ADR. Classifies by reversal cost, scales options to it including doing nothing, argues against its own recommendation, and writes an immutable record with a revisit trigger. Refuses complexity the team cannot operate. Schema, index and database engine details go to data-layer, hosting and deploy mechanics to infra-deploy, moving an existing system to migration-plan. Triggers on monolith or microservices, modular monolith, event driven, message queue, Kafka, CQRS, multi-tenant, system design, design doc, RFC, ADR, build vs buy, vendor lock-in, sync or async, tech stack choice.
license: MIT
metadata:
  version: 1.1.0
  suite: ai-skill
---

# Architecture decisions

Most architecture argument gets spent on decisions that are cheap to reverse, while the expensive ones
get made by default, with no options compared and no record of why. This skill corrects that by
matching effort to the cost of reversal and writing down the decision with the condition that should
reopen it.

## When to use and when to stay off

Run when a structural choice is being made: deployment shape, service boundaries, communication style,
tenancy, the primary datastore class, build against buy, or a vendor that will hold data. Run also when
the user asks for a design doc, an RFC or a decision record.

Stay off, and route instead, when:

- The question is schema design, indexing, a query or engine specific tuning. Use `data-layer`.
- The question is hosting, containers, pipelines or deploy mechanics. Use `infra-deploy`.
- The system already exists and the question is how to move it. Use `migration-plan`.
- The request is a whole build from a vague idea. Use `build-pilot`, which calls this skill at its decision stage.
- The decision is already made and the user wants it implemented. Record it if asked, then stay off.

The user says "stop", "I've decided", or "just execute": comply at once and stay off for the rest of
the session unless asked again.

## Non-negotiables

These override everything else in this file.

1. Classify the decision (one way, two way, hidden one way) before discussing options, and state it in the first two lines of the answer.
2. Match the design to the team that operates it. State operational cost in people and ongoing hours, not only in components.
3. Every option listed is one a competent engineer would defend. No strawmen.
4. Give the argument against the recommendation.
5. Verify constraints, do not recall them. Limits, quotas, pricing, version compatibility and feature availability are retrieved with a date through `deep-research`, or marked unverified.
6. No invented thresholds. A threshold is measured, retrieved from a cited source, or labelled `ASSUMPTION:` with its reasoning.
7. Prefer the boring option unless a named requirement rules it out, and never propose a distributed system to solve a missing index.

## Procedure

### Step 1, classify

The classification decides how much process the decision deserves.

One way doors, where reversal costs months: the data model, the primary datastore, the public API
shape, the tenancy model, the authentication model, splitting into separately deployable services, and
anything that lands in a customer's integration. These get research, options and a written record.

Two way doors, where reversal costs days: internal library choices, code layout, the CI provider, most
framework choices inside an established stack, log format. Pick a reasonable option, note why, move on.

Hidden one way doors, which look cheap and are not: a message format that leaks into consumers, a third
party holding customer data, an identifier format that reaches other systems, a vendor whose export
path was never checked. Ask early how you would get out. The detection questions and per vendor exit
checks are in `references/exit-paths.md`. A hidden one way door that fails its exit check gets treated
as one way.

### Step 2, extract the forces

Load: current and expected requests, data volume and growth, steady or spiky. An honest answer here
usually shrinks the design.

Consistency: which operations must be correct immediately and which can settle later.

Recovery objectives as numbers: RPO, the amount of recent data the business accepts losing, and RTO,
the time it accepts being down. Get both from the person who owns the business consequence. "As little
as possible" is not a number, and the pair decides backup, replication and failover design.

Team: how many engineers, what they already know, who is on call.

Fixed constraints: existing systems, contracts, regulation, data residency, budget, deadline. If the
system holds personal data, payments or credentials, bring in `security-hardening` for the threat model
before options are compared.

When load is unknown, state the assumed range as an `ASSUMPTION:` and name the revisit trigger that
would show the range was wrong.

### Step 3, generate options scaled to the classification

One way door: at least three real options plus doing nothing. One is the simplest thing that could
work, usually a single deployable with one database. One is the conventional answer for this class of
problem. One exploits something specific about this situation.

Two way door: one reasonable option and doing nothing, a line each. Three options here is waste.

Doing nothing always gets a row, with what it costs to keep the current state.

Analyses for recurring decisions are in `references/tradeoffs.md`: deployment shape, service
communication and the transactional outbox, datastore class, caching, tenancy, state placement,
serverless, and build against buy.

### Step 4, cost each option

For each: build effort, operational burden in ongoing hours per month, running cost at expected load,
what it makes hard later, the failure mode it introduces, what the team has to learn, and how it meets
the RPO and RTO.

Operational burden is the number that gets omitted and then dominates. Count it. Running costs are
retrieved from current vendor pricing pages with a date, and the arithmetic goes through
`numbers-check`.

### Step 5, recommend and argue against

One recommendation. Then the strongest case against it, and the condition under which another option
wins.

State that condition as a measurable revisit trigger. Measure it where possible: load test the chosen
design and record the write rate, data size or tenant count at which latency, replication lag or cost
crosses the target. Where it has not been measured, write it as `ASSUMPTION:` with the reasoning and the
measurement that would confirm it.

### Step 6, record it

Find where the repository already keeps decision records (for example `docs/adr`, `docs/decisions`,
`adr`, or `doc/architecture/decisions`) and follow its numbering, template and status conventions.
Propose `docs/decisions/` only when the repository has none.

Where the repository has no template, use the "Decision record" section of the templates reference in
`doc-forge`: status, date, deciders, context, decision, options considered including doing nothing,
consequences, and reversal. The reversal section carries the reversal cost and the revisit trigger from
step 5. `build-pilot` uses the same fields.

Keep records immutable. When a decision changes, add a new record and mark the old one superseded with
a link.

If the decision replaces something already running, hand the transition to `migration-plan`.

## Anti-patterns worth naming directly

Resume driven design: the choice that is interesting to build instead of cheap to run.

Scaling for load that does not exist, paid for in slower delivery.

Splitting services along team boundaries that will change instead of along data ownership.

A shared database between services, which brings the cost of distribution with the coupling of a
monolith.

Distributed transactions, usually a sign the boundary is in the wrong place.

Writing to the database and publishing an event as two separate steps, which loses or invents events on
failure. See the outbox section in `references/tradeoffs.md`.

Event driven design adopted for its own sake.

A cache added to fix a query that has no index.

A vendor chosen without checking the export path.

## Self-audit

- The classification appears in the first two lines.
- Option count matches the classification, and doing nothing has a row.
- Operational burden is stated in ongoing hours or headcount for each option.
- RPO and RTO are numbers from a named owner, or marked as missing.
- Every external limit or price has a source and a retrieved date, or is marked unverified.
- Every threshold is measured, cited, or labelled `ASSUMPTION:`.
- The argument against the recommendation is present.
- Any design that writes to a store and publishes a message says how the two stay consistent.
- Vendors holding data passed the exit checks in `references/exit-paths.md`, or the failure is stated.
- The record went into the repository's existing decision directory, if one exists, and has a revisit trigger.

## What this cannot do

It cannot measure the user's system. Thresholds stay assumptions until someone runs the load test or
reads the production metrics.

It cannot read contracts it has not been given. Exit terms, data return clauses and termination fees
need the actual agreement. Ask a commercial or technology contracts lawyer: "Under this agreement, what
data do we get back on termination, in what format, within what period, at what cost, and what notice
or fees apply if we leave before the term ends?"

It cannot decide regulatory questions such as data residency. Ask a data protection lawyer: "Given
personal data about users in these countries, stored with this provider in these regions, which
transfer mechanisms or residency requirements apply to us?"
