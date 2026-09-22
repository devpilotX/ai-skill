---
name: performance-tuning
description: Make software faster by measuring first and changing the thing that dominates. Use when the user says something is slow, asks how to optimise or speed up code, a page, a query or an API, asks about profiling, caching, latency, throughput, memory usage or scaling, or asks why performance degraded. Refuses to optimise without a profile, sets a target before starting so there is a definition of done, fixes the largest contributor rather than the most interesting one, and reports before and after numbers from the same measurement method. Names the cost of every optimisation in complexity, because most of them trade clarity for speed. Triggers on this is slow, optimise this, improve performance, profiling, high latency, slow query, memory usage, throughput, it got slower, speed up my app, reduce load time.
license: MIT
metadata:
  version: 1.0.0
  suite: ai-skill
---

# Performance tuning

Intuition about what is slow is wrong often enough that acting on it wastes most of the effort. Measure,
fix the dominant cost, measure again.

## Non-negotiables

1. Profile before changing anything. No optimisation without a measurement showing where the time goes. This rule exists because guessing produces changes that add complexity and no speed.
2. Set a target first. "As fast as possible" has no completion condition, so it ends in either premature stopping or endless work. "Under 300 milliseconds at the 95th percentile for this endpoint" ends.
3. Measure the same way before and after, on the same data and the same hardware, and report both numbers. A comparison across different conditions is not a result.
4. Fix the largest contributor. A 60 percent improvement on 3 percent of the time is nothing, however satisfying it was to find.
5. Name the cost of each optimisation. Almost all of them trade readability, memory, correctness margin or operational complexity for speed. State the trade so somebody can refuse it.
6. Never report an improvement smaller than the variance between runs. Run it several times and give the spread.
7. Optimise the user's experience of time, not the number that is easiest to measure. A faster average with worse tail latency is usually a regression.

## Procedure

### Step 1, define the target

Which operation, measured at which percentile, under what load, on what data volume?

The percentile matters more than the average. Users experience the slow requests, and an average hides
them. Use the 95th and 99th.

Decide whether this is a latency problem, meaning one operation takes too long, or a throughput problem,
meaning the system cannot process enough. They have different fixes, and confusing them leads to adding
capacity where the fix was an index.

Get the real data volume. Performance work against a small dataset finds different problems from the real
ones.

### Step 2, measure where the time goes

Use a profiler, not timing statements, for a first pass. Timing statements confirm a hypothesis, and a
profiler generates one.

For a web request, split the total into server time, database time, external call time, transfer time and
client rendering time before looking at any code. This single breakdown usually identifies the area, and
it is frequently not where people were looking.

For database work, read the query plan. See `data-layer`.

For client performance, use the browser profiler with network throttling. See `frontend-build`.

For memory, take heap snapshots at two points and compare retained sizes rather than reading allocation
counts.

Write down the breakdown with numbers. This is the document the whole exercise depends on.

### Step 3, fix in order of contribution

The order that finds real wins fastest:

Remove work that does not need doing. The largest wins usually come from not doing something, rather than
doing it faster. Unused fields fetched, data loaded and discarded, work repeated per item that could be
done once, or an endpoint called twice by the client.

Fix the N+1 pattern. A query inside a loop is the single most common serious performance defect in
application code, and it scales with data so it appears after launch.

Index from the query plan.

Batch. One request for a hundred items beats a hundred requests, on both network and database.

Move work out of the request path into a background job, especially mail, file generation and third party
calls.

Cache, once the above are done, with an invalidation strategy decided before the cache exists.

Then algorithmic improvement inside the hot path, which is where people usually start and where the win is
often smallest.

### Step 4, verify honestly

Re-measure with the same method, and report before and after with the spread across runs.

Check the tail, not only the average, since some changes improve the mean and worsen the 99th percentile.

Check correctness. Caching and batching change behaviour, and a fast wrong answer is a defect. Run the
test suite.

Check resource use. A latency win paid for with memory that triggers termination under load is not a win.

Check the cold path: cold cache, first request after deploy, and an empty warm up state.

### Step 5, report

Give the target, the measured breakdown before, what was changed and why that item, the numbers after, the
cost of the change, and what now dominates.

Naming the new dominant cost matters, because it tells the reader whether further work is worthwhile.

## Frequent causes by area

Application code: a query in a loop, serialising more data than the caller uses, recomputing per item what
could be computed once, work in a constructor, synchronous work that could overlap, and logging in a tight
loop.

Database: no index on a filter or join column, a query returning far more rows than needed, a sort that
could have come from an index, a transaction held open across a network call, and connection pool
exhaustion from an unbounded pool.

Network: many small requests, no compression, no connection reuse, a chain of dependent calls, and an
external call with no timeout holding a worker.

Client: too much JavaScript, images larger than displayed, layout shift from unreserved space, long lists
rendered in full, and re-rendering caused by a new object identity on every render.

Memory: an unbounded cache, a listener added without removal, a closure retaining a large structure, and
loading a whole file rather than streaming it.

## Self-audit

- A target with an operation, a percentile and a load level was set first.
- A profile exists and the breakdown is in the report.
- The change addressed the largest contributor.
- Before and after measured identically, with run to run spread.
- Tail latency checked, not only the average.
- Correctness verified after the change.
- Cold path checked.
- The cost of the optimisation stated.
- The new dominant cost named.
