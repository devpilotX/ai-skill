# Recurring tradeoffs

Analyses for recurring decisions. Each ends with the threshold that changes the answer, stated as
something to measure or labelled `ASSUMPTION:`, never as a remembered figure.

## Deployment shape

A single deployable application with one database is the correct default, and remains correct much
longer than most teams believe. One repository, one deploy, one place to look when it breaks, real
transactions, and a call stack you can read.

Separate deployable services buy independent deployment, independent scaling, and a hard boundary that
survives staff turnover. They cost distributed tracing, network failure handling, eventual consistency,
schema coordination, and a platform to run them on. The cost is mostly operational and it is continuous.

Modules inside one deployable is the underused middle. Enforce boundaries in the code, keep one deploy,
and split later along seams that already exist. This keeps the option open cheaply.

What actually forces a split: a component with genuinely different scaling behaviour such as video
transcoding, a compliance boundary requiring separation, a team large enough that deploy contention is
measurable, or a part needing a different runtime.

Threshold: measure deploy contention before splitting. Count how often a deploy waits on or gets
reverted because of another team's change, and how long the wait is, over a few weeks.
`ASSUMPTION:` on a small team that shares one on call rota, that count is usually near zero, so a split
buys little. The measurement decides it, not the headcount.

## Service communication

Synchronous request and response is easy to reason about, easy to debug, and couples availability. If A
calls B and B is down, A is down, unless A handles it, which it usually does not.

Asynchronous messaging decouples availability and absorbs load spikes. It costs ordering questions,
duplicate delivery, a dead letter path somebody has to watch, and debugging across logs rather than in
one stack trace.

Choose synchronous when the caller needs the answer to continue, and asynchronous when the work can
finish later. That is the whole rule. Adopting messaging for work the user is waiting on adds latency and
complexity without decoupling anything the user experiences.

Every asynchronous consumer must be idempotent, because delivery will repeat. Design the idempotency key
before writing the consumer.

## Writing and publishing together: outbox and change data capture

A service that commits to its database and then publishes a message has two writes that are not atomic.
If the process dies between them, the event is lost. If it publishes first and the commit fails, the
event describes something that never happened. Retrying does not fix either case.

Transactional outbox: write the event into an outbox table in the same transaction as the business
change. A separate relay reads the outbox, publishes each row, and then marks it sent. Delivery becomes at least
once, so consumers stay idempotent. Costs: a relay process to run and watch, and outbox cleanup.

Change data capture: read the database's own change log (for example the PostgreSQL write ahead log
through logical decoding, or the MySQL binlog) and publish from it. No application change, and every
committed change is seen. Costs: a connector to operate, coupling consumers to table shape unless the
connector publishes from an outbox table, and replication slot or log retention management on the
database. Retrieve the current documentation of the chosen connector and database for retention and
failure behaviour.

Threshold: any design where a message must reflect a committed database change uses one of the two.
Choose the outbox when the team owns the service code and wants explicit event shapes. Choose change
data capture when the source cannot be changed, or when many tables need streaming.

## Datastore selection

A relational database is the default and covers a wide range of workloads further than people assume.
Engine choice and schema detail belong to `data-layer`. It
gives constraints, transactions, joins, and a query planner that has had decades of work. Modern ones
handle JSON documents, full text search, queueing and geospatial data adequately, which removes several
reasons teams historically added a second store.

A document store suits genuinely schema-variable data where you never need to query across documents.
The usual failure is discovering later that you do.

A key value store suits caching, sessions, rate limiting, and ephemeral state.

A search index suits real text search with ranking. Treat it as a derived store that can be rebuilt, and
never as the source of truth.

A time series store suits metrics and telemetry at volume, where writes dominate and old data ages out.

A graph store suits traversals several hops deep as the primary access pattern, which is a narrower case
than it appears. Two hops in SQL is a join.

Every additional store adds a consistency problem, a backup requirement, an upgrade path, and an
operational burden. The bar for the second store is high.

Threshold: add a specialised store when a specific query pattern is measurably too slow in the primary
store after indexing has been done properly, not before.

## Caching

Order of attempts: fix the query and add the index first, then cache.

Cache invalidation is the hard part and it needs deciding before the cache is added. Time based expiry is
simple and serves stale data for a known window. Event based invalidation is fresher and easy to get
wrong.

With cache-aside, the writer commits to the database and then deletes the cache key. It does not write
the new value into the cache. Setting the value on write races with a reader that missed the cache,
read the old row, and then fills the cache with that stale value after the writer's set, leaving stale
data that stays until expiry. Deleting after commit narrows that race without closing it, so still put
a TTL on every entry as the bound on how long a lost race can last. Where staleness is unacceptable,
use versioned keys or read from the database.

Cache the expensive and stable. Do not cache values whose staleness a user sees in a way that matters,
such as a balance, unless the read path tolerates it by design.

Permissions and roles may be cached only with a short TTL and explicit invalidation when a permission
changes (role removed, user suspended, membership revoked). An authorisation decision is never cached
without both. The TTL bounds how long a revoked permission survives if an invalidation event is lost,
and the invalidation makes revocation take effect at once in the normal case. The API design reference
in `backend-build` states the same rule.

Ask what happens on a cold cache. If the system cannot survive one, the cache is load bearing
infrastructure and needs the same care as the database.

## Tenancy

Shared schema with a tenant column is simplest and scales to many tenants. The risk is a missing filter
in one query leaking data across tenants, so enforce it at a layer that cannot be forgotten rather than
in each query.

Schema per tenant eases per tenant restore and export. Every migration runs once per schema, so
migration time grows with tenant count. Measure one schema's migration time on production sized data
and multiply by the expected tenant count before choosing it.

Database per tenant gives the strongest isolation and the highest operational cost, and is usually driven
by a contract rather than by engineering.

Threshold: start shared unless a regulatory requirement or a signed contract says otherwise, and design
the tenant filter so that omitting it fails rather than returns everything.

## Where state lives

Stateless application processes are worth the discipline, because they make scaling, restarting and
deploying straightforward.

Session state belongs in a shared store or a signed token, never in process memory, or the second
instance breaks logins in a way that is hard to reproduce.

Background jobs belong in a durable queue, not in a timer inside a web process, or the work disappears on
deploy.

Uploaded files belong in object storage, not the local disk, unless there is exactly one machine forever.

Scheduled work needs a lock, or it runs once per instance.

## Serverless against long running processes

Serverless suits spiky, short, stateless work and shifts operational burden to the provider. It costs
cold starts, execution time limits, a harder local development story, connection pool pressure on the
database, and pricing that becomes unfavourable under steady high load.

Long running processes suit steady load, long connections, websockets, and anything needing a warm cache.

Threshold: at steady high utilisation, reserved capacity can be cheaper than per invocation pricing.
Retrieve both current price pages, model the cost at expected load with `business-model`, and check the
arithmetic with `numbers-check` before assuming either direction.

## Build against buy, managed against self-hosted

Buying or using a managed service moves operational hours to a vendor and adds a bill, a dependency and
an exit problem. Building or self-hosting keeps control and adds hours that never stop.

Cost both sides in ongoing hours per month, not only in the invoice. Self-hosting a database means
patching, upgrades, backups, restore tests, failover, monitoring and being paged. Price those hours at
the team's loaded cost, labelled `ASSUMPTION:` if no figure is given, and compare them with the vendor's
current retrieved price at expected load.

Buy what is not the product and is well served by the market: auth, email delivery, payments, error
tracking. Build what is the product, or where no vendor meets a hard requirement.

Before buying anything that holds data, run the exit checks in `references/exit-paths.md`.

Threshold: self-host when the measured or estimated hours cost less than the managed price and the team
has someone who can own the pager for it. Otherwise buy, and record the exit path. Hosting mechanics
belong to `infra-deploy`.
