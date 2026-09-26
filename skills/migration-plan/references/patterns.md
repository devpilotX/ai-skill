# Migration patterns

Detail for steps 4 to 7 of the skill. Every mechanism here is judged by what happens when one side
fails, because that is where migrations diverge without anyone noticing.

## Keeping two stores in step

| Mechanism | How writes reach the new store | Failure mode | Detection and repair |
| --- | --- | --- | --- |
| Application dual write | The application writes to the old store, then the new one | Second write fails, or the process dies between writes, so the new store silently misses the change. Concurrent writers can apply the two writes in different orders, so the stores disagree on the final value | Record every failed second write durably (a retry table or queue) and replay it idempotently. Run periodic reconciliation over recently changed rows to catch writes lost before they were recorded. Order conflicts need a version column both stores honour |
| Transactional outbox | Business change and an outbox row commit in one transaction on the old store; a relay applies outbox rows to the new store | Relay stops or lags; a row applies twice | Monitor outbox depth and oldest unsent row. Apply idempotently, keyed on the outbox row ID or the source row version |
| Change data capture, log based replication | A connector reads the old store's change log and applies changes to the new store | Connector falls behind or stops; the source retains log until it catches up, which can fill the source's disk; schema changes on the source break the connector | Monitor replication lag and retained log size. Retrieve the connector's and source database's current documentation on retention, restart and schema change handling |
| Primary write plus asynchronous replay | The application writes only to the old store and appends an operation to a durable log; a worker replays the log into the new store | Replay falls behind; an operation fails on the new store because of a behavioural difference | Monitor lag. Failed operations go to a dead letter list that someone resolves one by one, never a log line |

The outbox and change data capture both give at least once delivery from a single atomic write, which
is why they are preferred over application dual write when the old store supports them. Application
dual write is acceptable only with both the durable retry record and reconciliation.

Whatever the mechanism, the new store's apply is idempotent and ordered per key, by source version or
commit position.

## Comparing the two systems

Shadow reads run the same read against both stores, return the old store's result to the caller, and
send both results to a comparator off the request path.

Rules for the comparison:

- Normalise before comparing: field order, whitespace, numeric representation, timestamp precision and timezone. Record each normalisation as an accepted difference, since each one is a behaviour change consumers may notice.
- Compare the whole result, including ordering when the caller depends on it and empty results.
- Sample if the volume demands it, and record the sampling rate, since it bounds what the rate can prove.
- Never let the comparator's failure or latency affect the caller.
- Emit counts per mismatch class as metrics.

Mismatch classes, each of which gets a cause and a decision:

| Class | Typical cause | Decision |
| --- | --- | --- |
| Missing in new | Lost second write, backfill gap, replication lag | Fix the mechanism; repair the rows |
| Missing in old | Write that reached only the new store, or a test write | Find the writer |
| Value differs, new is wrong | Behavioural difference: precision, collation, null handling, defaults | Fix the new path or the transform |
| Value differs, old is wrong | Existing bug surfaced by the comparison | Record it; decide whether the new system reproduces or fixes it (fixing is a redesign, see non-negotiable 6) |
| Ordering differs | Unstable sort, different collation | Add an explicit order, or accept in writing if no caller depends on it |
| Timing | Comparison ran while a write was in flight | Re-compare after a delay; if it resolves, classify as timing, and bound how long it lasts |

Move reads only when no class is unexplained and the residual explained rate is inside the tolerance
written before comparison began.

## Backfill checklist

- Snapshot or cursor chosen so every row is visited once, with progress recorded durably and resumable.
- Batch size and pause set by watching production load, and adjustable without a restart.
- Every write is a conditional upsert guarded by the source row's version or update timestamp, so a backfill copy never overwrites a newer row delivered by the live write path. If the source has no version or timestamp, add one before starting.
- Deletes handled: a row deleted in the source after the snapshot must not reappear. Use tombstones or reconcile deletes after the backfill.
- Counts and checksums compared per batch.
- Failed records listed and resolved, not left in a log.
- Behavioural transforms (types, encodings, timezones) tested on real samples, including the worst ones.

## Authentication migration

Password hashes: find out whether the old system can export hashes, in which algorithm and parameters,
and whether the new system can verify that format. If it can, import the hashes and let the new system
verify them.

Lazy rehash: if the new system should use a different algorithm, verify against the imported hash at
login, then rehash the plaintext the user just typed with the new algorithm and store that. Users who
never log in stay on the old format, so set a date after which remaining old hashes force a reset.
Current algorithm and parameter recommendations are in the
[OWASP Password Storage Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html);
use `security-hardening` for the choice.

If hashes cannot be exported, the options are a login time migration (the new system forwards the
first login to the old one, and on success stores a new hash) while the old system still runs, or a
forced password reset. Plan the reset communication in advance.

Session and token continuity: decide whether existing sessions survive the move. Either the new system
accepts the old tokens (shared signing keys or a validation shim) until they expire, or every user is
logged out at a planned time. Refresh tokens and API keys held by integrations need their own plan,
since they may live for months.

Identifier mapping: user IDs from the old system are stored in other tables and other systems. Keep the
old ID as the primary identifier, or keep a mapping table from old to new and update every foreign
reference. Multi factor enrolments, linked social logins and email verification state migrate with the
account or the user loses them.

## Provider cutover mechanics

DNS: lower the TTL on the records that will change well ahead of the cutover, at least one old TTL
period before, so caches pick up the short value. Retrieve the current TTL first, since the lowering only
takes effect once the old value expires from caches. Raise it again once the cutover is stable.

Endpoint indirection: put a name, load balancer or proxy that you control in front of the service
before the move, so cutover changes one target and rollback changes it back. Clients configured with a
provider specific hostname have to be changed first.

IDs and sequences: auto increment sequences in the new store must start above the highest value in the
old one, with headroom for writes during the transition, or new rows collide. If both stores accept
writes, allocate from disjoint ranges or use IDs that do not depend on a sequence. Provider generated
identifiers (object keys, resource IDs, URLs to stored files) that appear in data need a mapping.

Egress and exit terms: retrieve the current prices and any announced waiver for leaving customers from
the source provider's own documentation, at the measured data size, and confirm any waiver applies to
this account before relying on it.

## Point of no return checklist

Complete every line before the step that cannot be undone (usually stopping writes to the old system,
or deleting it).

- The comparison has run inside tolerance for the agreed period, with no unexplained mismatch class.
- Every dependant from the inventory has been moved and confirmed, including scheduled jobs and reports.
- A restore of the new store has been tested on this data, and its duration recorded.
- A final export or snapshot of the old system is taken and verified readable, and its retention decided.
- Rollback after this point is written down, even if it is only "restore from the final snapshot and replay", with its data loss window stated.
- The owners of the business outcome have agreed to the step, and a responder is available through the watch window.
- The old system's decommission date and the removal of migration scaffolding are scheduled.
