# Online DDL

Schema changes on tables that are serving traffic. Minimum versions below come from the vendor
documentation; confirm against the manual for your exact minor version before running anything, because
point releases have changed which operations are instant.

## What rewrites or locks, per engine

Postgres. Every ALTER TABLE takes a lock, most of them ACCESS EXCLUSIVE, even when no rewrite happens.
The lock is short only if nothing else holds a conflicting lock.

| Operation | Postgres | MySQL 8 InnoDB | SQLite |
|---|---|---|---|
| Add nullable column, no default | Metadata only | INSTANT from 8.0.12 | Fast, metadata only |
| Add column with constant default | No rewrite from 11 | INSTANT from 8.0.12 (last position only before 8.0.29) | Fast, but a NOT NULL column needs a non-null default |
| Add column with volatile default | Full rewrite | Expression defaults: check the manual for the algorithm used | Expression defaults not allowed |
| Drop column | Metadata only, space reclaimed later | INSTANT from 8.0.29, earlier rebuilds in place | From 3.35.0, with restrictions |
| Rename column | Metadata only | INSTANT from 8.0.28 | From 3.25.0 |
| Change column type | Usually a rewrite; widening `varchar(n)` or `varchar` to `text` is not | COPY, blocks writes; widening VARCHAR inside the same length byte range is in place | Rebuild the table |
| Set NOT NULL | Full scan under ACCESS EXCLUSIVE, skipped from 12 if a validated CHECK proves it | In place with rebuild | Rebuild the table |
| Add foreign key | Scan of the table unless `NOT VALID` | In place when `foreign_key_checks` is off, otherwise COPY | Rebuild the table |
| Create index | Blocks writes; use `CONCURRENTLY` | In place, `LOCK=NONE` | Blocks writers for the duration |
| DDL inside a transaction | Transactional, except `CONCURRENTLY` | Implicit commit, no rollback | Transactional |

SQLite has one writer for the whole database file, so any long rebuild blocks all writes. Its manual
describes a twelve step procedure for changes ALTER TABLE cannot express: create the new table, copy,
drop, rename, inside one transaction.

In MySQL, name the algorithm and lock so the server refuses instead of silently falling back:

```
ALTER TABLE orders ADD COLUMN note VARCHAR(200), ALGORITHM=INSTANT;
ALTER TABLE orders ADD INDEX idx_customer (customer_id), ALGORITHM=INPLACE, LOCK=NONE;
```

Every InnoDB online operation still takes a metadata lock at the start and end, and queues behind open
transactions on the table. For changes that need COPY on a large table, use an external tool such as
gh-ost or pt-online-schema-change.

## Lock timeout and retry

A migration that waits for a lock blocks every query behind it. Fail fast and retry instead.

```
SET lock_timeout = '3s';        -- ASSUMPTION: a few seconds is the longest stall most APIs tolerate
SET statement_timeout = '30s';  -- ASSUMPTION: generous for a metadata-only change, tune per statement
ALTER TABLE orders ADD COLUMN note text;
```

```
for attempt in 1 2 3 4 5; do
  psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f migration.sql && exit 0
  sleep $((attempt * 10))
done
exit 1
```

Before retrying, look for the blocker in `pg_stat_activity` (a long transaction or an idle in transaction
session). In MySQL, set `lock_wait_timeout` for the session, since the server default is very long, and
check `performance_schema.metadata_locks`.

## Concurrent index builds in Postgres

```
CREATE INDEX CONCURRENTLY idx_orders_customer ON orders (customer_id);
```

It cannot run inside a transaction block. Migration frameworks open one per migration, so turn it off for
that migration only: Rails `disable_ddl_transaction!`, Django `atomic = False` on the Migration class,
and the equivalent flag in other tools.

If the build fails or is cancelled, it leaves an index marked INVALID that still costs writes. Find and
drop it before retrying:

```
SELECT indexrelid::regclass FROM pg_index WHERE NOT indisvalid;
DROP INDEX CONCURRENTLY idx_orders_customer;
```

## Constraints without long locks in Postgres

Check and foreign key constraints: add without checking existing rows, then validate under a lock that
allows reads and writes.

```
ALTER TABLE orders ADD CONSTRAINT orders_total_positive CHECK (total >= 0) NOT VALID;
ALTER TABLE orders VALIDATE CONSTRAINT orders_total_positive;
```

NOT NULL on Postgres 12 and later:

```
ALTER TABLE orders ADD CONSTRAINT orders_customer_nn CHECK (customer_id IS NOT NULL) NOT VALID;
ALTER TABLE orders VALIDATE CONSTRAINT orders_customer_nn;
ALTER TABLE orders ALTER COLUMN customer_id SET NOT NULL;   -- skips the scan
ALTER TABLE orders DROP CONSTRAINT orders_customer_nn;
```

Unique:

```
CREATE UNIQUE INDEX CONCURRENTLY orders_ref_uniq ON orders (reference);
ALTER TABLE orders ADD CONSTRAINT orders_ref_key UNIQUE USING INDEX orders_ref_uniq;
```

Check for existing duplicates first, or the index build fails and leaves an INVALID index.

## Batched backfill

Idempotent, resumable, throttled. Walk the primary key in ranges, never OFFSET.

```
-- progress table, created once
CREATE TABLE backfill_progress (job text PRIMARY KEY, last_id bigint NOT NULL);

-- one batch; the runner loops until no rows change
UPDATE orders
SET    customer_ref = c.reference
FROM   customers c
WHERE  orders.customer_id = c.id
AND    orders.id >  :last_id
AND    orders.id <= :last_id + :batch_size
AND    orders.customer_ref IS NULL;

UPDATE backfill_progress SET last_id = :last_id + :batch_size WHERE job = 'orders_customer_ref';
```

Runner rules. Commit each batch in its own transaction. Sleep between batches. Stop when the id range
passes `max(id)` captured at the start, then run one final pass for rows inserted meanwhile if the
application is not already writing the new column. Pause when replica lag or p99 latency crosses a
threshold you state in advance. Batch size and sleep are ASSUMPTION values: start small, such as one
thousand rows and a hundred milliseconds, measure one batch, and scale.

## Integer key to bigint in Postgres

`ALTER COLUMN id TYPE bigint` rewrites the table under ACCESS EXCLUSIVE. Instead:

1. Add `id_new bigint` with no default.
2. Add a trigger that copies `id` into `id_new` on insert and update.
3. Backfill `id_new` with the batched template above.
4. `CREATE UNIQUE INDEX CONCURRENTLY` on `id_new`.
5. Repeat steps 1 to 4 for every foreign key column that references `id`.
6. In one short transaction with `lock_timeout` set: drop the old primary key, `ADD CONSTRAINT ... PRIMARY KEY USING INDEX`, swap the column names, move the sequence default to the new column, `ALTER SEQUENCE ... AS bigint`, drop the trigger, and recreate foreign keys as `NOT VALID`.
7. `VALIDATE CONSTRAINT` each foreign key, then drop the old columns later.

Rehearse the whole sequence on a restored copy of production and time each step. In MySQL, the same change
needs COPY, so use gh-ost or pt-online-schema-change.
