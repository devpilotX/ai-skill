#!/usr/bin/env python3
"""Match bank statement lines to ledger lines and report what does not reconcile.

Both inputs are CSV files with a header row containing the columns date, amount and
reference (other columns are ignored). Dates are ISO format (YYYY-MM-DD) unless
--date-format says otherwise. Amounts are plain decimals such as -1234.56, with an
optional leading plus sign, or accounting negatives such as (1234.56). Thousands
separators and currency symbols are rejected so that nothing is guessed.

Sign convention: both files are seen from the business bank account, receipts
positive and payments negative. If the ledger export uses the opposite sign, pass
--flip-ledger.

Matching pairs a bank line with an unused ledger line of exactly the same amount
whose date is within --window days (default 3; set it to the clearing time of the
bank). The closest date wins, then a matching reference.

For the lines left over, the report lists:
  - candidate transpositions and slides: pairs within the window whose difference,
    in minor units, is divisible by 9 (54 entered as 45, or 120.00 entered as 12.00);
  - doubled-sign errors: pairs where the ledger holds the same amount with the
    opposite sign, so the difference is twice the amount (posted on the wrong side);
  - duplicates: lines in the same file with the same amount and reference, or the
    same amount and no reference, within the window.

All arithmetic uses decimal.Decimal.

Usage:
  python3 reconcile.py bank.csv ledger.csv
  python3 reconcile.py bank.csv ledger.csv --window 5 --flip-ledger
  python3 reconcile.py bank.csv ledger.csv --date-format %d/%m/%Y

Exit codes: 0 everything matched, 1 unreconciled items remain, 2 input error.
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Dict, List, Optional, Sequence, Tuple

AMOUNT_RE = re.compile(r"^[+-]?\d+(\.\d+)?$")
REQUIRED = ("date", "amount", "reference")


class InputError(Exception):
    """Raised for a file that cannot be read as the expected CSV."""


class Line:
    def __init__(self, source: str, row: int, when: date, amount: Decimal, reference: str):
        self.source = source
        self.row = row
        self.date = when
        self.amount = amount
        self.reference = reference

    def label(self) -> str:
        ref = self.reference or "(no reference)"
        return "%s row %d  %s  %s  %s" % (self.source, self.row, self.date.isoformat(),
                                         self.amount, ref)


def parse_amount(text: str) -> Decimal:
    raw = text.strip()
    negative = False
    if raw.startswith("(") and raw.endswith(")"):
        negative = True
        raw = raw[1:-1].strip()
    if not AMOUNT_RE.match(raw):
        raise InputError("amount %r is not a plain decimal" % text)
    try:
        value = Decimal(raw)
    except InvalidOperation:
        raise InputError("amount %r is not a plain decimal" % text)
    return -value if negative else value


def read_lines(path: str, label: str, date_format: str, flip: bool = False) -> List[Line]:
    try:
        handle = open(path, newline="", encoding="utf-8-sig")
    except OSError as exc:
        raise InputError("cannot open %s: %s" % (path, exc))
    with handle:
        reader = csv.DictReader(handle)
        fields = [f.strip().lower() for f in (reader.fieldnames or [])]
        missing = [c for c in REQUIRED if c not in fields]
        if missing:
            raise InputError("%s is missing column(s): %s" % (path, ", ".join(missing)))
        lines = []
        for number, row in enumerate(reader, start=2):
            row = {(k or "").strip().lower(): (v or "") for k, v in row.items()}
            if not any(row.get(c, "").strip() for c in REQUIRED):
                continue
            try:
                when = datetime.strptime(row["date"].strip(), date_format).date()
            except ValueError:
                raise InputError("%s row %d: date %r does not match %s"
                                 % (path, number, row["date"], date_format))
            try:
                amount = parse_amount(row["amount"])
            except InputError as exc:
                raise InputError("%s row %d: %s" % (path, number, exc))
            if flip:
                amount = -amount
            lines.append(Line(label, number, when, amount, row["reference"].strip()))
    return lines


def days_apart(a: Line, b: Line) -> int:
    return abs((a.date - b.date).days)


def match(bank: List[Line], ledger: List[Line], window: int) -> Tuple[List[Tuple[Line, Line]], List[Line], List[Line]]:
    used = set()
    pairs = []
    unmatched_bank = []
    for b in sorted(bank, key=lambda x: (x.date, x.row)):
        best: Optional[Tuple[int, int, int]] = None
        for i, candidate in enumerate(ledger):
            if i in used or candidate.amount != b.amount:
                continue
            gap = days_apart(b, candidate)
            if gap > window:
                continue
            same_ref = 0 if (b.reference and b.reference.lower() == candidate.reference.lower()) else 1
            key = (gap, same_ref, i)
            if best is None or key < best:
                best = key
        if best is None:
            unmatched_bank.append(b)
        else:
            used.add(best[2])
            pairs.append((b, ledger[best[2]]))
    unmatched_ledger = [l for i, l in enumerate(ledger) if i not in used]
    return pairs, unmatched_bank, unmatched_ledger


def minor_units(value: Decimal) -> Decimal:
    """Scale to the smallest unit present so divisibility by 9 is tested on whole numbers."""
    exponent = value.as_tuple().exponent
    places = max(2, -exponent) if isinstance(exponent, int) else 2
    return value.scaleb(places)


def divisible_by_nine(diff: Decimal) -> bool:
    units = minor_units(diff)
    return diff != 0 and units == units.to_integral_value() and units % 9 == 0


def diagnose(unmatched_bank: List[Line], unmatched_ledger: List[Line], window: int) -> Dict[str, list]:
    nines = []
    signs = []
    for b in unmatched_bank:
        for l in unmatched_ledger:
            if days_apart(b, l) > window:
                continue
            if b.amount != 0 and l.amount == -b.amount:
                signs.append((b, l))
            elif divisible_by_nine(b.amount - l.amount):
                nines.append((b, l, b.amount - l.amount))
    return {"nines": nines, "signs": signs}


def duplicates(lines: Sequence[Line], window: int) -> List[Tuple[Line, Line]]:
    found = []
    ordered = sorted(lines, key=lambda x: (x.date, x.row))
    for i, a in enumerate(ordered):
        for b in ordered[i + 1:]:
            if (b.date - a.date).days > window:
                break
            if a.amount != b.amount:
                continue
            if a.reference.lower() == b.reference.lower():
                found.append((a, b))
    return found


def report(bank: List[Line], ledger: List[Line], window: int) -> Tuple[str, bool]:
    pairs, unmatched_bank, unmatched_ledger = match(bank, ledger, window)
    diag = diagnose(unmatched_bank, unmatched_ledger, window)
    dups = duplicates(bank, window) + duplicates(ledger, window)
    bank_total = sum((l.amount for l in bank), Decimal(0))
    ledger_total = sum((l.amount for l in ledger), Decimal(0))
    difference = bank_total - ledger_total

    out = []
    out.append("Matched pairs: %d" % len(pairs))
    out.append("Bank total: %s  Ledger total: %s  Difference (bank - ledger): %s"
               % (bank_total, ledger_total, difference))
    if difference != 0 and divisible_by_nine(difference):
        out.append("  The difference is divisible by 9: look for a transposition or a slide.")
    halves = [l for l in unmatched_bank + unmatched_ledger if l.amount != 0 and abs(difference) == 2 * abs(l.amount)]
    for l in halves:
        out.append("  The difference is twice %s: possible posting on the wrong side." % l.label())

    out.append("")
    out.append("Unmatched bank lines: %d" % len(unmatched_bank))
    out.extend("  " + l.label() for l in unmatched_bank)
    out.append("Unmatched ledger lines: %d" % len(unmatched_ledger))
    out.extend("  " + l.label() for l in unmatched_ledger)

    out.append("")
    out.append("Doubled-sign candidates (same amount, opposite sign): %d" % len(diag["signs"]))
    for b, l in diag["signs"]:
        out.append("  %s  <->  %s" % (b.label(), l.label()))
    out.append("Transposition or slide candidates (difference divisible by 9): %d" % len(diag["nines"]))
    for b, l, diff in diag["nines"]:
        out.append("  %s  <->  %s  difference %s" % (b.label(), l.label(), diff))
    out.append("Duplicate candidates: %d" % len(dups))
    for a, b in dups:
        out.append("  %s  ==  %s" % (a.label(), b.label()))

    reconciled = not unmatched_bank and not unmatched_ledger
    out.append("")
    out.append("RECONCILED" if reconciled else "NOT RECONCILED")
    return "\n".join(out) + "\n", reconciled


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Reconcile bank lines against ledger lines.")
    parser.add_argument("bank", help="CSV of bank statement lines (date, amount, reference)")
    parser.add_argument("ledger", help="CSV of ledger lines for the bank account (date, amount, reference)")
    parser.add_argument("--window", type=int, default=3,
                        help="maximum days between matching bank and ledger dates (default 3)")
    parser.add_argument("--date-format", default="%Y-%m-%d",
                        help="strptime format for the date column (default %%Y-%%m-%%d)")
    parser.add_argument("--flip-ledger", action="store_true",
                        help="negate ledger amounts when the export uses the opposite sign")
    args = parser.parse_args(argv)
    if args.window < 0:
        print("error: --window must be zero or more", file=sys.stderr)
        return 2
    try:
        bank = read_lines(args.bank, "bank", args.date_format)
        ledger = read_lines(args.ledger, "ledger", args.date_format, flip=args.flip_ledger)
    except InputError as exc:
        print("error: %s" % exc, file=sys.stderr)
        return 2
    text, reconciled = report(bank, ledger, args.window)
    sys.stdout.write(text)
    return 0 if reconciled else 1


if __name__ == "__main__":
    sys.exit(main())
