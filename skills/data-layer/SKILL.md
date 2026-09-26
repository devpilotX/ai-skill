---
name: data-layer
description: Design schemas, write migrations and make queries fast without guessing. Use when the user asks to design a database, model data, write a schema or a migration, add an index, fix a slow query, choose between normalised and denormalised design, handle soft deletes, store money, timestamps or IDs, or asks why their database is slow or locked up. Also use before any change to a production table. Reads the query plan before indexing, treats a migration on a large table as a production operation with a lock estimate, enforces invariants in the schema, and refuses to store money in floating point. Triggers on design a database, data model, schema design, write a migration, add an index, slow query, N+1, EXPLAIN, soft delete, foreign key, transaction, isolation level, deadlock, lock timeout, zero downtime migration, backfill, PgBouncer, Postgres, MySQL, SQLite, MongoDB. For moving data from one system to another use migration-plan instead. For latency outside the database use performance-tuning.
license: MIT
metadata:
  version: 1.1.0
  suite: ai-skill
---

# Data layer

The failure this corrects: schema and migration advice written as if every engine were Postgres and every
table had two hundred rows. That advice adds a guessed index, runs an ALTER that queues behind a long
query and takes the site down, or trusts a transaction that MySQL has already committed. The schema
outlives the code that reads it, so these mistakes are the most expensive to reverse.

## When to use and when to stay off

Run when the user is designing tables, writing or reviewing a migration, adding an index, chasing a slow
query, choosing isolation or locking, or about to touch a production table by hand.

Stay off when the question is a syntax lookup with no design consequence, or the database is a throwaway
prototype the user has said will be discarded.

Routing. Moving data or traffic from one system to another, such as Postgres to a managed service or one
schema to a new product, goes to `migration-plan`. Latency that the query plan shows is not in the
database goes to `performance-tuning`. Access control, encryption at rest and credential handling go to
`security-hardening`. API shape, pagination contracts and the service layer above the queries go to
`backend-build`.

The user says "stop", "I've decided", or "just execute": comply at once and stay off for the rest of the
session unless asked again.

## Non-negotiables

These override everything else in this file.

1. Name the engine and its major version before giving any DDL, locking or isolation advice. Behaviour differs between Postgres, MySQL and SQLite, and between versions of each.
2. Constraints live in the schema: not null, unique, foreign keys, check constraints. Application code gets bypassed by scripts and by hand edits.
3. Never store money in a binary floating point type. Use a decimal or an integer count of minor units, with the currency stored alongside.
4. Read the query plan before adding an index, and show it before and after.
5. Every production DDL statement runs with a lock timeout and a retry, and has a lock and duration estimate made against production row counts.
6. Never run a destructive statement without a verified backup. In MySQL, DDL and TRUNCATE commit implicitly, so a transaction there gives no protection.

## Procedure

### Step 1, model from the queries

List the queries the application will run, with expected frequency and the rows they touch. That list
decides the indexes and sometimes the shape.

Normalise first. One fact in one place. Denormalise later against a measured read problem, and write down
what keeps the copies consistent.

Name the invariants, such as an order always has at least one line, or a balance is never negative.
Enforce in the schema every one that the schema can express.

### Step 2, get the primitives right

Text. In Postgres, `text` and `varchar(n)` perform the same, so add a length check only where the domain
has a real bound. In MySQL the choice matters: `TEXT` columns can be stored off page, need a prefix length
to be indexed, and can push sorts and grouping into on-disk temporary tables. Use `VARCHAR(n)` in MySQL
for anything you filter, sort or index.

Identifiers. Default to `bigint` keys. A 32 bit signed integer tops out at 2,147,483,647, and running out
forces the key migration in `references/online-ddl.md` on your largest table. Anything exposed externally
should be opaque. A time ordered random identifier such as UUIDv7
([RFC 9562](https://www.rfc-editor.org/rfc/rfc9562)) or a ULID keeps index locality, which UUIDv4 loses.
Both embed the creation time, so anyone holding the ID learns when the row was created. Where that leaks
something sensitive, use a random ID externally.

Timestamps. Store instants in UTC. Postgres `timestamptz` converts input to UTC and stores no zone, so the
original offset is gone unless you store it. MySQL `TIMESTAMP` ends at 2038-01-19 03:14:07 UTC, so use
`DATETIME` with a UTC convention for dates that may pass it. Future events defined in local time, such as
an appointment at 09:00 in Berlin, store the local date and time plus the IANA zone name
(`Europe/Berlin`). Compute the instant when needed, because zone rules change between booking and the
event.

Enumerations. A lookup table with a foreign key survives change better than a database enum type, which is
awkward to alter, and better than free text, which drifts.

Nulls. Null means unknown. Using it to mean zero, empty or false produces queries that are wrong without
anyone noticing.

JSON columns hold genuinely variable data you do not filter across. Querying inside them at volume later
is the failure.

Shapes such as soft delete, history, multi tenancy, hierarchies and job queues are in
`references/patterns.md`.

### Step 3, index from the plan

`EXPLAIN ANALYZE` executes the statement. For UPDATE, DELETE or INSERT, wrap it so nothing persists, and
think before running an expensive query against production, since the plan costs the same as the query.

```
BEGIN;
EXPLAIN (ANALYZE, BUFFERS) UPDATE ...;   -- Postgres
ROLLBACK;

EXPLAIN ANALYZE SELECT ...;              -- MySQL 8.0.18 and later
EXPLAIN QUERY PLAN SELECT ...;           -- SQLite, does not execute
```

Look for a sequential scan on a large table, a row estimate far from the actual count, a sort that an
index could have supplied, and a nested loop over many rows.

Composite column order: equality columns first, then the sort column, then range columns (ESR). With the
sort column ahead of the range, the index returns rows already in order and a `LIMIT` stops early. The
trade-off is that the range condition is then checked row by row inside the index scan. When the range is
very selective and the result small, equality then range with an explicit sort can be cheaper. Compare
both plans. An index serves queries that use a prefix of its columns, so three single column indexes do
not equal one composite.

A covering index that includes the selected columns avoids reading the table on a hot path.

Every index costs writes and storage. Find unused ones from the engine's index usage statistics and drop
them.

N+1 queries: one query for a list, then one per row. Detect them by counting queries per request in the
slow log, the APM trace, or an ORM tool such as Bullet for Rails or nplusone for Django. Fix with a join,
eager loading (`includes`, `select_related`, `prefetch_related`), or one batched `WHERE id IN (...)` query
per relation. Add a test that asserts the query count for the endpoint so it does not come back.

### Step 4, transactions and concurrency

Keep transactions short. One held open across a call to another service exhausts the connection pool.

Name the isolation default for the engine in use: Postgres is READ COMMITTED, MySQL InnoDB is REPEATABLE
READ, SQLite is SERIALIZABLE. Read then write races are possible at READ COMMITTED, and in InnoDB at
REPEATABLE READ too, because a plain SELECT reads a snapshot. Protect the write with a conditional update,
a version column, or `SELECT ... FOR UPDATE`.

Take locks in a consistent order everywhere. Never wait for a user inside a transaction.

Handle the unique violation instead of checking existence first. In Postgres a unique violation aborts the
whole transaction, so later statements fail too. Use `INSERT ... ON CONFLICT` (Postgres, SQLite 3.24+),
`INSERT ... ON DUPLICATE KEY UPDATE` (MySQL), or a savepoint around the insert.

Behind PgBouncer in transaction mode, session state does not survive between transactions: `SET`, session
advisory locks, `LISTEN`, temporary tables and held cursors. Use `SET LOCAL` and `pg_advisory_xact_lock`.
Prepared statements need PgBouncer 1.21 or later with `max_prepared_statements` set.

### Step 5, migrations as production operations

Separate schema change, data change and code change, and deploy in an order where every intermediate state
works. Old and new code run at once during a deploy.

Rename safely: add the new column, write to both, backfill in batches, move reads, stop writing the old
one, drop it later.

Lock queueing is the outage people do not expect. In Postgres even a fast ALTER takes an ACCESS EXCLUSIVE
lock. If a long query holds a conflicting lock, the ALTER waits, and every query arriving after it queues
behind the ALTER, so the table stops serving. Set `lock_timeout` and `statement_timeout` on the migration
session and retry on timeout. MySQL has the same shape with metadata locks and `lock_wait_timeout`.

Engine specifics, with minimum versions and the pattern for each, are in `references/online-ddl.md`. The
decisions that come up most:

- Adding a column with a default: no rewrite in Postgres 11+ for a non-volatile default, a full rewrite for a volatile one such as `clock_timestamp()`. MySQL 8.0.12+ supports `ALGORITHM=INSTANT` for ADD COLUMN.
- Indexes on large Postgres tables: `CREATE INDEX CONCURRENTLY`. It cannot run inside a transaction, and migration frameworks wrap each migration in one, so disable that (Rails `disable_ddl_transaction!`, Django `atomic = False`). A failed build leaves an INVALID index that must be dropped before retrying.
- MySQL InnoDB online DDL works differently: state `ALGORITHM` and `LOCK` explicitly so the statement fails instead of silently taking a heavier lock.
- Constraints on large Postgres tables: add as `NOT VALID`, then `VALIDATE CONSTRAINT` separately. NOT NULL goes through a validated CHECK first (Postgres 12+). A unique constraint goes through `CREATE UNIQUE INDEX CONCURRENTLY` and then `ADD CONSTRAINT ... USING INDEX`.

Backfill in batches with a pause, resumable from a checkpoint. A single statement touching ten million rows
holds locks and cannot be interrupted safely. The template is in `references/online-ddl.md`.

Estimate before running: row count, table size, expected duration, and what blocks during it.

### Step 6, operational basics

Backups restored at least once. Point in time recovery where the data cannot be reconstructed.

Connection pool sized against the database's real connection limit.

Slow query logging on, with someone reading it.

Retention decided per table, including audit and log tables.

### Document stores

For MongoDB and similar, model from the access pattern even more strictly. Embed data read together and
bounded in size. Reference data that grows without limit, since a document has a hard size cap (16 MB in
MongoDB). Enforce shape with the engine's schema validation (`$jsonSchema` in MongoDB), because nothing
else will. Read plans with `explain("executionStats")`, and the ESR rule applies to compound indexes there
too. Multi-document transactions exist but cost more than single-document writes, so a design that needs
them often is a sign the data is relational. Use majority write concern for data you cannot lose.

## Self-audit

- Engine and major version named before any DDL or isolation advice.
- Constraints in the schema, not only in code.
- Money in decimal or minor units, with currency.
- Instants in UTC; future local events stored with an IANA zone.
- Keys are `bigint` or an opaque ID, and any time ordered ID's creation time leak considered.
- Query plan shown before and after each index, with data-changing statements rolled back.
- Composite index order justified against the plan.
- Isolation default stated for the actual engine.
- Every production DDL has `lock_timeout`, a retry, and a duration estimate from production counts.
- Concurrent index builds run outside the framework transaction, with INVALID index cleanup stated.
- Every intermediate deploy state works with both old and new code.
- Backfills batched, throttled and resumable.
- No reliance on a transaction for DDL or TRUNCATE in MySQL.

## What this cannot do

It cannot see your production row counts, lock contention or query plans unless you run the commands and
share the output, so every duration estimate is conditional on those numbers.

It cannot promise that a migration takes no lock. Version details and workload decide that, so confirm
against the documentation for your exact minor version.

It does not decide how long personal data may be kept or when it must be deleted. Ask a data protection
lawyer: "For table X holding Y about users in jurisdiction Z, what retention period and deletion
obligation applies, and does a soft delete satisfy it?"
