---
name: backend-build
description: Build services and APIs that stay correct under retries, concurrency, duplicate requests and dependency failure. Use when the user asks to build an API, backend, REST, gRPC or GraphQL endpoint, CRUD service, microservice, webhook sender or receiver, background job or queue consumer, asks about OpenAPI, authentication, JWT, authorisation, validation, rate limiting, pagination, idempotency, retries, timeouts, health checks or error formats, or asks why the service duplicates work, loses events or races. Builds object level authorisation, idempotency keys, jittered retries and the transactional outbox into the first version. Triggers on build an API, REST endpoint, gRPC, GraphQL, OpenAPI, CRUD, Express, FastAPI, Django, Spring, Go service, microservice, webhook, outbox, idempotency, retries, race condition, duplicate requests, background job. For a threat model use security-hardening. For API version release policy use release-manage. For load problems use performance-tuning.
license: MIT
metadata:
  version: 1.1.0
  suite: ai-skill
---

# Backend build

A backend that passes every test in development can still charge a card twice when a client retries,
publish an event for a transaction that rolled back, let one user read another's record by changing an
identifier, and restart every instance at once because a shared database was slow. None of that shows
up with one user on a laptop. This skill builds the retry, concurrency, failure and authorisation
behaviour into the first version.

## When to use and when to stay off

Run when the user is building or changing server side code: endpoints, handlers, jobs, consumers,
webhooks, authentication and authorisation checks, error handling, or service to service calls.

Stay off when:

- The question is a framework syntax lookup. Answer it.
- The user wants a threat model or a security review of the whole system. That belongs to `security-hardening`.
- The question is the release and deprecation policy for API versions. That belongs to `release-manage`. Which changes are breaking stays here.
- The service is slow or falling over under load and needs diagnosis. That belongs to `performance-tuning`.
- The question is schema design, migrations or query tuning. That belongs to `data-layer`.
- The question is which architecture or store to choose. That belongs to `arch-decide`.

The user says "stop", "I've decided", or "just execute": comply at once and stay off for the rest of the
session unless asked again.

## Non-negotiables

These override everything else in this file.

1. Authorise on the object, not only on the route. Broken access control is first in the [OWASP Top 10 2021](https://owasp.org/Top10/A01_2021-Broken_Access_Control/). Check ownership on every read and write.
2. Every write path states its concurrency assumption: what happens when it runs twice at once, or twice in sequence because a client retried.
3. Every outbound call has a chosen timeout. Retries use exponential backoff with jitter and a cap, apply only to idempotent operations, and happen at one layer only.
4. Anything retryable is idempotent, with a key bound to a fingerprint of the request.
5. Never make an external call inside a database transaction, and never rely on a commit and a publish both succeeding. Use the transactional outbox.
6. Validate every input at the boundary against a schema. Never trust identifiers, prices or roles because the client sent them.
7. Errors are structured and leak nothing internal. Never log a secret, a token, a card number or a full personal record.

## Procedure

### Step 1, define the contract before the code

Resources, operations, request and response shapes, error codes, and pagination, written as an OpenAPI,
protobuf or GraphQL schema and agreed with the consumers. Naming, status codes, error bodies,
pagination, versioning, idempotency and authentication rules are in `references/api-design.md`.

Error bodies use RFC 9457 Problem Details
([rfc-editor.org](https://www.rfc-editor.org/rfc/rfc9457)) with a stable machine readable code as an
extension member and a correlation identifier.

### Step 2, model the data and the transaction boundaries

Work out which operations must be atomic. That decides the transaction boundaries, and whether a piece
of work can be split across services at all. Enforce uniqueness, foreign keys and invariants in the
database, since application only checks get violated eventually. See `data-layer`.

Keep transactions short and local. An HTTP call, a queue publish, or an email send inside a transaction
holds locks and a pooled connection for the length of a network round trip, and cannot be rolled back if
the transaction then fails. When a commit must also produce a message, write the message to an outbox
table in the same transaction and let a relay publish it. The pattern is in `references/reliability.md`.

Use opaque identifiers on anything exposed externally, since sequential integers are enumerable.

### Step 3, build the request path

Each handler does the same things in the same order: authenticate, authorise on the object, validate
the input, call a service function, map the result to a response.

JWT validation pins the accepted algorithms in the verify call, rejects `alg: none`, and uses a key
whose type matches the algorithm, which blocks algorithm confusion such as an RSA public key accepted as
an HMAC secret. It checks `iss`, `aud`, `exp` and `nbf`, with a small stated clock skew. Keys come from
your own configured JWKS, never from a URL inside the token. See RFC 8725, JSON Web Token Best Current
Practices ([rfc-editor.org](https://www.rfc-editor.org/rfc/rfc8725)).

Keep transport concerns out of business logic, so service functions can be tested and reused. Set a
request identifier at the edge, put it in every log line, and return it in error responses.

Set a CORS policy on browser facing APIs: an explicit allowlist of origins, never the request's Origin
reflected back when credentials are allowed, `Vary: Origin` on responses, and the methods and headers the
API actually uses. CORS limits which browser pages can read responses. It does not authenticate anyone,
and non browser clients ignore it.

### Step 4, handle concurrency and duplicates

Read then write without protection is a lost update. Use a conditional update, a version column, a
unique constraint, or a row lock, chosen deliberately. Prefer the database's own atomic operations.
Take locks in a consistent order. Insert and handle the unique violation instead of checking first and
inserting after, which races.

Idempotency keys are stored with a fingerprint of the request (method, path, caller, body hash). A
repeat with the same key and fingerprint returns the stored outcome. The same key with a different body
is rejected with 422. A repeat that arrives while the first is still running gets 409 and does not start
the work again. Decide and document which outcomes are stored: completed successes and deterministic
client errors are, and a failure that happened before any side effect usually is not, so the retry can
succeed. Details in `references/api-design.md`.

### Step 5, background work, events and webhooks

Anything slow, external or retryable goes to a durable queue, not the request or a timer in the web
process. Every consumer is idempotent, using a processed message store written in the same transaction
as the effect. Every job has a retry limit and a dead letter destination that somebody watches. Jobs are
small or resumable.

Receiving webhooks: verify the signature over the raw request body before parsing, reject timestamps
outside a stated tolerance, return 2xx quickly after persisting the event, process it asynchronously,
and deduplicate on the provider's event identifier.

Sending webhooks to URLs your users supply is a server side request forgery risk. Resolve the hostname,
block private, loopback, link local and cloud metadata ranges on the resolved address, connect to that
address, and do not follow redirects. Recipes for both directions are in `references/reliability.md`.

### Step 6, protect the service

Rate limit per identity and per address on anything that authenticates, sends messages, or costs money.
Bound every input: page, payload, array, string and upload sizes, and query depth for GraphQL.

Size connection pools against the database's connection limit. The sum of pool maximums across every
instance and process at maximum scale, plus workers, cron jobs and migrations, stays below the limit
minus the connections the database reserves. Retrieve the limit from the database itself, for example
`SHOW max_connections` in PostgreSQL. When the sum does not fit, put a pooler such as PgBouncer in
front.

Probes, per the Kubernetes documentation "Configure Liveness, Readiness and Startup Probes"
([kubernetes.io](https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes/)):

- Liveness checks only that the process can serve, with no dependency calls. A liveness check that calls the database restarts every instance when the database is slow, which turns a slowdown into an outage.
- Readiness may check dependencies the instance needs to serve. If every instance checks the same shared dependency, all of them leave the load balancer at once, so prefer degrading or failing fast per request for shared dependencies.
- A startup probe covers slow boots, so the liveness probe does not kill an instance that is still starting.

Shut down gracefully in this order: fail readiness, wait for the load balancer to stop routing, stop
accepting work, finish in flight requests and jobs within a deadline, close consumers and pools, exit.

### Step 7, verify

Run the service, call the endpoints, and paste the real output. Test authorisation on someone else's
object, the same request twice, the same idempotency key with a different body, two concurrent
duplicates, an invalid payload, a dependency timing out, a forged webhook signature, and a webhook URL
pointing at a private address. Check what the logs contain and what they should not contain. Test
strategy beyond these paths belongs to `test-strategy`, and metrics, traces and alerts to
`observability-setup`. Probe and rollout configuration in the deploy belongs to `infra-deploy`.

## Self-audit

- Object level authorisation on every read and write of user owned data.
- Concurrency assumption stated for every write path.
- Every outbound call has a timeout. Retries are jittered, capped, limited to idempotent operations, and done at one layer.
- Idempotency keys bound to a request fingerprint, with in-flight duplicates and key reuse handled.
- No external call inside a database transaction, and every commit that emits a message uses the outbox.
- JWT verification pins algorithms and checks `iss`, `aud`, `exp` and `nbf`.
- Error bodies are Problem Details with a stable code and a correlation identifier, and no internal detail.
- Inbound webhooks verified over the raw body, time bounded, deduplicated and processed asynchronously.
- Outbound webhook delivery blocks private and metadata addresses after DNS resolution and follows no redirects.
- CORS allowlist explicit, and no reflected origin with credentials.
- Pool maximums summed against the retrieved database connection limit.
- Liveness checks the process only, and shutdown follows the order in Step 6.
- Endpoints called, with output shown, and logs checked for secrets and personal data.

## What this cannot do

It cannot observe the service under real traffic, real network partitions, or real provider retries.
The verification in Step 7 exercises the paths but does not prove behaviour at scale.

It does not replace a security review or penetration test of a system that handles money, health data or
credentials. `security-hardening` covers threat modelling, and a qualified tester covers the rest.

Card data brings PCI DSS obligations. Ask a PCI Qualified Security Assessor: "With this data flow, where
card data enters, is stored, and is transmitted, which of our systems are in PCI DSS scope, and which
self assessment questionnaire or assessment level applies to us?"

Retention and logging of personal data is a legal question. Ask a data protection lawyer: "For these
fields in our logs and database, listed with retention periods, what lawful basis and maximum retention
apply in the jurisdictions where our users are?"
