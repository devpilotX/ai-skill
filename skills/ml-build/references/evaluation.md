# Evaluating generative output

Generative systems fail differently from classifiers. The output is open ended, so there is no single
correct answer to compare against, and that is used as an excuse to skip evaluation. It is not a valid
excuse.

## Build the set before the system

Start with twenty to fifty real inputs before writing a prompt. Real means from actual users or from the
documents the system will face, not invented examples, which are usually easier than reality.

That is enough to find failure patterns, and not enough to measure anything. A pass rate on a small set
has a wide confidence interval. At 80 percent passing, the 95 percent Wilson score interval is:

| Items | Passed | 95 percent interval | Half width, points |
|---|---|---|---|
| 20 | 16 | 58.4 to 91.9 | about 17 |
| 50 | 40 | 67.0 to 88.8 | about 11 |
| 100 | 80 | 71.1 to 86.7 | about 8 |
| 200 | 160 | 73.9 to 85.0 | about 5.5 |
| 500 | 400 | 76.3 to 83.3 | about 3.5 |
| 1000 | 800 | 77.4 to 82.4 | about 2.5 |

Computed with the Wilson score interval, z = 1.96:

```
centre = (p + z*z/(2n)) / (1 + z*z/n)
half   = z * sqrt(p*(1-p)/n + z*z/(4*n*n)) / (1 + z*z/n)
```

So at fifty items, a drop from 80 to 72 percent is inside the noise. Grow the set to hundreds of items
before using it to gate regressions, and compute the interval for your own n and pass rate instead of
reading it off this table.

For each input, write what a good output contains and what disqualifies it. Not a model answer, since
there are many acceptable outputs, but the properties that decide.

Include these deliberately, because a random sample will miss them: the input where the answer is not
available, the ambiguous input, the adversarial input, the input in another language, the very long
input, and the input that looks like a previous case but differs in one detail.

Keep a frozen subset you never iterate against, or the prompt gets tuned to the test.

## Score with a rubric

Convert judgement into checkable items, because an overall quality rating is not reproducible between
runs or between people.

Factual correctness against the source, with any unsupported claim counted as a failure rather than a
deduction.

Completeness against the required elements listed for that input.

Format compliance, which is machine checkable and worth automating first.

Refusal behaviour, meaning it declines when it should and does not decline when it should not.

Safety, meaning the outputs the product must never produce.

Score each item as pass or fail. Partial credit hides regressions, because a drop from excellent to
adequate looks like noise.

## Automate what can be automated

Format, schema validity, required fields present, citation links resolving, length limits, and banned
content are all deterministic checks. Write them as a test that runs on every change.

This is the difference between an evaluation you run and one you intend to run.

## Using a model as a judge

Workable, with three conditions, and misleading without them.

Give the judge the rubric and the source material, not only the output. A judge without the source is
guessing about factual correctness.

Calibrate it against human scores on a sample, and treat thirty items as a floor, not a target. A judge
whose agreement with a person is unknown produces a number nobody should act on.

Raw agreement misleads when one outcome dominates. If 90 percent of outputs pass, a judge that always says
pass agrees with the human 90 percent of the time and has learned nothing. Report Cohen's kappa, which
corrects for chance agreement, and agreement per class: how often the judge catches the failures the human
found, and how often it passes what the human passed. Sample enough failures for the per class number to
mean something.

Watch for the known biases: preference for longer answers, preference for confident tone, preference for
its own family of outputs, and position bias when comparing two candidates. Randomise the order and
report it.

Errors correlate when the generator and judge share a model family, even with different prompts, because
they share training data and blind spots. Use a judge from a different family where possible, and keep a
human check on a sample either way.

## Regression discipline

Run the full set on every prompt, model or retrieval change. A prompt change that fixes one case and
breaks four is common and invisible without this.

Record the score with the exact configuration, meaning model version, prompt version, retrieval settings
and temperature. A score with no configuration is not reproducible.

Watch the variance. Run the set more than once at non-zero temperature, since a single run conflates
improvement with sampling noise.

When a provider updates a model behind an unpinned identifier, your system changed without a commit. Pin
the version where possible, and re-run the set when you move.

## Reporting honestly

Give the sample size every time. A result on twelve examples is a direction, not a measurement.

Give the pass rate per category rather than only overall, because a good average often hides one broken
category.

List the failures with what went wrong, since that list is what the next change should be aimed at.

State what the set does not cover. Every evaluation set has holes, and naming them prevents the number
being read as a guarantee.

Never report an improvement that is smaller than the run to run variance.

## Comparing two systems

Run both on the same items and use a paired test, which is far more sensitive than comparing two separate
intervals. For pass or fail items, McNemar's test uses only the items where the two systems disagree:
with b items that only A passed and c that only B passed, the test asks whether b and c differ more than
chance allows. When b plus c is small, use the exact binomial version. For scores that are not pass or fail, or for metrics computed over the whole set such as F1, use
a paired bootstrap: resample items with replacement, recompute the difference on each resample, and
report the interval of the differences. Report the number of discordant items, since a large set with
three disagreements shows very little.

## Ceiling checks for retrieval systems

Measure retrieval alone: for each question, does the correct passage appear in the results at all, and at
what position. This sets the maximum achievable answer quality.

When that number is low, work on chunking, indexing, reranking and query handling. Prompt work at that
point cannot help.

Test the case where the corpus does not contain the answer. The required behaviour is an explicit
statement that it is not known, and the failure mode is a fluent invention.
