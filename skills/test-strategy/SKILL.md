---
name: test-strategy
description: Decide what deserves a test and write tests that fail for the right reason. Use when the user asks what or how to test, asks about unit, integration or end to end tests, test coverage, mocking, fixtures, flaky tests, test driven development, snapshot tests or contract tests, asks why their tests pass while production breaks, or asks how to add tests to code that has none. Allocates effort by what a failure costs rather than by a coverage target, tests behaviour instead of implementation so refactoring does not break the suite, makes flakiness a defect rather than a retry, and states plainly that coverage percentage measures execution rather than correctness. Triggers on what should I test, how do I test, unit tests, integration tests, end to end tests, test coverage, mocking, flaky tests, TDD, snapshot tests, my tests pass but production breaks, add tests to legacy code.
license: MIT
metadata:
  version: 1.0.0
  suite: ai-skill
---

# Test strategy

A test suite exists to let you change code without fear. Judge it by that, and not by a percentage.

## What coverage actually means

Coverage measures which lines executed while the tests ran. It says nothing about whether the assertions
were meaningful. A suite that calls every function and asserts nothing reaches full coverage and catches
nothing.

Use coverage in one direction only: to find code with no test at all. Never as a target, because a target
produces tests written to touch lines.

The useful question is different. Pick the most dangerous function in the codebase, then find its test. If
there is none, that is the gap, whatever the percentage says.

## Non-negotiables

1. Allocate effort by the cost of failure. Money movement, authentication, authorisation, deletion and data integrity get tested first and thoroughly. A settings page does not.
2. Test behaviour through the public interface. A test asserting on internal structure breaks on every refactor, which teaches the team to delete tests.
3. A flaky test is a defect. Fix it or delete it. Retrying it teaches everyone to ignore red, which costs more than the test was worth.
4. Every bug fix gets a test that fails before the fix and passes after. Without that, there is no evidence the fix works and no protection against its return.
5. Never claim a test passes without running it. Include the command and the output.
6. Assert on something specific. A test asserting only that no exception was thrown passes when the result is wrong.
7. Tests must be deterministic. No real network, no real clock, no dependence on ordering, no shared mutable state between tests.

## What to test at each level

Unit tests for logic with branches: calculations, validation, state transitions, parsing, permission
rules. Fast, numerous, and where edge cases belong. If the code has no branches and no logic, a unit test
on it is ceremony.

Integration tests for the seams, which is where most real defects live. A handler with its database, a
repository against a real database engine rather than a fake, a consumer against a real queue. Use the
same engine as production, since an in memory substitute has different behaviour on constraints,
transactions and types.

End to end tests for a small number of complete user journeys. Signup, the main task, and checkout. These
are slow and brittle, so keep the count low and the value high. Five good ones beat fifty flaky ones.

Contract tests when separate teams own the two sides of an interface, so a provider change breaks the
provider's build rather than the consumer's production.

Property based tests for anything with an invariant, such as a round trip through serialisation, or an
ordering that must hold. These find inputs nobody would think to write.

## Procedure

### Step 1, list the failure costs

Write down what breaks the business if it is wrong. That list, ordered, is the test plan. Most codebases
have between five and fifteen of these, and they deserve more attention than everything else combined.

### Step 2, cover the risky paths, including failure paths

For each risky path, test the success case, the boundary cases, and the failure cases. Untested error
handling is usually broken error handling, and it runs at the worst moment.

Test the concurrency assumption where one exists: the same request twice, and two writers at once.

### Step 3, choose test doubles deliberately

Use the real thing where it is practical, which now includes the database and the queue in most stacks.

Mock at the boundary you do not own, meaning a third party HTTP service, and record real responses to
build the fixtures so they match reality.

Never mock the thing under test. Never assert only that a mock was called, because that tests wiring
rather than behaviour.

Beware the suite that passes because every mock returns what the test wants. That is the main way a green
suite coexists with broken production.

### Step 4, keep the suite fast and honest

Fast enough to run on every change. When it is not, people stop running it, which loses the whole benefit.

Parallelise, and make each test independent so it can run in any order.

Fresh state per test, created by the test rather than by a shared fixture that accumulates.

No sleeps. Wait for a condition with a timeout.

Freeze the clock rather than depending on real time.

Seed randomness and print the seed so a failure is reproducible.

### Step 5, existing code with no tests

Do not start by adding tests everywhere. Start where a change is about to happen.

Write a characterisation test first, which asserts what the code currently does rather than what it
should. That gives a safety net for the change without requiring the code to be correct first.

Find a seam to inject a dependency at. Where none exists, `refactor-safely` covers creating one without
changing behaviour.

Then make the change with the net in place.

### Step 6, run and report

Run the suite, the type checker and the linter. Include the real output.

Report the risky paths that remain untested, since that is the useful gap rather than the percentage.

## Self-audit

- The list of expensive failures exists, and the risky paths have tests.
- Failure paths tested, not only success paths.
- Tests assert on behaviour through the public interface.
- No test depends on the real clock, the real network, or another test.
- Every bug fix has a test that failed first.
- No mock asserted on as a substitute for behaviour.
- Suite runs fast enough that people will run it.
- Output included, with the untested risky paths named.
