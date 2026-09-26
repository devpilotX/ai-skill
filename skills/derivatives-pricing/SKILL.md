---
name: derivatives-pricing
description: Price, hedge and risk manage options and other derivatives the way a volatility trading desk does, with arbitrage-free inputs, validated numerics and a P&L that can be explained. Use when the user asks to price an option, compute Greeks, solve for implied volatility, build or check a volatility surface, fit SVI, SABR, Heston or local volatility, value American or exotic options, run Monte Carlo or PDE pricing, delta hedge, explain option P&L, trade volatility, or check quotes for arbitrage. Checks static arbitrage before fitting, validates every pricer against a closed form or a second method, attributes P&L to Greeks and realised against implied volatility, and states model risk. Portfolio aggregation goes to portfolio-risk, hedge execution to execution-microstructure. Triggers on option pricing, Black-Scholes, Greeks, implied volatility, vol surface, SVI, SABR, Heston, local volatility, delta hedging, gamma scalping, American option, Monte Carlo pricing, put call parity.
license: MIT
metadata:
  version: 1.0.0
  suite: ai-skill
---

# Derivatives pricing

The failure this corrects is a price produced by a formula the inputs do not fit. Black-Scholes applied to
the wrong forward, a smile fitted through quotes that contain arbitrage, a Monte Carlo pricer with a bug
nobody checked against a closed form, and a hedge ratio from a model whose dynamics the market does not
follow: each produces a confident number and a P&L nobody can explain. This skill checks the inputs for
arbitrage, validates the numerics, and makes the P&L explainable by the Greeks before any number is
trusted.

## When to use and when to stay off

Run when the user is pricing, hedging, calibrating, or explaining the P&L of an option or derivative,
or building a volatility surface.

Stay off, and route instead, when:

- The question is how an options book fits into total portfolio risk and limits. Use `portfolio-risk`, with Greeks supplied from here.
- The question is how to execute the hedge trades. Use `execution-microstructure`.
- The question is whether a volatility signal predicts returns. Use `quant-research` for the validation discipline.
- The user wants a probability puzzle or sizing question with no derivative in it. Use `quant-reasoning`.
- The user asks whether they personally should buy options. Decline the recommendation; offer to explain the payoff and the risks.

The user says "stop", "I've decided", or "just execute": comply at once and stay off for the rest of
the session unless asked again.

## Non-negotiables

These override everything else in this file.

1. Get the forward right first: spot, rates curve, dividends (discrete or yield), borrow cost and the settlement convention. Most pricing errors are forward errors.
2. Check quotes for static arbitrage before fitting anything to them, and fit only arbitrage-free surfaces.
3. Validate every pricer against a closed form, a second numerical method, or a known limit, and report the difference.
4. State the model's dynamics and what they imply for the hedge. A price is only as good as the hedge that replicates it.
5. Explain P&L with Greeks. An unexplained residual above a stated tolerance is a finding, not noise.
6. State units: vega per vol point or per unit, theta per day or per year, rates compounding, day count.
7. Compute with `scripts/options_lab.py` or other code that was run, and show the output.

## Procedure

### Step 1, specify the contract and the market data

Payoff, exercise style (European, American, Bermudan), settlement (cash or physical), underlying,
multiplier, expiry date and time, and any barrier or averaging feature. Market data with its timestamp:
spot or futures price, the discount curve, dividends or the implied forward from put-call parity,
borrow cost, and the option quotes as bid and ask, not only mid.

Compute the implied forward from put-call parity on liquid strikes and compare it with the forward from
the dividend and rate inputs. A gap means the dividends, borrow or rates are wrong, or the options are
American and early exercise matters.

```
python3 scripts/options_lab.py parity --call 10.45 --put 5.57 --spot 100 --strike 100 --rate 0.05 --expiry 1
```

From the repository root the path is `skills/derivatives-pricing/scripts/options_lab.py`.

### Step 2, clean the quotes and check for arbitrage

Drop crossed, stale and zero-bid quotes. Then check each expiry for static arbitrage (price bounds,
monotonicity, slope bounds, convexity) and across expiries for calendar arbitrage in total variance:

```
python3 scripts/options_lab.py chain calls_june.csv --rate 0.04 --expiry 0.25 --spot 100
python3 scripts/options_lab.py calendar 0.25:0.22 0.5:0.21 1.0:0.20
```

A violation on mids that disappears inside the bid-ask spread is not tradeable arbitrage; one that
survives the spread is either a data error or an opportunity. Say which you checked. Conditions and
fitting methods are in `references/volatility-surface.md`.

### Step 3, choose the model for the question

Pick the model by the question, not by habit:

- Vanilla European valuation and quoting: Black-Scholes-Merton or Black-76 on the forward, with implied volatility read from an arbitrage-free surface.
- Consistency across strikes and expiries for exotics sensitive to the smile: local volatility (Dupire) fits all vanillas but implies forward smiles that flatten, which misprices forward-starting and cliquet structures.
- Smile dynamics and volatility of volatility: stochastic volatility (Heston, SABR). SABR is the market standard for rates smiles by expiry; its Hagan et al. expansion can produce negative densities at low strikes.
- Early exercise: a lattice, finite differences, or least squares Monte Carlo (Longstaff and Schwartz, 2001).

Name what the chosen model gets wrong for this contract.

### Step 4, calibrate and check the fit

Calibrate to the quotes that matter for the hedge, weighted by vega or by inverse spread. Report fit
errors in volatility points and against the bid-ask. Check that parameters are stable day to day; a
calibration whose parameters jump while the market barely moved is fitting noise, and its Greeks will
jump too.

### Step 5, price and validate the numerics

```
python3 scripts/options_lab.py price --spot 100 --strike 105 --rate 0.04 --div 0.01 --vol 0.23 --expiry 0.5
python3 scripts/options_lab.py iv --price 4.10 --spot 100 --strike 105 --rate 0.04 --div 0.01 --expiry 0.5
python3 scripts/options_lab.py mc --spot 100 --strike 105 --rate 0.04 --div 0.01 --vol 0.23 --expiry 0.5 --paths 200000 --seed 1
```

For every numerical pricer: agree with a closed form in a limit where one exists, converge as the grid
or path count increases (report the rate), and give stable Greeks under bumping. Methods and their traps
are in `references/numerical-methods.md`.

### Step 6, hedge and attribute P&L

Delta hedge at a stated frequency or band. Attribute daily P&L into delta, gamma, vega, theta, vanna,
volga and a residual, using the rules in `references/greeks-and-hedging.md`. For a delta-hedged option the
core identity is that gamma P&L plus theta over a period is approximately one half gamma S squared times
the difference between realised and implied variance over the period. A hedged long option makes money
when realised volatility exceeds the implied volatility paid, and the path decides how much.

### Step 7, state the risks and limits

Vega by expiry bucket and by strike region, gamma concentration near expiry and near barriers, pin risk
at expiry, dividend and borrow risk, early exercise, correlation for multi-asset payoffs, and model risk
(the price range across reasonable models). Hand the aggregated Greeks to `portfolio-risk`.

## Self-audit

- The forward was built from rates, dividends and borrow, and checked against put-call parity.
- Quotes were cleaned and checked for static and calendar arbitrage, with bid-ask considered.
- The model was chosen for the question, and what it gets wrong is stated.
- Calibration errors are reported in vol points against the spread, and parameter stability was checked.
- Every numerical pricer was validated against a closed form or a second method, with convergence shown.
- Units are stated for every Greek.
- P&L is attributed to Greeks with the residual reported against a tolerance.
- Risks include vega buckets, gamma near expiry, pin risk, dividends, early exercise and model risk.
- Every number came from code that was run.

## What this cannot do

It cannot give a price that is right in any absolute sense. Prices are model outputs; the market price,
the hedge cost and the model range are what can be stated.

It cannot see the user's quotes, positions or market data unless supplied, and it cannot vouch for data it
was not given.

It does not provide investment advice, valuation opinions for accounts, or regulatory capital figures.
For fair value measurement in financial statements, ask the auditor or a valuation specialist: "Which
inputs to this valuation are observable, what level of the fair value hierarchy does it fall in, and what
valuation adjustments are required?" For model governance in a regulated firm, ask model risk management
or compliance: "What validation and documentation does this model need before it is used for pricing or
risk?"
