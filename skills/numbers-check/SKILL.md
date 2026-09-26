---
name: numbers-check
description: Verify quantitative work, arithmetic, units, statistics, and proofs by recomputing. Use when the user asks to check a calculation or maths, review a financial model or spreadsheet logic, check a statistic, percentage or percentage change, read an A/B test result, work out a sample size, validate a proof, convert units, make a Fermi estimate, or asks whether a number is plausible. Recomputes every figure with a script, carries units through, cross-checks against an independent estimate, states sample size and what the data cannot support, and refuses causal claims from correlational data. For unit economics use business-model, for bookkeeping use finance-books, for finding a figure use deep-research, for trading strategy statistics use quant-research. Triggers on check my maths, is this number right, check my model, does this add up, estimate how many, what are the odds, statistical significance, is this A/B test significant, how many users do I need, convert these units.
license: MIT
metadata:
  version: 1.1.0
  suite: ai-skill
---

# Numbers check

Language models state arithmetic in prose with confidence and get it wrong, and a wrong number in prose
cannot be checked. This skill computes with a script, carries units, and checks the answer a second
way.

## When to use and when to stay off

Run when a number is being produced, checked, or relied on for a decision: a calculation, a model, a
statistic, an experiment result, an estimate, or a proof.

Stay off, and route instead, when:

- The question is whether a business model or price works, beyond checking its arithmetic. Use `business-model`.
- The task is bookkeeping, reconciliation, or preparing statements. Use `finance-books`.
- The number does not exist yet and has to be found and cited. Use `deep-research`, then come back to check it.
- The work is backtesting or statistics of a trading strategy. Use `quant-research`.
- The arithmetic is trivial and nothing rides on it. Just answer.

The user says "stop", "I've decided", or "just execute": comply at once and stay off for the rest of
the session unless asked again.

## Non-negotiables

These override everything else in this file.

1. Compute with a tool, not in prose. Write and run a short script for anything beyond trivial mental arithmetic, and show the script and its output.
2. Carry units through every step and cancel them explicitly.
3. Check every result a second, independent way: an order of magnitude estimate, a different decomposition, or a boundary case.
4. Never invent an input. Every figure is supplied by the user, retrieved with a citation, or labelled `ASSUMPTION:` with the reasoning and a range.
5. State precision honestly. A result computed from a figure with one significant digit does not have four.
6. Use `decimal.Decimal` for money, with an explicit rounding mode, and never binary floats.
7. Separate what the numbers show from what they imply. Correlation is not causation, and a statistically significant result is not necessarily a meaningful one.

## Procedure

### Step 1, restate the question quantitatively

Write down what is being computed, the inputs, and their units. Percent of what, over which period,
measured how.

If two readings of the question give different answers, say so and compute both rather than picking
one silently.

### Step 2, list inputs with provenance

Each input gets a value, a unit, and a source: given, retrieved with a link, or assumed. Assumed values
get a range, because the range is what makes the sensitivity analysis possible later.

If the inputs come from a spreadsheet, check it for the structural errors listed under "Spreadsheets"
in `references/checks.md` before trusting any cell.

### Step 3, compute with a script

```
python3 - <<'PY'
# units live in the variable names; money is Decimal, built from strings, never floats
from decimal import Decimal, ROUND_HALF_EVEN
CENT = Decimal("0.01")
revenue_per_unit_usd = Decimal("34.50")
cogs_per_unit_usd = Decimal("21.10")
units_per_month = 1200
margin_per_unit_usd = revenue_per_unit_usd - cogs_per_unit_usd
monthly_gross_usd = margin_per_unit_usd * units_per_month
margin_pct = 100 * margin_per_unit_usd / revenue_per_unit_usd
print("gross margin per unit: %s usd" % margin_per_unit_usd.quantize(CENT, rounding=ROUND_HALF_EVEN))
print("monthly gross: %s usd" % monthly_gross_usd.quantize(CENT, rounding=ROUND_HALF_EVEN))
print("margin pct: %s%%" % margin_pct.quantize(Decimal("0.1"), rounding=ROUND_HALF_EVEN))
PY
```

Output when run:

```
gross margin per unit: 13.40 usd
monthly gross: 16080.00 usd
margin pct: 38.8%
```

Build `Decimal` values from strings, since `Decimal(34.5)` inherits the binary float error. Choose the
rounding mode on purpose: `ROUND_HALF_EVEN` (banker's rounding) is the Python default and avoids
upward drift over many roundings, `ROUND_HALF_UP` matches what many invoices and tax authorities
expect. Where a rule applies (tax, invoicing, a contract), retrieve the rounding rule from the
authority that sets it and say which one was used.

Keep full precision through intermediate steps and round only at the end, then say where rounding was
applied.

Floating point also fails outside money. Subtracting two nearly equal floats loses most significant
digits (catastrophic cancellation), and summing many floats gives an answer that depends on order. Use
`math.fsum` for sums, rearrange formulas to avoid subtracting close values, and compare floats with a
tolerance, never with `==`. Details in `references/checks.md`.

### Step 4, check it a second way

Order of magnitude. Off by a factor of ten usually means a unit error or a misplaced decimal.

Different decomposition. Compute it by a different route and compare.

Boundary cases. Set an input to zero, to one, and to a large value. Nonsense at a boundary means the
model is wrong even where it looks right.

Dimensional analysis. Do the units of the answer match what the question asked for?

### Step 5, sensitivity

Vary each assumed input across its range and report which one moves the answer most. That item is what
the user should go and verify.

For an estimate built from several ranged inputs, do not multiply the lows together and the highs
together, since that range needs every input at its extreme at once. Use the product of geometric
midpoints for a point estimate, and a Monte Carlo run for the range:

```
python3 scripts/stats_tools.py montecarlo 1e6:5e6 0.01:0.05 20:40 --seed 1
```

If the conclusion flips inside the plausible range of any assumption, say the conclusion is not
determined by the available data. That is a result, not a failure.

### Step 6, statistics and experiments

Traps for percentages, averages, rates, significance, money, spreadsheets and estimation are in
`references/checks.md`.

For an A/B test or any experiment, work through `references/experiments.md` before reading the result.
Three checks, each of which can invalidate a test on its own:

- Peeking. Checking significance repeatedly and stopping when it crosses the threshold inflates the false positive rate. The stopping rule has to be fixed in advance, or a sequential method used.
- Power. The sample size for the minimum detectable effect has to be computed before the test starts. An underpowered test that "shows no effect" shows nothing.
- Sample ratio mismatch. If a 50/50 split produced visibly unequal arms, the assignment is broken and the result is not trustworthy, whatever it says.

The helpers in `scripts/stats_tools.py` compute each of these with the standard library:

```
python3 scripts/stats_tools.py samplesize 0.10 0.02          # per arm, before the test
python3 scripts/stats_tools.py ztest 100 1000 130 1000        # after the test
python3 scripts/stats_tools.py wilson 8 10                    # interval for one proportion
python3 scripts/stats_tools.py bh 0.01 0.04 0.03 0.20         # many comparisons
```

### Step 7, proofs and derivations

Check each step independently rather than following the author's reasoning, which is how a plausible
error survives review. Name the step that fails and give the counterexample.

For an induction, check the base case, then check that the inductive step is valid for every n from
the base case upward, including the smallest transition. The "all horses are the same colour"
argument fails exactly there: the step from n = 1 to n = 2 relies on two overlapping subsets, and with
two horses the subsets do not overlap. Strong induction may use several earlier cases, which is fine as
long as each one is covered by a base case or an earlier step. Confirm that the hypothesis assumed is
the statement for smaller n, and not the claim being proved.

Check quantifier order, division by a quantity that may be zero, and any step taking a root or a
logarithm of something that may be non-positive.

If a step cannot be verified, say which one rather than passing the whole proof.

### Step 8, report

```
ANSWER
The figure, with units and honest precision.

INPUTS
Each with value, unit, and provenance: given, retrieved with link, or ASSUMPTION with range.

METHOD
The script, its output, and the units cancelling.

CROSS-CHECK
The second method and what it gave.

SENSITIVITY
Which input dominates, and the range over which the conclusion holds.

WHAT THIS DOES NOT SHOW
The claim a reader might wrongly draw from this number.
```

## Self-audit

- A script was run, and its output is in the answer.
- Units appear at every step and cancel correctly.
- Every input has provenance, and assumptions have ranges.
- A second independent check was done and reported.
- Precision reflects the weakest input.
- Money used `Decimal` built from strings, with a named rounding mode.
- Ranged estimates used geometric midpoints or Monte Carlo, not a product of extremes.
- For an experiment: the stopping rule, the power calculation, and the arm ratio were checked.
- The number of comparisons is stated, and adjusted for when there were many.
- The dominant assumption is named.
- The section on what the number does not show is present and specific.

## What this cannot do

It checks arithmetic, units, statistical method and logic. It cannot tell whether an input is true if
nobody can source it, and it cannot rescue an experiment whose data collection was broken.

Some numbers carry legal or regulatory weight, and a correct calculation is not the same as a correct
filing. Name the professional and give the exact question:

- Tax: a qualified accountant or tax adviser. "Under the rules for my jurisdiction and entity type, for the period in question, is this amount taxable or deductible, at what rate, and how must it be rounded and reported?"
- Pensions, insurance reserves, or life contingencies: a qualified actuary. "Given these cash flows and these mortality or claim assumptions, are the reserve and the discount rate I used acceptable for the purpose and standard this is reported under?"
- Investment decisions: a regulated financial adviser. "Given my circumstances and horizon, is this allocation suitable, and what are the fees and risks I have not modelled?"
