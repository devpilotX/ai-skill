# Test doubles and flakiness

Detail for steps 3 to 5 of `SKILL.md`: which double to use, how to find and fix flaky tests, the
quarantine policy, mutation testing, snapshot rules, and consumer-driven contract tests.

## Test doubles

| Double | What it is | Use it for | Risk |
| --- | --- | --- | --- |
| Fake | A working lightweight implementation, such as an in-memory repository | Fast tests of code that needs a collaborator with real behaviour | Diverges from the real thing on constraints, transactions and ordering |
| Stub | Returns canned answers, records nothing | Forcing a branch: a timeout, a 404, an empty list | Canned answers drift from what the real service returns |
| Mock | Pre-programmed with expected calls, fails if they do not happen | Verifying an outbound command whose effect you cannot observe, such as "sent exactly one email" | Tests wiring; breaks on refactor; can assert its own configuration |
| Spy | Wraps or records calls on a real or fake object for later assertion | Checking a side effect after the fact while keeping real behaviour | Same wiring risk as a mock if it is the only assertion |

Prefer, in order: the real dependency, a fake you also test against the real one, a stub, and a mock or
spy last. Assert on the outcome (the returned value, the stored row, the emitted message) whenever it
is observable.

## Flakiness root causes and fixes

| Cause | Symptom | Fix |
| --- | --- | --- |
| Time | Fails near midnight, month end, DST change, or on slow machines | Inject a clock and freeze it; never compare against real now |
| Ordering | Passes alone, fails in the full run or with a random order seed | Remove dependence on execution order; run with random order in CI to expose it |
| Shared state | Fails after a particular other test; leftover rows, globals, singletons, env vars | Fresh state per test, transactions rolled back, no module-level mutable state |
| Async waits | Fixed sleeps, assertions racing a background task | Wait for a condition with a timeout; await the task; use the framework's settle helper |
| Network | Real DNS or third party calls, port collisions | Stub the boundary; bind to port 0 and read the assigned port |
| Resource leaks | Fails late in the run: file handles, connections, threads exhausted | Close in teardown; assert no leaked handles in a suite-level check |
| Unseeded randomness | Fails on some seeds | Seed, print the seed, and replay it |
| Concurrency in the code under test | Real race in production code | Treat as a real bug; `debug-method` has race tooling |

To confirm a fix, run the single test in a loop enough times to see the old failure rate drop to zero.
ASSUMPTION: a test that failed once in fifty runs needs a few hundred clean runs before the fix is
credible; pick the count from the observed failure rate, not from a fixed number.

## Quarantine policy

1. A test that fails and then passes on the same commit is flaky. Move it out of the gating run the same day.
2. It still runs, in a non-gating job, so its failure rate stays visible and a fix can be confirmed.
3. It gets a named owner and a deadline, recorded in the tracker entry linked from the test.
4. At the deadline it is fixed and returned, or deleted with a note of the behaviour that is now untested and who accepted that gap.
5. The quarantine list is reported regularly. A growing list is a signal about the suite, not about individual tests.

Blind retries in the gating run are banned because they hide real races in production code along with
the test defects.

## Mutation testing workflow

1. Run it on the risky modules from the failure-cost list, not the whole codebase. Full runs are slow.
2. Read surviving mutants. Each one is a code change no test noticed.
3. For each survivor, either add an assertion that kills it, or mark it equivalent (the mutant behaves identically, such as a change to a log message) with a reason.
4. Track the survivors in risky code over time. Do not turn the mutation score into a target, for the same reason as coverage.
5. In CI, run it incrementally on changed files, since a full run is expensive.

Tools: Stryker for JavaScript, TypeScript and C#; PIT for Java and the JVM; mutmut for Python. Retrieve
the current supported language list from each project's documentation.

## Snapshot rules

Snapshot only output that is meant to be stable and whose whole shape matters: a serialised API response,
a rendered email, a CLI help text.

Keep each snapshot small enough to read in review. A snapshot of a whole page gets approved without being
read.

Review every snapshot diff as a code change. An updated snapshot is an assertion that the new output is
correct.

Never run the bulk update command to make a red build green without reading the diff.

Strip volatile values (timestamps, generated identifiers) before snapshotting, or the test becomes flaky.

## Consumer-driven contract tests

The consumer writes the interactions it relies on (request, and the parts of the response it reads).
Pact records these as a contract file. The provider's build replays each contract against the real
provider and fails if any interaction breaks. A broker shares contracts between repositories and can
answer whether a given version pair is safe to deploy together.

Use it when separate teams deploy the two sides independently. Within one repository deployed as a unit,
an ordinary integration test is cheaper.

Contracts cover shape and the fields the consumer reads. They do not cover provider business logic, which
stays in the provider's own tests.
