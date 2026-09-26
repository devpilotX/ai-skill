---
name: quant-reasoning
description: Reason about probability, expected value, sizing and uncertainty the way trading desks and their interviews expect, with every number computed and every assumption named. Use when the user asks a probability puzzle or brainteaser, an expected value or betting question, a Bayesian updating problem, Kelly or bet sizing, risk of ruin, a market making game or how to quote an uncertain quantity, a Fermi estimate, forecast calibration or scoring, or wants to check whether a trade idea has positive edge. Sets up the problem formally, solves it two ways where possible, checks against simulation, sizes by growth rather than by expected value, and accounts for adverse selection. Data-driven strategy research goes to quant-research, portfolio sizing to portfolio-risk, arithmetic checks to numbers-check. Triggers on probability puzzle, brainteaser, expected value, Kelly criterion, bet sizing, risk of ruin, Bayes, market making game, make me a market, Fermi estimate, calibration, Brier score, quant interview.
license: MIT
metadata:
  version: 1.0.0
  suite: ai-skill
---

# Quant reasoning

The failure this corrects is the fluent answer to a probability question that is wrong in the setup:
the conditioning event misread, independence assumed where there is none, the expected value computed
and the variance ignored, or a bet sized as if the edge were known exactly. Language models are
particularly prone to reciting the answer to the famous version of a puzzle when the question asked is a
variant. This skill writes the problem down formally, solves it, checks the answer a second way, and
treats the counterparty's willingness to trade as information.

## When to use and when to stay off

Run when the question is about probability, expected value, decisions under uncertainty, sizing, or
quoting, whether as a puzzle, an interview problem, or a live decision.

Stay off, and route instead, when:

- The question needs historical data and a backtest. Use `quant-research`.
- The question is sizing a portfolio of real positions with a covariance matrix. Use `portfolio-risk`.
- The task is checking the arithmetic or statistics in someone's document. Use `numbers-check`.
- The question is about gambling to recover losses, or the user shows signs of problem gambling. Do not help size the bet. Say plainly that no staking system beats a negative expected value game, and point to support services such as a national gambling helpline.

The user says "stop", "I've decided", or "just execute": comply at once and stay off for the rest of
the session unless asked again.

## Non-negotiables

These override everything else in this file.

1. Restate the problem formally before solving it: the sample space, the random variables, what is known, and exactly what is conditioned on. Check whether it is a variant of a famous problem, and if so, what changed.
2. Solve two ways where possible (a direct calculation and a symmetry, recursion or complement argument), or check by simulation. Two methods that disagree mean one setup is wrong.
3. Compute with code for anything beyond one line of arithmetic. `scripts/edge_calc.py` covers expected value, Kelly, Bayes, ruin and forecast scoring.
4. Report the variance or the distribution, not only the expected value, whenever a decision depends on it.
5. Size by growth and survival, not by expected value. With an estimated edge, use a fraction of Kelly and say why.
6. When a counterparty offers or accepts a trade, update on that fact before judging the price.
7. State uncertainty honestly. When an answer depends on an unstated assumption, give the answer under each reasonable reading.

## Procedure

### Step 1, formalise

Write the random variables and their distribution. Name every assumption the wording leaves open: with or
without replacement, independent or not, who chooses and how, what the observer knows and how they came to
know it. For a variant of a known puzzle, write down the known answer and the difference that could change
it.

### Step 2, find the structure

Look for the tool that makes the problem small, using `references/probability-toolkit.md`: symmetry,
linearity of expectation (which does not need independence), conditioning on the first step and solving
the recursion, complementary counting, indicator variables, the reflection principle, martingale arguments
for stopping problems, and Bayes in odds form.

### Step 3, solve and check

Solve exactly where possible. Check with a second argument or a limit case (what happens with one item,
two items, or a very large number). Simulate when in doubt, with a fixed seed and enough trials for the
standard error to be below the precision claimed.

```
python3 scripts/edge_calc.py ev 100:0.2 -20:0.8
python3 scripts/edge_calc.py bayes --prior 0.001 --sensitivity 0.99 --specificity 0.98
```

From the repository root the path is `skills/quant-reasoning/scripts/edge_calc.py`.

### Step 4, turn the answer into a decision

For a bet or trade: edge per unit, variance, the Kelly fraction and the growth at the fraction actually
used, and the probability of an unacceptable drawdown.

```
python3 scripts/edge_calc.py kelly --p 0.55 --odds 1 --fraction 0.5
python3 scripts/edge_calc.py ruin --p 0.55 --odds 1 --stake-fraction 0.1 --rounds 500 --floor 0.5 --seed 1
```

If the edge estimate comes from a small sample, show how the decision changes when the win probability is
at the lower end of its interval.

### Step 5, quote when asked to make a market

For "make me a market on X": estimate the expected value and the uncertainty, quote a bid and ask around
the expected value with width reflecting that uncertainty and the risk that the asker knows more, and state
the size. When hit or lifted, update the estimate toward the side the counterparty took and requote. The
full reasoning is in `references/probability-toolkit.md` under adverse selection.

### Step 6, score and calibrate

For forecasts, record the probability and the outcome, and score:

```
python3 scripts/edge_calc.py score forecasts.csv
```

Report the Brier score against the base-rate forecast, the log loss, and the calibration table. A
forecaster who is right on average but miscalibrated in the tails is taking risk they do not see.

## Self-audit

- The problem was restated formally, with every assumption the wording leaves open named.
- A variant of a famous problem was checked for the change that matters.
- The answer was checked by a second method or a simulation, with the seed and trial count.
- Arithmetic beyond one line came from code that was run.
- The variance or distribution is reported where the decision depends on it.
- Sizing uses growth and a Kelly fraction justified by the uncertainty in the edge.
- Counterparty behaviour was treated as information in any trading question.
- Answers that depend on interpretation are given under each reading.

## What this cannot do

It cannot make an edge out of a game without one. If the expected value is negative, no sizing rule or
stopping rule changes that, and the output says so.

It cannot know the true probability behind a real-world forecast; it can only structure the estimate and
score it after the fact.

It does not give investment or gambling advice. For a decision about personal savings, ask a regulated
financial adviser: "Given my income, savings, debts and time horizon, how much of my wealth, if any, is it
suitable to put into a speculative position with this return profile?"
