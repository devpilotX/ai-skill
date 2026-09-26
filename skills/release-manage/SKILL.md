---
name: release-manage
description: Ship changes to users in a way that limits damage and can be undone quickly. Use when the user asks how to release, version, tag or roll out a change, cut a release, write release notes or a changelog, publish to npm or PyPI, yank a version, asks about semantic versioning, feature flags, a kill switch, canary, percentage or staged rollout, blue green, deprecating an API, a breaking change, or says a release went wrong. Separates deploying from releasing, sets the abort condition and watcher first, picks the rollback path per artefact type, keeps migrations compatible with both versions, and requires deprecation with a date and a migration path. Platform rollback mechanics go to infra-deploy, live debugging of a failure goes to debug-method. Triggers on how do I release, cut a release, release notes, changelog, semver, publish to npm, publish to PyPI, yank a version, feature flag, kill switch, canary, percentage rollout, blue green, breaking change, deprecate, rollback, hotfix, bad release, release went wrong.
license: MIT
metadata:
  version: 1.1.0
  suite: ai-skill
---

# Release management

A bad change becomes an outage when the only way to stop it is another deploy, when nobody decided in
advance what "bad" looks like, or when the rollback path does not exist for that kind of artefact. This
skill corrects that by separating deploying code from releasing behaviour, fixing the abort condition
and the watcher before the rollout starts, and choosing a rollback path that works for what is being
shipped.

## When to use and when to stay off

Run when a change is about to reach users or consumers: a deploy of a service, a published package, a
mobile build, a schema or config change, a flag flip, a deprecation. Run also when a release went wrong
and the question is how to contain it.

Stay off, and route instead, when:

- The question is how the hosting platform performs a rollback, blue green switch or deploy pipeline. Use `infra-deploy`.
- The release is contained and the question is why it failed. Use `debug-method`.
- The question is how to write the migration itself (expand and contract, backfill, locking). Use `data-layer`.
- The change moves the system to a different technology or provider. Use `migration-plan`.
- The question is whether the whole product is ready to launch. Use `ship-audit`.

The user says "stop", "I've decided", or "just execute": comply at once and stay off for the rest of
the session unless asked again.

## Non-negotiables

These override everything else in this file.

1. Every rollout has an abort condition defined before it starts: a metric, the baseline it is compared with, a threshold, a named watcher, and a watch window.
2. A responder is available for the full watch window. If nobody can act on the abort condition until it closes, the rollout waits.
3. Every database migration shipped with a release works with both the old and the new code, so the code can roll back while the migration stays. Destructive steps ship in a later release, after the old code is gone.
4. The rollback path for this artefact type is known and has been performed at least once on purpose, with its duration written down. Where no rollback exists (a published package, a store build), the fix forward path is prepared instead.
5. Risky behaviour goes behind a flag, so disabling does not need a deploy.
6. Every breaking change gets a version, a changelog entry written for users, and a migration path.
7. Deprecation comes with a date, a replacement, and a way to see who still uses the old thing.

## Procedure

Templates for the stage ladder, the abort condition, the rollback matrix, deprecation headers and
incident messages are in `references/rollout-playbook.md`.

### Step 1, classify the artefact and the change

Name the artefact type: web service, published package, mobile store build, database schema, runtime
config, or flag. The type decides the rollback path in step 3.

Then decide whether the change is breaking, in both directions of the interface.

Inputs consumers send (request bodies, parameters, function arguments): making an optional field
required, narrowing accepted values, removing an accepted value, or tightening validation breaks
callers. Adding an optional field does not.

Outputs consumers read (response bodies, return values, events): removing a field, renaming it, changing
its type, or making an always present field optional or nullable breaks readers. Making a field always
present that used to be optional does not break them. Adding an enum value to a response can break
clients that match exhaustively or reject unknown values, so treat it as breaking unless the contract
told clients to tolerate unknown values.

Also breaking in either direction: changing a default, changing the meaning of an error code, and
changing behaviour consumers depend on with the signature unchanged.

### Step 2, pick the version

For anything other people depend on, use [semantic versioning](https://semver.org/): major when
consumers must do work, minor for compatible additions, patch for compatible fixes.

Under 0.x, the SemVer specification treats the public API as unstable and anything may change. Say in
the README how this project uses 0.x (a common convention is breaking changes in the minor number), or
move to 1.0.0 once people depend on it.

Pre-release tags such as `1.4.0-rc.1` sort before `1.4.0` and let testers opt in. Package managers
generally do not select pre-releases unless asked; check the current behaviour of the target registry
and client.

For an application nobody imports, a date or build number is fine.

### Step 3, choose the rollout shape and confirm the rollback path

Pick the rollout shape by what a failure costs and how fast it would show: all at once, canary, staged by
cohort or percentage, blue green, or a shadow run. The stage ladder is in the playbook.

A shadow run (sometimes called a dark launch) sends a copy of real traffic through the new path and
discards its results. It is one way to see performance under real traffic before anyone depends on it;
load tests and canaries are others. The shadow path must not cause side effects: no emails, no charges,
no writes to shared stores, no calls to third parties that act on them. Stub or sandbox those calls, and
check that it is enforced in code, not by convention.

Look up the rollback path for the artefact type in the rollback matrix in
`references/rollout-playbook.md`. Web services roll back by redeploying the previous build or switching
traffic. Published packages usually cannot be withdrawn (registries restrict unpublishing; retrieve the
current npm and PyPI policies), so the path is fix forward with a new version plus yanking or deprecating
the bad one. Mobile store builds cannot be pulled from devices that installed them, so the path is a
phased release that can be paused, server side flags, and a minimum supported version gate; see
`mobile-build` for store specifics. Schemas follow step 4. Config and flags roll back by reverting the
value, which is why they need an audit trail.

### Step 4, make migrations compatible with both versions

Use expand and contract, the add, backfill, switch, remove sequence that `data-layer` details for safe
schema changes. Release N adds the new shape (nullable or defaulted columns, new tables) and writes to
both; the backfill runs. Release N+1 moves reads to the new shape and stops writing the old one. Release N+2, after the old code is gone
everywhere including workers and scheduled jobs, removes the old shape.

Check before shipping: could the previous build run against the migrated schema without errors? If not,
split the migration.

### Step 5, put risky behaviour behind a flag

Flag anything risky, large, or needing a staged rollout. Keep flags boolean. Default to off, and make the
off path the existing behaviour so a failure to evaluate the flag is safe. Test both sides. Give every
flag an owner and a removal date at creation, and remove it once the rollout completes.

A kill switch is a flag whose only job is to turn a feature off fast. It should need no deploy and no
approval chain to flip.

Implementation of flags in services belongs to `backend-build`.

### Step 6, define the abort condition

Fill in the abort condition template from the playbook: metric, baseline, threshold, watcher, window.

Compare the canary with a baseline running the old version over the same period, not with yesterday.
Traffic mix, time of day and upstream incidents move both groups; the difference is the signal.

A small canary may lack the traffic to show a real difference. Work out how many requests the canary
needs before a change in error rate of the size you care about is distinguishable from noise, check the
arithmetic with `numbers-check`, and lengthen the stage or widen it if it cannot get there. Until then,
"no errors seen" means "not enough data", not "safe".

Tie the threshold to the service level objective and its error budget where one exists, as set up in
`observability-setup`: abort when the canary burns budget faster than the rate the SLO allows. Without an
SLO, state the threshold as an `ASSUMPTION:` with its reasoning.

Confirm the per version metrics exist before starting. Without them a canary is a slower deploy.

### Step 7, prepare the release

Write the changelog for the person deciding whether to upgrade. The format at
[Keep a Changelog](https://keepachangelog.com) is a reasonable default: sections for added, changed,
deprecated, removed, fixed and security, newest first, with an unreleased section on top. Put breaking
changes first with the migration step inline, and describe fixes by the symptom that is gone. "You no
longer get logged out when two tabs refresh at once" tells a user whether to upgrade.

If commits follow [Conventional Commits](https://www.conventionalcommits.org), tooling can propose the
version bump and draft the changelog. Treat the draft as raw material and rewrite it for users. Longer
release notes go through `doc-forge`.

Tag the release in version control and make the artefact traceable to the commit.

Branch flow: release from the main branch where possible. When an older version needs support, cut a
release branch from its tag. A hotfix goes to the main branch first and is cherry-picked to each
supported release branch, so the fix is not lost in the next release. Every hotfix gets its own version
and changelog entry.

Keep one change per release where possible, so a failure can be attributed.

### Step 8, run the rollout

Confirm the watcher and responder are on for the whole window. Move through the stage ladder, checking
the abort condition at each stage for its full wait. For anything touching data, the wait is long enough
for the problem to appear, often hours.

### Step 9, if the release goes wrong

Mitigate before diagnosing. Flip the flag, pause the phased release, or roll back, then work out why with
`debug-method`.

Prefer the flag, then the rollback path from step 3, then a forward fix. A rushed forward fix is how a
second incident starts. For packages and store builds the forward fix is the rollback path, so prepare it
before the release.

If a migration already ran, roll back only the code. Step 4 is what makes that safe.

Communicate early with what is known, what is not, and when the next update comes, using the incident
template in the playbook.

Write it up afterwards, focused on the system. The useful output is a change that makes the class of
failure impossible.

### Step 10, deprecate and remove on schedule

Announce with a date, in the changelog and directly to the people affected. Add usage telemetry so you
know who is still calling.

For HTTP APIs, send the `Deprecation` response header defined in
[RFC 9745](https://www.rfc-editor.org/rfc/rfc9745), and the `Sunset` header defined in
[RFC 8594](https://www.rfc-editor.org/rfc/rfc8594) with the removal date, plus a link to the migration
guide. Examples are in the playbook. For packages, use the registry's deprecation mechanism so the
warning shows at install time.

Keep the old path working for the stated period and remove it on the stated date. For a widely used
interface, provide a tool that performs the migration.

## Self-audit

- The abort condition names a metric, a baseline, a threshold, a watcher and a window, and was written before the rollout.
- A responder was confirmed for the whole watch window.
- The canary has enough traffic to detect the threshold, or the report says it does not.
- The rollback path matches the artefact type, and was practised with its duration recorded.
- Every migration in the release runs against the previous build without errors.
- Breaking change analysis covered both inputs and outputs, including new enum values in responses.
- Any shadow path has side effects blocked in code.
- The version number reflects whether consumers must act, with 0.x and pre-release use stated.
- The changelog is written in user terms, with migration steps for breaking changes.
- Risky behaviour is behind a flag with an owner and removal date, and both paths are tested.
- Deprecations carry a date, a replacement, usage telemetry, and the `Deprecation` and `Sunset` headers for HTTP.

## What this cannot do

It cannot see the user's metrics, so it cannot say whether a canary is healthy; it can only define the
check.

It cannot change registry or store policy. Unpublish windows, yank behaviour, phased release rules and
review times belong to npm, PyPI, Apple and Google, and have to be retrieved from their current
documentation.

It cannot decide contractual obligations around deprecation or downtime. If customers have a service
agreement, ask the lawyer who drafted it or the account's commercial owner: "What notice period and
communication channel does our agreement require before we remove or change this API, and does this
rollout's expected degradation count against any availability commitment?"
