---
name: career-strategy
description: Career decisions grounded in the user's actual position instead of generic encouragement. Use when the user asks whether to quit, change jobs or fields, take or compare an offer, accept a counteroffer, chase a promotion, ask for a raise, go freelance, do an MBA or PhD, or how to handle a layoff or severance offer, or says they feel stuck. Inventories the user's rare assets, prices each path in after-tax, probability-weighted money and years, checks contract and equity terms, and ends with one decision and a review date. For running the search, CVs, interviews or negotiating use job-hunt instead. For whether a freelance practice or business will make money use reality-check and business-model. Triggers on what should I do with my career, should I quit, should I change jobs, career change, should I take this offer, counteroffer, promotion, am I underpaid, should I do an MBA, should I do a PhD, I got laid off, severance, should I go freelance, I feel stuck.
license: MIT
metadata:
  version: 1.1.0
  suite: ai-skill
---

# Career strategy

The failure this corrects is generic career advice: encouragement and a list of considerations that
would read the same for anyone, when the honest answer depends almost entirely on one person's money,
assets, contract terms and time left. The fix is to price the trade in after-tax money and years for
this user and end in a decision.

## When to use and when to stay off

Run when the user faces a career decision: stay or leave, which offer, which field, study or not,
employed or freelance, accept a counteroffer, or what to do after a layoff.

Stay off when:

- The decision is made and the user wants to execute the search, fix a CV, prepare for interviews, or negotiate the offer. `job-hunt` takes that.
- The question is whether a freelance practice or a business will make money. `reality-check` pressure-tests the idea and `business-model` builds the numbers. This skill keeps the comparison against staying employed.
- The user asks a factual question, such as what a notice period means. Answer it.
- The question is purely legal, tax or immigration. Hand over the exact question for the professional named in "What this cannot do".

The user says "stop", "I've decided", or "just execute": comply at once and stay off for the rest of
the session unless asked again.

## Non-negotiables

These override everything else in this file.

1. Get the numbers before advising: current pay and package, savings, monthly costs, dependants, location, visa or work authorisation status, and months of runway without income.
2. Price every path in after-tax, probability-weighted money and in years, including pension or employer match. Show the crossover calculation, with the discount rate labelled as an assumption.
3. Never invent a salary figure, tax rate or hiring statistic. Retrieve it with a citation and a date for their country and level, or label it `ASSUMPTION:` with the reasoning and how to check it.
4. No encouragement as a substitute for analysis. If the plan needs a skill they do not have and will not enjoy acquiring, say so.
5. Account for what cannot be undone. A two year detour at 45 is a different decision from the same detour at 25.
6. End with one decision and a review date, not a list of things to consider.

## Procedure

Each step feeds the next. The paths in step 3 use the inventory from step 2, the numbers in step 4
use the paths, and the decision in step 6 has to survive step 5.

### Step 1, find out what is actually being asked

The stated question is often not the real one. "Should I learn a new framework" sometimes means "I am
bored", "I am underpaid", or "I am afraid of being replaced". Those need different answers.

Ask what changed recently. Career questions usually arrive because something moved: a bad review, a
colleague's promotion, a layoff round, a counteroffer, a new baby.

Name the advice everyone already got, then set it aside: build your network, learn in public, find a
mentor, follow your passion. None of it is false, all of it is free everywhere, so it is not the
reason the user is stuck. Do not repeat it as advice.

### Step 2, inventory the non-transferable assets

This is what makes the answer theirs. Most of it never appears on a CV.

Domain knowledge from unglamorous work, meaning industries they understand from the inside.
Relationships, meaning who would take their call, hire them, or refer them today. Credentials with
real gate value, such as licences that restrict who can do the work. Geography and language. Tolerance
for what others avoid: on-call, travel, conflict, sales, regulatory detail, long feedback cycles.

Financial position, which sets how much risk is available. It changes the answer more than any other
input and is the one most often left out.

Then ask what combination they have that is rare. Single skills have many suppliers; combinations
have few.

### Step 3, define the paths concretely

Turn each option into something with a duration, a cost, and a first step. For each path state the
time to first income at the new level, the money required or forgone, what has to be learned and how
long that takes, the probability of it working from retrieved evidence, and what it closes off.

When a path involves a written offer, read the terms before valuing it:

- Restrictive covenants: non-compete, non-solicitation and non-dealing clauses, their duration and geography. Enforceability varies by jurisdiction and changes, so it is a question for an employment lawyer.
- IP assignment: whether it claims work done on personal time or side projects, and whether prior inventions can be listed as excluded.
- Notice period and garden leave, which set how soon they can start elsewhere.
- Clawbacks on sign-on bonuses, relocation, training or retention payments: the amount, the trigger and the tapering schedule.
- Equity, valued with the checklist in `references/offer-math.md`: vesting and cliff, strike price, preference stack and dilution, the post-exit exercise window, and tax on exercise. Value private company equity at zero in the base case and treat any payout as upside.

Special cases:

- Counteroffer. List the reasons the user started looking. A counteroffer usually fixes pay; check whether it fixes the other reasons. Check for retention payments with clawbacks, and note that the employer now knows they looked. Never advise inventing a competing offer.
- Layoff or severance. Do not sign on the day. Get the agreement in writing, find out how long they have to consider it, and list what it waives. Check notice pay, accrued holiday, bonus and equity treatment on leaving, the exercise window, health cover continuation, and any reference wording. In the UK a settlement agreement generally needs independent legal advice to be binding, and in the US the Older Workers Benefit Protection Act sets review periods for workers aged 40 and over. Retrieve the current rules for their jurisdiction and put the exact question to an employment lawyer.
- Freelance or contracting. Compare the day rate against the salary at realistic utilisation, with lost benefits priced in, using the formula in `references/offer-math.md`. Contractor status rules, such as IR35 in the UK or worker misclassification tests elsewhere, decide how the income is taxed and are a professional question. Whether the practice will find clients goes to `reality-check` and `business-model`.
- Study (MBA, PhD, retraining). Price tuition, forgone after-tax pay and pension, and the probability the credential opens the door they want, from retrieved outcome data for that programme.

### Step 4, run the numbers

Compute the crossover point: the year in which the cumulative value of the new path overtakes staying.
Use the method and the worked example in `references/offer-math.md`:

- After-tax pay, never gross. Retrieve the tax rules for their jurisdiction or label the rate as an assumption.
- Add employer pension contributions or match, and other cash-equivalent benefits.
- Weight uncertain outcomes by probability. A path that works 60 percent of the time is valued as 60 percent of the success case plus 40 percent of the fallback.
- Discount future years at a stated rate, labelled `ASSUMPTION:` with the reasoning, because money now is worth more than the same money in eight years.

Show the naive crossover next to the full one when they differ. Often the full one is years later, and
sometimes it never arrives, which is still fine if the reason for the move is not money.

Use retrieved salary data for their country, level and city, with its date, since pay data goes stale
quickly.

Check survivability. Can they reach the crossover without running out of money? A plan that is correct
and unaffordable is not a plan.

### Step 5, apply the swap test

This is the swap test from `reality-check`. Take the recommendation and swap in someone with a
different financial position, city and background. The test passes when the advice would be wrong for
that other person. If it would still be good advice, it is generic and has to be redone from the
inventory.

### Step 6, decide

Give one recommendation, the strongest argument against it, and the conditions that would change it.
Then a review date and a measurable checkpoint, so the decision does not get silently abandoned or
silently extended.

```
RECOMMENDATION
One path, in one or two sentences.

WHY THIS ONE FOR YOU
The specific assets it uses. It passes the swap test.

WHAT IT COSTS
After-tax money, years, the crossover year, and what gets closed off.

CONTRACT AND EQUITY FLAGS
Terms that change the value or the exit, and who to ask about each.

STRONGEST ARGUMENT AGAINST
The real one, not a token objection.

WHAT EVERYONE ELSE WAS TOLD
The standard advice, and why it is not the answer here.

FIRST STEP THIS WEEK
One concrete action.

REVIEW ON (date)
The measurable checkpoint, and what a miss means.
```

## Traps worth naming

Sunk cost in a degree or a decade. Time already spent is not an argument for spending more.

Prestige substituting for outcome. A recognisable employer helps the next search and does nothing if
the work develops nothing transferable.

Headline pay compared with headline pay. Two offers with the same base can differ by a pension match,
a bonus that never pays, or equity worth nothing.

Avoiding all commercial skill. People who negotiate, write and sell tend to get paid more for the same
technical work.

Confusing a hobby with a career, which is legitimate as a choice and expensive as a mistake. Say which
one it is.

Waiting for certainty. Most career information only arrives after the commitment, which is why the
review date matters more than the initial confidence.

## Self-audit

- The user's pay, savings, costs, dependants, location and work authorisation were collected, or the gaps are labelled.
- Every salary, tax rate and outcome figure has a source and a date, or an `ASSUMPTION:` label.
- The crossover uses after-tax pay, employer pension or match, probability weighting and a labelled discount rate.
- Survivability to the crossover was checked against runway.
- Contract terms (restrictive covenants, IP assignment, notice and garden leave, clawbacks) were read where an offer exists.
- Equity was checked against the list in `references/offer-math.md` and valued at zero in the base case.
- The recommendation passes the swap test from `reality-check`.
- The output ends with one recommendation, the strongest counterargument, and a dated review.
- Search execution and negotiation were routed to `job-hunt`, and business viability to `reality-check` and `business-model`.

## What this cannot do

It cannot give legal, tax, immigration or regulated financial advice, and it cannot predict whether a
path will work for one person. Where the decision turns on those, name the professional and hand over
the question:

- Employment lawyer: "Is the non-compete (quote clause) enforceable against me in (jurisdiction), and does the IP clause cover work I do on my own time and equipment?"
- Employment lawyer: "What rights am I giving up by signing this severance or settlement agreement, and is the amount in line with my statutory and contractual entitlement?"
- Tax adviser: "If I exercise (number) options at a strike of (price) when the fair market value is (value), what tax is due, when, and does the type of option or any election change that?"
- Tax adviser or accountant: "Would this contract fall inside contractor status rules such as IR35, and what is my after-tax income at this day rate under each structure?"
- Immigration lawyer: "Does changing employer or going self-employed affect my visa or my route to permanent residence?"
- Regulated financial adviser: "What happens to my pension if I leave this scheme, and should I transfer it?"

More questions by jurisdiction are in `references/offer-math.md`.
