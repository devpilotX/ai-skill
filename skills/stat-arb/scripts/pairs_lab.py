#!/usr/bin/env python3
"""Mean reversion diagnostics for a pair or a spread: hedge ratio, Engle-Granger
cointegration test, Ornstein-Uhlenbeck fit, half-life and the current z-score.

Standard library only. Python 3.9 or later.

Input is a CSV with a header. For a pair, --y and --x name two price (or log price)
columns; the spread is y - beta x - alpha from an OLS fit. For a ready-made spread,
--spread names one column and the fit is skipped.

Usage:
  python3 pairs_lab.py prices.csv --y KO --x PEP --log
  python3 pairs_lab.py prices.csv --y KO --x PEP --log --lags 2 --window 60
  python3 pairs_lab.py spread.csv --spread s --dt 1

Methods:
  hedge ratio   OLS of y on x with an intercept, in-sample. Fitting and testing on
                the same data biases the test toward finding cointegration, so
                confirm on data the fit never saw.
  ADF           augmented Dickey-Fuller regression with a constant,
                d s_t = a + b s_{t-1} + sum_i c_i d s_{t-i} + e_t, t statistic of b.
  --spread      only for spreads whose weights are fixed in advance (a futures
                calendar, a merger ratio). A residual from a regression on the same data
                needs --estimated, or the plain ADF values over-reject.
  critical      for a fitted pair the Engle-Granger critical values apply, not the
  values        plain ADF ones, because beta was estimated. Asymptotic values with a
                constant and two variables, from MacKinnon (2010), "Critical values
                for cointegration tests", Queen's Economics Department Working Paper
                1227: 1% -3.90, 5% -3.34, 10% -3.04. For a given spread the ADF
                values with a constant: 1% -3.43, 5% -2.86, 10% -2.57.
  OU fit        s_t = a + b s_{t-1} + e_t. With b in (0, 1): theta = -ln(b) / dt,
                mean = a / (1 - b), equilibrium sd = sd(e) / sqrt(1 - b^2),
                half-life = ln 2 / theta, in the units of dt.
  z-score       (last value - rolling mean) / rolling sd over --window, or over the
                whole sample if no window is given.

Exit codes: 0 success, 2 invalid input.
"""

from __future__ import annotations

import argparse
import csv
import math
import sys
from typing import Dict, List, Optional, Sequence, Tuple

EG_CRITICAL = {"1%": -3.90, "5%": -3.34, "10%": -3.04}
ADF_CRITICAL = {"1%": -3.43, "5%": -2.86, "10%": -2.57}


class InputError(ValueError):
    """Raised for input that cannot produce a meaningful result."""


def read_columns(path: str, names: Sequence[str]) -> Dict[str, List[float]]:
    with open(path, newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        fields = reader.fieldnames or []
        for name in names:
            if name not in fields:
                raise InputError("column %r not found in %s" % (name, path))
        out: Dict[str, List[float]] = {n: [] for n in names}
        for number, row in enumerate(reader, start=2):
            if all(not (row.get(n) or "").strip() for n in names):
                continue
            try:
                values = [float(row[n]) for n in names]
            except (TypeError, ValueError):
                raise InputError("row %d has a missing or non-numeric value" % number)
            for n, v in zip(names, values):
                out[n].append(v)
    return out


def ols(y: Sequence[float], cols: Sequence[Sequence[float]]) -> Tuple[List[float], List[float], List[float]]:
    """OLS with the columns given (include a column of ones for an intercept).

    Returns coefficients, their standard errors, and residuals.
    """
    n, k = len(y), len(cols)
    if n <= k:
        raise InputError("not enough observations for the regression")
    xtx = [[math.fsum(cols[i][t] * cols[j][t] for t in range(n)) for j in range(k)] for i in range(k)]
    xty = [math.fsum(cols[i][t] * y[t] for t in range(n)) for i in range(k)]
    inv = invert(xtx)
    beta = [math.fsum(inv[i][j] * xty[j] for j in range(k)) for i in range(k)]
    resid = [y[t] - math.fsum(beta[i] * cols[i][t] for i in range(k)) for t in range(n)]
    s2 = math.fsum(e * e for e in resid) / (n - k)
    se = [math.sqrt(max(inv[i][i] * s2, 0.0)) for i in range(k)]
    return beta, se, resid


def invert(a: List[List[float]]) -> List[List[float]]:
    k = len(a)
    m = [list(a[i]) + [1.0 if i == j else 0.0 for j in range(k)] for i in range(k)]
    scale = max(abs(v) for row in a for v in row) or 1.0
    for col in range(k):
        pivot = max(range(col, k), key=lambda r: abs(m[r][col]))
        if abs(m[pivot][col]) < 1e-14 * scale:
            raise InputError("regressors are collinear; is one series constant?")
        m[col], m[pivot] = m[pivot], m[col]
        p = m[col][col]
        m[col] = [v / p for v in m[col]]
        for r in range(k):
            if r != col:
                f = m[r][col]
                m[r] = [m[r][c] - f * m[col][c] for c in range(2 * k)]
    return [row[k:] for row in m]


def hedge_ratio(y: Sequence[float], x: Sequence[float]) -> Tuple[float, float, List[float]]:
    (alpha, beta), _, resid = ols(y, [[1.0] * len(y), list(x)])
    return alpha, beta, resid


def default_lags(n: int) -> int:
    """Schwert (1989) rule of thumb, floor(12 (n/100)^(1/4)), capped for short samples."""
    return max(0, min(int(12 * (n / 100.0) ** 0.25), n // 5))


def adf(series: Sequence[float], lags: Optional[int] = None) -> Dict[str, float]:
    n = len(series)
    if n < 20:
        raise InputError("need at least 20 observations for the ADF test")
    p = default_lags(n) if lags is None else lags
    if p < 0 or p > n // 3:
        raise InputError("lag count %d is not sensible for %d observations" % (p, n))
    diff = [series[t] - series[t - 1] for t in range(1, n)]
    rows = range(p, len(diff))
    y = [diff[t] for t in rows]
    cols = [[1.0] * len(y), [series[t] for t in rows]]
    for i in range(1, p + 1):
        cols.append([diff[t - i] for t in rows])
    beta, se, _ = ols(y, cols)
    return {"stat": beta[1] / se[1], "gamma": beta[1], "lags": p, "nobs": len(y)}


def ou_fit(series: Sequence[float], dt: float = 1.0) -> Dict[str, float]:
    if dt <= 0:
        raise InputError("dt must be positive")
    y = list(series[1:])
    x = list(series[:-1])
    (a, b), _, resid = ols(y, [[1.0] * len(y), x])
    sd_e = math.sqrt(math.fsum(e * e for e in resid) / (len(resid) - 2))
    out = {"a": a, "b": b, "residual_sd": sd_e}
    if 0 < b < 1:
        theta = -math.log(b) / dt
        out.update({"theta": theta, "mean": a / (1 - b),
                    "equilibrium_sd": sd_e / math.sqrt(1 - b * b),
                    "half_life": math.log(2) / theta})
    else:
        out.update({"theta": float("nan"), "mean": float("nan"), "equilibrium_sd": float("nan"),
                    "half_life": float("inf")})
    return out


def zscore(series: Sequence[float], window: Optional[int] = None) -> float:
    data = list(series[-window:]) if window else list(series)
    if len(data) < 2:
        raise InputError("window too short for a z-score")
    mean = math.fsum(data) / len(data)
    sd = math.sqrt(math.fsum((v - mean) ** 2 for v in data) / (len(data) - 1))
    if sd == 0:
        raise InputError("spread has zero variance in the window")
    return (series[-1] - mean) / sd


def verdict(stat: float, table: Dict[str, float]) -> str:
    passed = [level for level, cv in sorted(table.items(), key=lambda kv: kv[1]) if stat < cv]
    return "rejects a unit root at %s" % passed[0] if passed else "does not reject a unit root at 10%"


def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser(prog="pairs_lab.py", description="Pair and spread diagnostics.")
    ap.add_argument("path")
    ap.add_argument("--y", help="dependent series for a pair")
    ap.add_argument("--x", help="hedge series for a pair")
    ap.add_argument("--spread", help="column holding a ready-made spread")
    ap.add_argument("--estimated", action="store_true",
                    help="the --spread weights were estimated from this data (for example a saved "
                         "regression residual), so use Engle-Granger critical values")
    ap.add_argument("--log", action="store_true", help="take logs of y and x first")
    ap.add_argument("--lags", type=int, help="ADF lag count, default floor(12 (n/100)^0.25)")
    ap.add_argument("--dt", type=float, default=1.0, help="time between observations, for the half-life unit")
    ap.add_argument("--window", type=int, help="rolling window for the z-score")
    try:
        args = ap.parse_args(argv)
    except SystemExit as exc:
        return 0 if exc.code == 0 else 2
    try:
        if args.spread and (args.y or args.x):
            raise InputError("give either --spread or --y and --x")
        if args.spread:
            spread = read_columns(args.path, [args.spread])[args.spread]
            if args.estimated:
                table, label = EG_CRITICAL, "Engle-Granger"
            else:
                table, label = ADF_CRITICAL, "ADF"
            print("spread %s, %d observations" % (args.spread, len(spread)))
        elif args.y and args.x:
            data = read_columns(args.path, [args.y, args.x])
            y, x = data[args.y], data[args.x]
            if args.log:
                if min(y + x) <= 0:
                    raise InputError("--log needs positive prices")
                y = [math.log(v) for v in y]
                x = [math.log(v) for v in x]
            alpha, beta, spread = hedge_ratio(y, x)
            table, label = EG_CRITICAL, "Engle-Granger"
            print("pair %s on %s%s, %d observations" % (args.y, args.x, " (logs)" if args.log else "", len(y)))
            print("hedge ratio beta %.6g, intercept %.6g (in-sample OLS)" % (beta, alpha))
        else:
            raise InputError("give --spread, or both --y and --x")
        test = adf(spread, args.lags)
        print("%s statistic %.3f with %d lags on %d observations" % (label, test["stat"], test["lags"], test["nobs"]))
        print("critical values " + ", ".join("%s %.2f" % kv for kv in sorted(table.items(), key=lambda kv: kv[1])))
        print("result: %s" % verdict(test["stat"], table))
        ou = ou_fit(spread, args.dt)
        if math.isinf(ou["half_life"]):
            print("AR(1) coefficient %.4f is not in (0, 1): no mean reversion to fit" % ou["b"])
        else:
            print("OU fit: theta %.4g, mean %.6g, equilibrium sd %.6g, half-life %.2f (dt units)"
                  % (ou["theta"], ou["mean"], ou["equilibrium_sd"], ou["half_life"]))
        print("current z-score %.2f%s" % (zscore(spread, args.window),
                                          " over %d observations" % args.window if args.window else " over the full sample"))
        print("in-sample diagnostics only; a pair that passes here still needs an out-of-sample test")
    except (InputError, OSError) as exc:
        print("error: %s" % exc, file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
