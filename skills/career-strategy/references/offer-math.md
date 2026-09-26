# Offer maths

Formulas and checklists for comparing offers, equity, freelance rates and career paths. Every input is
either retrieved with a source and a date, or labelled `ASSUMPTION:`. The figures in the worked examples
are illustrative assumptions, not market data.

## Total compensation comparison

Compare offers on the same annual basis, line by line:

| Component | How to value it |
|---|---|
| Base pay | After tax, using retrieved rules for the jurisdiction |
| Bonus | Target times the historical payout rate, if the employer will share it. A discretionary bonus with no history is worth zero in the base case |
| Employer pension or retirement match | Cash value of the employer contribution, including any vesting schedule on the match |
| Equity | Zero in the base case for private companies. See the checklist below |
| Sign-on, relocation, retention | Divide by the clawback period, and note the clawback trigger |
| Health, life and disability cover | What the user would pay to buy the same cover privately |
| Holiday | Extra days times the daily rate |
| Commute, remote allowance, equipment | Annual cash cost or saving |
| Training budget | Only if the user would spend that money anyway |

Then list the non-cash terms that change the value or the exit: notice period, garden leave,
non-compete, IP assignment, probation, and on-call.

## Equity checklist

Ask the employer for each item in writing. A refusal to answer is information.

1. Instrument: options (and which type), restricted stock units, restricted stock, or phantom or growth shares.
2. Number of units and the fully diluted share count, so the percentage ownership can be computed.
3. Vesting schedule and cliff. What happens to unvested equity on dismissal, resignation, acquisition, or change of control (single or double trigger acceleration).
4. Strike or exercise price, and the most recent valuation used to set it.
5. Preference stack: total investment raised, the liquidation preference multiple, and whether preferences are participating. Common shareholders are paid after the stack, so an exit below the stack can pay common holders nothing.
6. Dilution: expected future rounds and the size of the option pool top-up.
7. Post-exit exercise window: how long after leaving the user has to exercise, and what exercising all vested options would cost in cash plus tax.
8. Liquidity: whether there are secondary sales or tender offers, and any transfer restrictions.
9. Tax on grant, vesting, exercise and sale. Rules differ by instrument and country and change often, so put the exact question to a tax adviser: "If I exercise (number) options at a strike of (price) when the fair market value is (value), what tax is due, when, and would any election or scheme change that?"

## Freelance day rate against salary

The rate has to replace salary, benefits and business costs across the days that actually get billed.

```
available days  = working days in the year - holiday - public holidays - sick days
billable days   = available days x utilisation
required rate   = (target salary + value of lost benefits + business costs) / billable days
```

Utilisation is the share of available days that are paid. Selling, admin, gaps between contracts and
training all come out of it, so it is well below 100 percent.

Worked example, all figures `ASSUMPTION:` for illustration:

- Working days 260, holiday 25, public holidays 8, sick days 5, so 222 available days.
- Utilisation 70 percent, so 155 billable days (222 x 0.7 = 155.4, rounded down).
- Target salary 60,000, lost employer pension 3,000, other lost benefits 2,000, business costs 4,000 (insurance, accounting, equipment). Total 69,000.
- Required day rate 69,000 / 155 = 445.16 before any difference in tax.

The tax on that income depends on structure and on contractor status rules, which is a question for an
accountant or tax adviser. In the UK, HMRC publishes
[Understanding off-payroll working (IR35)](https://www.gov.uk/guidance/understanding-off-payroll-working-ir35).
Elsewhere, retrieve the local worker classification rules from the tax authority.

## Crossover formula

For each year t from 1 to N:

```
V_stay(t)   = after-tax pay + employer pension or match + cash benefits, staying
V_switch(t) = p x V_success(t) + (1 - p) x V_fallback(t) - one-off costs in year t
D(t)        = 1 / (1 + r)^t
gap(N)      = sum over t of (V_switch(t) - V_stay(t)) x D(t)
```

The crossover year is the first N where gap(N) is above zero. p is the probability the path works, from
retrieved evidence where possible. r is the discount rate, labelled `ASSUMPTION:` with the reasoning, for
example the return the user could earn on savings, or the interest rate on debt they carry.

### Worked example

All inputs are `ASSUMPTION:` for illustration.

- Stay: 42,000 after tax plus 3,000 employer pension, so 45,000 in year 1, growing 2 percent a year.
- Switch, years 1 and 2: 28,000 after tax plus 1,000 pension, so 29,000, with a course fee of 8,000 in year 1.
- Switch success from year 3: 55,000 after tax plus 4,000 pension, so 59,000, growing 3 percent a year.
- Switch fallback from year 3: back to the stay path.
- p = 0.6, r = 4 percent.

Computed with Python `decimal`, cumulative gap by year (negative means the switch is still behind):

| Year | Naive (p = 1, r = 0) | p = 1, r = 4% | p = 0.6, r = 0 | Full (p = 0.6, r = 4%) |
|---|---|---|---|---|
| 1 | -24,000 | -23,077 | -24,000 | -23,077 |
| 2 | -40,900 | -38,702 | -40,900 | -38,702 |
| 3 | -28,718 | -27,872 | -33,591 | -32,204 |
| 4 | -15,702 | -16,746 | -25,781 | -25,529 |
| 5 | -1,819 | -5,335 | -17,451 | -18,682 |
| 6 | 12,969 | 6,352 | -8,579 | -11,670 |
| 7 | 28,696 | 18,303 | 858 | -4,499 |
| 8 | 45,403 | 30,510 | 10,882 | 2,826 |

The naive calculation crosses over in year 6. With probability weighting and discounting it crosses in
year 8. The user also has to survive a cumulative shortfall of about 38,700 in present value by the end of
year 2, which is the survivability check.

The script used:

```python
from decimal import Decimal as D

def gap_by_year(r, p, years=8):
    stay_pv = switch_pv = D(0)
    rows = []
    for t in range(1, years + 1):
        stay = D(45000) * D("1.02") ** (t - 1)
        if t <= 2:
            switch = D(29000) - (D(8000) if t == 1 else D(0))
        else:
            switch = p * D(59000) * D("1.03") ** (t - 3) + (1 - p) * stay
        factor = 1 / (1 + r) ** t
        stay_pv += stay * factor
        switch_pv += switch * factor
        rows.append((t, (switch_pv - stay_pv).quantize(D(1))))
    return rows

print(gap_by_year(D("0.04"), D("0.6")))
```

## Professional questions by jurisdiction

Rules in this section change. Retrieve the current position from the named authority before relying on
any of it, and put the question to a professional licensed in the user's jurisdiction.

United Kingdom:

- Tax adviser: "Is this share scheme tax-advantaged (for example EMI), and what tax and National Insurance is due on grant, exercise and sale?"
- Tax adviser: "Would this engagement fall inside IR35, and who decides status under the current off-payroll rules?"
- Employment solicitor: "Is this restrictive covenant enforceable, and how does garden leave interact with it?"
- Employment solicitor: "Does this settlement agreement meet the requirements to be binding, and what am I waiving?"
- Regulated financial adviser: "How does leaving this pension scheme or reducing contributions affect my annual allowance and retirement income?"

United States:

- Tax adviser: "Are these ISOs or NSOs, what is the ordinary income and AMT exposure if I exercise now, and should I consider an 83(b) election for early-exercised shares?"
- Employment attorney: "Is this non-compete enforceable in my state, and does the invention assignment clause comply with state limits on claiming personal-time inventions?"
- Employment attorney: "Does this severance agreement give me the review and revocation periods required for my age and the size of the layoff?"
- Tax adviser: "Would I be classed as an employee or an independent contractor for this work, and what does that change about my tax and benefits?"

European Union and elsewhere:

- Tax adviser: "How is employee equity taxed here on grant, vesting, exercise and sale, and does moving country before a sale change it?"
- Employment lawyer: "Is a post-termination non-compete valid here without compensation during the restricted period?"
- Tax adviser: "What are the tests for self-employed status here, and what social contributions would I owe as a contractor?"
- Immigration lawyer, in any country: "Does changing employer, role or working as self-employed affect my permit, and what notice do I have to give?"
