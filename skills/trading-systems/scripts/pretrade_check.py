#!/usr/bin/env python3
"""Replay orders through a set of pre-trade risk limits and report every rejection.

Standard library only. Python 3.9 or later. This is a reference model for testing
and reviewing a production risk gateway: feed it the same orders and limits, and the
decisions should agree. It is not itself a risk control.

Orders are a CSV with a header and the columns ts (seconds, any epoch), id (client
order id), symbol, side (buy or sell), qty and price, plus an optional ref column with
the reference price used for the collar. Limits are a JSON object:

  {
    "max_order_qty": 10000,
    "max_order_notional": 500000,
    "price_collar_pct": 5,
    "max_position": {"*": 20000, "XYZ": 5000},
    "max_gross_notional": 2000000,
    "max_orders_per_second": 20,
    "restricted": ["ABC"],
    "kill_after_rejects": 5,
    "kill_window_seconds": 10
  }

Every key is optional; a missing key means that check is off, and the report lists
which checks were off. A limit of the wrong type is an input error, never a weaker
check. Position and gross exposure (the sum of absolute positions at their last order
price) are computed as if every accepted order fills in full, the conservative
assumption a gateway should make. Rejected orders are never sent, so they do not count
toward the message rate. A reference price that is missing or not finite fails the
collar rather than passing it.
Once the kill switch trips, every later order is rejected until the run ends.

Usage:
  python3 pretrade_check.py orders.csv limits.json
  python3 pretrade_check.py orders.csv limits.json --quiet

Exit codes: 0 every order accepted, 1 at least one rejection, 2 invalid input.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from collections import deque
from typing import Deque, Dict, List, Optional, Sequence, Set, Tuple

KNOWN_LIMITS = {
    "max_order_qty", "max_order_notional", "price_collar_pct", "max_position",
    "max_gross_notional", "max_orders_per_second", "restricted", "kill_after_rejects",
    "kill_window_seconds",
}


class InputError(ValueError):
    """Raised for orders or limits that cannot be read."""


class Order:
    def __init__(self, row: int, ts: float, oid: str, symbol: str, side: str, qty: float,
                 price: float, ref: Optional[float]):
        self.row, self.ts, self.id, self.symbol = row, ts, oid, symbol
        self.side, self.qty, self.price, self.ref = side, qty, price, ref


def read_orders(path: str) -> List[Order]:
    with open(path, newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        fields = set(f.strip().lower() for f in (reader.fieldnames or []))
        missing = {"ts", "id", "symbol", "side", "qty", "price"} - fields
        if missing:
            raise InputError("orders file is missing column(s): %s" % ", ".join(sorted(missing)))
        orders = []
        for number, raw in enumerate(reader, start=2):
            if None in raw:
                raise InputError("row %d has more fields than the header" % number)
            row = {(k or "").strip().lower(): (v or "").strip() for k, v in raw.items()}
            if not any(row.values()):
                continue
            side = row["side"].lower()
            if side not in ("buy", "sell"):
                raise InputError("row %d: side must be buy or sell" % number)
            try:
                ts, qty, price = float(row["ts"]), float(row["qty"]), float(row["price"])
                ref = float(row["ref"]) if row.get("ref") else None
            except ValueError:
                raise InputError("row %d: ts, qty, price and ref must be numbers" % number)
            if not all(math.isfinite(v) for v in (ts, qty, price) + ((ref,) if ref is not None else ())):
                raise InputError("row %d: non-finite number" % number)
            orders.append(Order(number, ts, row["id"], row["symbol"].upper(), side, qty, price, ref))
    return orders


def read_limits(path: str) -> Dict[str, object]:
    with open(path, encoding="utf-8") as handle:
        try:
            limits = json.load(handle)
        except json.JSONDecodeError as exc:
            raise InputError("limits file is not valid JSON: %s" % exc)
    if not isinstance(limits, dict):
        raise InputError("limits must be a JSON object")
    unknown = set(limits) - KNOWN_LIMITS
    if unknown:
        raise InputError("unknown limit key(s): %s" % ", ".join(sorted(unknown)))
    validate_limits(limits)
    return limits


def _positive_number(value: object) -> bool:
    return (isinstance(value, (int, float)) and not isinstance(value, bool)
            and math.isfinite(value) and value > 0)


def validate_limits(limits: Dict[str, object]) -> None:
    """Reject limits of the wrong type, so a typo cannot silently weaken a check."""
    for key in ("max_order_qty", "max_order_notional", "price_collar_pct", "max_gross_notional",
                "max_orders_per_second", "kill_after_rejects", "kill_window_seconds"):
        if key in limits and not _positive_number(limits[key]):
            raise InputError("%s must be a positive finite number" % key)
    if "restricted" in limits:
        value = limits["restricted"]
        if not isinstance(value, list) or not all(isinstance(v, str) and v for v in value):
            raise InputError("restricted must be a list of symbol strings")
    if "max_position" in limits:
        value = limits["max_position"]
        if not isinstance(value, dict) or not all(
                isinstance(k, str) and _positive_number(v) for k, v in value.items()):
            raise InputError("max_position must map symbols (or *) to positive numbers")


def check_orders(orders: Sequence[Order], limits: Dict[str, object]) -> List[Tuple[Order, List[str]]]:
    validate_limits(limits)
    positions: Dict[str, float] = {}
    marks: Dict[str, float] = {}
    seen: Set[str] = set()
    recent: Deque[float] = deque()
    rejects: Deque[float] = deque()
    killed = False
    restricted = {s.upper() for s in limits.get("restricted", [])}  # type: ignore[union-attr]
    pos_limits = {k.upper(): float(v) for k, v in dict(limits.get("max_position", {})).items()}  # type: ignore[arg-type]
    results = []
    last_ts = -math.inf
    for o in orders:
        reasons: List[str] = []
        if o.ts < last_ts:
            reasons.append("timestamp goes backwards; the feed is out of order")
        last_ts = max(last_ts, o.ts)
        if killed:
            reasons.append("kill switch active")
        if o.qty <= 0 or o.qty != int(o.qty):
            reasons.append("quantity must be a positive whole number")
        if o.price <= 0:
            reasons.append("price must be positive")
        if not o.id:
            reasons.append("missing client order id")
        elif o.id in seen:
            reasons.append("duplicate client order id %s" % o.id)
        if o.symbol in restricted:
            reasons.append("symbol %s is restricted" % o.symbol)
        notional = abs(o.qty * o.price)
        if "max_order_qty" in limits and o.qty > float(limits["max_order_qty"]):  # type: ignore[arg-type]
            reasons.append("quantity %.0f above max_order_qty" % o.qty)
        if "max_order_notional" in limits and notional > float(limits["max_order_notional"]):  # type: ignore[arg-type]
            reasons.append("notional %.2f above max_order_notional" % notional)
        if "price_collar_pct" in limits:
            if o.ref is None or not math.isfinite(o.ref) or o.ref <= 0:
                reasons.append("no reference price for the collar; reject rather than guess")
            else:
                away = 100 * abs(o.price - o.ref) / o.ref
                if away > float(limits["price_collar_pct"]):  # type: ignore[arg-type]
                    reasons.append("price %.6g is %.2f%% from reference %.6g, outside the collar"
                                   % (o.price, away, o.ref))
        signed = o.qty if o.side == "buy" else -o.qty
        new_pos = positions.get(o.symbol, 0.0) + signed
        cap = pos_limits.get(o.symbol, pos_limits.get("*"))
        if cap is not None and abs(new_pos) > cap:
            reasons.append("position would be %.0f, limit %.0f" % (new_pos, cap))
        if "max_gross_notional" in limits:
            # Gross exposure after the order, as if it filled: sum of |position| x last price.
            new_marks = dict(marks)
            new_marks[o.symbol] = o.price
            new_positions = dict(positions)
            new_positions[o.symbol] = new_pos
            gross = math.fsum(abs(q) * new_marks.get(s, 0.0) for s, q in new_positions.items())
            if gross > float(limits["max_gross_notional"]):  # type: ignore[arg-type]
                reasons.append("gross exposure would be %.2f, above max_gross_notional" % gross)
        if "max_orders_per_second" in limits:
            while recent and recent[0] <= o.ts - 1.0:
                recent.popleft()
            if len(recent) + 1 > int(limits["max_orders_per_second"]):  # type: ignore[arg-type]
                reasons.append("order rate above max_orders_per_second")
        if o.id:
            seen.add(o.id)
        if reasons:
            if "kill_after_rejects" in limits and not killed:
                window = float(limits.get("kill_window_seconds", math.inf))  # type: ignore[arg-type]
                rejects.append(o.ts)
                while rejects and rejects[0] < o.ts - window:
                    rejects.popleft()
                if len(rejects) >= int(limits["kill_after_rejects"]):  # type: ignore[arg-type]
                    killed = True
                    reasons.append("kill switch tripped: %d rejects in the window" % len(rejects))
        else:
            # Only accepted orders are sent, so only they count toward the message rate.
            recent.append(o.ts)
            positions[o.symbol] = new_pos
            marks[o.symbol] = o.price
        results.append((o, reasons))
    return results


def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser(prog="pretrade_check.py", description="Replay orders through pre-trade limits.")
    ap.add_argument("orders")
    ap.add_argument("limits")
    ap.add_argument("--quiet", action="store_true", help="print only rejections and the summary")
    try:
        args = ap.parse_args(argv)
    except SystemExit as exc:
        return 0 if exc.code == 0 else 2
    try:
        orders = read_orders(args.orders)
        limits = read_limits(args.limits)
    except (InputError, OSError) as exc:
        print("error: %s" % exc, file=sys.stderr)
        return 2
    try:
        results = check_orders(orders, limits)
    except (InputError, TypeError, ValueError) as exc:
        print("error: %s" % exc, file=sys.stderr)
        return 2
    rejected = 0
    for o, reasons in results:
        if reasons:
            rejected += 1
            print("REJECT row %d %s %s %s %.0f @ %.6g: %s"
                  % (o.row, o.id, o.side, o.symbol, o.qty, o.price, "; ".join(reasons)))
        elif not args.quiet:
            print("ACCEPT row %d %s %s %s %.0f @ %.6g" % (o.row, o.id, o.side, o.symbol, o.qty, o.price))
    off = sorted(KNOWN_LIMITS - set(limits) - {"kill_window_seconds"})
    print("\n%d orders, %d accepted, %d rejected" % (len(results), len(results) - rejected, rejected))
    if off:
        print("checks not configured: %s" % ", ".join(off))
    return 1 if rejected else 0


if __name__ == "__main__":
    sys.exit(main())
