---
name: stat-arb
description: Build and judge statistical arbitrage strategies, pairs, baskets and residual mean reversion, with the discipline that separates a stable spread from a historical coincidence. Use when the user asks about pairs trading, cointegration, mean reversion, a spread or z-score strategy, the Engle-Granger or Johansen test, an Ornstein-Uhlenbeck fit or half-life, a Kalman filter hedge ratio, PCA or factor residual reversion, ETF against constituents, or why a pair stopped working. Selects candidates by economic link before statistics, corrects for the pair search, tests out of sample, derives entry and exit from the fitted dynamics and costs, and plans for structural breaks and crowded unwinds. General signal validation goes to quant-research, sizing to portfolio-risk, costs to execution-microstructure. Triggers on pairs trading, cointegration, mean reversion, spread trading, z-score, half-life, Ornstein-Uhlenbeck, Engle-Granger, Johansen, Kalman filter hedge ratio, statistical arbitrage, stat arb, residual reversion.
license: MIT
metadata:
  version: 1.0.0
  suite: ai-skill
---

# Statistical arbitrage

The failure this corrects is the pair that was cointegrated in the sample it was found in. Test a
thousand pairs at the 5 percent level and about fifty pass by chance; fit the hedge ratio on the same
data and the test looks better still. Then the spread drifts, the z-score keeps widening, and the
strategy doubles down on a relationship that ended. This skill starts from an economic reason for two
prices to move together, corrects for the search, tests on data the selection never saw, and decides in
advance what a broken spread looks like.

## When to use and when to stay off

Run when the user is finding, testing, trading or diagnosing a mean-reverting spread between related
instruments, or a residual from a factor or PCA model.

Stay off, and route instead, when:

- The signal is directional or cross-sectional and not a spread. Use `quant-research`.
- The question is how much capital to give the strategy, or how it combines with others. Use `portfolio-risk`.
- The question is what the round trip costs, or how to leg into a spread. Use `execution-microstructure`.
- The spread involves options or volatility. Use `derivatives-pricing` for the instrument side.

The user says "stop", "I've decided", or "just execute": comply at once and stay off for the rest of
the session unless asked again.

## Non-negotiables

These override everything else in this file.

1. Every candidate has an economic link stated before testing: same business and cost drivers, an ETF and its holdings, a dual listing, a merger with fixed terms, a futures calendar, or a common factor model.
2. The number of candidates tested is recorded and the significance threshold is adjusted for it. Report how many were tested, not only how many passed.
3. Hedge ratios and test statistics for a fitted pair use Engle-Granger or Johansen critical values, not the plain Dickey-Fuller ones.
4. Selection, parameter fitting and evaluation use separate periods. A pair is judged on data after the period used to choose it.
5. Entry, exit and stop rules are fixed before evaluation, derived from the fitted half-life, the spread volatility and the round-trip cost.
6. A break rule exists: the condition under which the relationship is declared broken and the position closed, not averaged into.
7. Compute with `scripts/pairs_lab.py` or other code that was run, and show the output.

## Procedure

### Step 1, choose candidates by mechanism

List candidate pairs or baskets with the reason each should share a stochastic trend. Examples, strongest
first: an ETF against a replicating basket of its holdings; the same company listed in two markets or two
share classes; a cash-and-stock merger with announced terms (a separate risk: deal break); futures
calendar spreads with a carry relation; companies with the same inputs, customers and regulation; residuals
from a sector factor model. "The prices look alike on a chart" is not a mechanism.

Write the population and the search size down. Distance-based and correlation-based screening
(Gatev, Goetzmann and Rouwenhorst, 2006, "Pairs Trading: Performance of a Relative-Value Arbitrage Rule",
Review of Financial Studies) is a legitimate first filter, as long as its candidates count as trials.

### Step 2, test on the formation period

```
python3 scripts/pairs_lab.py prices.csv --y SHELL --x BP --log --lags 1
python3 scripts/pairs_lab.py spread.csv --spread resid --estimated   # a saved regression residual
```

From the repository root the path is `skills/stat-arb/scripts/pairs_lab.py`. It fits the hedge ratio by
OLS, runs the augmented Dickey-Fuller regression on the residual with Engle-Granger critical values,
fits an Ornstein-Uhlenbeck process, and reports the half-life and the current z-score. A ready-made
spread uses plain ADF critical values only when its weights were fixed in advance; pass `--estimated`
for a residual whose weights came from the same data. For baskets of
three or more series, use the Johansen test (Johansen, 1991, Econometrica), which estimates the number of
cointegrating vectors; method notes in `references/pairs-and-baskets.md`.

Adjust for the search: with many candidates, require a stricter threshold (Bonferroni, or control of the
false discovery rate with Benjamini-Hochberg, available in `numbers-check`), and prefer candidates that pass
on several sub-periods.

### Step 3, fit the dynamics that set the rules

From the OU fit: the mean, the speed theta, the half-life ln 2 / theta, and the equilibrium standard
deviation. A half-life longer than the intended holding period means the spread will not revert in time
to be traded; a half-life of a fraction of a bar means the fit is picking up bid-ask bounce.

Decide how the hedge ratio adapts: fixed from the formation period, rolling, or a Kalman filter state
(details in `references/pairs-and-baskets.md`). An adaptive ratio tracks slow changes and also absorbs
the divergence you meant to trade, so it can hide a break.

### Step 4, set entry, exit and stop from the fit and the costs

Entry at a z-score band where expected reversion exceeds the round-trip cost (both legs, spread, impact,
borrow on the short, financing), exit near the mean, and a stop in z-score or in time (for example three
half-lives without reversion). Bertram (2010, "Analytic solutions for optimal statistical arbitrage
trading", Physica A) derives cost-aware optimal bands for an OU process; use it or a simulation of the
fitted OU with costs to choose the band, then fix it.

### Step 5, evaluate out of sample

Run the fixed rules on the trading period that followed formation, with realistic execution: legging
risk, both sides at bid and ask, borrow availability and recalls, dividends and corporate actions on both
legs. Report per pair and pooled: trades, win rate, average holding time against the half-life, P&L net
of costs, and the statistics from `quant-research` (the same deflated Sharpe logic applies, with the pair
search counted as trials).

### Step 6, plan for breaks and crowding

Define the break rule in advance: for example, an ADF statistic on a rolling window above the 10 percent
critical value for a stated time, a z-score beyond the stop, or a fundamental event (merger, index change,
spin-off, regulatory change, guidance cut on one side). On a break, close; do not add.

Stat arb books are prone to joint unwinds when similar funds deleverage; the August 2007 episode is the
standard case (Khandani and Lo, 2007). Stress the book for it with `portfolio-risk`, and cap gross
exposure so that a correlated unwind is survivable.

### Step 7, run it

Monitor per pair: live z-score, live half-life on a rolling window, hedge ratio drift, P&L against the
model's expectation, borrow cost and availability. Retire pairs whose live behaviour departs from the
formation fit by more than the stated tolerance.

## Self-audit

- Each candidate has a stated economic link.
- The number of candidates tested is reported, with an adjusted threshold.
- Fitted pairs were tested with Engle-Granger or Johansen critical values.
- Formation, fitting and evaluation used separate periods.
- Entry, exit and stops were fixed from the half-life, spread volatility and costs before evaluation.
- Out-of-sample results are net of both legs' costs, borrow and financing.
- A break rule is written down and was applied in the evaluation.
- A joint unwind stress was run with `portfolio-risk`.
- Every statistic came from code that was run.

## What this cannot do

It cannot guarantee a relationship persists. Cointegration is a property of a sample, and mechanisms
change with mergers, regulation, technology and ownership.

It cannot see borrow availability or recall risk unless the user supplies prime broker data; the short leg
is often the binding constraint.

It does not give investment advice. For event-driven spreads such as merger arbitrage, or strategies that
trade around corporate announcements, ask a compliance officer: "Does our information barrier and trading
policy permit this strategy in these securities, and what pre-clearance or restricted list checks apply?"
