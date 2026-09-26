# Experiments and A/B tests

The design decides what a test can show, so most of these checks happen before any data arrives. All
commands below use `scripts/stats_tools.py`, run from the skill folder.

A general reference for the online experiment traps covered here is Kohavi, Tang and Xu,
"Trustworthy Online Controlled Experiments" (Cambridge University Press, 2020).

## Before the test: power and sample size

Fix four things in writing before starting:

1. The primary metric, one only. Secondary metrics are exploratory.
2. The minimum detectable effect (MDE): the smallest change worth acting on, as an absolute difference. This is a business judgement, not a statistical one.
3. Alpha, the false positive rate accepted, and whether the test is one-sided or two-sided.
4. Power, the probability of detecting the MDE if it is real.

Then compute the sample size per arm:

```
python3 scripts/stats_tools.py samplesize 0.10 0.02 --alpha 0.05 --power 0.8
3841 per arm, 7682 total (baseline 0.1000, target 0.1200, alpha 0.05 two-sided, power 0.8)
```

The script uses the pooled normal approximation stated in its docstring. Other calculators use an
unpooled variant or a continuity correction and give slightly different figures, so name the formula
when reporting.

The sample needed scales with one over the MDE squared. Halving the MDE roughly quadruples the sample.
Divide the total by the eligible traffic per day to get the duration, and round up to whole weeks if
behaviour differs by day of week.

If the duration is impractical, the options are a larger MDE, a more sensitive metric, or not running
the test. Running it anyway and reading "no significant difference" as "no effect" is the failure.
An underpowered null result is inconclusive.

## During the test: peeking and optional stopping

A fixed sample test is valid only if analysed once, at the planned sample size. Checking the p value
repeatedly and stopping the first time it drops below 0.05 raises the false positive rate above 0.05,
and the more often you look, the higher it goes.

If early looks are needed, use a method built for them and choose it in advance:

- Group sequential designs with a pre-set number of looks and adjusted boundaries (O'Brien-Fleming or Pocock).
- Always-valid inference such as the mixture sequential probability ratio test, described in Johari, Pekelis and Walsh, "Always Valid Inference: Bringing Sequential Analysis to A/B Testing".

To see the inflation for a specific plan, simulate it: generate A/A data with no true difference, apply
the peeking schedule, and count how often it declares a winner.

Stopping early for harm, meaning a guardrail metric breaks badly, is fine. It is a safety decision,
not a claim about the effect.

## Sample ratio mismatch

If the design splits traffic 50/50 and the arms came out visibly unequal, the assignment or logging is
broken: bots filtered in one arm, a redirect that loses users, a crash in one variant. The effect
estimate is then unreliable regardless of its p value.

Check it with a binomial test of the observed counts against the designed split:

```
python3 - <<'PY'
from statistics import NormalDist
import math
n_a, n_b, share_a = 50412, 49210, 0.5          # counts per arm, designed share for A
n = n_a + n_b
z = (n_a - n * share_a) / math.sqrt(n * share_a * (1 - share_a))
print("z %.2f, p %.3g" % (z, 2 * (1 - NormalDist().cdf(abs(z)))))
PY
```

The counts in that example are illustrative. Kohavi, Tang and Xu recommend a strict threshold for this
check because it runs on every experiment; find the root cause of any mismatch before reading the
result.

## After the test: reading the result

Two proportions:

```
python3 scripts/stats_tools.py ztest 100 1000 130 1000
```

Report the difference with its confidence interval, not only the p value. A significant result with an
interval from 0.1 to 5.9 points says something different from one from 2.9 to 3.1.

One proportion, such as a conversion rate or an error rate on a small sample:

```
python3 scripts/stats_tools.py wilson 8 10
proportion 0.8000, 95% Wilson interval 0.4902 to 0.9433
```

The Wilson interval behaves far better than the textbook normal interval (p plus or minus 1.96 standard
errors) at small n and near 0 or 1, where the normal interval can run below 0 or above 1.

## Confidence interval interpretation

A 95 percent confidence interval comes from a procedure that captures the true value in 95 percent of
repeated experiments. For one computed interval, the true value is either inside or not. Saying "95
percent probability the true value is in this interval" is a Bayesian credible interval statement and
needs a prior.

Overlapping intervals for two groups do not show that the difference is non-significant. Compute the
interval for the difference directly.

An interval that includes zero does not show the effect is zero. It shows the data cannot distinguish
the effect from zero at this sample size, and the width says how large an effect is still possible.

## Many comparisons

Every extra metric, segment, or variant is another chance of a false positive. With twenty independent
true nulls at 0.05, the chance of at least one false positive is 1 - 0.95^20, about 64 percent.

Bonferroni controls the family-wise error rate, the chance of any false positive: test each at alpha
divided by the number of tests. Simple and conservative, and it costs power when the tests are many.

Benjamini-Hochberg controls the false discovery rate, the expected share of false positives among the
results declared significant. Less conservative, and suited to screening many metrics or segments:

```
python3 scripts/stats_tools.py bh 0.01 0.04 0.03 0.20 --fdr 0.05
```

Segments found after the fact ("it worked for mobile users in Germany") are hypotheses for the next
test, not findings from this one.

## Monte Carlo estimation

For a quantity that is a product of uncertain inputs (a Fermi estimate, a market size, a capacity
plan), sample every input from its range and look at the spread of the product:

```
python3 scripts/stats_tools.py montecarlo 1e6:5e6 0.01:0.05 20:40 --seed 1
python3 scripts/stats_tools.py montecarlo 100:200:400 0.1:0.2:0.5 --dist triangular --seed 1
```

Log-uniform (`low:high`) suits inputs where each order of magnitude inside the range is equally
plausible. Triangular (`low:mode:high`) suits inputs with a best guess. Report the 5th to 95th
percentile, and pass `--seed` so the run is reproducible.

The simulation assumes the inputs are independent. If two inputs move together (price and volume,
for example), the real spread differs, and the report has to say so.
