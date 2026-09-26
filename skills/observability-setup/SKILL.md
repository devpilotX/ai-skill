---
name: observability-setup
description: Make a system diagnosable before it breaks, with logs, metrics, traces, dashboards and alerts that someone will act on. Use when the user asks about logging, monitoring, metrics, tracing, alerting, dashboards, error tracking, uptime or synthetic checks, cron heartbeats, real user monitoring, crash reporting, SLOs, error budgets or burn rate alerts, or asks why they did not notice an outage, why they get too many alerts, or what they should alert on. Starts from the questions an incident needs answered, puts a trace ID through every log line, ties every alert to a human action, and audits logs for secrets and personal data. For debugging a live incident use debug-method instead. For rolling back a bad release use release-manage. Triggers on set up logging, logs are useless, structured logs, what should I alert on, alert fatigue, pager, on call, error budget, burn rate, SLO, Prometheus, Grafana, Loki, Datadog, CloudWatch, OpenTelemetry, Sentry, tracing, dashboards, why did we not notice.
license: MIT
metadata:
  version: 1.1.0
  suite: ai-skill
---

# Observability

The failure this corrects: a customer reports the outage before the team notices, and when the team
looks, the logs cannot say which request failed, for whom, or what changed. That is the normal state of
a setup built by installing tools and collecting everything. Here the work starts from the questions
someone has to answer at three in the morning on a system they cannot attach a debugger to, and works
back to the instrumentation.

## When to use and when to stay off

Run when the user is adding or fixing logging, metrics, tracing, dashboards, alerting, SLOs, uptime
checks or crash reporting, or asks why an outage went unnoticed or why the pager is noisy.

Stay off, or hand over, when:

- A production incident is happening now and the user needs the cause. Use `debug-method`. Come back afterwards to close the gap that made it hard to diagnose.
- The question is whether to roll back or how to stage a release. Use `release-manage`.
- The request is provisioning the hosts, clusters or managed services the monitoring stack runs on. Use `infra-deploy`.
- The user wants a whole release readiness verdict, where observability is one gate of many. Use `ship-audit`.

Off switch: the user says "stop", "I've decided", or "just execute". Comply at once and stay off for
the rest of the session unless asked again.

## Non-negotiables

These override everything else in this file.

1. One trace ID per request, carried in the W3C `traceparent` header, written on every log line and returned in error responses.
2. Every alert names an owner and an action. No action means no alert.
3. No secrets, tokens, card numbers or full personal records in logs. Audit what is written, do not assume.
4. Latency is reported from histograms at high percentiles. Never average percentiles across hosts.
5. The alerting path, including the watchdog, is tested end to end to a human.
6. Every retention period is a decision with a cost attached.

## Procedure

Each step uses the output of the one before it. The long material (SLO worked example, burn rate
pairs, alert template, cardinality rules, sampling, log audit queries) is in
`references/alerts-and-slos.md`.

### Step 1, write down the questions

Is it broken right now, and for whom? When did it start, and what changed near that time? Is it
everyone, or one customer, region or version? Which dependency is slow? What happened to the specific
request a user is complaining about? Is it getting worse or recovering?

Every later step exists to answer one of these. Instrumentation that answers none of them is cost.

### Step 2, structured logs with a trace ID

Emit JSON, one object per event, with a fixed set of fields: timestamp, level, message, `trace_id`,
`span_id`, and the identifiers relevant to the operation such as tenant or order.

Use the W3C Trace Context `traceparent` header ([W3C Trace Context](https://www.w3.org/TR/trace-context/))
for propagation, and use its trace ID as the correlation ID. Do not invent a second request ID header
that has to be kept in step with it. Generate a new trace at the public edge when there is no trusted
inbound context, propagate it on every outbound call and queue message, and return the trace ID in error
responses so a user report can be matched to the logs. The OpenTelemetry SDKs do this propagation by
default.

Log at boundaries: request received and completed with status and duration, each outbound call with
target, duration and outcome, background job start and finish, and every handled error with its cause.
Do not log inside tight loops or log every trivial success.

Levels mean something. Error means a human should look. Warn is recoverable but notable. Info is the
operational narrative. Debug is off in production.

### Step 3, metrics

Per service: request rate, error rate, latency distribution, and saturation of whatever is scarce, such
as connection pool in use, queue depth or worker occupancy. Add one or two business events that show
the product works, such as orders placed or messages delivered, because those catch failures that leave
the infrastructure looking healthy.

Choose the type by what is measured. Counters for things that accumulate, such as requests and errors.
Histograms for distributions, such as latency and payload size. Gauges for current levels, which is
what most saturation signals are. A gauge is read at scrape time, so a spike that starts and ends
between scrapes is invisible; the loss comes from the scrape interval, not from the type. Where short
spikes matter, also export the maximum over the interval or a histogram of wait time, or scrape more
often.

Percentiles cannot be averaged or summed. The mean of each host's p99 is not the fleet p99. Export
histograms, aggregate the bucket counts across hosts, then compute the percentile from the aggregate.
Client side summaries with precomputed quantiles cannot be aggregated at all.

Keep label cardinality bounded. A label holding a user ID, request ID or raw path multiplies series
until the backend slows down or the bill jumps. Use templated routes. Rules in
`references/alerts-and-slos.md`.

### Step 4, traces

Trace across service boundaries when there is more than one service, or when latency is spread across
external calls. For a single application, logs with durations cover most of it. Use
[OpenTelemetry](https://opentelemetry.io/docs/) so the instrumentation is not tied to one vendor.

Keeping every error and slow trace while sampling the rest needs tail based sampling, done in a
collector after the whole trace has arrived, for example the OpenTelemetry Collector tail sampling
processor. Head based sampling in the SDK decides when the trace starts, before the outcome is known, so
it drops errors at the same rate as successes. Tail sampling needs every span of a trace routed to the
same collector instance and memory to buffer traces while waiting. Trade-offs in
`references/alerts-and-slos.md`.

Span names stay low cardinality. Identifiers go in attributes.

### Step 5, change markers

Record every deploy, configuration change, feature flag change and migration as an event with version,
time and author, and overlay it on dashboards. "What changed near that time" is the question most often
left unanswered, and a marker answers it in one glance.

### Step 6, dashboards

One dashboard per service, laid out to answer the step 1 questions in order: SLO and error rate, traffic,
latency percentiles from histograms, saturation, dependency latency and errors, with change markers on
every time axis. Breakdowns by region, version and tenant come next.

No vanity panels. A panel nobody would act on, such as total signups ever or the CPU of a host that
autoscales, pushes the useful panels off the screen. Remove it.

### Step 7, SLOs and error budget

Pick one or two user facing objectives, such as the share of requests served successfully within a
stated latency over a rolling 30 days. Set the target from what users need and the business accepts,
not from what the system happens to achieve. Compute the error budget in minutes or requests, and use
what remains to decide between shipping and stabilising. Worked example in
`references/alerts-and-slos.md`.

### Step 8, alerts

Alert on symptoms users feel, not causes. Page on SLO burn rate using the multiwindow, multi burn rate
method from the Google SRE workbook ([Alerting on SLOs](https://sre.google/workbook/alerting-on-slos/)).
A fixed error rate threshold either pages on brief blips or misses slow burns. The workbook pairs and
the expressions are in `references/alerts-and-slos.md`.

Every alert follows the template in that file: name, threshold and duration, owner, runbook, action.
Two tiers only: page for action within minutes, ticket for everything else.

Alert on absence as well as excess:

- A watchdog alert that always fires, routed to an external dead man's switch service that pages when the watchdog stops arriving. This is the only thing that tells you the monitoring system itself is down.
- A heartbeat per cron job and scheduled task. The job pings on success, and a missing ping after the expected interval plus a grace period alerts. A job that silently stops running produces no errors.
- A consumer that stops consuming, shown by queue age or depth rising while the processed count is flat.

Run external synthetic checks from outside your own network and cloud provider, over the real user path
including DNS and TLS, from more than one location, alerting only when several locations fail. Internal
health checks cannot see a DNS, certificate or CDN failure.

Review fired alerts monthly. An alert that fired and needed no action gets fixed or deleted.

### Step 9, client side

Server metrics cannot see a JavaScript error, a slow render on a cheap phone, or a crash on launch. For
web, collect real user monitoring (Core Web Vitals and front end errors, with source maps uploaded so
stack traces are readable). For mobile, use crash reporting with symbol files uploaded for every build
(dSYM for iOS, the R8 or ProGuard mapping file for Android) and track crash free sessions per release.
Tag client events with release version so a regression lines up with a change marker.

### Step 10, verify

Trigger a real error and follow it: it reaches the aggregator with the trace ID and enough context to
diagnose without reproducing. Take that trace ID and find every log line and span for the request across
services. Fire a test page and confirm it reaches a human on the right channel, out of hours included.
Stop the watchdog in a test and confirm the dead man's switch pages. Skip a cron heartbeat and confirm it
alerts. Run the log audit queries from `references/alerts-and-slos.md` and fix what they find. Check the
monthly cost of logs, metrics and traces, which grows quietly.

## Self-audit

- The step 1 questions are written down, and each dashboard panel maps to one of them.
- A single trace ID from `traceparent` appears on every log line and in error responses.
- Latency comes from histograms aggregated before the percentile is computed; no averaged percentiles.
- Gauges used for saturation have a stated scrape interval, and spikes are covered where they matter.
- If the design keeps errors and slow traces, tail sampling in a collector is configured, not head sampling.
- Paging alerts use burn rate pairs, and each has an owner, a runbook and an action.
- A watchdog with an external dead man's switch exists and was tested.
- Every cron job has a heartbeat, and external synthetic checks run from outside the provider.
- Deploys and config changes appear as markers on dashboards.
- Client errors, and crashes for mobile, are collected with symbols or source maps.
- Label cardinality is bounded, and the log audit for secrets and personal data was run.
- Retention and cost are decided for each signal.

## What this cannot do

It cannot see production. Every recommendation depends on the traffic, the stack and the vendor the
user describes, and alert thresholds must be set from observed data, which this skill does not have.

It cannot price the setup. Vendor pricing for logs, metrics and traces changes; retrieve the current
price list from the vendor before comparing options.

It cannot decide the SLO target. That is a business decision about what users will tolerate.

Log retention for personal data is a legal question in many jurisdictions. Ask a privacy lawyer: "Our
application logs contain these fields (list them) about users in these jurisdictions (list them); what
is the longest we may retain them, and do they need to be covered by our records of processing and
deletion requests?"
