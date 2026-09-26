#!/usr/bin/env python3
"""Performance statistics for a strategy return series, with the corrections for
non-normal returns, serial correlation and multiple testing that a raw Sharpe ratio
leaves out.

Standard library only. Python 3.9 or later.

Input is a file of periodic returns (simple returns, 0.01 means one percent), either
one number per line or a CSV with a header, in which case --column names the column.
Use - to read standard input.

Usage:
  python3 strategy_stats.py returns.csv --column pnl --periods 252
  python3 strategy_stats.py returns.txt --periods 252 --trials 200 --trial-sr-var 0.25
  python3 strategy_stats.py returns.txt --periods 252 --trial-srs trials.txt
  python3 strategy_stats.py returns.txt --periods 12 --benchmark-sr 0.5 --json

What it reports, and where each formula comes from:
  sharpe            mean / sample standard deviation per period, and annualised by
                    sqrt(periods). The annualisation assumes independent returns.
  lo_sharpe         annualised Sharpe corrected for autocorrelation, Lo (2002),
                    "The Statistics of Sharpe Ratios", Financial Analysts Journal:
                    SR_q = SR * q / sqrt(q + 2 * sum_{k=1}^{L} (q - k) rho_k), with the
                    sum truncated at L = min(q - 1, Newey-West lag) because the far
                    lags of a daily series are noise.
  psr               probabilistic Sharpe ratio, Bailey and Lopez de Prado (2012),
                    "The Sharpe Ratio Efficient Frontier", Journal of Risk:
                    Phi((SR - SR*) sqrt(n - 1) / sqrt(1 - g3 SR + (g4 - 1) / 4 SR^2))
                    with per period SR, skewness g3 and non-excess kurtosis g4.
  min_track_record  periods needed for PSR to reach the confidence level, same paper.
  dsr               deflated Sharpe ratio, Bailey and Lopez de Prado (2014),
                    "The Deflated Sharpe Ratio", Journal of Portfolio Management:
                    PSR evaluated at the expected maximum Sharpe ratio of N trials,
                    SR0 = sqrt(V) ((1 - e_g) Z(1 - 1/N) + e_g Z(1 - 1/(N e))),
                    e_g the Euler-Mascheroni constant, V the variance of the trial
                    Sharpe ratios. V and N are in the same units as --trial-sr-var:
                    annualised, converted to per period internally.
  newey_west_t      t statistic of the mean return with a Newey and West (1987)
                    Bartlett kernel long run variance, lag floor(4 (n/100)^(2/9))
                    unless --nw-lags is given.
  drawdown          maximum drawdown of the compounded equity curve, and the longest
                    time under water in periods.

Exit codes: 0 success, 2 invalid input.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from statistics import NormalDist
from typing import Dict, List, Optional, Sequence

EULER_GAMMA = 0.5772156649015329
PHI = NormalDist()


class InputError(ValueError):
    """Raised for input that cannot produce a meaningful statistic."""


def read_series(path: str, column: Optional[str] = None) -> List[float]:
    """Read numbers from a one-per-line file or a CSV column. Blank lines are skipped."""
    handle = sys.stdin if path == "-" else open(path, newline="", encoding="utf-8-sig")
    try:
        text = handle.read()
    finally:
        if handle is not sys.stdin:
            handle.close()
    values: List[float] = []
    if column:
        reader = csv.DictReader(text.splitlines())
        if not reader.fieldnames or column not in reader.fieldnames:
            raise InputError("column %r not found in %s" % (column, path))
        rows = [row[column] for row in reader]
    else:
        lines = [line for line in text.splitlines() if line.strip()]
        if any("," in line for line in lines[1:]):
            raise InputError("%s has several columns; name the returns column with --column" % path)
        rows = lines
    for number, raw in enumerate(rows, start=1):
        raw = (raw or "").strip()
        if not raw:
            continue
        try:
            value = float(raw)
        except ValueError:
            if number == 1 and not column:
                continue  # a header line
            raise InputError("value %r on row %d is not a number" % (raw, number))
        if not math.isfinite(value):
            raise InputError("value on row %d is not finite" % number)
        values.append(value)
    return values


def moments(x: Sequence[float]) -> Dict[str, float]:
    """Mean, sample standard deviation, skewness and non-excess kurtosis.

    Skewness and kurtosis use population central moments, as in the PSR papers.
    """
    n = len(x)
    if n < 3:
        raise InputError("need at least 3 returns, got %d" % n)
    mean = math.fsum(x) / n
    dev = [v - mean for v in x]
    m2 = math.fsum(d * d for d in dev) / n
    if m2 <= (abs(mean) * 1e-12) ** 2 or m2 == 0:
        raise InputError("returns have zero variance")
    m3 = math.fsum(d ** 3 for d in dev) / n
    m4 = math.fsum(d ** 4 for d in dev) / n
    sd = math.sqrt(m2 * n / (n - 1))
    return {"n": n, "mean": mean, "sd": sd, "skew": m3 / m2 ** 1.5, "kurt": m4 / m2 ** 2}


def autocorrelation(x: Sequence[float], lag: int) -> float:
    n = len(x)
    mean = math.fsum(x) / n
    denom = math.fsum((v - mean) ** 2 for v in x)
    num = math.fsum((x[t] - mean) * (x[t - lag] - mean) for t in range(lag, n))
    return num / denom


def lo_adjusted_annual_sharpe(sr_period: float, x: Sequence[float], q: int,
                              max_lag: Optional[int] = None) -> Optional[float]:
    """Lo (2002) annualisation, truncating the autocorrelation sum at max_lag.

    Lo's formula sums q - 1 autocorrelations. For daily data (q = 252) most of those
    are estimation noise, so the sum is truncated at the Newey-West lag by default.
    Returns None when the truncated sum makes the variance ratio non-positive.
    """
    if q < 1:
        raise InputError("periods per year must be at least 1")
    n = len(x)
    if max_lag is None:
        max_lag = int(math.floor(4 * (n / 100.0) ** (2.0 / 9.0)))
    lags = max(0, min(q - 1, max_lag, n - 2))
    total = q + 2 * math.fsum((q - k) * autocorrelation(x, k) for k in range(1, lags + 1))
    if total <= 0:
        return None
    return sr_period * q / math.sqrt(total)


def psr(sr: float, sr_star: float, n: int, skew: float, kurt: float) -> float:
    """Probabilistic Sharpe ratio with per period Sharpe ratios."""
    denom = 1 - skew * sr + (kurt - 1) / 4 * sr * sr
    if denom <= 0:
        raise InputError("higher moments make the PSR variance non-positive")
    return PHI.cdf((sr - sr_star) * math.sqrt(n - 1) / math.sqrt(denom))


def min_track_record(sr: float, sr_star: float, skew: float, kurt: float,
                     confidence: float = 0.95) -> float:
    """Minimum number of periods for PSR(sr_star) to reach the confidence level."""
    if sr <= sr_star:
        return math.inf
    z = PHI.inv_cdf(confidence)
    return 1 + (1 - skew * sr + (kurt - 1) / 4 * sr * sr) * (z / (sr - sr_star)) ** 2


def expected_max_sharpe(trials: int, var_sr: float) -> float:
    """Expected maximum Sharpe ratio of independent trials with true Sharpe zero."""
    if trials < 2:
        raise InputError("the deflated Sharpe ratio needs at least 2 trials")
    if var_sr < 0:
        raise InputError("variance of trial Sharpe ratios cannot be negative")
    z1 = PHI.inv_cdf(1 - 1 / trials)
    z2 = PHI.inv_cdf(1 - 1 / (trials * math.e))
    return math.sqrt(var_sr) * ((1 - EULER_GAMMA) * z1 + EULER_GAMMA * z2)


def newey_west_t(x: Sequence[float], lags: Optional[int] = None) -> Dict[str, float]:
    n = len(x)
    if lags is None:
        lags = int(math.floor(4 * (n / 100.0) ** (2.0 / 9.0)))
    lags = max(0, min(lags, n - 1))
    mean = math.fsum(x) / n
    dev = [v - mean for v in x]
    lrv = math.fsum(d * d for d in dev) / n
    for lag in range(1, lags + 1):
        weight = 1 - lag / (lags + 1)
        gamma = math.fsum(dev[t] * dev[t - lag] for t in range(lag, n)) / n
        lrv += 2 * weight * gamma
    if lrv <= 0:
        raise InputError("long run variance is not positive")
    return {"t": mean / math.sqrt(lrv / n), "lags": lags}


def drawdown(x: Sequence[float]) -> Dict[str, float]:
    """Maximum drawdown of compounded equity, and the longest spell under water."""
    equity = 1.0
    peak = 1.0
    worst = 0.0
    under = 0
    longest = 0
    for r in x:
        if r <= -1:
            raise InputError("a return of -100 percent or worse ends the equity curve")
        equity *= 1 + r
        if equity >= peak:
            peak = equity
            under = 0
        else:
            under += 1
            longest = max(longest, under)
            worst = max(worst, 1 - equity / peak)
    return {"max_drawdown": worst, "longest_underwater_periods": longest,
            "total_return": equity - 1}


def analyse(x: Sequence[float], periods: int, benchmark_sr_annual: float = 0.0,
            trials: Optional[int] = None, trial_sr_var_annual: Optional[float] = None,
            confidence: float = 0.95, nw_lags: Optional[int] = None) -> Dict[str, object]:
    if periods < 1:
        raise InputError("periods per year must be at least 1")
    m = moments(x)
    sr = m["mean"] / m["sd"]
    root = math.sqrt(periods)
    sr_star = benchmark_sr_annual / root
    out: Dict[str, object] = {
        "n": m["n"], "periods_per_year": periods,
        "mean": m["mean"], "sd": m["sd"], "skew": m["skew"], "excess_kurtosis": m["kurt"] - 3,
        "sharpe_period": sr, "sharpe_annual": sr * root,
        "lo_sharpe_annual": lo_adjusted_annual_sharpe(sr, x, periods, nw_lags),
        "psr": psr(sr, sr_star, m["n"], m["skew"], m["kurt"]),
        "benchmark_sharpe_annual": benchmark_sr_annual,
        "min_track_record_periods": min_track_record(sr, sr_star, m["skew"], m["kurt"],
                                                     confidence),
        "hit_rate": sum(1 for v in x if v > 0) / m["n"],
    }
    out.update(newey_west_t(x, nw_lags))
    out["newey_west_t"] = out.pop("t")
    out["newey_west_lags"] = out.pop("lags")
    out.update(drawdown(x))
    if trials is not None:
        if trial_sr_var_annual is None:
            raise InputError("--trials needs --trial-sr-var or --trial-srs")
        sr0_annual = expected_max_sharpe(trials, trial_sr_var_annual)
        out["trials"] = trials
        out["expected_max_sharpe_annual"] = sr0_annual
        out["dsr"] = psr(sr, sr0_annual / root, m["n"], m["skew"], m["kurt"])
    return out


def sample_variance(values: Sequence[float]) -> float:
    if len(values) < 2:
        raise InputError("need at least 2 trial Sharpe ratios")
    mean = math.fsum(values) / len(values)
    return math.fsum((v - mean) ** 2 for v in values) / (len(values) - 1)


def format_report(r: Dict[str, object]) -> str:
    def f(key: str, fmt: str = "%.4f") -> str:
        value = r[key]
        if value is None:
            return "undefined (autocorrelations make the variance ratio non-positive)"
        if isinstance(value, float) and math.isinf(value):
            return "never (Sharpe does not exceed the benchmark)"
        return fmt % value

    lines = [
        "observations: %d at %d per year" % (r["n"], r["periods_per_year"]),
        "mean per period: %s   sd per period: %s" % (f("mean", "%.6g"), f("sd", "%.6g")),
        "skewness: %s   excess kurtosis: %s" % (f("skew", "%.3f"), f("excess_kurtosis", "%.3f")),
        "Sharpe annualised (iid): %s" % f("sharpe_annual", "%.3f"),
        "Sharpe annualised (Lo autocorrelation corrected): %s" % f("lo_sharpe_annual", "%.3f"),
        "PSR against annual Sharpe %s: %s" % (f("benchmark_sharpe_annual", "%.2f"), f("psr")),
        "minimum track record for the PSR confidence level: %s" % f("min_track_record_periods", "%.0f periods"),
        "Newey-West t of the mean: %s (%d lags)" % (f("newey_west_t", "%.3f"), r["newey_west_lags"]),
        "hit rate: %s" % f("hit_rate", "%.3f"),
        "max drawdown: %.2f%%   longest under water: %d periods"
        % (100 * r["max_drawdown"], r["longest_underwater_periods"]),
    ]
    if "dsr" in r:
        lines.append("expected max Sharpe of %d null trials: %s annualised"
                     % (r["trials"], f("expected_max_sharpe_annual", "%.3f")))
        lines.append("deflated Sharpe ratio: %s" % f("dsr"))
        if r["dsr"] < 0.95:
            lines.append("DSR below 0.95: the result is consistent with the best of %d "
                         "trials of a strategy with no edge" % r["trials"])
    else:
        lines.append("DSR not computed: pass --trials and the trial Sharpe variance. "
                     "Every configuration tried counts as a trial.")
    return "\n".join(lines)


def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser(prog="strategy_stats.py",
                                 description="Sharpe, PSR, DSR and drawdown for a return series.")
    ap.add_argument("path", help="returns file, or - for standard input")
    ap.add_argument("--column", help="CSV column holding the returns")
    ap.add_argument("--periods", type=int, required=True,
                    help="periods per year: 252 daily, 52 weekly, 12 monthly")
    ap.add_argument("--benchmark-sr", type=float, default=0.0,
                    help="annualised Sharpe ratio the PSR is tested against (default 0)")
    ap.add_argument("--trials", type=int, help="number of strategy variants tried")
    group = ap.add_mutually_exclusive_group()
    group.add_argument("--trial-sr-var", type=float,
                       help="variance of the annualised Sharpe ratios across trials")
    group.add_argument("--trial-srs", help="file of annualised Sharpe ratios, one per trial")
    ap.add_argument("--confidence", type=float, default=0.95)
    ap.add_argument("--nw-lags", type=int, help="Newey-West lag count")
    ap.add_argument("--json", action="store_true", help="print JSON instead of text")
    try:
        args = ap.parse_args(argv)
    except SystemExit as exc:
        return 0 if exc.code == 0 else 2
    try:
        returns = read_series(args.path, args.column)
        var_sr = args.trial_sr_var
        trials = args.trials
        if args.trial_srs:
            trial_values = read_series(args.trial_srs)
            var_sr = sample_variance(trial_values)
            trials = trials or len(trial_values)
        if not 0 < args.confidence < 1:
            raise InputError("confidence must be between 0 and 1")
        result = analyse(returns, args.periods, args.benchmark_sr, trials, var_sr,
                         args.confidence, args.nw_lags)
    except (InputError, OSError) as exc:
        print("error: %s" % exc, file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps({k: (None if isinstance(v, float) and math.isinf(v) else v)
                          for k, v in result.items()}, indent=2, sort_keys=True))
    else:
        print(format_report(result))
    return 0


if __name__ == "__main__":
    sys.exit(main())
