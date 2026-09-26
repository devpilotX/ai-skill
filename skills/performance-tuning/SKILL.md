---
name: performance-tuning
description: Make software faster by measuring first and changing the thing that dominates. Use when the user says something is slow, asks how to optimise or speed up code, a page, an API or a service, asks about profiling, caching, latency, p99, throughput, memory usage, OOM, CPU at 100 percent, timeouts under load, bundle size, Lighthouse scores or Core Web Vitals, or scaling. Refuses to optimise without a profile, sets a target before starting, fixes the largest contributor, and compares before and after with repeated runs and a statistical test. Names the cost of every optimisation. For one slow SQL query use data-layer instead. For it got slower after a specific change, bisect with debug-method. For release readiness use ship-audit instead. Triggers on this is slow, optimise this, speed up my app, profiling, high latency, p99, throughput, timeout under load, CPU at 100 percent, OOM, memory usage, bundle size, Lighthouse, reduce load time.
license: MIT
metadata:
  version: 1.1.0
  suite: ai-skill
---

# Performance tuning

The failure this corrects is optimising on intuition: changing the code that looks slow, reporting one
before-and-after run, and calling noise a win. Intuition about what is slow is wrong often enough that
acting on it wastes the effort. Measure, fix the dominant cost, measure again with statistics.

## When to use and when to stay off

Run when there is a performance complaint or goal: latency, throughput, memory, CPU, load time, bundle
size, or a scaling question.

Stay off when:

- The problem is one slow SQL query. `data-layer` takes that, starting from the query plan.
- It got slower after a specific change and a good version is known. `debug-method` bisects to the commit; come back here to measure and fix.
- The user wants a whole release judged. `ship-audit` takes that.
- The code is not yet correct. Correctness first.

The user says "stop", "I've decided", or "fast enough": comply at once and stay off for the rest of
the session unless asked again.

## Non-negotiables

These override everything else in this file.

1. Profile before changing anything. No optimisation without a measurement showing where the time goes.
2. Set a target first: an operation, a percentile, a load level, and a data volume. "Under 300 milliseconds at the 95th percentile for this endpoint at the current peak request rate" ends; "as fast as possible" does not.
3. Measure the same way before and after, on the same data and hardware, and report both.
4. Fix the largest contributor. By Amdahl's law, speeding up a part that takes a fraction p of the time by a factor s gives an overall speedup of 1 / ((1 - p) + p / s). A part that is 3 percent of the time can never give more than about 3 percent.
5. Name the cost of each optimisation in readability, memory, correctness margin, or operational complexity.
6. No claimed improvement without repeated runs. Report the median and a spread (standard deviation or interquartile range), and claim a difference only when confidence intervals do not overlap or a significance test says so.
7. Judge a change against the Step 1 target. Whether a faster mean with a worse tail is a regression depends on the workload: for interactive requests the tail is usually what the target names; for batch throughput the mean or total may be.

## Procedure

### Step 1, define the target

Which operation, measured at which percentile, under what load, on what data volume?

For user-facing latency, target percentiles such as p95 and p99; an average hides the slow requests.
For batch jobs, target total time or throughput.

Decide whether this is a latency problem (one operation takes too long) or a throughput problem (the
system cannot process enough). They have different fixes. A throughput problem needs a load test, method
in `references/measurement.md`.

For web pages, use Core Web Vitals from field data at the 75th percentile. The current "good" thresholds
from [web.dev](https://web.dev/articles/vitals) are LCP at most 2.5 seconds, INP at most 200
milliseconds, and CLS at most 0.1. INP replaced FID as a Core Web Vital in March 2024. Lighthouse is a lab
tool, useful for diagnosis, and its score is not the field measurement.

Get the real data volume. Performance work against a small dataset finds different problems.

### Step 2, measure where the time goes

Use a profiler for the first pass; timing statements confirm a hypothesis, and a profiler generates one.
Sampling profilers have low overhead and suit production; instrumenting profilers count every call and
distort short functions. Read the result as a flame graph. Continuous profiling in production shows the
real workload over time. Profiler choice per runtime is in `references/measurement.md`.

For a web request, split the total into server time, database time, external call time, transfer time,
and client rendering time before looking at any code.

For database work, read the query plan. See `data-layer`.

For client performance, use the browser profiler with network and CPU throttling, and field data for
Web Vitals. See `frontend-build`.

For memory, state which question you are answering. For a leak or OOM, take heap snapshots at two points
under steady load and compare retained sizes. For latency caused by garbage collection pressure, measure
allocation rate and GC pause time, since short-lived allocations retain nothing and still cost pauses.

For a microbenchmark, use a benchmark framework (JMH, pytest-benchmark, Criterion, BenchmarkDotNet) that handles JIT
warmup, dead-code elimination, and repeated sampling, and pin CPU frequency scaling where possible.
Rules in `references/measurement.md`.

Write down the breakdown with numbers.

### Step 3, fix in order of contribution

Remove work that does not need doing: unused fields fetched, data loaded and discarded, work repeated per
item that could be done once, an endpoint called twice by the client.

Fix the N+1 pattern. A query inside a loop scales with data, so it tends to appear after launch.

Index from the query plan.

Batch. One request for a hundred items replaces a hundred round trips.

Move work out of the request path into a background job: mail, file generation, third party calls.

Cache, once the above are done, with an invalidation strategy decided before the cache exists.

Then algorithmic improvement inside the hot path.

### Step 4, verify honestly

Re-measure with the same method, repeated, and compare with the statistics from non-negotiable 6.

Percentiles cannot be averaged across hosts or time windows: the mean of ten hosts' p99 values is not the
fleet p99. Merge histograms (HdrHistogram, or the histogram type in your metrics system) and read the
percentile from the merged result.

For load tests, check the generator for coordinated omission, which hides the tail. Detail in
`references/measurement.md`.

Check correctness. Caching and batching change behaviour. Run the test suite.

Check resource use: memory, connections, CPU headroom.

Check the cold path: cold cache, first request after deploy, empty warm-up state.

### Step 5, report

Give the target, the measured breakdown before, what changed and why that item, the numbers after with
their spread and the comparison method, the cost of the change, and what now dominates.

If production dashboards are needed to track the result, `observability-setup` covers them. Capacity and
instance sizing go to `infra-deploy`. For checking the arithmetic in a performance claim, `numbers-check`.

## Frequent causes by area

Application code: a query in a loop, serialising more data than the caller uses, recomputing per item what
could be computed once, work in a constructor, synchronous work that could overlap, logging in a tight
loop.

Database: no index on a filter or join column, a query returning far more rows than needed, a sort that
could have come from an index, a transaction held open across a network call. Connection pool problems
come in two forms. Exhaustion, where requests queue waiting for a connection, comes from a pool too small
for the concurrency, connections leaked on an error path, or connections held across slow external
calls. An unbounded or oversized pool causes the opposite failure: it lets load through to the database
until the database itself saturates.

Network: many small requests, no compression, no connection reuse, a chain of dependent calls, an
external call with no timeout holding a worker.

Client: too much JavaScript, images larger than displayed, layout shift from unreserved space, long lists
rendered in full, re-rendering caused by a new object identity on every render, long tasks blocking
input (INP).

Memory: an unbounded cache, a listener added without removal, a closure retaining a large structure,
loading a whole file where streaming was possible, high allocation rate in a hot loop.

## Self-audit

- A target with an operation, a percentile, a load level and a data volume was set first.
- A profile exists and the breakdown is in the report.
- The change addressed the largest contributor, with Amdahl's bound considered.
- Before and after measured identically, repeated, with spread and a comparison method stated.
- No percentile was averaged across hosts or windows.
- Load tests were checked for coordinated omission.
- The tail and the mean were judged against the Step 1 target.
- Correctness verified after the change.
- Cold path checked.
- The cost of the optimisation stated, and the new dominant cost named.

## What this cannot do

It cannot measure a system it has no access to. Without a profile, traces, or field data from the user,
it can only propose measurements, and any bottleneck it names is a hypothesis.

It cannot reproduce production load faithfully. A load test models traffic; real traffic mixes, caches,
and noisy neighbours differ, so confirm wins in production metrics after release.

It cannot promise a Lighthouse score or search ranking outcome. Web Vitals thresholds and how search
engines use them change; retrieve the current values from web.dev and the search engine's own
documentation.
