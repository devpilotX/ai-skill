# Stage artefacts

The formats each stage produces, so the next stage can consume them without rework.

## Fact sheet row (stage 2)

One row per fact the design depends on. A fact with no row does not get used in stage 4.

| Claim | Source URL | Retrieved | Grade |
| --- | --- | --- | --- |
| One falsifiable sentence, with the version or tier it applies to | The primary page the claim was read from | ISO date the page was read this session | Independence, currency and primacy, as graded by `deep-research` |

Rules for the columns:

- Claim: specific enough to be wrong. "Free tier allows N requests per minute on plan P" is a claim. "Generous free tier" is not.
- Source URL: the page that states the claim, not a search result or a summary of it. Vendor docs are fine for the vendor's own limits and prices.
- Retrieved: the date it was read in this session. Recalled facts have no retrieved date, so they go in the assumptions list instead.
- Grade: write the three axes out, for example "interested, volatile, primary". A volatile fact older than the session gets rechecked.

Below the table, list what could not be established, each with an `ASSUMPTION:` label, the reasoning,
and what in the design it would change if wrong.

## Options table (stage 3)

| Option | Optimises for | Build cost | Operational hours per month | Makes hard later | Failure mode | New learning needed | Reversibility |
| --- | --- | --- | --- | --- | --- | --- | --- |

One row per option, including do nothing or adopt an existing tool. Costs are either retrieved (cite the
fact sheet row) or labelled `ASSUMPTION:`. Reversibility is one way, two way, or hidden one way, as
classified in `arch-decide`.

Under the table: the recommendation, the strongest case against it, and the condition under which
another option wins.

## Slice card (stage 5)

```
Slice: short name of the demonstrable outcome
Risk retired: the question this slice answers about the design
Acceptance criteria:
  1. a check someone else can run, with the command or the manual step
  2. ...
Depends on: other slices, or none
Size class: small / medium / large (relative, for ordering and splitting only, not a time estimate)
Domain skills: the skills that own this slice
Deferred from this slice: what was left out on purpose
```

Split any slice classed large whose acceptance criteria cannot all be demonstrated together.

## Routing table, stage to skill

| Stage | Skill | When |
| --- | --- | --- |
| 1 think | `reality-check` | Only if the user asks whether the idea is worth building. Otherwise stay off. |
| 2 research | `deep-research` | Every fact that decides the design. |
| 2 research | `ship-audit` | Mapping an existing codebase before proposing changes. |
| 3 discuss | `arch-decide` | Classifying reversibility and costing options. |
| 3 discuss | `reality-check` | Consensus firewall only (phases 1 and 2). |
| 3 discuss | `security-hardening` | Threat model when money or personal data is involved. Required before stage 4. |
| 4 decide | `doc-forge` | Decision record, "Decision record" section of its templates reference. |
| 4 decide | `reality-check` | Ground reality questions only (phase 5). No verdict. |
| 4 decide | `business-model`, `numbers-check` | Running cost and any arithmetic. |
| 6 build | `frontend-build`, `backend-build`, `data-layer`, `mobile-build`, `ml-build`, `infra-deploy` | The slice parts each one owns. |
| 6 build | `test-strategy`, `code-review` | Every slice, before it counts as finished. |
| 6 build | `quant-research`, `portfolio-risk`, `execution-microstructure`, `derivatives-pricing`, `stat-arb`, `trading-systems`, `quant-reasoning` | Quantitative trading or pricing work. |
| 6 build | `migration-plan` | When a slice replaces an existing system or datastore. |
| 7 hand over | `ship-audit` | Readiness against the bar this project needs. |
| 7 hand over | `release-manage`, `observability-setup` | Before handover: rollout, rollback, alerts. |
| 7 hand over | `doc-forge`, `human-prose` | README, runbook, and any prose that ships. |
