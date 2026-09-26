---
name: portfolio-risk
description: Size positions, build portfolios and measure risk the way an institutional risk desk does, treating the covariance matrix and expected returns as noisy estimates. Use when the user asks how to size a position, combine strategies or assets, build a mean-variance, minimum variance, risk parity or Kelly portfolio, estimate a covariance matrix, compute VaR, expected shortfall, risk contributions, factor exposures or drawdown limits, backtest a risk model, stress test a book, or set leverage. Shrinks and denoises estimates, budgets risk rather than capital, costs turnover, stress tests against named historical episodes, and sets limits with an owner and an action. Signal research goes to quant-research, trading cost to execution-microstructure, option Greeks to derivatives-pricing. Triggers on position sizing, portfolio optimisation, covariance matrix, Ledoit-Wolf, risk parity, Kelly criterion, VaR, expected shortfall, risk contribution, factor exposure, drawdown, leverage, stress test.
license: MIT
metadata:
  version: 1.0.0
  suite: ai-skill
---

# Portfolio risk

The failure this corrects is optimising on estimates as if they were facts. A mean-variance optimiser
fed a sample covariance matrix and historical mean returns concentrates in the assets whose errors are
most favourable, which Michaud (1989, "The Markowitz Optimization Enigma: Is 'Optimized' Optimal?",
Financial Analysts Journal) called error maximisation. The same book then fails in a stress because
correlations rise together, liquidity disappears, and the positions that looked diversified were one
trade. This skill treats every input as an estimate with an error, budgets risk instead of capital, and
tests the portfolio against the episodes that break portfolios.

## When to use and when to stay off

Run when the user is deciding how much to hold, how to combine positions or strategies, how to measure
the risk of a book, or what limits to set.

Stay off, and route instead, when:

- The question is whether a signal has an edge at all. Use `quant-research` first; sizing a strategy with no edge only decides how fast it loses.
- The question is the cost of trading into or out of the positions. Use `execution-microstructure`, then bring the cost back into step 5.
- The book holds options and the question is Greeks, volatility or hedging. Use `derivatives-pricing` for the instrument risk, then aggregate here.
- The question is the risk controls inside the trading platform (order limits, kill switches). Use `trading-systems`.
- The user asks what to invest their personal savings in. Decline the recommendation; offer the arithmetic instead.

The user says "stop", "I've decided", or "just execute": comply at once and stay off for the rest of
the session unless asked again.

## Non-negotiables

These override everything else in this file.

1. Never feed a raw sample covariance matrix to an optimiser when the number of assets is not small relative to the number of observations. Shrink it, use a factor model, or denoise it, and report which.
2. Never optimise on historical mean returns alone. Expected returns come from a stated model, are shrunk toward a prior, or are replaced by a risk-based construction.
3. Budget risk, not capital. Report each position's and each strategy's contribution to total risk.
4. Every risk number states its horizon, confidence level, method and the data window, and is backtested against realised outcomes.
5. Stress test against named historical episodes and hypothetical shocks, including a correlation and liquidity shock, not only against a distribution fitted to calm data.
6. Leverage is sized to survive the stress case with margin still available. Size to the stress loss, not to the volatility.
7. Every limit has an owner, a measurement, a breach action and a review date. Compute with `scripts/risk_lab.py` or other code that was run.

## Procedure

### Step 1, define the objective and the constraints

Write down what is being optimised (return per unit of risk, growth, tracking error to a benchmark,
drawdown), the horizon, the risk measure, and every constraint that binds in practice: long only or not,
gross and net exposure, position limits, sector and factor limits, liquidity (a share of average daily
volume), turnover, borrow availability, margin, and regulatory limits.

### Step 2, estimate risk

Follow `references/covariance-and-factors.md`. Choose the window and weighting (an exponentially
weighted estimate with a stated half-life reacts faster than an equal weighted one), then control
estimation error:

```
python3 scripts/risk_lab.py cov returns.csv --skip date          # sample and Ledoit-Wolf, with the intensity
python3 scripts/risk_lab.py spectrum returns.csv --skip date     # eigenvalues against the Marchenko-Pastur edge
```

From the repository root the path is `skills/portfolio-risk/scripts/risk_lab.py`. With N assets and T
observations the demeaned sample covariance has rank at most T - 1, so it is singular once N reaches
T and badly conditioned well before that. Eigenvalues inside the Marchenko-Pastur band are indistinguishable from noise for independent
data; a factor model or shrinkage replaces them.

For a large universe use a factor model: exposures to a small number of factors, a factor covariance,
and specific risk per asset.

### Step 3, decide how expected returns enter

Options in order of how much they trust the return forecast:

- None: minimum variance or equal risk contribution. Trusts only the risk estimate.
- A prior plus views: Black and Litterman (1992, "Global Portfolio Optimization", Financial Analysts Journal) start from the returns implied by market weights and blend in views with stated confidence.
- A forecast from `quant-research`, converted to expected returns through the IC and volatility (alpha = IC x volatility x standardised score, per Grinold and Kahn), with the forecast shrunk toward zero.

Say which, and why the forecast deserves that much trust.

### Step 4, construct

Construction methods and their failure modes are in `references/construction.md`. Compute rather than
guess:

```
python3 scripts/risk_lab.py minvar returns.csv --skip date --shrink
python3 scripts/risk_lab.py riskparity returns.csv --skip date --shrink
python3 scripts/risk_lab.py kelly returns.csv --skip date --shrink --fraction 0.25
```

Prefer constructions whose output changes little when the inputs are perturbed. Test that: resample the
returns (bootstrap), re-estimate, re-optimise, and report how much the weights move. Weights that swing
wildly between resamples reflect estimation noise.

Kelly sizing maximises long-run growth only with a known edge. With an estimated edge, full Kelly
overbets; fractional Kelly (a quarter to a half, labelled `ASSUMPTION:` with the reasoning) is the usual
response, and `quant-reasoning` covers the arithmetic.

### Step 5, cost the rebalance

Put transaction costs and turnover into the objective or as a constraint, using impact estimates from
`execution-microstructure`. A portfolio that is optimal before costs and rebalanced daily is usually
worse after costs than a slower one. Report expected turnover and cost per year.

### Step 6, measure and decompose risk

```
python3 scripts/risk_lab.py contrib returns.csv --skip date --weights A=0.4 B=0.35 C=0.25
python3 scripts/risk_lab.py var returns.csv --skip date --weights A=0.4 B=0.35 C=0.25 --alpha 0.99
```

Report volatility, Euler risk contributions by position and by factor, value at risk and expected
shortfall at the stated horizon and confidence, and the drawdown distribution. Prefer expected shortfall
for limits, since VaR says nothing about the size of losses beyond it; the Basel Committee's
Fundamental Review of the Trading Book moved bank market risk capital from 99 percent VaR to 97.5 percent
expected shortfall for that reason.

### Step 7, stress test

Run the portfolio through the historical episodes and hypothetical shocks in
`references/tail-and-liquidity.md`: at minimum a crash with correlations going to one, a volatility
spike, a liquidity shock where exit takes several times longer and costs several times more, and a
crowded-trade unwind. Report the loss, the margin call it triggers, and whether the book can meet it
without forced selling.

### Step 8, set limits and backtest the risk model

Limits: gross and net exposure, risk budget per strategy, expected shortfall, stress loss, drawdown
triggers with a defined de-risking action, concentration and liquidity. Each with an owner and a breach
action.

Backtest VaR by counting exceptions and testing coverage:

```
python3 scripts/risk_lab.py kupiec --exceptions 7 --observations 250 --alpha 0.99
```

Add an independence check (exceptions should not cluster; Christoffersen, 1998, "Evaluating Interval
Forecasts", International Economic Review). A model that passes coverage but produces exceptions in
bunches is underestimating risk in stress.

## Self-audit

- The covariance estimate was shrunk, factor-based or denoised, with the method and intensity reported.
- The source and shrinkage of expected returns are stated, or the construction does not use them.
- Weight stability under resampling was checked.
- Risk contributions by position and factor are reported, and the largest contributor is named.
- Every risk figure has horizon, confidence, method and data window.
- Costs and turnover are inside the construction, not added afterwards.
- Stress tests include correlation and liquidity shocks, with the margin consequence.
- Leverage survives the stress loss with margin to spare.
- Each limit has an owner, a breach action and a review date.
- The VaR model was backtested for coverage and clustering.
- Every number came from code that was run, with the output shown.

## What this cannot do

It cannot know the future covariance. Estimates describe the window they were fitted on, and the
episodes that matter most tend to be the ones the window did not contain.

It cannot model liquidity it has no data for. Exit cost in a stress is an assumption, and the output
labels it as one.

It does not give personal investment advice or suitability judgements. For client money, ask a
regulated investment adviser or compliance officer: "For this client with this objective, horizon,
liquidity need and loss tolerance, is this allocation and its leverage suitable, and what disclosures
must accompany it?" For a fund, ask the fund's counsel: "Which leverage, concentration and liquidity
limits apply to this vehicle under its offering documents and the rules of the jurisdictions it is sold
in?"
