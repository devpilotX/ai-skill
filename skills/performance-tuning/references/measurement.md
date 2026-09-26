# Measurement

Detail for steps 2 and 4 of `SKILL.md`: which profiler to use, how to run a benchmark, how to compare
two sets of runs, how to load test without hiding the tail, how to handle percentiles, and the Web
Vitals thresholds. Tool names below were current when written; retrieve the current recommended tools
from each runtime's official documentation.

## Profiler choice per runtime

| Runtime | Sampling (low overhead, production-safe) | Other |
| --- | --- | --- |
| JVM | async-profiler, Java Flight Recorder | VisualVM for local inspection |
| Python | py-spy, Scalene | cProfile (deterministic, higher overhead); memray or tracemalloc for memory |
| Node.js | node --cpu-prof, Chrome DevTools via --inspect, 0x | heap snapshots in DevTools |
| Go | pprof (CPU, heap, allocs, block, mutex profiles) | go tool trace for scheduling |
| .NET | dotnet-trace, dotnet-counters | dotnet-gcdump for heap |
| Native (C, C++, Rust) | perf on Linux, Instruments on macOS | Valgrind callgrind (instrumenting, slow); heaptrack for memory |
| Browser | Performance panel in DevTools with CPU and network throttling | Lighthouse for lab diagnosis; field data from the Chrome UX Report or your own RUM |

Sampling profilers take a stack sample at intervals and show where time is spent in proportion.
Instrumenting profilers record every call, which gives exact counts but inflates the cost of small,
frequently called functions. Start with sampling.

Read the output as a flame graph: width is time, and the wide frames near the top of a stack are where
the time goes. Continuous profiling (a sampling profiler running on a fraction of production hosts
all the time) shows the real workload and lets you diff profiles before and after a deploy.

## Benchmark framework rules

Use a benchmark framework: JMH (JVM), pytest-benchmark (Python), Criterion (Rust), BenchmarkDotNet (.NET), the
built-in testing.B in Go. Hand-rolled timing loops fall into the pitfalls below.

JIT warmup. The first iterations run interpreted or at a lower optimisation tier. The framework runs
warmup iterations and discards them.

Dead-code elimination. If the result is never used, the compiler may remove the work. Consume the result
through the framework (a Blackhole in JMH, black_box in Rust and Criterion).

Constant folding. Inputs known at compile time can be precomputed. Feed inputs from state the compiler
cannot see through.

CPU frequency scaling and turbo. Clock speed changes with temperature and load. Pin the governor to a
fixed frequency or disable turbo where you control the machine, and run on an otherwise idle host.

Noise from other processes, garbage collection, and thermal throttling. Repeat, and report the spread.

Benchmark the realistic input size. A benchmark on ten items says little about ten million.

## Statistical comparison

1. Repeat each variant. ASSUMPTION: at least 10 to 30 independent runs per variant, chosen so the spread stabilises; noisy environments need more. Alternate or randomise the order of variants so drift does not favour one.
2. Report the median and a spread: standard deviation for roughly symmetric data, interquartile range for skewed timings. Variance is in squared units and is not comparable to the measurement directly.
3. Compute a 95 percent confidence interval for each variant's median or mean (bootstrap works without distribution assumptions). If the intervals do not overlap, the difference is real at that level. If they overlap, run a significance test, such as Mann-Whitney U for skewed timing data, before claiming anything.
4. State the effect size with the result: "median 41.2 ms to 37.9 ms, 95 percent CI of the difference 2.6 to 4.0 ms, 30 runs each."
5. Treat a result that needs many more runs to become significant as too small to matter unless the target says otherwise.

## Load testing and coordinated omission

Use a load test for throughput problems and for latency that only appears under concurrency.

Method:

1. Model the traffic: request mix, payload sizes, and arrival rate from production logs.
2. Use an open-model generator that sends requests at a fixed arrival rate regardless of responses (for example wrk2, k6 with an arrival-rate executor, Gatling open injection). Real users do not wait for each other.
3. Ramp the rate in steps, holding each step long enough for latency to settle. Record throughput, latency percentiles, error rate, and resource saturation (CPU, memory, connection pools, queue depth) at each step.
4. The capacity is the highest rate at which the target percentile and error rate still hold. Past it, find which resource saturated first; that is the bottleneck to fix.
5. Test with production-like data volume and warm caches, then once cold.

Coordinated omission: a closed-loop generator with a fixed number of workers waits for each response
before sending the next request. When the server stalls, the generator stops sending, so the requests
that would have arrived during the stall are never measured and the tail looks far better than users
experience. Use an open-model generator, or one that corrects for the intended send time, and record
latency from the intended send time.

## Histogram percentiles

Percentiles do not compose. The average of per-host p99 values, or of per-minute p99 values, is not the
p99 of the combined traffic and can be far off in either direction.

Record latency into histograms (HdrHistogram, Prometheus histograms, OpenTelemetry exponential
histograms), merge the histograms across hosts and windows, and compute the percentile from the merged
histogram. The precision is limited by bucket boundaries, so choose buckets around the target value.

## Web Vitals thresholds

From [web.dev, Web Vitals](https://web.dev/articles/vitals), assessed at the 75th percentile of field
page loads, split by mobile and desktop:

| Metric | Good | Measures |
| --- | --- | --- |
| LCP, Largest Contentful Paint | at most 2.5 s | loading |
| INP, Interaction to Next Paint | at most 200 ms | responsiveness; replaced FID in March 2024 |
| CLS, Cumulative Layout Shift | at most 0.1 | visual stability |

These thresholds are revised from time to time. Retrieve the current values from web.dev before quoting
them in a target. Lab tools such as Lighthouse cannot measure INP from real interactions; use field data
from real user monitoring or the Chrome UX Report for the assessment, and lab tools to diagnose.
