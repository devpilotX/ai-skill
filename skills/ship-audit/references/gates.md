# The twelve gates

Each gate lists what to look for and the questions that surface real defects rather than generic
advice. Skip nothing, but record a gate as not applicable when it genuinely is. The specialist skill
named under each gate has the deeper method.

## Gate 1, correctness

Specialist: `code-review`.

Every external call (network, disk, database, subprocess, clock) can fail. Find the ones with no
handling.

Empty catch blocks, and catches that log and continue as though nothing happened.

Errors swallowed into a generic message that loses the cause.

Promise rejections and goroutine or thread panics with no handler at the top level.

Retries with no backoff, no jitter and no cap, which turn a brief outage into a self inflicted denial of
service.

Operations that are not idempotent but get retried anyway. Payment capture and email sending are the
classic pair.

Race conditions on money paths. Look for check then act sequences: read a balance, compare, then write;
check a coupon is unused, then mark it used; check stock, then decrement. Two concurrent requests both
pass the check. The fix is an atomic conditional update (`UPDATE ... SET balance = balance - x WHERE id =
? AND balance >= x` and check the row count), a row lock inside a transaction, a unique constraint, or an
idempotency key stored with a unique index. Test by firing the same request many times in parallel and
checking the ledger.

Partial failure in multi step work. If step three of five fails, what is the state of the first two?

Timezone and locale handling around dates, and any floating point arithmetic on money.

Off by one and boundary handling on pagination, slicing and limits.

Questions that find real bugs: what happens on the second click of the submit button, what happens if
this request arrives twice at the same moment, and what happens if the response is empty rather than
absent.

## Gate 2, tests

Specialist: `test-strategy`.

Coverage percentage says little on its own. Look for whether the tests would catch a regression in the
code that matters.

Does a test exist for each money path, auth path and destructive operation?

Are failure paths tested, or only success paths? Untested error handling is usually broken error
handling.

Is there a concurrency test for each money path from gate 1?

Do tests run in CI on every change? Are they deterministic, with no sleeps, real network calls, real
clocks or shared mutable fixtures?

Is there at least one test that exercises the full path a user takes?

A useful check: pick the most dangerous function in the codebase, then find its test. If there is none,
that is the finding.

## Gate 3, secrets and configuration

Specialist: `security-hardening`.

Scan full history as well as the working tree, because a removed secret is still in the log. Prefer a
dedicated scanner:

```
gitleaks git -v .
trufflehog git file://.
```

Older gitleaks releases use `gitleaks detect --source .`. If neither tool is available, use this
fallback. It is case insensitive, matches quoted JSON and YAML keys as well as bare assignments, skips
`.git` and `node_modules`, and searches every commit on every branch:

```
grep -rInEi --exclude-dir=.git --exclude-dir=node_modules \
  "[\"']?(secret|token|passw(or)?d|api[_-]?key|private[_-]?key)[\"']?[[:space:]]*[:=]" .
grep -rIl --exclude-dir=.git --exclude-dir=node_modules "PRIVATE KEY-----" .
git log -p --all -i -G "(secret|token|passw(or)?d|api[_-]?key|private[_-]?key)[\"']?[[:space:]]*[:=]"
git log -p --all -S "PRIVATE KEY-----"
```

The fallback was tested against a scratch repository containing `const API_KEY = "..."` (deleted in a
later commit), `{"apiKey": "..."}` in JSON, `"password":` and `Secret_Token:` in YAML, and a token under
`node_modules`: the tree grep found the JSON and YAML keys and skipped `node_modules`, and the history
search found the deleted key. It is a pattern match, so it misses secrets under unusual key names and
reports placeholders; a scanner with provider specific rules finds more and verifies some.

Hardcoded credentials, keys and connection strings in source, config, test fixtures or CI files.

Secrets in client side code or anything bundled for the browser, including environment variables inlined
at build time.

`.env` files committed, or absent from `.gitignore`.

Default or example credentials left active.

No separation between development, staging and production configuration.

No secret scan in CI.

No rotation path. If a key leaks today, what is the procedure, and is it written down?

A live secret goes in the first line of the report, because the fix includes rotation and not only
deletion.

## Gate 4, authentication and authorisation

Specialist: `security-hardening`.

Authorisation checked at the boundary but not on the object: a handler confirms someone is logged in,
then loads a record by an identifier from the request without checking ownership.

Fields a client can set but should not (mass assignment), such as role, price, owner or tenant in an
update body.

Roles checked in the client only.

Session handling: expiry, invalidation on logout, on password change and on permission change, and
rotation on privilege change. Cookie flags `HttpOnly`, `Secure`, `SameSite`.

Password storage with Argon2id, scrypt, bcrypt or PBKDF2 at current OWASP parameters, not a general
purpose digest.

Multi factor and account recovery flows, which are a frequent bypass.

Token validation (algorithm pinned, `none` rejected, expiry, issuer and audience checked), scope,
lifetime, and whether refresh tokens can be replayed.

Administrative endpoints reachable from the public internet.

Rate limiting on login, password reset, and anything that sends mail or costs money.

Sequential identifiers are defence in depth. If object level checks exist and pass the test below,
record enumerable identifiers as an observation, not a finding. If the object check is missing, the
finding is the missing check, and enumerable identifiers raise its reachability.

The test: as user A, can I read or change user B's data by changing one value in the request?

## Gate 5, input handling and web security

Specialist: `security-hardening`.

Database access built by string concatenation anywhere, including inside an ORM escape hatch.

Shell invocation built from user input. Deserialisation of untrusted input into objects.

User content rendered into HTML without escaping, and every use of the framework's raw HTML bypass.

File uploads: extension allowlist plus a content check, size limits, generated filenames, storage outside
the web root, and user files served from a separate origin with `Content-Disposition: attachment` and
`X-Content-Type-Options: nosniff`.

Server side request forgery on any feature that fetches a user supplied URL, including DNS rebinding and
redirects.

Redirect targets taken from request parameters.

CSRF protection on state changing requests, and whether the cookie policy supports it.

CORS: an `Access-Control-Allow-Origin` that reflects the request origin while
`Access-Control-Allow-Credentials: true` is set lets any site read authenticated responses. Look for
origin checks by suffix or substring.

Security headers on HTML responses: Content Security Policy, frame-ancestors, HSTS,
`X-Content-Type-Options: nosniff`. Check the live response headers, not only the code, since a proxy or
CDN may add or strip them.

Server side validation for everything validated in the client.

## Gate 6, data, migrations and backups

Specialist: `data-layer`.

Stated recovery objectives. A written RPO (how much data loss is acceptable, which sets backup
frequency) and RTO (how long restoration may take). If neither is written down, that is the finding.

Backups automated, stored outside the primary account or region, and restored at least once. Record the
measured restore time from a real restore drill and compare it with the RTO. An untested backup, or a
restore slower than the RTO, is a finding.

Migration reversibility, and what happens to a migration that fails halfway.

Migrations that lock a large table, measured against production row counts rather than a development
dataset.

Data that cannot be reconstructed if lost, and whether it has stronger protection than the rest.

Personal data inventory: what is collected, where it lives, who can read it, how long it is kept, and
whether deletion deletes.

Encryption at rest for anything sensitive, and in transit everywhere.

Foreign key and uniqueness constraints in the schema, not only in application code.

Soft delete semantics, and whether deleted rows still appear in exports and reports.

## Gate 7, failure and recovery

Specialists: `infra-deploy`, and `release-manage` for rollback.

Single points of failure. What is the one process, host or third party that takes the product down?

Liveness and readiness are separate checks. Liveness answers "is this process stuck" and must not call
dependencies, otherwise a database outage makes the orchestrator restart every healthy instance at once.
Readiness answers "can this instance serve traffic now" and does check the dependencies it needs, so a
failing instance is taken out of rotation instead of restarted. A single endpoint that returns success
unconditionally, or one used for both purposes, is a finding.

Behaviour when a dependency is slow rather than down. Timeouts on every outbound call, with values
chosen rather than defaulted.

Circuit breaking or load shedding under overload, or at least a bounded queue.

Graceful shutdown: in flight requests finished, connections drained, work requeued.

Deploy rollback. Can the previous version be restored in minutes, and has that been done once on
purpose?

Data corruption recovery, which is distinct from outage recovery.

## Gate 8, performance and cost

Specialist: `performance-tuning`.

Any performance number in the report is measured with a named command or labelled as an estimate.

Queries inside loops (N+1).

Missing indexes on columns used in filters, joins and ordering. Read the query plan.

Unbounded queries with no limit, and endpoints that return everything.

Payload sizes, image handling, and whether the client downloads more than it displays.

Caching: what is cached, how it is invalidated, and what happens on a cold cache.

Work done in a request that belongs in a background job, especially sending mail and generating files.

Cost per user or per request at the current price list, retrieved from the vendor, and which line grows
fastest. For anything calling a paid model API, compute cost at the usage of the heaviest users, not the
average.

Anything that scales with total data rather than with the page being viewed.

## Gate 9, observability

Specialist: `observability-setup`.

Can the team tell it is broken before a user tells them? If not, that is the finding, and it usually
outranks the individual defects.

Structured logs with a trace ID that crosses service boundaries.

Errors reaching an aggregator, not only a log file.

Metrics for error rate, latency from histograms, saturation, and the main business event.

Alerts that page a human, with an owner and a runbook, and an external uptime check.

Heartbeats on scheduled jobs.

Logs checked for personal data, tokens and card numbers.

Audit trail for administrative and destructive actions, with actor, target and time.

## Gate 10, accessibility and client quality

Specialist: `frontend-build`. Criteria from [WCAG 2.2](https://www.w3.org/TR/WCAG22/); retrieve the
level the product is legally or contractually required to meet.

Keyboard only operation of every interactive path, including modals and menus.

Focus visible, trapped in dialogs, and restored on close.

Form labels associated with inputs, and errors announced rather than only coloured.

Contrast measured with a tool, not eyeballed: at least 4.5:1 for normal text and 3:1 for large text
([1.4.3 Contrast (Minimum)](https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html)), and 3:1
for user interface components and meaningful graphics (1.4.11 Non-text Contrast).

Reflow: content usable at a width of 320 CSS pixels without two dimensional scrolling
([1.4.10 Reflow](https://www.w3.org/WAI/WCAG22/Understanding/reflow.html)). Text resizable to 200 percent
without loss (1.4.4 Resize Text).

Images with alternative text that carries the same information, and decorative images marked as such.

Content that depends on hover or on colour alone.

Motion honouring a reduced motion preference.

Loading, empty and error states for every view that fetches data.

## Gate 11, dependencies and licences

Specialist: `security-hardening`.

Known advisories in the dependency tree, retrieved from the audit tools and advisory databases, and
separated into runtime and development.

Unmaintained packages, single maintainer packages, and anything pinned to a version with a published
advisory.

Lockfile committed, and builds reproducible.

Supply chain: dependency installation scripts, CI actions and base images pinned by digest, and who can
push to the default branch or publish releases.

Licence compatibility for every dependency against how the product ships. A copyleft dependency inside a
distributed proprietary binary may be a legal problem. Ask a lawyer: "Our product is distributed as
(describe: SaaS, binary, mobile app) and includes these dependencies under these licences (list them);
do any of them impose obligations on our source code or distribution, and what must we do to comply?"

## Gate 12, operations and legal

Specialists: `release-manage` and `infra-deploy`.

A way for users to report problems, and a named owner or on call rota.

A rollback runbook that someone other than the author has followed.

Documentation sufficient for a second person to deploy without asking the author.

TLS certificates renew automatically, the renewal has been observed working, and expiry is monitored
with an alert well before the date. Domain registration is on auto renew with a current payment method,
registrar lock enabled, and expiry monitored. A lapsed domain takes down every service and email address
on it.

Email deliverability for signup, verification and password reset mail: SPF
([RFC 7208](https://www.rfc-editor.org/rfc/rfc7208)), DKIM ([RFC 6376](https://www.rfc-editor.org/rfc/rfc6376))
and DMARC ([RFC 7489](https://www.rfc-editor.org/rfc/rfc7489)) records published and passing for the
sending domain, checked by sending to a real external mailbox and reading the authentication results
header. Large mailbox providers publish sender requirements that change; retrieve the current ones from
Google and Yahoo sender guidelines. A user who cannot receive the reset mail is locked out.

Legal items. Each one ends with the question for a lawyer, because the requirement depends on
jurisdiction and facts this audit cannot judge.

- Terms and privacy notice, if personal data is collected. Ask a lawyer: "We collect these data categories (list them) from users in these countries (list them) for these purposes (list them); what must our privacy notice and terms contain before launch?"
- Cookie and tracking consent. Ask a lawyer: "We set these cookies and run these trackers (list them) for users in these countries; which require prior consent, and does our banner meet that?"
- Accessibility statement or conformance obligations. Ask a lawyer: "Given our sector, customers and countries of sale, are we legally or contractually required to meet a specific WCAG level or publish an accessibility statement?"
- Payments. Ask a PCI Qualified Security Assessor: "Given this payment flow (describe it), which PCI DSS self-assessment questionnaire applies?"
