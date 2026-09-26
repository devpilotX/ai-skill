# Reliability recipes

Each section is a recipe to apply as written, then adapt. Figures that depend on your system, such as
timeout values and breaker thresholds, come from measured latency of the dependency, not from this file.

## Timeouts

Set three separate limits on every outbound call: a connect timeout, a per attempt timeout, and an
overall deadline for the operation including retries. Library defaults are often unbounded or very
long, so set each one explicitly.

Derive the per attempt timeout from the measured latency distribution of the dependency, a little above
its high percentile, and record the percentile used. Label it `ASSUMPTION:` until measured.

Propagate the deadline. A service with 2 seconds left on its caller's deadline must not start a call
with a 5 second timeout. gRPC carries deadlines natively. Over HTTP, pass the remaining budget in a
header and have each hop subtract its own work.

## Retries

Retry only when the operation is idempotent, either by nature (GET, PUT, DELETE on a known resource) or
because it carries an idempotency key. Retry only on errors that can succeed on a second try:
connection failures before the request was sent, 429 and 503 (honour Retry-After), and 502 or 504 for
idempotent calls. Never retry other 4xx responses.

Use capped exponential backoff with full jitter: before attempt n, sleep a random duration between zero
and the smaller of the cap and base times 2 to the power n. Without jitter, every client that failed
together retries together, and the synchronised wave hits the recovering dependency again. The AWS
Architecture Blog post "Exponential Backoff And Jitter"
([aws.amazon.com](https://aws.amazon.com/blogs/architecture/exponential-backoff-and-jitter/)) compares
the variants.

Retry amplification is multiplicative. If three layers each make 3 attempts, the bottom service
receives up to 3 x 3 x 3 = 27 attempts for one user request, at the moment it is least able to serve
them. Retry at one layer only. Lower layers return an error that says "overloaded, do not retry"
instead of retrying themselves.

Add a retry budget. The Google SRE book chapter "Handling Overload"
([sre.google](https://sre.google/sre-book/handling-overload/)) describes a per request limit on attempts
plus a per client budget that stops retrying once retries exceed a set fraction of requests. Choose the
fraction, record it, and alert when the budget is exhausted, because that means the dependency is down.

## Circuit breaking

Keep one breaker per dependency, or per host when a dependency has several. Closed passes calls
through and counts failures and timeouts over a rolling window. When the failure rate crosses a
threshold with enough calls in the window to mean something, the breaker opens and fails fast, returning
a fallback or a 503 with Retry-After without calling the dependency. After a cool down, half open lets a
few trial calls through, closing on success and reopening on failure.

Set the threshold, window and cool down from the dependency's normal error rate, and label them
`ASSUMPTION:` until a real incident has tested them. Export breaker state as a metric, since an open
breaker is an incident signal.

## Transactional outbox

The problem: a service commits a database change and then publishes a message. If the process dies
between the two, the change exists and the message never goes out. Publishing first and committing
second fails the other way. There is no atomic commit across a database and a broker.

The recipe:

1. In the same transaction as the business change, insert a row into an `outbox` table: message identifier, aggregate identifier, message type, payload, created time, published time left empty.
2. A relay process reads unpublished rows in created order, publishes each, and sets the published time. Poll with `SELECT ... FOR UPDATE SKIP LOCKED` so several relays can run, or read the database's change stream with a change data capture tool such as Debezium.
3. Use the aggregate identifier as the partition or ordering key, so messages about one entity stay in order.
4. Delete or archive published rows on a schedule, so the table stays small.

The relay can publish a message and crash before marking it, so delivery is at least once. Consumers
must deduplicate.

## Consumer idempotency store

Keep a `processed_messages` table with a primary key on consumer name plus message identifier. For each
message, in one transaction: insert the key, and if the insert hits the unique constraint, skip the
message. Otherwise apply the effect, commit, then acknowledge the message to the broker. A crash after
commit and before the acknowledgement causes a redelivery, which the stored key absorbs.

When the effect is external, such as sending an email or charging a card, the database transaction
cannot cover it. Pass the message identifier to the provider as its idempotency key, and record the
outcome after the call returns.

## Probes and graceful shutdown

Liveness answers "is this process wedged". It checks the process only, such as whether the event loop
or a worker thread responds, and never calls a database or another service. A liveness probe that
depends on a shared database restarts every instance at once when that database is slow.

Readiness answers "should this instance get traffic now". It can check dependencies this instance alone
needs, such as a warmed cache. For a dependency every instance shares, a failing readiness check removes
all instances from the load balancer together, so it converts a partial degradation into a full outage.
Prefer serving degraded responses or failing those requests fast.

A startup probe holds off liveness checks until a slow boot finishes, such as loading a model or
running a cache warm up.

Shutdown order on SIGTERM:

1. Start failing readiness.
2. Wait for the load balancer or service mesh to stop routing to the instance. In Kubernetes the endpoint removal and the SIGTERM happen concurrently, so a short `preStop` delay covers the gap.
3. Stop accepting new connections and stop pulling new jobs or messages.
4. Finish in flight requests and jobs within a deadline. Requeue or abandon unfinished jobs so another worker picks them up.
5. Flush logs, traces and metrics, close consumers and connection pools.
6. Exit. The platform's grace period, `terminationGracePeriodSeconds` in Kubernetes, must exceed the sum of steps 2 to 5.

## Inbound webhook verification

1. Read the raw request bytes before any JSON parser touches them, because a signature computed over re-serialised JSON will not match. In Express, mount a raw body parser on the webhook route. In FastAPI or Starlette, read `await request.body()`. In Django, use `request.body`.
2. Rebuild the signed string exactly as the provider documents it, often a timestamp joined to the raw body, and compute the HMAC or verify the asymmetric signature with the provider's secret or public key.
3. Compare signatures in constant time, such as `hmac.compare_digest` in Python or `crypto.timingSafeEqual` in Node.
4. Reject the request if the signed timestamp is outside the tolerance the provider documents. This stops replay of a captured request.
5. Accept more than one active secret during rotation.
6. Persist the event with a unique constraint on the provider's event identifier, return 2xx at once, and process it from a queue. Slow handlers cause provider timeouts, which cause redeliveries.
7. On a duplicate event identifier, return 2xx and do nothing.
8. Do not assume events arrive in order. When order matters, fetch the current state of the object from the provider's API instead of trusting the event payload.

The [Standard Webhooks](https://www.standardwebhooks.com/) specification documents one common signing
scheme, and is a reasonable default for webhooks you send.

## SSRF guard for user supplied URLs

Webhook destinations, URL previews, image fetchers and import from URL features all make the server
fetch an address a user chose. Without a guard, a user can point it at internal services or at the cloud
metadata endpoint and read credentials. Follow the
[OWASP SSRF Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Server_Side_Request_Forgery_Prevention_Cheat_Sheet.html).

1. Parse the URL with a standard parser. Allow only `https` (and `http` if you must), and only the ports you intend, usually 443.
2. Resolve the hostname yourself. Reject the request if any resolved address is not globally routable: loopback, private, carrier grade NAT, link local (which includes the 169.254.169.254 metadata address), multicast, reserved, unspecified, IPv6 unique local and link local, and IPv4 mapped IPv6 addresses whose embedded IPv4 address fails the same test. The IANA IPv4 and IPv6 Special-Purpose Address Registries list the ranges. In Python, `ipaddress.ip_address(addr).is_global` is the check.
3. Connect to the address you validated, keeping the original hostname for the Host header and TLS server name. Resolving again at connect time allows DNS rebinding, where the second lookup returns an internal address.
4. Do not follow redirects. If redirects must be supported, validate every hop with steps 1 to 3.
5. Set tight timeouts and a response size cap, and do not return the fetched body or detailed errors to the user.
6. As a second layer, send these requests through an egress proxy or network policy that blocks internal ranges, so a bug in the application check is not the only defence.
