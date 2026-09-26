# Rollout playbook

Templates for the procedure in the skill. Every percentage and wait below is an `ASSUMPTION:` starting
point, chosen so that each stage multiplies exposure by five to ten. Adjust them to the traffic volume
needed for a signal (step 6 of the skill) and to how quickly the failure would show.

## Stage ladder

| Stage | Exposure | Minimum wait | Move on when |
| --- | --- | --- | --- |
| 0 | Internal users or staff accounts | Until the main paths have been used | No abort condition met, and someone exercised the change by hand |
| 1 | 1 percent of traffic or users | Until the canary has enough requests to detect the threshold | Canary against baseline inside threshold |
| 2 | 10 percent | Same, and at least one daily peak for anything load related | Same |
| 3 | 50 percent | Same, and hours for anything touching stored data | Same |
| 4 | 100 percent | Full watch window before the release counts as done | Same, then schedule flag removal |

Cohort choice matters. Hash on a stable user or account ID, so a user does not flip between versions on
each request, and so a failure is reproducible.

## Abort condition template

```
Metric:     what is measured, per version (for example 5xx rate on checkout requests)
Baseline:   the same metric on the old version over the same period
Threshold:  the difference that triggers abort (tie to SLO burn rate where one exists)
Minimum n:  requests the canary needs before the threshold can be judged
Watcher:    named person who checks it, and how they are alerted
Responder:  named person who can act, available for the whole window
Window:     how long the stage is watched
Action:     exactly what abort means here (flip flag X, pause phased release, redeploy build Y)
```

Write it before the rollout. A threshold chosen after seeing the numbers gets chosen to pass.

## Rollback matrix

| Artefact | Rollback path | What blocks it | Prepare before release |
| --- | --- | --- | --- |
| Web service | Redeploy the previous build, or switch traffic back (blue green, canary weight to zero) | A migration the old code cannot run against; state held only in the new version | Previous build retained and deployable; migrations compatible with both versions |
| Published package (npm, PyPI, crates, Maven) | Fix forward: publish a new version, then yank or deprecate the bad one | Registries restrict or forbid unpublishing, and caches and lockfiles already hold the bad version | Retrieve the registry's current unpublish and yank policy; know the deprecate or yank command; have a patch release process ready |
| Mobile store build | Pause the phased release, disable the feature with a server side flag, then ship a fixed build; force upgrade through a minimum supported version gate if needed | Installed builds cannot be pulled back; store review adds delay to the fix | Phased release enabled; flags for new features; a minimum version check the app obeys; retrieve current store review and phased release rules |
| Database schema | Roll back the code only; the schema stays, which is why it must support both versions | A destructive step (drop, rename, type change) shipped with the code | Expand and contract across releases; destructive steps last and separate |
| Runtime config | Revert the value | No history of the previous value | Config in version control or a store with an audit trail |
| Feature flag | Flip it off | The off path was never tested, or the flag interacts with another | Both paths tested; default off equals existing behaviour |

Yanking in PyPI (defined in [PEP 592](https://peps.python.org/pep-0592/)) hides a release from
resolvers that are not pinned to it, while leaving it installable by exact pin. On npm, the deprecate
command attaches a warning to a version at install time. Check the current behaviour in each registry's
documentation before relying on it.

## Deprecation headers

`Deprecation` is defined in [RFC 9745](https://www.rfc-editor.org/rfc/rfc9745). Its value is a
structured field date, written as `@` followed by Unix time in seconds, saying when the resource was or
will be deprecated. `Sunset` is defined in [RFC 8594](https://www.rfc-editor.org/rfc/rfc8594). Its
value is an HTTP date saying when the resource is expected to stop responding. The sunset date should
not be earlier than the deprecation date.

Example response for an endpoint deprecated from 1 January 2026 and removed after 31 December 2026:

```
HTTP/1.1 200 OK
Deprecation: @1767225600
Sunset: Thu, 31 Dec 2026 23:59:59 GMT
Link: <https://example.com/docs/migrate-orders-v2>; rel="deprecation"
Link: <https://example.com/docs/orders-v1-sunset>; rel="sunset"
```

The `deprecation` link relation comes from RFC 9745 and the `sunset` link relation from RFC 8594. The
example.com URLs stand for the API's own migration guide and sunset policy pages.

Log every request that receives these headers, with the caller's identity, so usage can be counted
before removal.

## Incident comms template

First message, sent as soon as impact is confirmed, before the cause is known:

```
Status: investigating
Impact: who is affected and what they cannot do, in their terms
Started: time, with timezone
What we have done: for example, the new release has been switched off
What we do not know yet: cause, full scope
Next update: a specific time, even if there is nothing new
```

Updates repeat the same fields and say what changed. The resolution message adds when impact ended,
whether any data was affected and what users need to do, if anything, and when the written review will
be available.

Send updates at the promised time even when nothing changed. A missed update reads as silence.
