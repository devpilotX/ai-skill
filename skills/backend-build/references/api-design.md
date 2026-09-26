# API design

## Resources and methods

Name resources as plural nouns. Put the verb in the method, not the path. `POST /orders` rather than
`/createOrder`.

Nest only to show ownership, and only one level. `/orders/{id}/items` is fine. Three levels deep becomes
unusable, so link by identifier instead.

For operations that genuinely are not resource shaped, such as a state transition, a sub resource is
clearer than an invented verb. `POST /orders/{id}/cancellation` beats `POST /cancelOrder`.

Keep identifiers opaque in anything public. Sequential integers let anyone count your customers and
guess other records.

## Status codes

200 for a successful read or update that returns a body. 201 with a Location header for a creation. 202
when the work was accepted and will finish later. 204 for success with nothing to return.

400 for a malformed request. 401 when authentication is missing or invalid. 403 when the caller is
authenticated but not permitted. 404 when the resource does not exist, or when it exists and the caller
may not know that. 409 for a conflict such as a duplicate or a version mismatch. 422 when the request
parsed but failed domain validation. 429 when rate limited, with a Retry-After header.

5xx codes mean the server side failed, and each one tells the client something different
([RFC 9110, section 15.6](https://www.rfc-editor.org/rfc/rfc9110)):

- 500 for an unexpected fault in your own code.
- 502 when an upstream service your gateway or service called returned an invalid response.
- 503 when you are overloaded, shedding load, or in maintenance, with a Retry-After header saying when to come back.
- 504 when an upstream call timed out.

Never return a 5xx for a client error such as a validation failure. It sends clients into retry loops and
hides real faults in your alerting. The split between 502, 503 and 504 lets clients and on call staff see
whether to retry, back off, or look at a dependency.

Be consistent. Clients build error handling once.

## Error bodies

Use RFC 9457 Problem Details ([rfc-editor.org](https://www.rfc-editor.org/rfc/rfc9457)) with media type
`application/problem+json`. The standard members are `type` (a URI identifying the problem type),
`title`, `status`, `detail` and `instance`. Add extension members for a stable machine readable code, the
failing fields, and a correlation identifier.

```
{
  "type": "https://api.example.com/problems/insufficient-funds",
  "title": "Insufficient funds",
  "status": 422,
  "detail": "The account balance is lower than the requested amount.",
  "instance": "/payments/01HQ8F2K9M3N4P",
  "code": "insufficient_funds",
  "request_id": "01HQ8F2K9M3N4P"
}
```

The `type` URI and the code are the contract, so never change their meaning. The `title` and `detail`
can be reworded freely, which is why clients must not match on them.

For validation failures, return every failing field at once in an extension member such as `errors`,
each entry with a field pointer and a code. Returning them one at a time forces a round trip per
mistake.

Never include a stack trace, a query, an internal hostname, or a database error.

## Pagination

Cursor based pagination for anything that changes while being read, which is most things. Offset
pagination skips and duplicates rows when items are inserted during iteration.

Return the cursor for the next page and a flag for whether more exists. Avoid promising a total count on
a large table, because computing it is expensive and it is usually decoration.

Cap the page size on the server and document the cap. A client will request everything.

Keep the sort deterministic by including a unique tiebreaker, or pagination drifts.

## Filtering and sorting

Allow filtering on a defined set of fields and reject the rest, rather than passing arbitrary input into a
query.

Allow sorting on a defined set of fields, all of which have an index.

Document the default sort, since clients depend on it whether or not it is specified.

## Versioning

Version when you must break something. Adding an optional field is not breaking, so it does not need a
version.

Prefer a version in the path, since it is visible in logs and easy to route. Header versioning is
technically tidier and harder to debug.

Support the previous version for a stated period, and state it in writing. An undocumented deprecation is
an outage scheduled for a random date. The deprecation and release policy itself belongs to
`release-manage`.

Breaking changes include removing or renaming a field, changing a type, making an optional field
required, narrowing an enum a client sends, changing a default, and changing an error code's meaning.

Not breaking: adding an optional field, adding an endpoint, adding an enum value the client only reads,
though clients must handle unknown values for that to hold.

## Idempotency

Accept an idempotency key on any unsafe operation a client might retry, conventionally in an
`Idempotency-Key` header as described in the IETF HTTPAPI working group draft "The Idempotency-Key HTTP
Header Field". Scope keys to the caller, so two clients cannot collide.

Bind the key to a request fingerprint: a hash of the method, path, caller identity and canonicalised
body. Then handle each case explicitly:

- New key. Insert a record with status in progress under a unique constraint on the key, before doing the work. The constraint is what makes concurrent duplicates safe.
- Same key, same fingerprint, completed. Return the stored status code and body without doing the work again.
- Same key, same fingerprint, still in progress. Return 409 with a Retry-After header, or wait briefly for the first request to finish. Never start the work a second time.
- Same key, different fingerprint. Reject with 422 and a problem type saying the key was reused with a different request.

Decide which outcomes are stored, and document it. Store successes and deterministic client errors such
as validation failures, since repeating them gives the same answer. For a server failure, store it if any
side effect may have happened, and delete the in progress record if it provably did not, so the client's
retry can succeed. An in progress record left by a crashed worker needs an expiry, or the key is stuck.

Keep keys for long enough to cover the client's retry window, and document how long.

For webhooks you receive, treat the provider's event identifier as the idempotency key, because providers
redeliver. Verification and processing are in `references/reliability.md`.

## Bulk operations

Decide whether the whole batch is atomic, and say so in the documentation. Partial success with a per
item result is usually more useful than all or nothing.

Return a per item outcome with the item's identifier, so a client can retry only what failed.

Cap the batch size.

For large batches, return 202 with a job identifier and provide a way to check progress.

## Authentication and authorisation

Short lived access tokens with a refresh path. When validating a JWT, pass an explicit allowlist of
algorithms to the library, reject `alg: none`, and bind each key to one algorithm and key type so an
RSA public key can never be accepted as an HMAC secret. Check `iss`, `aud`, `exp` and `nbf`, allowing a
small stated clock skew. Look up keys by `kid` in your own configured key set only, and ignore `jku` and
`x5u` headers in the token. RFC 8725 ([rfc-editor.org](https://www.rfc-editor.org/rfc/rfc8725)) lists
the attacks these checks close.

Scope tokens to what the caller needs. A token that can do everything turns any leak into a total
compromise.

Check permission on the object on every request. If an authorisation decision or a permission set is
cached, it gets both a short TTL and explicit invalidation when a permission changes. The TTL bounds how
long a revoked permission survives if an invalidation event is lost, and the invalidation makes revocation
take effect at once in the normal case. Keep this rule identical to the caching guidance in
`arch-decide`, so the two skills do not disagree.

For service to service calls, use short lived credentials rather than a static shared secret.

Rate limit authentication endpoints separately and more tightly than the rest.

## Webhooks you send

Sign the payload and a timestamp together, and document the verification steps.

Include an event identifier and a timestamp so receivers can deduplicate and reject replays.

Destination URLs supplied by users are a server side request forgery risk. Resolve the hostname, reject
the delivery if any resolved address is private, loopback, link local, or a cloud metadata address, then
connect to the address you checked, and do not follow redirects. The full guard is in
`references/reliability.md`.

Retry with exponential backoff and jitter, and give up after a stated number of attempts. Expose the
failed deliveries so the receiver can see what they missed.

Keep the payload small and let the receiver fetch detail, or the payload becomes a second API you have to
version.

Send from a stable set of addresses and document them, since receivers will want to allow them.

## GraphQL specifics

Limit query depth and complexity, because an unbounded nested query is a denial of service.

Solve the N+1 problem with batching at the data loading layer. It appears immediately and is the default
behaviour of a naive resolver.

Authorise per field where fields have different sensitivity, not only per query.

Disable introspection in production if the schema is not public.

Remember that a single endpoint hides per operation metrics unless operation names are logged.
