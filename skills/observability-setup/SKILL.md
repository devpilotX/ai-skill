---
name: observability-setup
description: Make a system diagnosable before it breaks, with logs, metrics, traces and alerts that someone will act on. Use when the user asks about logging, monitoring, metrics, tracing, alerting, dashboards, error tracking, uptime checks, service level objectives, or asks how to debug production, why they did not notice an outage, or why they get too many alerts. Starts from the questions that need answering during an incident and works back to the instrumentation, keeps every alert tied to a human action, puts a correlation identifier through every log line, and checks logs for leaked secrets and personal data. Triggers on set up logging, structured logs, monitoring, metrics, Prometheus, Grafana, OpenTelemetry, tracing, alerting, on call, SLO, error tracking, Sentry, dashboards, alert fatigue, why did we not notice.
license: MIT
metadata:
  version: 1.0.0
  suite: ai-skill
---

# Observability

The purpose is answering questions at three in the morning with a system you cannot attach a debugger to.
Start from the questions, not from the tools.

## The questions to design for

Write these down first. The instrumentation follows from them.

Is it broken right now, and for whom?

When did it start, and what changed near that time?

Is it everyone or one customer, one region, one version?

Which dependency is slow?

What happened to this specific request that a user is complaining about?

Is this getting worse or recovering?

An observability setup that cannot answer these has volume without value, which is the normal state of
an unplanned setup.

## Non-negotiables

1. A correlation identifier generated at the edge, attached to every log line, propagated to every downstream call, and returned in error responses. Nothing else gives as much diagnostic value per unit of effort.
2. Every alert names an action. An alert with no action gets muted, and muting one teaches people to mute the next. Alert fatigue is a design failure.
3. Logs carry no secrets, tokens, card numbers or full personal records. Audit what is actually being written rather than assuming.
4. Measure at a high percentile as well as an average. An average hides the slow requests that generate complaints.
5. Errors go to an aggregator with a stack trace and context, not only to a file. An error log nobody opens is not monitoring.
6. Every retention period is a decision with a cost attached, for logs, traces and metrics.
7. Test the alerting path end to end. An alert that fires into a disconnected channel is worse than none, because it creates false confidence.

## Procedure

### Step 1, structured logs

Emit JSON, one object per event, with a consistent set of fields: timestamp, level, message, correlation
identifier, and the identifiers relevant to the operation such as user, tenant, order. Unstructured text
cannot be queried when it matters.

Log at boundaries: request received with method, path and identity; request completed with status and
duration; outbound call with target, duration and outcome; background job start and finish; and every
handled error with its cause.

Do not log inside tight loops, and do not log success for every trivial operation. Volume costs money and
buries signal.

Use levels deliberately. Error means a human should look. Warn means it is recoverable but notable. Info
is the operational narrative. Debug is off in production.

Log the cause when handling an error. An error log without the original failure forces reproduction.

### Step 2, metrics

Four numbers cover most needs, per service: request rate, error rate, duration at the 95th and 99th
percentiles, and saturation of whatever is scarce such as connection pool, queue depth or worker
occupancy.

Add the one or two business events that indicate the product is working, such as orders placed or
messages delivered. These detect failures that leave the infrastructure healthy, which is the most
dangerous category.

Keep label cardinality under control. A label containing a user identifier or a raw path with identifiers
in it will multiply series until the metrics system falls over. Use templated routes.

Counters and histograms over gauges where possible, since a gauge sampled between scrapes loses the
spike.

### Step 3, traces

Trace across service boundaries when there is more than one service, or when latency is distributed
across external calls. For a single application, good logs with durations cover most of it.

Use [OpenTelemetry](https://opentelemetry.io/docs/) so the instrumentation is not tied to one vendor.

Sample intelligently: keep every error and slow request, sample the rest. Tracing everything at volume
costs a lot and adds little.

Span names should be low cardinality, with identifiers as attributes rather than in the name.

### Step 4, alerts

Alert on symptoms users feel, not on causes. High error rate and high latency are symptoms. High CPU is a
cause that may be harmless.

Every alert gets a name, a threshold with a duration, an owner, a link to the runbook, and the action to
take. No action means no alert.

Two tiers only. Page a human for something requiring action within minutes. Ticket everything else. A
third tier becomes noise.

Set thresholds from observed behaviour, not from a round number. Look at a week of data first.

Alert on absence as well as excess. A queue consumer that stops consuming often produces no errors at
all, and silence is the signal.

Include a rate of change alert for anything that should be stable, since a slow leak never crosses a
static threshold until it is too late.

Review fired alerts monthly. Any alert that fired and needed no action gets fixed or deleted.

### Step 5, service level objectives

Pick one or two user facing objectives, such as the share of requests served successfully within a stated
time over a rolling month.

Set the target from what users need and the business accepts, not from what is currently achieved.

Use the remaining error budget to decide whether to ship or to stabilise. That is the practical value of
an objective, and without that link it is a dashboard nobody reads.

### Step 6, verify

Trigger a real error and follow it through: does it appear in the aggregator with the correlation
identifier and enough context to diagnose without reproducing?

Take a real correlation identifier and find every log line for that request across services.

Fire a test alert and confirm it reaches a human on the correct channel, including out of hours.

Query the logs for patterns that look like tokens, card numbers, email addresses and passwords, and fix
what you find.

Check the monthly cost of logs, metrics and traces, since this grows quietly and is often the largest
observability surprise.

## Self-audit

- Correlation identifier through every log line and propagated downstream.
- Logs structured and queryable, with levels used deliberately.
- Request rate, error rate, high percentile latency and saturation in place.
- At least one business event monitored.
- Label cardinality bounded.
- Every alert has an owner, a runbook and an action.
- Absence alerts exist for consumers and scheduled work.
- An error was traced end to end as a test.
- Alert delivery verified to a human.
- Logs audited for secrets and personal data.
- Retention and cost decided.
