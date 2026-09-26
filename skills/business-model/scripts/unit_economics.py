#!/usr/bin/env python3
"""Unit economics arithmetic with exact decimal money.

Every figure is computed with decimal.Decimal, so money never passes through
binary floating point. Each subcommand prints labelled lines that can be pasted
into a report next to the inputs that produced them.

Usage:
  python3 unit_economics.py contribution --price 120 --variable-cost 38 --variable-cost 6.5
  python3 unit_economics.py contribution --price 120 --vat-rate 0.20 --variable-cost 38
  python3 unit_economics.py breakeven --fixed 9000 --contribution 45.50
  python3 unit_economics.py ccc --inventory-days 45 --receivable-days 60 --payable-days 30 \
      --monthly-cogs 20000 --monthly-revenue 50000
  python3 unit_economics.py payback --cac 300 --monthly-contribution 25
  python3 unit_economics.py ltv --monthly-contribution 25 --churn 0.05 --months 36
  python3 unit_economics.py ltv --monthly-contribution 25 --retention 1 0.8 0.7 0.65 --cac 60
  python3 unit_economics.py peak-funding --flows -12000 -8000 -3000 2000 6000 9000

Definitions:
  contribution   net price minus variable cost per unit. With --vat-rate the price
                 is treated as VAT inclusive and the tax is removed first.
  breakeven      fixed cost per period divided by contribution per unit, rounded up.
  ccc            cash conversion cycle = DIO + DSO - DPO in days. Cash tied up =
                 inventory days x daily COGS + receivable days x daily revenue -
                 payable days x daily COGS, with daily = monthly x 12 / 365.
  payback        CAC divided by monthly contribution per customer.
  ltv            sum of monthly contribution weighted by the fraction of the cohort
                 still paying. A constant monthly churn c gives retention (1-c)^t.
  peak-funding   the deepest point of cumulative cash from a list of monthly net
                 cash flows, which is the funding the plan needs before it pays back.

Exit codes:
  0  computed
  2  invalid input, such as a negative day count or a churn outside 0 to 1
  3  no finite answer: contribution is zero or negative, so break-even or payback
     never arrives, or a cohort never recovers its CAC inside the retention data
"""

from __future__ import annotations

import argparse
import sys
from decimal import ROUND_CEILING, ROUND_HALF_UP, Decimal, InvalidOperation, getcontext

getcontext().prec = 28

CENT = Decimal("0.01")
TENTH = Decimal("0.1")
DAYS_PER_YEAR = Decimal(365)
MONTHS_PER_YEAR = Decimal(12)

EXIT_OK = 0
EXIT_INPUT = 2
EXIT_NO_ANSWER = 3


class NoAnswer(Exception):
    """The inputs are valid but the quantity has no finite value."""


def money(value: Decimal) -> str:
    return str(value.quantize(CENT, rounding=ROUND_HALF_UP))


def one_dp(value: Decimal) -> str:
    return str(value.quantize(TENTH, rounding=ROUND_HALF_UP))


def pct(value: Decimal) -> str:
    return one_dp(value * 100) + "%"


def dec(text: str) -> Decimal:
    try:
        value = Decimal(text)
    except InvalidOperation:
        raise argparse.ArgumentTypeError("not a number: %r" % text)
    if not value.is_finite():
        raise argparse.ArgumentTypeError("not a finite number: %r" % text)
    return value


def contribution(price: Decimal, variable_costs: list[Decimal],
                 vat_rate: Decimal | None = None) -> dict:
    """Contribution per unit. A VAT inclusive price is converted to net first."""
    if price < 0 or any(c < 0 for c in variable_costs):
        raise ValueError("price and variable costs must not be negative")
    net = price
    vat = Decimal(0)
    if vat_rate is not None:
        if vat_rate < 0 or vat_rate >= 1:
            raise ValueError("vat rate is a fraction such as 0.20, between 0 and 1")
        net = price / (1 + vat_rate)
        vat = price - net
    variable = sum(variable_costs, Decimal(0))
    unit = net - variable
    margin = unit / net if net else Decimal(0)
    return {"net_price": net, "vat": vat, "variable_cost": variable,
            "contribution": unit, "margin": margin}


def breakeven(fixed: Decimal, unit_contribution: Decimal) -> Decimal:
    """Units per period needed to cover fixed cost, rounded up to a whole unit."""
    if fixed < 0:
        raise ValueError("fixed cost must not be negative")
    if unit_contribution <= 0:
        raise NoAnswer("contribution per unit is not positive, so no volume breaks even")
    return (fixed / unit_contribution).to_integral_value(rounding=ROUND_CEILING)


def cash_cycle(inventory_days: Decimal, receivable_days: Decimal, payable_days: Decimal,
               monthly_cogs: Decimal | None = None,
               monthly_revenue: Decimal | None = None) -> dict:
    """Cash conversion cycle, and the cash it ties up when monthly figures are given.

    Inventory and payables are valued at cost of goods. Receivables are valued at
    revenue, because the customer owes the selling price, not the cost.
    """
    for label, days in (("inventory", inventory_days), ("receivable", receivable_days),
                        ("payable", payable_days)):
        if days < 0:
            raise ValueError("%s days must not be negative" % label)
    out = {"ccc_days": inventory_days + receivable_days - payable_days}
    if monthly_cogs is not None and monthly_revenue is not None:
        if monthly_cogs < 0 or monthly_revenue < 0:
            raise ValueError("monthly figures must not be negative")
        daily_cogs = monthly_cogs * MONTHS_PER_YEAR / DAYS_PER_YEAR
        daily_revenue = monthly_revenue * MONTHS_PER_YEAR / DAYS_PER_YEAR
        inventory = inventory_days * daily_cogs
        receivables = receivable_days * daily_revenue
        payables = payable_days * daily_cogs
        out.update({"inventory": inventory, "receivables": receivables,
                    "payables": payables,
                    "cash_tied_up": inventory + receivables - payables})
    return out


def payback(cac: Decimal, monthly_contribution: Decimal) -> Decimal:
    """Months to recover acquisition cost from contribution, not from revenue."""
    if cac < 0:
        raise ValueError("CAC must not be negative")
    if monthly_contribution <= 0:
        raise NoAnswer("monthly contribution is not positive, so CAC is never recovered")
    return cac / monthly_contribution


def retention_from_churn(churn: Decimal, months: int) -> list[Decimal]:
    if churn < 0 or churn > 1:
        raise ValueError("churn is a monthly fraction between 0 and 1")
    if months < 1:
        raise ValueError("months must be at least 1")
    # Month 1 is the whole cohort. Decimal rejects 0 ** 0, so start the curve at 1.
    curve = [Decimal(1)]
    for _ in range(months - 1):
        curve.append(curve[-1] * (1 - churn))
    return curve


def ltv(monthly_contribution: Decimal, retention: list[Decimal],
        cac: Decimal | None = None) -> dict:
    """Lifetime contribution per acquired customer over the retention curve.

    retention[t] is the fraction of the starting cohort still paying in month t+1.
    With a CAC, also report the first month in which cumulative contribution per
    acquired customer reaches the CAC.
    """
    if not retention:
        raise ValueError("retention curve is empty")
    if any(r < 0 or r > 1 for r in retention):
        raise ValueError("retention values are fractions between 0 and 1")
    cumulative = Decimal(0)
    payback_month = None
    for month, share in enumerate(retention, start=1):
        cumulative += monthly_contribution * share
        if cac is not None and payback_month is None and cumulative >= cac:
            payback_month = month
    out = {"ltv": cumulative, "months": len(retention), "payback_month": payback_month}
    if cac is not None:
        out["ltv_to_cac"] = cumulative / cac if cac else None
    return out


def peak_funding(flows: list[Decimal], opening: Decimal = Decimal(0)) -> dict:
    """Deepest cumulative cash position from monthly net flows.

    Returns the funding needed so cash never goes below zero, the month the low
    point occurs, and the first later month in which cumulative cash is back at or
    above the opening balance.
    """
    if not flows:
        raise ValueError("no cash flows given")
    balance = opening
    low = opening
    low_month = 0
    series = []
    for month, flow in enumerate(flows, start=1):
        balance += flow
        series.append(balance)
        if balance < low:
            low, low_month = balance, month
    recovered = None
    for month in range(low_month + 1, len(series) + 1):
        if series[month - 1] >= opening:
            recovered = month
            break
    return {"peak_funding": max(Decimal(0), -low), "low_point": low,
            "low_month": low_month, "recovered_month": recovered,
            "closing": balance}


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(prog="unit_economics.py",
                                 description="Unit economics with exact decimal arithmetic.")
    sub = ap.add_subparsers(dest="command")

    p = sub.add_parser("contribution", help="contribution per unit")
    p.add_argument("--price", type=dec, required=True, help="price per unit")
    p.add_argument("--variable-cost", type=dec, action="append", default=[],
                   help="one variable cost per unit, repeat for each line")
    p.add_argument("--vat-rate", type=dec,
                   help="treat the price as VAT inclusive at this fraction, such as 0.20")

    p = sub.add_parser("breakeven", help="units per period to cover fixed cost")
    p.add_argument("--fixed", type=dec, required=True, help="fixed cost per period")
    p.add_argument("--contribution", type=dec, required=True, help="contribution per unit")

    p = sub.add_parser("ccc", help="cash conversion cycle and cash tied up")
    p.add_argument("--inventory-days", type=dec, required=True, help="DIO")
    p.add_argument("--receivable-days", type=dec, required=True, help="DSO")
    p.add_argument("--payable-days", type=dec, required=True, help="DPO")
    p.add_argument("--monthly-cogs", type=dec, help="cost of goods per month")
    p.add_argument("--monthly-revenue", type=dec, help="revenue per month, net of VAT")
    p.add_argument("--growth-multiple", type=dec, default=Decimal(3),
                   help="also report cash tied up at this multiple of revenue (default 3)")

    p = sub.add_parser("payback", help="months to recover CAC")
    p.add_argument("--cac", type=dec, required=True, help="acquisition cost per customer")
    p.add_argument("--monthly-contribution", type=dec, required=True,
                   help="contribution per customer per month, not revenue")

    p = sub.add_parser("ltv", help="lifetime contribution from a retention curve")
    p.add_argument("--monthly-contribution", type=dec, required=True,
                   help="contribution per active customer per month")
    group = p.add_mutually_exclusive_group(required=True)
    group.add_argument("--churn", type=dec, help="constant monthly churn, such as 0.05")
    group.add_argument("--retention", type=dec, nargs="+",
                       help="fraction of the cohort still paying in month 1, 2, 3 and so on")
    p.add_argument("--months", type=int, default=36,
                   help="horizon for --churn, in months (default 36)")
    p.add_argument("--cac", type=dec, help="acquisition cost, to report cohort payback")

    p = sub.add_parser("peak-funding", help="peak funding need from monthly cash flows")
    p.add_argument("--flows", type=dec, nargs="+", required=True,
                   help="net cash flow per month in order, outflows negative")
    p.add_argument("--opening", type=dec, default=Decimal(0), help="opening cash balance")
    return ap


def run(args: argparse.Namespace) -> list[str]:
    if args.command == "contribution":
        r = contribution(args.price, args.variable_cost, args.vat_rate)
        lines = []
        if args.vat_rate is not None:
            lines += ["price incl. VAT: %s" % money(args.price),
                      "VAT: %s" % money(r["vat"])]
        lines += ["net price: %s" % money(r["net_price"]),
                  "variable cost: %s" % money(r["variable_cost"]),
                  "contribution per unit: %s" % money(r["contribution"]),
                  "contribution margin: %s" % pct(r["margin"])]
        if r["contribution"] <= 0:
            lines.append("WARNING: each unit loses money, volume makes it worse")
        return lines
    if args.command == "breakeven":
        units = breakeven(args.fixed, args.contribution)
        return ["break-even units per period: %s" % units]
    if args.command == "ccc":
        r = cash_cycle(args.inventory_days, args.receivable_days, args.payable_days,
                       args.monthly_cogs, args.monthly_revenue)
        lines = ["cash conversion cycle days: %s" % one_dp(r["ccc_days"])]
        if "cash_tied_up" in r:
            lines += ["inventory at cost: %s" % money(r["inventory"]),
                      "receivables at revenue: %s" % money(r["receivables"]),
                      "payables at cost: %s" % money(r["payables"]),
                      "cash tied up: %s" % money(r["cash_tied_up"])]
            m = args.growth_multiple
            if m <= 0:
                raise ValueError("growth multiple must be positive")
            grown = cash_cycle(args.inventory_days, args.receivable_days, args.payable_days,
                               args.monthly_cogs * m, args.monthly_revenue * m)
            lines.append("cash tied up at %sx revenue: %s"
                         % (m.normalize(), money(grown["cash_tied_up"])))
        elif args.monthly_cogs is not None or args.monthly_revenue is not None:
            raise ValueError("give both --monthly-cogs and --monthly-revenue, or neither")
        return lines
    if args.command == "payback":
        months = payback(args.cac, args.monthly_contribution)
        return ["payback months: %s" % one_dp(months)]
    if args.command == "ltv":
        if args.churn is not None:
            curve = retention_from_churn(args.churn, args.months)
        else:
            curve = args.retention
        r = ltv(args.monthly_contribution, curve, args.cac)
        lines = ["LTV over %d months: %s" % (r["months"], money(r["ltv"]))]
        if args.churn is not None and args.churn > 0:
            lines.append("LTV with no horizon (contribution / churn): %s"
                         % money(args.monthly_contribution / args.churn))
        if args.cac is not None:
            if r["ltv_to_cac"] is not None:
                lines.append("LTV to CAC: %s" % one_dp(r["ltv_to_cac"]))
            if r["payback_month"] is None:
                lines.append("cohort payback: not reached within the retention data")
                raise NoAnswer("\n".join(lines))
            lines.append("cohort payback month: %d" % r["payback_month"])
        return lines
    if args.command == "peak-funding":
        r = peak_funding(args.flows, args.opening)
        lines = ["peak funding needed: %s" % money(r["peak_funding"]),
                 "lowest cumulative cash: %s in month %d" % (money(r["low_point"]), r["low_month"]),
                 "closing cash: %s" % money(r["closing"])]
        if r["recovered_month"] is None:
            lines.append("recovered to opening balance: not within the flows given")
        else:
            lines.append("recovered to opening balance: month %d" % r["recovered_month"])
        return lines
    raise ValueError("no subcommand given")


def main(argv: list[str] | None = None) -> int:
    ap = build_parser()
    try:
        args = ap.parse_args(argv)
    except SystemExit as exc:
        return EXIT_OK if exc.code == 0 else EXIT_INPUT
    if not args.command:
        ap.print_help(sys.stderr)
        return EXIT_INPUT
    try:
        lines = run(args)
    except NoAnswer as exc:
        print(str(exc))
        return EXIT_NO_ANSWER
    except ValueError as exc:
        print("error: %s" % exc, file=sys.stderr)
        return EXIT_INPUT
    print("\n".join(lines))
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
