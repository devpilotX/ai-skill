---
name: code-review
description: Review a diff, pull request, commit, or file for defects that matter, with a verdict and no filler. Use when the user asks to review code, review a PR or merge request, check a diff, look over an implementation, find bugs in a change, or asks whether a change is correct or safe to merge. Also use after writing a non-trivial change, before requesting human review. Reads the code and its callers before judging, ranks findings by consequence, ignores anything a formatter or linter owns, names the input that triggers each defect, checks deploy-time compatibility and new dependencies, and reports a clean change as clean. For a whole-repo release readiness audit use ship-audit instead. For a threat model use security-hardening instead. Triggers on review this code, review my PR, check my PR before merge, check this diff, review this commit, sanity check this change, LGTM?, find bugs in this change, is this safe to merge, code review.
license: MIT
metadata:
  version: 1.1.0
  suite: ai-skill
---

# Code review

Reviews fail in two directions. They miss the defect that reaches production because nobody read the
caller, and they bury the one real finding under style comments written to look thorough. This skill
corrects both: find the defects that cost something, name what triggers them, and ignore the rest.

## When to use and when to stay off

Run when there is a concrete change to judge: a diff, a pull request, a commit, a branch, or a file the
user wants checked before merge. Also run on your own non-trivial change before handing it to a human.

Stay off when:

- The user wants a whole repository judged for release readiness. `ship-audit` takes that.
- The user wants a threat model, an attack surface review, or a security design. `security-hardening` takes that. A security defect found inside a diff stays here.
- The request is a test plan with no diff to review. `test-strategy` takes that.
- The request is to restructure code safely. `refactor-safely` takes that; review its output here afterwards if asked.
- The user asks a syntax or API question. Answer it.

The user says "stop", "I've decided", or "just merge it": comply at once and stay off for the rest of
the session unless asked again.

## Non-negotiables

These override everything else in this file.

1. Read the code, including the surrounding context the diff does not show. A diff hides the caller, and the caller is often where the bug becomes real.
2. Every finding names the input, state, or sequence that triggers it, and the consequence. A finding without a trigger is a guess and gets labelled as one.
3. No manufactured findings. A clean change gets a short review saying it is clean and what was checked.
4. Do not claim a test passes or fails without running it. Say which commands ran and what they printed, or write NOT RUN with the reason.
5. Distinguish a defect from a preference, and label them differently, because the author needs to know which ones are negotiable.
6. Review the change, not the person.

## What gets reviewed and what does not

Not reviewed, ever: formatting, import order, quote style, line length, naming preferences that do not
mislead, and anything a linter or formatter already decides.

Reviewed in this order of priority:

1. Correctness on the path the author intended.
2. Correctness on paths the author did not consider: empty input, failure, retry, concurrent use.
3. Security consequences.
4. Data safety, including migrations, deletes, and anything irreversible.
5. Deploy-time compatibility between old and new versions running side by side.
6. Failure behaviour, including partial failure and retry.
7. Concurrency, ordering, and idempotency.
8. Resource handling, including unbounded growth and unclosed handles.
9. Interface and contract changes that break callers.
10. New dependencies.
11. Test adequacy for this change specifically.
12. Clarity, only where it will cause a future defect. Say why, or drop the comment.

## Procedure

### Step 1, establish intent and size

Read the description, the linked issue, and the tests. State in one sentence what this change is meant
to do. If the code does something else, that is the first finding.

If intent cannot be determined, ask, or return NEEDS MORE CONTEXT with the exact question.

Check the size. ASSUMPTION: above roughly 400 changed lines of non-generated code, review depth drops
because a reviewer cannot hold the whole change at once. This is a working heuristic, not a measured
threshold. When a change is over that size, or mixes a refactor with a behaviour change, either ask for
a split (refactor first, behaviour second) or proceed and state in NOT REVIEWED which parts got reduced
depth.

### Step 2, read the change in context

For each modified function, find every caller. For each modified interface, find every implementation
and every consumer. For each removed line, work out what depended on it.

Use the language server or the editor's find-references where available. Text search misses dynamic
dispatch, reflection, dependency injection, string-keyed handlers, and generated code, so treat a grep
result as a lower bound.

```
git diff --stat main...HEAD
git log --oneline main...HEAD
git grep -n "functionName"
```

Look at what the diff does not contain. A new field with no migration, a new branch with no test, a new
error type nobody catches, a new dependency with no lockfile change, a new feature flag with no stated
default.

### Step 3, run what can be run

Tests, type checker, linter, build. Report the real output.

When a command cannot run (no environment, missing secrets, no access to the CI result), write it in
CHECKED as `NOT RUN, because <reason>`, for example `pytest: NOT RUN, because the suite needs a database
this session cannot reach`. Then lower the confidence of any correctness claim that depended on it. Never
leave the reader to assume a suite passed.

### Step 4, hunt the specific defect classes

Checklist in `references/defect-classes.md`, organised by the class of bug rather than by language. It
covers deploy-time compatibility, dependencies, logging of secrets and personal data, feature flag
defaults, and the failure patterns typical of AI-generated code. Work the classes that apply to the
change.

For security findings that need a threat model beyond the diff, name the concern and route to
`security-hardening`. For migrations and query plans, `data-layer` has the detail. For judging whether
the tests are the right tests, `test-strategy`.

### Step 5, verify each finding before writing it

Ask what exact input triggers this, and what the consequence is. If the answer is "in some cases" or
"potentially", either find the case or move the item to observations.

Then check whether the codebase already handles it somewhere you have not read. Reporting a defect that
is handled two frames up costs the review its credibility.

### Step 6, choose the verdict

APPROVE: no blocking or non-blocking defects. Preferences may exist.

APPROVE WITH FIXES: no blocking defects, and each non-blocking fix is small, specified exactly, and
local. The author applies them and merges without another review round. If the author changes anything
beyond the listed fixes, or a fix turns out larger than described, the change needs a re-review. Say
which of these applies in the verdict line.

REQUEST CHANGES: at least one blocking defect. The reviewer re-checks after the fix.

NEEDS MORE CONTEXT: the intent, a caller, or a runtime fact cannot be determined, and the verdict
depends on it. Name the exact question.

Severity rules and worked examples of each verdict are in `references/review-output-examples.md`.

### Step 7, report

```
VERDICT: APPROVE / APPROVE WITH FIXES / REQUEST CHANGES / NEEDS MORE CONTEXT
<One sentence. If REQUEST CHANGES, the blocking reason goes here.>

WHAT THIS CHANGE DOES
<One sentence, in your own words. If this does not match the description, say so.>

CHECKED
<Commands run and their output, or NOT RUN with the reason. Files read beyond the diff.>

BLOCKING
1. path/file.py:88 - <defect>
   Trigger: <exact input or sequence>
   Consequence: <what breaks and for whom>
   Fix: <the change>

NON-BLOCKING
<Same shape, condensed.>

PREFERENCES
<Labelled as negotiable. Keep this short or empty.>

TESTS
<What this change needs a test for, and whether it has one.>

NOT REVIEWED
<Anything skipped or reviewed at reduced depth, and why.>
```

## Self-audit

- Every finding has a trigger and a consequence.
- No finding concerns formatting or anything a linter owns.
- Defects and preferences are labelled separately.
- Every test or build claim is backed by output that was seen, or marked NOT RUN with a reason.
- Callers were found with find-references where available, and grep results were treated as incomplete.
- Deploy-time compatibility was checked for any schema, message, cache, or API shape change.
- Every new dependency was checked for licence, maintenance, name correctness, and lockfile diff.
- The verdict is explicit, and APPROVE WITH FIXES says whether a re-review is needed.
- Oversized or mixed changes got a split request or a stated reduced depth.
- Anything unread is disclosed in NOT REVIEWED.
- If the change is clean, the review is short and says what was checked.

## What this cannot do

It cannot prove a change correct. A review finds defects in what was read, and anything outside the
files read, the commands run, and the environments available stays unknown. NOT REVIEWED says where
that boundary sits.

It cannot see production data volumes, traffic, or configuration unless the user supplies them, so
lock duration of a migration and load behaviour are estimates until measured.

It cannot judge licence compatibility of a new dependency with legal authority. When a dependency
carries a copyleft or unusual licence and the product is distributed, ask a software licensing lawyer:
"Does shipping package X under licence Y, linked in the way this change links it, impose obligations on
our distributed product, and what are they?"
