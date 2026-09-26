#!/usr/bin/env python3
"""Tests for the unit economics calculator in the business-model skill.

Checks each formula against hand computed values, the unit conventions that are
easy to get wrong (daily not monthly cost in the cash cycle, receivables at
revenue, payback on contribution), and the exit codes.

Run with: python3 tests/test_unit_economics.py
"""

from __future__ import annotations

import contextlib
import importlib.util
import io
import sys
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills" / "business-model" / "scripts" / "unit_economics.py"

spec = importlib.util.spec_from_file_location("unit_economics", SCRIPT)
assert spec and spec.loader, "cannot load calculator at %s" % SCRIPT
ue = importlib.util.module_from_spec(spec)
sys.modules["unit_economics"] = ue
spec.loader.exec_module(ue)

failures: list[str] = []
D = Decimal


def check(condition: bool, message: str) -> None:
    if condition:
        print("  pass  %s" % message)
    else:
        print("  FAIL  %s" % message)
        failures.append(message)


def cli(*argv: str) -> tuple[int, str]:
    out = io.StringIO()
    err = io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        rc = ue.main(list(argv))
    return rc, out.getvalue()


print("\ncontribution")
r = ue.contribution(D("100"), [D("38"), D("6.50")])
check(r["contribution"] == D("55.50"), "price minus the sum of variable costs")
check(r["margin"] == D("0.555"), "margin is contribution over net price")
r = ue.contribution(D("120"), [D("38"), D("6.50")], D("0.20"))
check(r["net_price"] == D("100"), "VAT inclusive price of 120 at 20 percent nets to 100")
check(r["vat"] == D("20"), "VAT removed is 20, not 24")
check(r["contribution"] == D("55.50"), "contribution is computed on the net price")
check(isinstance(r["contribution"], Decimal), "money stays Decimal")

print("\nbreak-even")
check(ue.breakeven(D("9000"), D("55.50")) == D("163"), "break-even rounds up to a whole unit")
check(ue.breakeven(D("9000"), D("45")) == D("200"), "exact division is not rounded up further")
try:
    ue.breakeven(D("9000"), D("0"))
    check(False, "zero contribution has no break-even")
except ue.NoAnswer:
    check(True, "zero contribution has no break-even")

print("\ncash conversion cycle")
r = ue.cash_cycle(D("45"), D("60"), D("30"), D("36500"), D("73000"))
check(r["ccc_days"] == D("75"), "CCC = DIO + DSO - DPO")
# Daily COGS 1200 and daily revenue 2400 when the year has 365 days.
check(r["inventory"] == D("54000"), "inventory = days x daily COGS")
check(r["receivables"] == D("144000"), "receivables are valued at revenue, not cost")
check(r["payables"] == D("36000"), "payables = days x daily COGS")
check(r["cash_tied_up"] == D("162000"), "cash tied up sums the three")
check(r["cash_tied_up"] < D("75") * D("36500"), "days are not multiplied by monthly cost")

print("\npayback")
check(ue.payback(D("300"), D("25")) == D("12"), "payback = CAC / monthly contribution")
try:
    ue.payback(D("300"), D("-1"))
    check(False, "negative contribution never pays back")
except ue.NoAnswer:
    check(True, "negative contribution never pays back")

print("\nlifetime value")
curve = ue.retention_from_churn(D("0.5"), 3)
check(curve == [D("1"), D("0.5"), D("0.25")], "churn gives a geometric retention curve")
check(ue.retention_from_churn(D("1"), 2) == [D("1"), D("0")], "full churn does not crash")
r = ue.ltv(D("10"), curve)
check(r["ltv"] == D("17.5"), "LTV sums contribution weighted by retention")
r = ue.ltv(D("25"), [D("1"), D("0.8"), D("0.7"), D("0.65")], D("60"))
check(r["payback_month"] == 3, "cohort payback month is when cumulative reaches CAC")
check(r["ltv"] == D("78.75"), "LTV from an explicit retention list")
r = ue.ltv(D("25"), [D("1"), D("0.8")], D("300"))
check(r["payback_month"] is None, "no payback inside the data is reported as none")

print("\npeak funding")
r = ue.peak_funding([D("-12000"), D("-8000"), D("-3000"), D("2000"), D("6000"),
                     D("9000"), D("8000")])
check(r["peak_funding"] == D("23000"), "peak funding is the deepest cumulative deficit")
check(r["low_month"] == 3, "month of the low point")
check(r["recovered_month"] == 7, "month cumulative cash is back to the opening balance")
r = ue.peak_funding([D("-5000"), D("1000")], D("10000"))
check(r["peak_funding"] == D("0"), "opening cash that covers the dip needs no funding")

print("\ncommand line")
rc, out = cli("contribution", "--price", "120", "--vat-rate", "0.20", "--variable-cost", "38")
check(rc == 0 and "contribution per unit: 62.00" in out, "contribution subcommand")
rc, out = cli("breakeven", "--fixed", "100", "--contribution", "0")
check(rc == 3, "exit 3 when break-even never arrives")
rc, out = cli("ltv", "--monthly-contribution", "25", "--churn", "0.05", "--months", "36")
check(rc == 0 and "LTV with no horizon (contribution / churn): 500.00" in out,
      "ltv subcommand with churn")
rc, out = cli("ltv", "--monthly-contribution", "25", "--retention", "1", "0.8", "--cac", "300")
check(rc == 3, "exit 3 when the cohort never recovers CAC")
rc, out = cli("ltv", "--monthly-contribution", "25", "--churn", "1.5")
check(rc == 2, "exit 2 on churn outside 0 to 1")
rc, out = cli("payback", "--cac", "abc", "--monthly-contribution", "1")
check(rc == 2, "exit 2 on a value that is not a number")
rc, out = cli()
check(rc == 2, "exit 2 with no subcommand")
rc, out = cli("ccc", "--inventory-days", "10", "--receivable-days", "10",
              "--payable-days", "5", "--monthly-cogs", "100")
check(rc == 2, "exit 2 when only one monthly figure is given")

print()
if failures:
    print("%d check(s) failed" % len(failures))
    sys.exit(1)
print("all checks passed")
