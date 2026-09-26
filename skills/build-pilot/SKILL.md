---
name: build-pilot
description: Run a multi-component or vague build as staged work that thinks, researches, argues, decides, then implements and verifies. Use when the user hands over a vague idea and expects working software, asks to build an app, a website, a SaaS product, an MVP, a prototype or a greenfield system spanning more than one component, or asks to spec this out, plan it, or draw up a roadmap. Size rule: a request for one component, screen, endpoint, schema or script goes to the matching domain skill such as frontend-build, backend-build, data-layer, mobile-build, ml-build or infra-deploy. For one architecture choice use arch-decide, for whether the idea is worth building use reality-check, for a readiness audit use ship-audit. Verifies facts before code, borrows the consensus firewall from reality-check, stops at gates, builds in slices. Triggers on build me, create an app, MVP, prototype, greenfield, from scratch, end to end, spec this out, plan this project, roadmap, how should I approach, I want to build.
license: MIT
metadata:
  version: 1.1.0
  suite: ai-skill
---

# Build pilot

The expensive mistakes in software get made before any code is written, by jumping straight to
implementation on a request nobody restated, with facts nobody checked, and a choice nobody argued
against. This skill corrects that by running seven stages with gates between them. Each stage consumes
the output of the one before it, so the order is not a suggestion.

## When to use and when to stay off

Run when the request spans several components (for example an interface, a service and a datastore),
or when it is vague enough that coding now would be guessing: an MVP, a prototype, a greenfield
product, "spec this out", a roadmap.

Stay off, and route instead, when:

- The request is for one component. A screen or a frontend goes to `frontend-build`, an endpoint or a worker to `backend-build`, a schema or a query to `data-layer`, an app screen to `mobile-build`, a model or an evaluation to `ml-build`, hosting or a pipeline to `infra-deploy`.
- The request is one architecture choice with no build attached. Use `arch-decide`.
- The question is whether the idea is worth building at all. Use `reality-check`.
- Something is broken. Use `debug-method`.
- The work already exists and the question is whether it can ship. Use `ship-audit`.
- The task falls under the small task exception in non-negotiable 1.

The user says "stop", "I've decided", or "just execute": comply at once and stay off for the rest of
the session unless asked again. Record any decisions already made so the work that follows can use
them.

## Non-negotiables

These override everything else in this file.

1. No implementation code before stage 4 records a decision. One exception: a task small and reversible enough that the stages cost more than the work, such as a typo or a one line config change. State that the exception applies and why. The exception never covers a fact that decides the design, and never covers a one way door.
2. No fact used in a decision unless it was verified this session or labelled `ASSUMPTION:` with its risk. Versions, API shapes, limits, prices and platform rules change, and recall is not verification.
3. Present the argument against the recommendation. A stage 3 that only supports one option is advocacy.
4. When the build handles money or personal data, a threat model from `security-hardening` exists before the stage 4 decision is recorded.
5. Never claim code works without running it. Say which command was run and what it printed.
6. Report unfinished work as unfinished. Stubs, mocks, hardcoded values and skipped tests all get named.
7. Stop at the gates. Scope creep gets named with its cost and what it displaces, never absorbed.
8. Never commit to the user's repository, and never to its default branch, without asking. Work on a branch.

## Procedure

Templates for every artefact below (fact sheet rows, options table, slice card) and the full routing
table from stage to skill are in `references/stage-artefacts.md`. Gate rules are in
`references/phase-gates.md`.

### Stage 1, think

Restate the request in your own words, including what the user seems to want as distinct from what
they asked for. Getting this wrong wastes the whole build, and checking it costs one message.

Produce four lists: certain because the user stated it, assumed and would change the design if wrong,
unknown and must be researched, and out of scope.

Name the single hardest part of the problem. A plan that does not mention it is built around the easy
parts.

Ask at most five questions, each chosen because the answer changes the design. Typical ones: who uses
this and how many of them, does it handle money or personal data, what has to integrate with it, what
is the deadline and what is fixed about it, what is already decided.

If the work is quantitative trading or pricing, say so here, because it changes the routing from stage 2
onward. See the quantitative routing in stage 6.

Gate 1. The restatement is confirmed before stage 2 starts.

### Stage 2, research

Verify everything the decision rests on, with the `deep-research` method: grade sources, prefer primary
ones, date everything.

Check current versions and whether they are compatible with each other. Check the real API shape.
Check limits, quotas, pricing tiers and rate limits with a link. Check licences on dependencies. Check
whether something maintained already solves the problem, since adopting is sometimes the right answer.

If there is an existing codebase, read it before proposing anything. Use the mapping step in
`ship-audit` to find entry points, data stores, the auth boundary and the test suite.

Output a fact sheet in the row format from `references/stage-artefacts.md`, plus a list of what could
not be established and how that limits the design.

### Stage 3, discuss

Generate options scaled to the reversibility of the choice, as `arch-decide` does: at least three for
a one way door, two for a two way door, and "do nothing or adopt something existing" considered in
both cases.

Apply the consensus firewall from `reality-check` (its phase 1 and phase 2): write down the obvious
default approach, then make sure at least one option is not it.

For each option give what it optimises for, what it costs in time, money and operational hours, what
it makes hard later, its failure mode, and who has to learn something new. Use the options table in
`references/stage-artefacts.md`.

State the strongest case for each option, then the strongest case against the one you prefer.

If the build handles money or personal data, run the threat model with `security-hardening` now, while
it can still change the choice.

Gate 2. Put the options to the user with a recommendation.

### Stage 4, decide

Commit to one approach and write a decision record in the shape defined in the "Decision record"
section of the templates reference in `doc-forge`, which `arch-decide` also uses: status, date,
deciders, context, decision, options considered including doing nothing, consequences, and reversal.
The reversal section names the revisit trigger, meaning the measurable condition that reopens the
decision.

Before accepting it, borrow only the ground reality questions from `reality-check` (phase 5): what must
be true for this to work and is it true, what it costs to run at the expected scale, and what the do
nothing option costs. Do not run its other phases and do not issue a BUILD, PIVOT or KILL verdict. The
user already decided to build. If the decision survives only under optimistic assumptions, name the
assumption.

Where money is involved use `business-model` for the cost side. Where numbers are involved use
`numbers-check`.

### Stage 5, plan

Break the work into vertical slices. A slice goes from interface to storage and produces something
demonstrable. Horizontal layers hide integration problems until the end.

Order slices by risk, hardest and least certain first, so a wrong design shows up while changing it is
cheap.

Each slice gets a slice card from `references/stage-artefacts.md`: acceptance criteria someone else
could check, dependencies, the risk it retires, and a relative size class (small, medium, large) used
only to order and split slices. That class is not a time estimate. Time estimates follow the rule in
`references/status-reporting.md`: none unless asked, and then a range with the assumption that decides
it.

Name what is deliberately deferred.

Gate 3. Confirm the slice order, since it decides what exists if the work stops early.

### Stage 6, build

Before the first commit, ask where the work goes. Create a branch for it. Do not commit to the user's
default branch, and do not commit to their repository at all until they have said yes.

Implement one slice at a time. Finished means it runs, the risky part has a test, and it is committed
on the working branch with a message saying what changed and why. Never leave the tree broken between
slices.

Route each slice to the domain skill that owns it: `frontend-build`, `backend-build`, `data-layer`,
`mobile-build`, `ml-build`, `infra-deploy`. Use `test-strategy` for what deserves a test, and write the
test first for money, auth, deletion or data integrity. Run `code-review` on each slice's diff before
calling the slice finished.

For quantitative trading or pricing work, route the domain logic: research and backtests to
`quant-research`, position and portfolio risk to `portfolio-risk`, order execution and market impact to
`execution-microstructure`, option and derivative valuation to `derivatives-pricing`, statistical
arbitrage to `stat-arb`, the trading platform itself to `trading-systems`, and the soundness of the
quantitative argument to `quant-reasoning`.

Follow the conventions already in the repository: error handling, logging, naming, test style.

Run the code after every slice: test suite, type checker, linter. Paste real output.

When something turns out harder than planned, stop and report. The schedule is the user's decision.

### Stage 7, verify and hand over

Run `ship-audit` against the result, with the bar set by what this project is.

Before handover, plan the release with `release-manage` (abort condition, rollback, versioning) and
set up logs, metrics and alerts with `observability-setup`, so the first failure in production is
visible to someone.

Report in the shape in `references/status-reporting.md`: what works with the command that proves it,
what is stubbed, what is untested, what was cut and by whom, known defects, what to do next.

Use `doc-forge` for the README or runbook, and `human-prose` on prose before it ships.

## Other allowed skips

Beyond the small task exception in non-negotiable 1, two skips are allowed, and each gets stated.

A decision the user already made and stated. Record it and move on.

A plan or specification supplied by the user. Verify its facts in stage 2, raise anything that looks
wrong, then continue from stage 5.

## Self-audit

- The restatement was confirmed at gate 1, or the small task exception was stated with its reason.
- Every fact in the fact sheet has a source URL, a retrieved date and a grade, or an `ASSUMPTION:` label.
- The options list includes one that is not the obvious default, and a do nothing or adopt option.
- The argument against the recommendation is written down.
- Money or personal data present: a `security-hardening` threat model exists and predates the decision record.
- The decision record has every field, including a revisit trigger.
- The reality-check borrowing stopped at ground reality questions, with no verdict issued.
- Slices are vertical, ordered by risk, and carry size classes, not time estimates.
- No commit landed on the user's default branch, and committing was agreed before the first commit.
- Every slice went through its domain skill and `code-review`.
- Every "works" claim quotes the command run and its output.
- `release-manage` and `observability-setup` ran before handover.

## What this cannot do

It cannot verify facts without a way to retrieve them. Without web access every external fact stays an
`ASSUMPTION:` and the report says so.

It cannot run code in an environment it has no access to, such as the user's production account, so
claims stop at what ran here.

It does not replace the domain skills it routes to, and the quantitative skills named above are only
as good as the data the user supplies.

It cannot decide legal obligations. When personal data is involved, ask a data protection lawyer or the
organisation's data protection officer: "Given that we process these categories of personal data about
users in these countries for these purposes, what lawful basis applies, and do we need a data
protection impact assessment before launch?" When the product moves or holds customer money, ask a
payments or financial regulation lawyer: "Does this flow, where we accept, hold or transfer funds in
this way in these countries, require us to be licensed or to use a licensed partner?"
