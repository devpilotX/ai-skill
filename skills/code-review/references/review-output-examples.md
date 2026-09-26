# Review output examples

Worked examples of the report format in `SKILL.md`, plus the rules for labelling severity. The code and
file names are invented for illustration.

## Severity labelling rules

BLOCKING: merging causes a defect with a named trigger that reaches users, loses or corrupts data,
opens a security hole, breaks a caller, or fails during a rolling deploy. Also blocking: the change does
something other than its stated intent.

NON-BLOCKING: a real defect with a named trigger whose consequence is limited, rare, easy to reverse, or
already contained elsewhere. It should be fixed, and it can be fixed in this change or the next without
harm in between.

PREFERENCE: no trigger and no consequence, only a different way to write it. Always negotiable.

OBSERVATION: a suspicion you could not confirm. State what would confirm it. Never labelled as a
defect.

Severity follows consequence, never how easy the item was to spot or how confident the wording sounds.
If you cannot name the trigger, the item is an observation, whatever its category.

## A clean review

```
VERDICT: APPROVE
Adds a retry with backoff to the invoice export client; no defects found.

WHAT THIS CHANGE DOES
Wraps the export HTTP call in three retries with exponential backoff on 5xx and timeouts.

CHECKED
pytest tests/export: 14 passed.
mypy src/export: no issues.
Read: src/export/client.py, both callers in src/jobs/nightly.py and src/api/export.py.
Confirmed the export endpoint is idempotent on invoice_id (server docs linked in the PR).

BLOCKING
None.

NON-BLOCKING
None.

PREFERENCES
None.

TESTS
New test covers retry on 503 and give-up after the third failure. Adequate.

NOT REVIEWED
Server-side behaviour of the export endpoint beyond its documented idempotency.
```

Short, because there was nothing to find. Listing what was checked is what makes the approval worth
something.

## A blocking finding

```
VERDICT: REQUEST CHANGES
The new update endpoint lets any authenticated user change another user's role.

WHAT THIS CHANGE DOES
Adds PATCH /users/{id} to let users edit their profile.

CHECKED
npm test: 212 passed.
npm run typecheck: NOT RUN, because the project has no typecheck script and tsc is not configured.
Read: src/routes/users.ts, src/models/user.ts, src/middleware/auth.ts.

BLOCKING
1. src/routes/users.ts:41 - request body spread directly into User.update
   Trigger: an authenticated user sends PATCH /users/<their id> with {"role": "admin"}.
   Consequence: privilege escalation to admin for any account holder.
   Fix: pick an explicit allow list (displayName, avatarUrl, timezone) from the body before updating.

2. src/routes/users.ts:38 - no check that {id} matches the session user
   Trigger: user A sends PATCH /users/<user B's id>.
   Consequence: any user can edit any other user's profile.
   Fix: return 403 unless req.user.id equals the path id or the caller has the admin role.

NON-BLOCKING
None.

TESTS
Needs a test that a non-admin PATCH with a role field leaves role unchanged, and one for cross-user
PATCH returning 403. Neither exists.

NOT REVIEWED
Frontend form changes in web/, which are presentation only.
```

Each blocking item carries a trigger someone can reproduce, a consequence stated in terms of who is
harmed, and a fix small enough to act on.

## Needs more context

```
VERDICT: NEEDS MORE CONTEXT
Whether this migration is safe depends on how many rows orders has in production.

WHAT THIS CHANGE DOES
Adds a NOT NULL column region with a default to orders and backfills it.

CHECKED
Migration runs cleanly against the development database (1,204 rows).
Read: migrations/0042_add_region.sql, src/orders/repository.py.

QUESTION
How many rows does orders hold in production, and which database engine and version runs there?
On some engines and versions, adding a column with a default rewrites the table under a lock; on
others it is a metadata change. The answer decides whether this needs an expand and contract sequence.

NOT REVIEWED
Everything downstream of the migration, pending the answer.
```

Use this verdict only when a named, obtainable fact decides the outcome. It is never a way to avoid
committing to a verdict on code you could have read.
