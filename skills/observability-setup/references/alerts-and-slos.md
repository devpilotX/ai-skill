# Alerts, SLOs and telemetry hygiene

## SLO worked example

Objective: 99.9 percent of HTTP requests to the checkout API succeed (non 5xx, under the stated latency)
over a rolling 30 days.

Error budget as a share: 1 - 0.999 = 0.1 percent of requests.

Error budget as time, for a service that is either up or down: 30 days x 24 hours x 60 minutes = 43,200
minutes, and 0.1 percent of that is 43.2 minutes. Checked with
`python3 -c "print(0.001 * 30 * 24 * 60)"`, which prints 43.2.

For other targets over the same 30 days, from the same formula: 99.5 percent gives 216 minutes, 99.95
percent gives 21.6 minutes, 99.99 percent gives 4.32 minutes. A request based SLO spends budget in
failed requests, so a partial outage spends it more slowly than the minute figure suggests.

Burn rate is how fast budget is spent relative to the rate that would use exactly all of it in the
window. Burn rate 1 spends 100 percent in 30 days. Burn rate 14.4 spends it in 720 / 14.4 = 50 hours.
For a 99.9 percent SLO, a burn rate of 14.4 means an error rate of 14.4 x 0.1 = 1.44 percent.

Budget policy, decided in advance: what happens when the remaining budget reaches zero (for example,
feature releases pause and reliability work takes priority until the budget recovers). Without a policy
the budget is a number on a dashboard.

## Burn rate alert pairs

From the Google SRE workbook, [Alerting on SLOs](https://sre.google/workbook/alerting-on-slos/),
recommended parameters for a 99.9 percent SLO over 30 days. Each alert fires only when the burn rate is
above the threshold over both the long window and the short window. The short window, one twelfth of the
long one, lets the alert reset quickly once the problem stops.

| Severity | Long window | Short window | Burn rate | Budget spent when it fires |
| --- | --- | --- | --- | --- |
| Page | 1 hour | 5 minutes | 14.4 | 2 percent |
| Page | 6 hours | 30 minutes | 6 | 5 percent |
| Ticket | 3 days | 6 hours | 1 | 10 percent |

The budget column follows from burn rate x long window / 30 days: 14.4 x 1 / 720 = 2 percent, 6 x 6 /
720 = 5 percent, 1 x 72 / 720 = 10 percent, checked with python.

Prometheus form for the first pair, with the SLO error ratio 0.001:

```
(
  sum(rate(http_requests_total{job="checkout",code=~"5.."}[1h]))
    / sum(rate(http_requests_total{job="checkout"}[1h])) > (14.4 * 0.001)
)
and
(
  sum(rate(http_requests_total{job="checkout",code=~"5.."}[5m]))
    / sum(rate(http_requests_total{job="checkout"}[5m])) > (14.4 * 0.001)
)
```

The workbook itself warns that services with little traffic produce noisy ratios, because a handful of
failed requests is a large share. For those, add synthetic traffic, combine small services into one SLO,
or alert on absolute failure counts.

## Alert template

Every alert is written in this shape before it is created. A field left empty means the alert is not
ready.

```
name:       CheckoutErrorBudgetFastBurn
condition:  burn rate > 14.4 over 1h and over 5m, SLO 99.9% / 30d
severity:   page
owner:      payments on call rotation
runbook:    link to the runbook page for this alert
action:     check the latest change marker; roll back if a deploy is within the window, otherwise follow the runbook dependency checks
```

The runbook opens with the first three things to check and the command or query for each. An alert whose
action is "investigate" is a ticket.

## Cardinality budget rules

Series for one metric = the product of the distinct values of each label. A histogram multiplies that
again by its bucket count plus two. Estimate before adding a label.

No unbounded labels: user ID, request or trace ID, email, session, raw URL path, full error message, IP
address. Put those in logs and trace attributes, which are built for high cardinality.

Paths use the route template (`/orders/{id}`), never the raw path.

Status codes can be grouped into classes where the exact code is not needed for an alert.

Set a series budget per service with the owner of the metrics backend. ASSUMPTION: the right number
depends on the backend's limits and the vendor's price per series, so retrieve both from the vendor
documentation rather than picking a round number.

Find the worst offenders on Prometheus with the TSDB status page (`/api/v1/status/tsdb`) or:

```
topk(10, count by (__name__) ({__name__=~".+"}))
```

## Head versus tail sampling

Head sampling decides at the root span, in the SDK, usually with a parent based trace ID ratio sampler.
It is cheap, needs no extra infrastructure, and keeps whole traces, but it cannot know whether a trace
will error or be slow, so it keeps errors at the same rate as everything else.

Tail sampling decides in a collector after the trace completes, for example the `tail_sampling`
processor in the OpenTelemetry Collector contrib distribution, with policies such as "keep status error",
"keep latency above the SLO threshold", and "keep a small probabilistic share of the rest". Costs: every
span of a trace has to reach the same collector instance (use a load balancing exporter keyed on trace
ID in front of the sampling tier), the collector buffers each trace for a decision wait period, which
takes memory, and spans arriving after the decision are sampled on their own.

A common combination: light head sampling only if volume forces it, then tail sampling for the errors and
slow traces. Any head sampling reduces the errors the tail sampler can keep, so keep the head rate as
high as cost allows.

## Log audit queries for secrets and personal data

Run these against a recent day of production logs. Each hit is a finding: fix the emitter, then decide
whether the stored logs need purging.

Patterns:

```
JWT or bearer token     eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.
Authorization header    (?i)authorization["']?\s*[:=]\s*["']?(bearer|basic)
AWS access key ID       AKIA[0-9A-Z]{16}
Private key             -----BEGIN [A-Z ]*PRIVATE KEY-----
Password field          (?i)"pass(word)?"\s*:\s*"[^"]+
Email address           [A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}
Card number candidate   \b(?:\d[ -]?){13,19}\b   then confirm with a Luhn check
```

Loki (LogQL, backtick strings avoid double escaping):

```
{app="checkout"} |~ `eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.`
sum by (app) (count_over_time({env="prod"} |~ `(?i)"pass(word)?"\s*:` [24h]))
```

CloudWatch Logs Insights:

```
fields @timestamp, @logStream, @message
| filter @message like /eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\./
| limit 50
```

Files on disk:

```
grep -rEc 'eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.' /var/log/app/
grep -rEo '[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}' /var/log/app/ | sort | uniq -c | sort -rn | head
```

Email hits are expected in some audit logs by design. The question for each hit is whether that field
has a reason to be there and a retention period that matches it.
