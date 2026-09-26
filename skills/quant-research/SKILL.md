---
name: quant-research
description: Research systematic trading signals to the standard of a professional quant desk, where most backtests are false discoveries. Use when the user asks to find alpha, build or backtest a trading strategy or factor, evaluate a signal, compute a Sharpe ratio or information coefficient, check a backtest for overfitting, look-ahead or survivorship bias, apply machine learning to returns, or asks whether a result is real. Starts from a falsifiable hypothesis with a mechanism, builds point-in-time data, counts every trial, deflates the Sharpe ratio for the search, validates with purged splits, nets out costs and capacity, and ends with kill criteria. Sizing goes to portfolio-risk, execution cost to execution-microstructure, pairs to stat-arb, options to derivatives-pricing. Triggers on backtest, alpha, factor, signal, Sharpe ratio, information coefficient, overfitting, look-ahead bias, survivorship bias, walk-forward, deflated Sharpe, systematic trading, machine learning for trading.
license: MIT
metadata:
  version: 1.0.0
  suite: ai-skill
---

# Quant research

The failure this corrects is the backtest that is a record of the search rather than evidence of an
edge. Try enough variants on the same history and one of them will show a high Sharpe ratio by chance,
and a model asked for a strategy will usually hand over the most published anomaly with a look-ahead
bug in the data join. Harvey, Liu and Zhu (2016, "... and the Cross-Section of Expected Returns",
Review of Financial Studies) argue that after hundreds of published factors a new one needs a t
statistic above about 3.0 rather than 2.0. This skill treats every result as a false discovery until
the data, the trial count, the validation design and the costs say otherwise.

## When to use and when to stay off

Run when the user is proposing, building, testing or judging a systematic signal or strategy, or wants
to know whether a performance record is evidence of skill.

Stay off, and route instead, when:

- The question is how large to make positions or how to combine strategies under a risk budget. Use `portfolio-risk`.
- The question is what it costs to trade the signal, or how to work an order. Use `execution-microstructure`.
- The idea is a pair or basket spread that should mean revert. Use `stat-arb`, which applies the same validation rules.
- The instrument is an option or other derivative and the question is its value or hedge. Use `derivatives-pricing`.
- The work is the production trading platform. Use `trading-systems`.
- The user wants a probability or sizing puzzle worked, with no data. Use `quant-reasoning`.
- The request is for a stock tip or a personal investment recommendation. Decline that part: this skill evaluates research, it does not advise anyone what to buy.

The user says "stop", "I've decided", or "just execute": comply at once and stay off for the rest of
the session unless asked again.

## Non-negotiables

These override everything else in this file.

1. Every hypothesis states the economic mechanism (risk premium, behavioural bias, structural flow, or information advantage) and who is on the other side of the trade, before any data is touched.
2. Every trial is logged. The deflated Sharpe ratio is computed with the full trial count, including variants abandoned along the way. An uncounted trial makes every statistic optimistic.
3. Data is point in time. No value enters a signal before the moment it was knowable, including restatements, index membership, corporate actions and vendor revisions.
4. The final holdout is touched once. A holdout used to choose between variants is a training set.
5. Performance is reported net of transaction costs, borrow, financing and fees, at a capacity stated in currency.
6. Numbers come from running code, with `scripts/strategy_stats.py` for the statistics. No Sharpe ratio, t statistic or drawdown is estimated in prose.
7. Never present a backtest as a forecast of future returns, and never give a personal investment recommendation.

## Procedure

### Step 1, write the hypothesis and its falsifier

One paragraph: the mechanism, the population it applies to, the horizon, the expected sign, and why the
effect has not been arbitraged away (capacity limits, risk, constraints on the other side, or cost).
Then the result that would kill it: "If the rank IC over the holdout is below 0.01 with a Newey-West t
below 2, the hypothesis is rejected."

Name the consensus version of the idea, the one a textbook or a thousand blog posts describe, and say
what this version adds. A crowded signal has lower expected return and a worse unwind.

### Step 2, build the data as it was known

Follow `references/data-integrity.md`. The usual defects, in the order they tend to appear:

- Survivorship: a universe of today's constituents or today's listed stocks. Use membership as of each date and include delisted securities with their delisting returns.
- Look-ahead: fundamentals stamped with the period end instead of the filing or release time, closing prices used to trade at the same close, index changes applied from the announcement you could not have seen.
- Timestamps: time zones, exchange calendars, asynchronous closes across markets, and daylight saving shifts.
- Corporate actions: splits, dividends, spin-offs, symbol and identifier changes. Map on a permanent identifier, never a ticker.
- Vendor revisions: backfilled history that did not exist at the time.

Record the data version and a hash of every input file, so the result can be reproduced.

### Step 3, define the trial budget before searching

Write down the parameter grid, the universe variants and the model families to try, and how many trials
that makes. Log every run in a trial registry with its configuration and result. The count and the
spread of the trial Sharpe ratios feed the deflated Sharpe ratio in step 6. If the search expands, the
count expands with it.

### Step 4, evaluate the signal before the strategy

Measure the raw signal first, per `references/signal-evaluation.md`: rank information coefficient by
date with its Newey-West t statistic, IC decay across horizons, quantile spread returns, turnover and
autocorrelation of the signal, and exposure to known factors (market, size, value, momentum, sector,
beta). Neutralise the exposures you do not intend to hold and re-measure. A signal whose IC disappears
after neutralising to known factors is a known factor.

Check stability: by year, by sector, by size bucket, long leg against short leg. An effect that lives in
one year or in the smallest decile is a finding about that year or that decile.

### Step 5, validate with splits that respect time

Use walk-forward validation, or combinatorial purged cross-validation where labels overlap in time,
with purging of training observations whose label windows overlap the test fold and an embargo after
each test fold (Lopez de Prado, 2018, Advances in Financial Machine Learning, chapters 7 and 12). Never
shuffle time series observations into random folds. For machine learning models follow
`references/financial-ml.md`, including sample weighting for overlapping labels.

Estimate the probability of backtest overfitting with combinatorially symmetric cross-validation
(Bailey, Borwein, Lopez de Prado and Zhu, 2017, "The Probability of Backtest Overfitting", Journal of
Computational Finance) when many configurations were compared. Method in
`references/overfitting-controls.md`.

### Step 6, compute the statistics that account for the search

Run the script on the net return series:

```
python3 scripts/strategy_stats.py returns.csv --column net --periods 252 \
    --trials 140 --trial-sr-var 0.35 --benchmark-sr 0
python3 scripts/strategy_stats.py returns.csv --column net --periods 252 --trial-srs trials.txt
```

From the repository root the path is `skills/quant-research/scripts/strategy_stats.py`. Report the
annualised Sharpe with and without the Lo (2002) autocorrelation correction, skewness and kurtosis, the
probabilistic Sharpe ratio, the minimum track record length, the deflated Sharpe ratio with the trial
count used, the Newey-West t statistic, maximum drawdown and the longest time under water. A deflated
Sharpe ratio below 0.95 means the result is consistent with the best of the trials of a strategy with
no edge. Say that plainly.

### Step 7, net out costs and find the capacity

Apply costs from `execution-microstructure`: half spread, market impact that grows with participation
(square root law as a starting point, calibrated if fills exist), fees, borrow cost and availability
for shorts, and financing. Recompute the statistics net. Then raise the traded capital until the net
Sharpe ratio halves; that capital is a rough capacity. A strategy whose net Sharpe depends on trading
the smallest names at zero impact has no capacity.

### Step 8, stress and attribute

Run the strategy through known stress windows (for equity market neutral strategies, August 2007 is the
standard case, described by Khandani and Lo, 2007, "What Happened to the Quants in August 2007?").
Attribute returns to known factors with a regression and report the residual alpha and its t
statistic. Check crowding: correlation with published factor returns and with the returns of similar
public strategies.

### Step 9, decide and set kill criteria

Verdict: REJECT, RESEARCH MORE (with the specific question), or PAPER TRADE. Never "deploy" from a
backtest alone. For PAPER TRADE, write dated kill criteria: the live statistic, its threshold, and the
date by which it is judged, derived from the minimum track record length. Then hand sizing to
`portfolio-risk` and the production path to `trading-systems`.

## Self-audit

- The hypothesis names a mechanism, a counterparty and a falsifying result, written before the data work.
- Universe membership, fundamentals and corporate actions are point in time, and delisted securities are included.
- The trial registry exists and the DSR used its full count.
- The holdout was used once, after every choice was fixed.
- Splits respect time, with purging and embargo where labels overlap.
- IC, decay, turnover and factor exposures were measured on the raw signal before building the strategy.
- Every statistic came from `scripts/strategy_stats.py` or other code that was run, with output shown.
- Results are net of spread, impact, fees, borrow and financing, with capacity stated in currency.
- Stress windows and factor attribution were reported, including residual alpha.
- The verdict is REJECT, RESEARCH MORE or PAPER TRADE, with dated kill criteria.

## What this cannot do

It cannot make a backtest predict the future. At best it removes the known ways a backtest lies. Live
performance also depends on regime change, crowding and execution the history did not contain.

It cannot audit data it has not been given. Point-in-time correctness depends on the vendor, and a
vendor that backfilled history without saying so will fool every check here.

It does not give investment advice, and nothing it produces is a recommendation to buy or sell a
security. Before trading outside money or marketing a track record, ask a securities lawyer or a
compliance officer: "We intend to trade this strategy with capital from these investors in these
jurisdictions and to show this backtest in marketing material; what registration applies to us, and
what disclosures and hypothetical performance rules govern how the backtest may be presented?"
