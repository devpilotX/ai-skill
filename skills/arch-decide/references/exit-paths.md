# Exit paths

A vendor is a one way door when leaving it costs more than the team can pay at the moment it needs to
leave. Check the way out before signing up, while the answer can still change the choice.

Every check below is phrased as something to retrieve. Export features, egress prices and contract
terms change, so read the vendor's current documentation, current price page and the actual agreement,
and record the date read.

## Four checks for any vendor holding data

Export format: is the data exportable in an open or documented format that another system can import,
or only in a proprietary one?

Bulk export: is there a full export of everything, including metadata, history and relationships, that
can run without the vendor's support team, and how long does it take at the current data size?

Egress cost: what does moving the full data set out cost at the current and expected size? Retrieve the
current network egress and any export or API charges from the vendor's price page, and check whether
the vendor publishes a waiver or credit for customers leaving. Compute the figure with `numbers-check`.

Contractual exit terms: notice period, termination fees, minimum commitments, how long data is kept
after termination, and whether the vendor must return or delete it. Read the agreement itself.

## By vendor class

Managed relational database: export is usually a logical dump in the engine's native format. Check
whether the managed service allows replication out to a self-managed instance, since that is what makes
a low downtime exit possible, and whether any proprietary extensions are in use that the target lacks.

Document or key value database as a service: check whether export preserves types (dates, decimals,
binary) and whether the query language or change stream API has any equivalent elsewhere.

Backend as a service (hosted auth plus database plus functions in one product): check each part
separately. The database export may be easy while security rules, triggers and functions have no
portable form and must be rewritten.

Object storage: the format is portable. Egress is the cost to check, retrieved at current size.

Identity and authentication provider: check whether password hashes can be exported, in which algorithm
and parameters, and whether the target can verify that format. If hashes cannot leave, every user
resets their password or logs in once through a migration path. Check how user identifiers map, since
other systems store them.

Payments processor: stored card data sits with the processor. Check whether the processor offers a
card data export to another compliant processor, the process and timeline, and how subscriptions,
customer records and dispute history move.

Email, SMS and notification providers: check export of templates, suppression and unsubscribe lists,
and sender reputation implications of changing sending infrastructure. Losing the suppression list can
break consent obligations.

Search, analytics and event pipelines: check whether raw events can be exported, or only aggregates.
A derived index can be rebuilt from the source of truth; raw history that only the vendor holds cannot.

Observability vendor: check whether instrumentation uses an open standard such as OpenTelemetry or a
vendor agent, since the agent is the part that has to be replaced in every service.

Language model and machine learning APIs: check whether prompts, fine tuned weights, embeddings and
evaluation sets can be exported, and whether embeddings from one provider are usable with another
(generally they are not, so the corpus gets re-embedded).

Content management systems: check export of content with its structure, references, media and revision
history, not only rendered pages.

## Hidden one way doors, with a detection question each

| Door | Detection question |
| --- | --- |
| Message format leaking into consumers | If we change this payload, how many teams must deploy, and do we know who they are? |
| Identifier format reaching other systems | Which systems outside ours store this ID, and would they break if its format or source changed? |
| Vendor specific query language or rules | How many lines of our code or configuration only run on this vendor? |
| Password hashes held by an identity provider | Can we export the hashes, and can our target verify them? |
| Card data held by a payments processor | Is there a documented card data export to another processor, and what does it require from us? |
| Proprietary database extensions | Would our schema and queries run unchanged on the open source engine underneath? |
| Webhooks and callback URLs registered with partners | How many external parties have our URL configured, and can we change it without asking each one? |
| Data only the vendor holds (raw events, history) | If the account closed tomorrow, what data would we no longer have anywhere? |
| Egress that grows with data | What does leaving cost at today's size, and at the size in two years? |
| Contract minimum or auto renewal | What is the earliest date we can leave without a fee, and what notice does that require? |

Any "we don't know" answer is a finding. Record it in the decision record's consequences, and either
resolve it before committing or treat the choice as one way.
