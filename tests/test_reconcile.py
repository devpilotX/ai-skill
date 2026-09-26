#!/usr/bin/env python3
"""Tests for the bank reconciliation script in the finance-books skill.

Writes small bank and ledger CSV fixtures to a temporary directory, runs the
script, and checks matching, the diagnostics it claims to find, and exit codes.

Run with: python3 tests/test_reconcile.py
"""

from __future__ import annotations

import contextlib
import importlib.util
import io
import sys
import tempfile
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills" / "finance-books" / "scripts" / "reconcile.py"

spec = importlib.util.spec_from_file_location("reconcile", SCRIPT)
assert spec and spec.loader, "cannot load reconciler at %s" % SCRIPT
reconcile = importlib.util.module_from_spec(spec)
sys.modules["reconcile"] = reconcile
spec.loader.exec_module(reconcile)

failures: list[str] = []


def check(condition: bool, message: str) -> None:
    if condition:
        print("  pass  %s" % message)
    else:
        print("  FAIL  %s" % message)
        failures.append(message)


def run(tmp: Path, bank: str, ledger: str, *extra: str) -> tuple[int, str, str]:
    bank_path = tmp / "bank.csv"
    ledger_path = tmp / "ledger.csv"
    bank_path.write_text(bank, encoding="utf-8")
    ledger_path.write_text(ledger, encoding="utf-8")
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        rc = reconcile.main([str(bank_path), str(ledger_path)] + list(extra))
    return rc, out.getvalue(), err.getvalue()


CLEAN_BANK = """date,amount,reference
2024-03-01,1200.00,INV-101
2024-03-04,-45.50,Stationery
2024-03-05,-0.10,Fee
"""

CLEAN_LEDGER = """date,amount,reference,category
2024-03-02,1200.00,INV-101,Sales
2024-03-04,-45.50,Stationery,Office
2024-03-05,-0.10,Fee,Bank charges
"""

with tempfile.TemporaryDirectory() as tmpdir:
    tmp = Path(tmpdir)

    print("\nclean reconciliation")
    rc, out, _ = run(tmp, CLEAN_BANK, CLEAN_LEDGER)
    check(rc == 0, "exit 0 when every line matches")
    check("Matched pairs: 3" in out, "matches within the date window")
    check("RECONCILED" in out and "NOT RECONCILED" not in out, "reports reconciled")
    check("Difference (bank - ledger): 0" in out, "difference is zero")

    print("\ndate window")
    late = CLEAN_LEDGER.replace("2024-03-02,1200.00", "2024-03-09,1200.00")
    rc, out, _ = run(tmp, CLEAN_BANK, late)
    check(rc == 1, "exit 1 when a match falls outside the window")
    rc, out, _ = run(tmp, CLEAN_BANK, late, "--window", "8")
    check(rc == 0, "a wider window matches it")

    print("\ntransposition")
    bank = "date,amount,reference\n2024-03-10,-54.00,Taxi\n"
    ledger = "date,amount,reference\n2024-03-10,-45.00,Taxi\n"
    rc, out, _ = run(tmp, bank, ledger)
    check(rc == 1, "exit 1 when unreconciled")
    check("difference is divisible by 9" in out, "total difference flagged as divisible by 9")
    check("Transposition or slide candidates (difference divisible by 9): 1" in out,
          "transposed pair reported")

    print("\nslide")
    bank = "date,amount,reference\n2024-03-11,-120.00,Parts\n"
    ledger = "date,amount,reference\n2024-03-11,-12.00,Parts\n"
    rc, out, _ = run(tmp, bank, ledger)
    check("Transposition or slide candidates (difference divisible by 9): 1" in out,
          "decimal shift reported as divisible by 9")

    print("\nnot divisible by 9")
    bank = "date,amount,reference\n2024-03-11,-100.00,Parts\n"
    ledger = "date,amount,reference\n2024-03-11,-99.50,Parts\n"
    rc, out, _ = run(tmp, bank, ledger)
    check("Transposition or slide candidates (difference divisible by 9): 0" in out,
          "0.50 difference is not reported as a transposition")

    print("\ndoubled sign")
    bank = "date,amount,reference\n2024-03-12,-300.00,Rent\n"
    ledger = "date,amount,reference\n2024-03-12,300.00,Rent\n"
    rc, out, _ = run(tmp, bank, ledger)
    check("Doubled-sign candidates (same amount, opposite sign): 1" in out,
          "opposite-sign pair reported")
    check("possible posting on the wrong side" in out, "difference equal to twice an amount flagged")

    print("\nflip ledger sign convention")
    rc, out, _ = run(tmp, bank, ledger, "--flip-ledger")
    check(rc == 0, "--flip-ledger reconciles an export with the opposite sign")

    print("\nduplicates")
    bank = "date,amount,reference\n2024-03-15,-80.00,SUP-7\n"
    ledger = "date,amount,reference\n2024-03-15,-80.00,SUP-7\n2024-03-16,-80.00,SUP-7\n"
    rc, out, _ = run(tmp, bank, ledger)
    check(rc == 1, "duplicate leaves an unmatched ledger line")
    check("Duplicate candidates: 1" in out, "duplicate ledger entry reported")
    check("Unmatched ledger lines: 1" in out, "exactly one ledger line left over")

    print("\ndecimal arithmetic")
    bank = "date,amount,reference\n" + "".join("2024-03-20,0.10,c%d\n" % i for i in range(3))
    ledger = "date,amount,reference\n2024-03-20,0.30,combined\n"
    rc, out, _ = run(tmp, bank, ledger)
    check("Bank total: 0.30" in out, "0.10 three times totals exactly 0.30")
    check("Difference (bank - ledger): 0.00" in out, "no binary floating point residue")
    check(reconcile.parse_amount("(12.34)") == Decimal("-12.34"), "accounting negative parsed")

    print("\ninput errors")
    rc, _, err = run(tmp, "date,amount\n2024-03-01,1.00\n", CLEAN_LEDGER)
    check(rc == 2 and "reference" in err, "missing column gives exit 2")
    rc, _, err = run(tmp, "date,amount,reference\n2024-03-01,\"1,200.00\",x\n", CLEAN_LEDGER)
    check(rc == 2 and "plain decimal" in err, "thousands separator rejected")
    rc, _, err = run(tmp, "date,amount,reference\n01/03/2024,1.00,x\n", CLEAN_LEDGER)
    check(rc == 2 and "does not match" in err, "wrong date format rejected")
    rc, out, _ = run(tmp, "date,amount,reference\n01/03/2024,1200.00,INV-101\n",
                     "date,amount,reference\n02/03/2024,1200.00,INV-101\n",
                     "--date-format", "%d/%m/%Y")
    check(rc == 0, "--date-format accepts day first dates")

print()
if failures:
    print("%d check(s) failed" % len(failures))
    sys.exit(1)
print("all checks passed")
