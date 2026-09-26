# Quantitative traps

Errors that recur in business, engineering, and reported statistics. Experiment design and A/B tests
have their own file, `references/experiments.md`.

## Percentages

Percentage against percentage point. Moving from 4 percent to 6 percent is two percentage points and a
fifty percent increase. Reporting one as the other is a frequent misstatement in
business writing.

Percentage of which base. A 20 percent discount followed by a 20 percent increase does not return to
the original. Order matters, and the base changes.

Percentages that cannot be averaged. A 50 percent conversion rate on 10 visitors and 10 percent on 1000
is not a 30 percent average. Weight by the denominator.

Growth compounding. Ten percent a month is not 120 percent a year, it is about 214 percent
(1.1 to the power 12 is 3.138). Check
whether a rate is simple or compound before using it.

Percentages above 100, which are fine for growth and impossible for a share of a whole. A share above
100 means double counting.

Change from a small base, where a large percentage means very little. Two to four customers is a
hundred percent increase and two customers.

## Averages and distributions

The mean on a skewed distribution misleads. Income, revenue per customer, response time, and file size
are all skewed, and the median is usually the honest summary.

A high percentile matters more than a mean for anything a user experiences. Average latency hides the
slow requests that cause complaints. Report the 95th or 99th percentile.

Simpson's paradox. A trend present in every subgroup can reverse when the groups are pooled. Check
subgroups before believing an aggregate.

Averaging over the wrong unit. Average revenue per user depends heavily on whether the denominator is
signups, active users, or paying users. State which.

Survivorship. Averaging the customers who stayed excludes the ones who left, which is usually the
number that matters.

## Rates and ratios

The denominator has to be the population at risk. A churn rate needs the customers who could have
churned, not total ever.

Rates over different periods cannot be compared without converting, and converting a monthly rate to
annual is not multiplication by twelve for anything compounding.

Ratios of small numbers are unstable. A change from 1 to 2 in the numerator moves the ratio wildly and
means almost nothing.

Per capita and per unit figures need the same time window on both sides.

Cohort against snapshot. A snapshot retention figure mixes cohorts of different ages and usually flatters
the number. Cohort it.

## Statistical claims

Significance is not size. A p value is the probability of data at least as extreme as what was
observed, assuming the null hypothesis is true. It is not the probability that the null hypothesis is
true, and it says nothing about how large or important the effect is. Report the effect size and a
confidence interval.

Sample size determines what can be concluded. Ask for it every time. A result with no stated sample size
is not a result.

Multiple comparisons. Testing twenty independent true nulls at the 0.05 threshold gives one false
positive on average, and the chance of at least one is 1 - 0.95^20, about 64 percent. Ask how many
comparisons were made, and adjust with Bonferroni or Benjamini-Hochberg as described in
`references/experiments.md`.

Selection. Who was excluded, who did not respond, and who never got asked. Nonresponse is rarely random.

Regression to the mean, which makes any intervention applied to extreme cases look effective.

Correlation without causation, and the specific version worth naming: a third factor causing both. Never
convert a correlational finding into a recommendation without saying it is correlational.

Base rates. A test with 99 percent accuracy for a condition affecting one in ten thousand people
produces far more false positives than true ones. Work the actual numbers rather than trusting the
accuracy figure.

## Money

Use decimal arithmetic, not binary floating point. Financial arithmetic in floating point accumulates
error that becomes visible in totals and reconciliations.

Nominal against real. Comparing figures across years without adjusting for inflation is comparing
different units.

Currency conversion needs a date, since the rate moved.

Gross against net, and which costs are inside which. Most margin disputes are definition disputes.

Cash against accrual. A profitable month with no cash is normal and it is also how businesses fail.
Model the timing, not just the totals.

Value added tax and sales tax are not revenue. They are collected for the tax authority and passed on.
Including them in the top line inflates revenue and understates margin percentage, so exclude them.

Annual recurring revenue computed from one good month is an extrapolation, so label it as one.

Sunk cost has no place in a forward looking calculation, however much was spent.

## Estimation

When an exact figure is unavailable, estimate deliberately rather than guessing. Decompose into
quantities that can be bounded and estimate each with a range.

Do not multiply all the lows together and all the highs together. That range is reached only if every
input sits at the same extreme at once, so with four inputs each spanning a factor of ten the result
spans a factor of ten thousand and tells the reader nothing. For a point estimate, take the geometric
midpoint of each range (the square root of low times high) and multiply those. For the range, run a
Monte Carlo simulation with `scripts/stats_tools.py montecarlo`, which samples each input and reports
the 5th and 95th percentiles of the product. State that it assumes the inputs are independent.

State the answer as a range, never as a false point estimate.

Check against a known anchor. If the estimate implies more customers than exist in the country, it is
wrong.

Say which input the estimate is most sensitive to, because that is what to verify first.

## Reading someone else's model

Find the circular reference, meaning an output that feeds one of its own inputs.

Find the hardcoded number with no source, which is where the desired conclusion usually got inserted.

Check that the growth assumption is not the whole result. A model where revenue depends mostly on an
assumed growth rate is a statement about the assumption, not about the business.

Check the terminal period, since a large share of the total often sits in whatever happens after the
explicit forecast.

Test what happens when the best case input becomes the base case input, which is the substitution people
make without noticing.

Run every input to zero once. Models often fail to behave sensibly at zero, which reveals a structural
error.

## Floating point beyond money

Catastrophic cancellation. Subtracting two nearly equal floats keeps the rounding error and loses the
significant digits. Computing a variance as the mean of squares minus the square of the mean is the
classic case. Use `statistics.variance`, a two pass formula, or rearrange the expression algebraically.

Summation order. Float addition is not associative, so the same numbers summed in a different order
can give a different total, and adding small values to a large running total loses them. In Python,
`sum([0.1] * 10)` gives 0.9999999999999999 while `math.fsum([0.1] * 10)` gives 1.0. Use `math.fsum`
for any sum that matters.

Equality. Never compare floats with `==`. Use `math.isclose` with a tolerance chosen for the problem.

Large integers. Values above 2^53 lose integer precision in a double, which affects identifiers and
counters passed through JavaScript or JSON parsers that use doubles.

## Spreadsheets

Ranges not extended. A `SUM` over rows 2 to 50 silently ignores rows added below 50. Check that every
total covers the whole data range, and prefer whole column references or tables.

Absolute against relative references. A formula copied down with `B2` where `$B$2` was meant shifts the
reference row by row. Spot check the last copied cell, not the first.

Hidden rows and columns, and filtered views. `SUM` includes hidden rows, `SUBTOTAL` with the right code
excludes them. Unhide everything before auditing.

Text stored as numbers. A number imported as text is skipped by `SUM` and sorts wrongly. Look for left
aligned numbers or the warning marker, and convert explicitly.

Date serials. Spreadsheets store dates as day counts from an epoch, and Excel keeps a 1900 leap year
bug for compatibility with Lotus 1-2-3 while its Mac 1904 date system starts elsewhere. Dates pasted
between workbooks or parsed as text can shift by years or swap day and month. Check a few dates by
hand.

Hardcoded overrides. A number typed over a formula in one cell of a column of formulas. Check that
formulas are consistent along each row or column.
