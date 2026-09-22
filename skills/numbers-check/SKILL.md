---
name: numbers-check
description: Verify quantitative work, arithmetic, units, statistics, and proofs, and recompute rather than trust. Use when the user asks to check a calculation, verify maths, review a financial model or spreadsheet logic, check a statistic or a percentage, validate a proof or derivation, work out unit conversions, estimate a quantity, or asks whether a number is plausible. Also use whenever a task involves arithmetic that a wrong answer would make harmful, since language models make confident arithmetic errors. Recomputes every figure with a script instead of in prose, carries units through the whole calculation, sanity checks the result against an independent estimate, states the sample size and what the data cannot support, and refuses causal claims from correlational data. Triggers on check my maths, verify this calculation, is this number right, check my model, does this add up, validate this proof, estimate how many, what are the odds, statistical significance.
license: MIT
metadata:
  version: 1.0.0
  suite: ai-skill
---

# Numbers check

Arithmetic written as prose is unverifiable and frequently wrong. This skill computes with a script,
carries units, and checks the answer a second way.

## Non-negotiables

1. Compute with a tool, not in prose. Write and run a short script for anything beyond trivial mental arithmetic, and show the script. A script is checkable and a paragraph of numbers is not.
2. Carry units through every step and cancel them explicitly. Most real errors are unit errors, not arithmetic errors.
3. Check every result a second, independent way. An order of magnitude estimate, a different decomposition, or a boundary case. Two methods agreeing is weak evidence and still much better than one.
4. Never invent an input. Every figure is supplied by the user, retrieved with a citation, or labelled `ASSUMPTION:` with the reasoning and the sensitivity attached.
5. State precision honestly. A result computed from a figure with one significant digit does not have four. Do not report precision the inputs cannot support.
6. Separate what the numbers show from what they imply. Correlation is not causation, and a statistically significant result is not necessarily a meaningful one.

## Procedure

### Step 1, restate the question quantitatively

Write down what is being computed, the inputs, and their units. Ambiguity resolved here saves the whole
calculation. Percent of what, over which period, measured how.

If two readings of the question give different answers, say so and compute both rather than picking one
silently.

### Step 2, list inputs with provenance

Each input gets a value, a unit, and a source. Mark each as given, retrieved with a link, or assumed.
Assumed values get a range, not a point, because the range is what makes the sensitivity analysis
possible later.

### Step 3, compute with a script

```
python3 - <<'PY'
# state units in comments and keep them in variable names
revenue_per_unit_usd = 34.50
units_per_month = 1200
cogs_per_unit_usd = 21.10
monthly_gross_usd = (revenue_per_unit_usd - cogs_per_unit_usd) * units_per_month
print("gross margin per unit: %.2f usd" % (revenue_per_unit_usd - cogs_per_unit_usd))
print("monthly gross: %.2f usd" % monthly_gross_usd)
print("margin pct: %.1f%%" % (100 * (revenue_per_unit_usd - cogs_per_unit_usd) / revenue_per_unit_usd))
PY
```

Use exact decimal arithmetic for money, meaning a decimal type rather than binary floating point.
Rounding a currency figure with floating point produces errors that compound through a model.

Keep full precision through intermediate steps and round only at the end, then say where rounding was
applied.

### Step 4, check it a second way

Order of magnitude. Does the answer sit where a rough estimate puts it? Off by a factor of ten usually
means a unit error or a misplaced decimal.

Different decomposition. Compute it by a different route and compare.

Boundary cases. Set an input to zero, to one, and to a large value. Does the result behave sensibly?
Nonsense at a boundary means the model is wrong even where it looks right.

Dimensional analysis. Do the units of the answer match what the question asked for? If the question
wants a rate and the answer has units of a quantity, something was dropped.

### Step 5, sensitivity

Vary each assumed input across its range and report which one moves the answer most. That single item
is what the user should go and verify, and naming it is often more useful than the answer itself.

If the conclusion flips inside the plausible range of any assumption, say the conclusion is not
determined by the available data. That is a result, not a failure.

### Step 6, report

```
ANSWER
[The figure, with units and honest precision.]

INPUTS
[Each with value, unit, and provenance: given, retrieved with link, or ASSUMPTION with range.]

METHOD
[The script, and the units cancelling.]

CROSS-CHECK
[The second method and what it gave.]

SENSITIVITY
[Which input dominates, and the range over which the conclusion holds.]

WHAT THIS DOES NOT SHOW
[The claim a reader might wrongly draw from this number.]
```

## Statistics specifics

Rules and traps in `references/checks.md`, covering percentages, averages, rates, significance,
sample size, survivorship, and the errors that appear most in business and engineering numbers.

## Proofs and derivations

Check each step independently rather than following the author's reasoning, which is how a plausible
error survives review. Name the step that fails and give the counterexample. For an induction, check
the base case and confirm the inductive step uses the hypothesis exactly once and validly. Check
quantifier order, division by a quantity that may be zero, and any step taking a root or a logarithm of
something that may be non-positive.

If a step cannot be verified, say which one rather than passing the whole proof.

## Self-audit

- A script was run, and its output is in the answer.
- Units appear at every step and cancel correctly.
- Every input has provenance, and assumptions have ranges.
- A second independent check was done and reported.
- Precision reflects the weakest input.
- Money used decimal arithmetic.
- The dominant assumption is named.
- The section on what the number does not show is present and specific.
