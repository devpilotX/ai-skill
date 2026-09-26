---
name: debug-method
description: Find the cause of a bug by narrowing it down instead of guessing at fixes. Use when the user reports something broken, pastes an error, exception or stack trace, reports a crash, segfault, hang or deadlock, says it used to work, reports a regression, says it works locally but not in production or only sometimes, asks about a race condition, memory leak or heisenbug, or has tried several fixes. Requires a reproduction before any fix, tests one falsifiable hypothesis at a time, changes one thing per experiment, automates bisection, and refuses to call a symptom fixed without an explanation. In a live incident it mitigates first and preserves evidence. For flaky test policy use test-strategy instead. For general slowness with no regression use performance-tuning instead. Triggers on why is this broken, debug this, stack trace, exception, crash, segfault, hangs, deadlock, it used to work, regression, works locally but not in production, intermittent failure, race condition, memory leak, I tried everything.
license: MIT
metadata:
  version: 1.1.0
  suite: ai-skill
---

# Debugging method

The failure this corrects is guessing at fixes: changing things until the symptom pauses, then shipping
changes nobody can justify while the cause stays in the code. The discipline is one hypothesis at a time
with a prediction that could turn out wrong.

## When to use and when to stay off

Run when something behaves wrong and the cause is unknown: an error, a crash, a hang, wrong output, a
regression, or an intermittent failure.

Stay off when:

- The user wants a policy for flaky tests in general. `test-strategy` takes that. The root cause of one flaky test stays here.
- Something is slow and did not get slower after a specific change. `performance-tuning` takes that. A slowdown with a known good version stays here for bisection.
- The cause is already known and the user wants the fix written. Write it, with the regression test.
- The user asks what an error message means in general, with no failing system in front of them. Answer it.

The user says "stop", "I've decided", or "just fix it": comply at once and stay off for the rest of the
session unless asked again.

## Non-negotiables

These override everything else in this file.

1. Reproduce before fixing. Exception: during a live incident, mitigate first (see incident mode), preserve evidence, then reproduce before the real fix.
2. One change per experiment.
3. Write the prediction before running the experiment. Unwritten predictions get retrofitted to whatever happened.
4. A symptom that stopped without an explanation is not fixed. Say so plainly.
5. Read the actual error, all of it, including the cause chain and the line numbers.
6. Keep a list of what has been ruled out and how.
7. Distinguish the cause from the trigger. Fixing only the trigger leaves the bug.

## Incident mode

When users are affected now, restoring service outranks understanding the cause.

1. Mitigate: roll back the last deploy, turn off the feature flag, fail over, shed load, or scale. Pick the smallest action that is reversible. `release-manage` covers rollback and flag procedure.
2. Preserve evidence before it disappears: copy the relevant logs and traces, take a core dump or heap dump of a misbehaving process before restarting it, save the failing input or request, and note the exact versions and the time window. Restarts and rollbacks destroy most of this.
3. Once stable, reproduce from the preserved evidence and continue with the procedure below. The mitigation is not the fix.

If the telemetry needed to answer "what changed and where" does not exist, `observability-setup` covers
adding it.

## Procedure

### Step 1, get the facts straight

What exactly happens, and what was expected instead?

Which environment, which version, which commit? When did it last work? A working commit plus a broken
commit converts the problem into a search.

Is it everyone or one user, one tenant, one region, one device, one browser?

What changed near the start of it? A deploy, a configuration change, a dependency update, a data change, a
certificate expiry, a third party incident, or a clock change.

Read the whole error text and the whole stack trace, from the innermost cause outwards.

Pick the matching playbook in `references/techniques-by-symptom.md`: crash or exception, hang or
deadlock, memory leak, race, works locally but not in production, only one browser or device, and slow
regression. Each lists the tools and the first three experiments.

### Step 2, reproduce

Reliably if possible. Intermittently if that is all there is, and then record the rate, because a change
from one in ten to one in a hundred looks like a fix and is not.

Shrink the reproduction. Remove inputs and steps until removing anything makes it stop.

For anything intermittent, run it in a stress loop (the same test or request N times, in parallel where
relevant) to get a rate, and suspect a race, an ordering dependence, a resource limit under load, or time
and timezone behaviour.

If it cannot be reproduced locally, add observability where it does happen. Logging the inputs at the
failure point is faster than reasoning about what they might be.

### Step 3, bisect the space

In time, using version control. Automate it when a script can tell good from bad:

```
git bisect start <bad> <good>
git bisect run ./repro.sh     # exit 0 good, 1 to 127 bad, 125 skip
git bisect skip               # for a commit that cannot be built or tested
git bisect reset
```

A script exit code of 125 tells bisect to skip that commit, so broken intermediate commits do not derail the
search.

In the stack, by checking whether the data is correct at each layer. The first place it is wrong is
where to look, not where the exception surfaced.

In the data, by finding which record triggers it.

In the configuration, by comparing environments field by field: a version, a variable, a permission, a
limit, a concurrency level, or the data volume.

In the code, by removing halves until the smallest failing piece remains.

### Step 4, observe with tools instead of prints

A debugger with breakpoints and conditional breakpoints shows the whole state at the failure point
without an edit and a rebuild per question. For a process you cannot stop, attach a tracer: strace or
ltrace on Linux, dtruss or DTrace on macOS, eBPF tools such as bpftrace for production kernels. Print
statements are acceptable for a quick confirmation, and they change timing, which matters for races.

### Step 5, form and test one hypothesis

State it as a falsifiable claim. For example: the handler reads the record before the transaction that
writes it has committed, so under concurrent requests it sees the previous value.

Write the prediction so it can fail. If this is true, forcing the read to happen between the write and
the commit, with a barrier or an injected delay at exactly that point, will show the stale value every
time, and forcing the opposite order will never show it.

Adding a lock or extra logging and watching the symptom stop is weak evidence, because both change the
timing and can hide a race without explaining it. Force the interleaving instead. For native code, run
under ThreadSanitizer or AddressSanitizer; for hard-to-reproduce native failures, record once with rr and
replay deterministically. Where the runtime supports it, use a deterministic scheduler or a
concurrency testing tool that explores interleavings.

Run the experiment, change one thing, and record the result whether or not it matched. A failed
prediction rules the hypothesis out; record it and move on.

### Step 6, confirm the cause

You have the cause when you can explain every observed symptom with it, including the part that seemed
odd, and when you can turn the bug on and off deliberately.

An explanation that covers only some of the symptoms suggests two problems, or the wrong one.

### Step 7, fix it properly

Write the failing test first, so there is proof the fix works and protection against its return.

Fix the cause, not the symptom. A null check where the null should never have arrived hides the real
defect.

Search for other instances of the same pattern.

Check the fix does not break the case the original code was written for.

For a bug in a query, migration, or data shape, `data-layer` has the detail.

### Step 8, report

State the cause, the trigger, the evidence, the fix, the test, and anything ruled out along the way.
Include where else the pattern might exist.

If the cause was never found and the symptom stopped, say that explicitly.

## Causes worth checking early

Not the code at all: a configuration difference, an expired credential or certificate, a full disk, a
clock skew, a permission change, or a third party incident.

Caching at any layer: the browser, a CDN, an application cache, a DNS resolver, a build cache.

An old version still running somewhere, which makes a fix appear not to work.

Two versions running at once during a deploy.

Character encoding, and a locale difference between environments.

A timezone or daylight saving boundary.

Silent truncation by a column length or a payload limit.

A retry that succeeded and left duplicate work behind.

## Self-audit

- A reproduction exists, with its rate if intermittent, or incident mode was used and evidence preserved.
- Each experiment changed one thing, with the prediction written first.
- Race hypotheses were tested by forcing the interleaving, not by adding a lock or logging.
- Bisection was automated with a script where a script could decide.
- Ruled out list maintained.
- The cause explains every symptom, and the bug can be switched on and off.
- Cause fixed rather than symptom.
- A test fails before the fix and passes after.
- Other instances of the same pattern searched for.
- If the cause was not found, that is stated.

## What this cannot do

It cannot debug a system it cannot observe. Without logs, a reproduction, or access to the failing
environment, it can rank hypotheses and design experiments, and someone with access has to run them.

It cannot guarantee a race is gone. Forcing interleavings and sanitizers raise confidence; they do not
prove absence.

It cannot replace a forensic investigation when the cause may be a security breach. If evidence points
to unauthorised access, stop changing the system and ask the security incident response lead: "Should
we isolate this host and preserve disk and memory images before any further debugging or rollback?"
