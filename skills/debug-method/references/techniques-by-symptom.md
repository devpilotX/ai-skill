# Techniques by symptom

One playbook per symptom for step 1 of `SKILL.md`. Each gives the tools and the first three experiments.
Run the experiments in order; each one narrows what the next should test. Tool availability differs by
platform and version, so check the current documentation for the runtime in front of you.

## Crash or exception

Tools: the full stack trace with the cause chain, a debugger, core dumps for native processes (enable
with the platform's core size limit and read with gdb or lldb), AddressSanitizer and
UndefinedBehaviorSanitizer for native memory errors, error reporting service events for production.

1. Read the innermost cause and its line. Get the exact input or request that reached that line, from logs or the error event.
2. Replay that input locally under a debugger with a breakpoint on the throwing line, or on the signal for a segfault. Inspect the values that made it fail.
3. Walk back up the stack to the first frame where a value was already wrong. For a native crash with no obvious culprit, rebuild with AddressSanitizer and rerun: it reports the original bad write, not the later crash.

## Hang or deadlock

Tools: thread dumps (jstack for the JVM, py-spy dump for Python, dotnet-stack or dotnet-dump for .NET,
gdb "thread apply all bt" for native, SIGQUIT for Go), strace or dtruss to see which system call is
blocking, database lock views for database-level waits.

1. Take two or three thread dumps a few seconds apart. Threads that stay on the same frame are the stuck ones.
2. For each stuck thread, identify what it waits on: a lock, a socket read, a pool checkout, a database lock, a future. Find who holds it.
3. If two threads each hold what the other wants, it is a deadlock: record the lock order on each path. If a thread waits on I/O with no timeout, reproduce with the remote end stalled (a proxy that accepts and never answers) to confirm.

## Memory leak

Tools: heap snapshots (Chrome DevTools and Node inspector, Eclipse MAT or VisualVM for JVM heap dumps,
tracemalloc or memray for Python, dotnet-gcdump for .NET, Valgrind massif or heaptrack for native),
process RSS over time.

1. Confirm it is a leak. Run steady load and watch memory after garbage collection. A leak grows without bound at a constant request rate; a cache that warms up and then plateaus is not a leak.
2. Take a heap snapshot at two points under the same steady load, well apart in time, and diff them. Look for object types whose retained count or retained size grows between the snapshots.
3. For the growing type, follow the retainer path from the GC roots to the objects. The path names the collection, listener, closure, or cache holding them. Fix the holder, then repeat the two-snapshot diff to confirm growth stops.

## Race condition

Tools: stress loops, ThreadSanitizer for C, C++ and Go (go test -race), rr record and replay on Linux,
deterministic scheduling or interleaving explorers where the runtime has one, database isolation level
settings.

1. Get a rate. Run the suspect operation N times, concurrently, and count failures. This number is the baseline every later experiment is judged against.
2. Run under a race detector where the language has one. A reported data race with two stack traces is often the answer.
3. Force the suspected interleaving: add a barrier, latch, or injected delay at the exact point between the two operations, so the bad order happens every run. If the failure goes to 100 percent, the hypothesis holds; if not, it is ruled out. Do not treat "adding a lock made it stop" as confirmation.

## Works locally, not in production

Tools: a field-by-field environment diff (versions, configuration, feature flags, environment variables,
permissions, limits), production logs and traces, a staging environment with production-like data.

1. Diff the environments: runtime and dependency versions from the lockfile and the image, configuration and flags, and the build artefact itself (is production running the commit you think?).
2. Diff the data: volume, encoding, null rates, and the specific record in the failing request. Replay that record locally.
3. Diff the conditions: concurrency, network latency and timeouts, file system and permissions, time zone and locale, memory and CPU limits. Reproduce the suspect condition locally (limit memory, add latency with a proxy, run concurrent requests).

## Only one browser or device

Tools: the browser's own developer tools, remote debugging for mobile browsers, a cloud device lab or
physical device, the compatibility data on MDN for the API involved.

1. Capture the exact browser or OS version and the console errors from that environment. An unsupported API or syntax is usually visible there.
2. Check the API and CSS features used on that path against the compatibility data for that version.
3. Reproduce in that exact version and bisect the page: disable scripts, extensions and styles by halves until the failing piece remains. Check for differences in date parsing, locale, autoplay and storage policies, and touch versus mouse events.

## Slow regression

Tools: git bisect with a timing script, a profiler, the same benchmark run on both versions.
`performance-tuning` covers measurement rules.

1. Measure the good and bad versions with the same method, repeated enough to separate them from run-to-run noise. If the ranges overlap, there is no confirmed regression yet.
2. Write a script that exits 0 when the timing is inside the good range and 1 when inside the bad range, and 125 when the result is ambiguous. Run git bisect run with it.
3. Profile both versions at the offending commit's boundary and diff the profiles. The frame that grew is where the change made its cost.
