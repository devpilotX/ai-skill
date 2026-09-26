---
name: execution-microstructure
description: Trade with the cost measured and the market structure understood, the way an electronic execution or market making desk does. Use when the user asks how to execute a large order, what a trade will cost, how to measure slippage or implementation shortfall, how to choose between VWAP, TWAP, participation or arrival price algorithms, how market impact works, how order books, queues, tick sizes, auctions, maker-taker fees or dark pools work, how to build or evaluate a market making strategy, or why fills lag the backtest. Decomposes cost into spread, impact, timing and opportunity, calibrates impact on real fills, measures markouts for adverse selection, and states every model assumption. Signal research goes to quant-research, the order gateway and risk checks to trading-systems. Triggers on market impact, slippage, implementation shortfall, TCA, VWAP, TWAP, Almgren-Chriss, order book, market making, bid ask spread, adverse selection, markouts, dark pool, maker taker, queue position.
license: MIT
metadata:
  version: 1.0.0
  suite: ai-skill
---

# Execution and market microstructure

The failure this corrects is treating the price on the screen as the price you get. Backtests fill at the
mid or the close with no impact; live trading pays the spread, moves the price against itself, trades
with people who know more, and misses the fills that would have been most profitable. For many strategies
that difference is the whole edge. This skill measures cost from the decision to the last fill, models
impact with named assumptions, calibrates on real fills, and designs execution and quoting around who is
on the other side.

## When to use and when to stay off

Run when the user is estimating or measuring trading cost, working an order, choosing or evaluating an
execution algorithm, designing quoting, or trying to understand why live fills differ from the model.

Stay off, and route instead, when:

- The question is whether the signal predicts returns. Use `quant-research`, then return here for the cost model it needs.
- The question is target position sizes. Use `portfolio-risk`; this skill supplies the cost term.
- The question is the order gateway, pre-trade checks, kill switches or the market data pipeline. Use `trading-systems`.
- The question is option pricing or hedging. Use `derivatives-pricing`; bring the hedge execution back here.
- The user wants to manipulate prices, spoof, layer, or front-run client orders. Refuse: those are market abuse offences in most jurisdictions.

The user says "stop", "I've decided", or "just execute": comply at once and stay off for the rest of
the session unless asked again.

## Non-negotiables

These override everything else in this file.

1. Measure cost from the decision price, not from the arrival price or the average fill alone. Delay and unfilled shares are costs.
2. Every impact figure names its model, its parameters and where they came from. An uncalibrated coefficient is labelled `ASSUMPTION:`.
3. Compare execution against a benchmark chosen before the order, and never switch benchmark after seeing the result.
4. Measure adverse selection with markouts after fills for any passive or market making activity. A high fill rate with negative markouts is losing money.
5. Never recommend spoofing, layering, wash trades, trades placed to move the closing price, or trading ahead of a client order. Name the rule when asked about it.
6. Compute with `scripts/execution_cost.py` or other code that was run, and show the output.
7. State the market structure facts (fees, tick sizes, auction times, order types) as retrieved from the venue with a date. They change.

## Procedure

### Step 1, state the order and its urgency

Instrument, side, size in shares and as a share of average daily volume, the decision time and price,
the alpha horizon (how fast the reason for the trade decays), the benchmark, constraints (must finish by
the close, cannot exceed a participation rate), and whether information leakage is a concern.

Urgency sets the trade-off: fast execution pays more impact, slow execution pays more timing risk and
alpha decay.

### Step 2, estimate the cost before trading

Start with the square root law and the half spread, then refine with a schedule model:

```
python3 scripts/execution_cost.py sqrt-impact --shares 250000 --adv 5000000 --daily-vol 0.02 \
    --price 40 --coefficient 1.0 --spread-bps 4
python3 scripts/execution_cost.py almgren-chriss --shares 250000 --horizon 1 --steps 13 \
    --sigma 0.8 --eta 1e-6 --gamma 1e-7 --epsilon 0.01 --risk-aversion 1e-6
```

From the repository root the path is `skills/execution-microstructure/scripts/execution_cost.py`. The
models, their parameters and their limits are in `references/impact-and-tca.md`. For orders above a
few percent of daily volume, compare single-day and multi-day schedules.

### Step 3, choose the execution approach

Match the algorithm to the benchmark and urgency:

- Arrival price or implementation shortfall: front-loaded when alpha decays fast or risk aversion is high; the Almgren-Chriss schedule is the classical form.
- VWAP: tracks the day's volume curve. Appropriate when the benchmark is VWAP and there is no view on intraday alpha. It trades heavily at the open and close where volume is.
- TWAP: even slices in time. Predictable, therefore detectable.
- Percentage of volume: a fixed participation rate. Finish time depends on volume.
- Closing auction: for benchmarks at the close, or index rebalances. Check the imbalance publication times and cut-offs for the venue.
- Liquidity seeking in dark venues and conditional orders: lower impact for patient orders, at the cost of information leakage risk and adverse selection.

Randomise slice sizes and timing inside the schedule, and cap participation, since a regular pattern is
visible to other participants.

### Step 4, choose passive or aggressive at the child order level

A passive limit order earns the spread and fees or rebates if filled, but fills more often when the price
is about to move against it, and misses when the price moves away. An aggressive order pays the spread and
fills now. Queue position matters: in a price-time priority book, an order at the back of a long queue
fills mostly when the level is about to be traded through. Details in
`references/market-structure.md`.

### Step 5, if making markets, design the quote

Follow `references/market-making.md`. Start from a reservation price skewed against inventory and a
spread that covers adverse selection, inventory risk and fees:

```
python3 scripts/execution_cost.py avellaneda-stoikov --mid 100 --inventory 500 --gamma 0.01 \
    --sigma 0.5 --time-left 0.25 --k 1.5
```

Then measure. The model assumes fills independent of future price moves, which is exactly what informed
flow violates.

### Step 6, measure after trading

Implementation shortfall against the decision price, split into delay, execution, opportunity cost and
fees:

```
python3 scripts/execution_cost.py shortfall --side buy --decision 50.00 --arrival 50.10 \
    --fills 3000@50.15 5000@50.22 --target 10000 --close 50.40 --fees 12.50
```

Add markouts: the mid price change at fixed intervals after each fill (for example 1 second, 10 seconds,
1 minute, 5 minutes), signed by side. Persistent negative markouts on passive fills are adverse selection.
Compare realised cost to the pre-trade estimate and use the residuals to recalibrate the impact
coefficient, per `references/impact-and-tca.md`.

### Step 7, feed the costs back

Send the calibrated cost model to `quant-research` for net backtests and to `portfolio-risk` for the
turnover penalty. A strategy whose net Sharpe ratio does not survive the calibrated costs is not a
strategy.

## Self-audit

- The order is stated with size as a share of ADV, urgency, benchmark and constraints.
- The pre-trade estimate names the model, parameters and their source.
- The benchmark was fixed before trading.
- Post-trade cost is measured from the decision price, including delay, opportunity and fees.
- Markouts were measured for passive fills, at several horizons.
- The impact coefficient was calibrated on the user's own fills, or labelled an assumption.
- Venue facts (fees, tick sizes, auction times, order types) were retrieved with a date.
- No recommendation could be read as spoofing, layering, wash trading, closing price manipulation or front-running.
- Every number came from code that was run.

## What this cannot do

It cannot see the order book or the user's fills unless they are supplied, so every pre-trade estimate
is a model output until calibrated on real executions.

It cannot tell who is on the other side of a trade. Adverse selection is inferred from markouts after the
fact.

It does not give legal opinions on market conduct. For questions about order handling, best execution
duties or whether a trading pattern could be viewed as manipulative, ask a compliance officer or a
securities lawyer: "Given this order handling logic and these example order sequences, do our practices
meet our best execution obligations and the market abuse rules in the jurisdictions where we trade, and
what records must we keep?"
