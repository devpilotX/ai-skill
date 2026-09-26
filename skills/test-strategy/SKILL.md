---
name: test-strategy
description: Decide what deserves a test and write tests that fail for the right reason. Use when the user asks what or how to test, asks about unit, integration or end to end tests, the test pyramid, coverage, what to mock, fixtures, flaky tests, slow tests, TDD, snapshot tests, contract tests, mutation testing, property-based tests, or a regression test for a bug, or asks why tests pass while production breaks. Allocates effort by what a failure costs rather than a coverage target, tests behaviour instead of implementation, quarantines flaky tests instead of retrying them, and measures assertion strength with mutation testing. For the root cause of one flaky test use debug-method instead. For adding tests before refactoring legacy code use refactor-safely instead. Triggers on what should I test, how do I test this, test coverage, what to mock, flaky tests, tests are slow, test pyramid, TDD, snapshot tests, mutation testing, regression test, property-based testing, my tests pass but production breaks.
license: MIT
metadata:
  version: 1.1.0
  suite: ai-skill
---

# Test strategy

Suites fail in a specific way: they go green while production breaks, because they were written to touch
lines, assert on mocks, or retry until they pass. A test suite exists to let you change code without
fear. Judge it by that, and not by a percentage.

## When to use and when to stay off

Run when the user is deciding what to test, how to test it, how to structure a suite, or why a suite is
slow, flaky, or failing to catch real defects.

Stay off when:

- One specific test fails intermittently and the user wants the cause. `debug-method` takes the diagnosis; come back here for the quarantine policy.
- The user wants a safety net before restructuring legacy code. `refactor-safely` owns characterisation tests and seams for that purpose.
- The user wants a diff reviewed, including its tests. `code-review` takes that.
- The user asks a syntax question about a test framework. Answer it.

The user says "stop", "I've decided", or "just write the tests": comply at once and stay off for the
rest of the session unless asked again.

## Non-negotiables

These override everything else in this file.

1. Allocate effort by the cost of failure. Money movement, authentication, authorisation, deletion and data integrity get tested first and thoroughly.
2. Test behaviour through the public interface. A test asserting on internal structure breaks on every refactor, which teaches the team to delete tests.
3. A flaky test is a defect. Quarantine it: out of the gating run, still running, with an owner and a deadline. Never add a blind retry.
4. Every bug fix gets a regression test that fails before the fix and passes after.
5. Never claim a test passes without running it. Include the command and the output.
6. Assert on something specific. A test asserting only that no exception was thrown passes when the result is wrong.
7. Tests must be deterministic. No real network, no real clock, no dependence on ordering, no shared mutable state between tests.

## What coverage actually means

Line coverage measures which lines executed. Branch coverage measures whether each side of each decision
ran. Condition coverage, and the stricter modified condition/decision coverage, check each boolean
sub-expression separately. None of them says whether the assertions were meaningful: a suite that calls
every function and asserts nothing reaches full coverage and catches nothing.

Use coverage in one direction only: to find code with no test at all. Prefer branch coverage for that,
since line coverage counts a one-line `if` as covered when only one side ran. Never set coverage as a
target, because a target produces tests written to touch lines.

To measure whether assertions would catch a defect, use mutation testing. The tool changes the code (flips
a comparison, removes a call) and reruns the tests; a surviving mutant is a change no test noticed.
Stryker (JavaScript, TypeScript, C#), PIT (Java), and mutmut (Python) are the usual tools. Workflow in
`references/test-doubles-and-flakiness.md`.

## What to test at each level

Unit tests for logic with branches: calculations, validation, state transitions, parsing, permission
rules. Fast, numerous, and where edge cases belong. Code with no branches and no logic does not need its
own unit test.

Integration tests for the seams between your code and what it talks to: a handler with its database, a
repository against a real database engine, a consumer against a real queue. Use the same engine as
production, since an in-memory substitute behaves differently on constraints, transactions and types.
Testcontainers, or a database service in CI, makes the real engine cheap to start per run.

End to end tests for a small number of complete user journeys, such as signup, the main task, and
checkout. They are slow and brittle, so keep the count low and each one high value.

Contract tests when separate teams own the two sides of an interface, so a provider change breaks the
provider's build before it breaks the consumer's production. Consumer-driven contracts with Pact are
covered in the reference.

Property-based tests for anything with an invariant: a round trip through serialisation, an ordering
that must hold, a total that must balance. Hypothesis (Python) and fast-check (JavaScript, TypeScript)
generate inputs and shrink a failure to the smallest case.

Snapshot tests only for output that is meant to be stable and reviewed as a whole. Keep each snapshot
small, review every snapshot diff as a code change, and never update snapshots in bulk to make a run
green.

## Position on TDD

Writing the test first is a design aid, not a requirement of this skill. It pays most where the behaviour
is well specified and the design is uncertain: parsers, calculations, state machines, bug fixes. For a
bug fix the regression test comes first always (non-negotiable 4). For exploratory work, a spike without
tests followed by tests before merge is acceptable. Judge the result by the suite, not by the order it
was typed.

## Procedure

### Step 1, list the failure costs

Write down what breaks the business if it is wrong, ordered by consequence. That list is the test plan,
and it gets more attention than everything else combined.

### Step 2, cover the risky paths, including failure paths

For each risky path, test the success case, the boundary cases, and the failure cases. Error handling
with no test tends to fail when it finally runs.

Test the concurrency assumption where one exists: the same request twice, and two writers at once.

### Step 3, choose test doubles deliberately

Use the real thing where practical, which now includes the database and the queue in most stacks.

Mock at the boundary you do not own, such as a third party HTTP service. Fake, stub, mock and spy are
different tools; the table is in `references/test-doubles-and-flakiness.md`.

Recorded fixtures go stale when the provider changes, and a raw recording can capture tokens, cookies,
and personal data. Scrub secrets and personal data before committing a recording, re-record on a
schedule, and pair recordings with a contract test so drift fails a build.

Never mock the thing under test. Never assert only that a mock was called, because that tests wiring
rather than behaviour. A suite in which every mock returns what the test wants will stay green while
production breaks.

### Step 4, build test data locally

Use test data builders or factories that create exactly the records a test needs, with defaults for the
rest. A shared fixture file that every test depends on accumulates special cases until nobody can change
it. Each test states the fields it relies on.

### Step 5, keep the suite fast and honest

Fast enough to run on every change. When it is not, people stop running it.

Parallelise, and make each test independent so it can run in any order. In CI, shard the suite across
runners, and consider test impact selection (running only tests affected by the changed files) on pull
requests, with the full suite still running on the main branch.

Fresh state per test, created by the test.

No sleeps. Wait for a condition with a timeout.

Freeze the clock rather than depending on real time.

Seed randomness and print the seed so a failure is reproducible.

Flaky tests go to quarantine under the policy in `references/test-doubles-and-flakiness.md`, and the
root cause goes to `debug-method`.

### Step 6, existing code with no tests

Start where a change is about to happen, not everywhere. Write a characterisation test first, asserting
what the code currently does. For restructuring that code, `refactor-safely` covers seams and the full
method.

### Step 7, run and report

Run the suite, the type checker and the linter. Include the real output.

Report the risky paths that remain untested, and surviving mutants in risky code if mutation testing
ran. That is the useful gap, not the percentage.

## Self-audit

- The list of expensive failures exists, and each risky path has a test.
- Failure paths tested, not only success paths.
- Tests assert on behaviour through the public interface.
- No test depends on the real clock, the real network, or another test.
- Every bug fix has a regression test that failed first.
- No mock asserted on as a substitute for behaviour.
- Recorded fixtures are scrubbed and backed by a contract test.
- Every flaky test is quarantined with an owner and a deadline, or fixed.
- Coverage used only to find untested code, never quoted as quality.
- Output included, with the untested risky paths named.

## What this cannot do

It cannot prove the absence of defects. Tests show the presence of the behaviours they check and nothing
about the ones nobody thought of; mutation testing and property-based tests narrow that gap without
closing it.

It cannot decide which failures cost the business most without the user's knowledge of the business.
The failure-cost list in step 1 needs their input.

It cannot certify software for regulated use. For safety-critical or regulated systems (medical devices,
avionics, automotive), ask the quality or regulatory assurance engineer: "Which standard applies to this
component, what coverage criterion and evidence does it require, and which tool qualification is
needed for our test tooling?"
