#!/usr/bin/env python3
"""Tests for the statistics helpers in the numbers-check skill.

Checks each function against values computed independently by hand or from the published
formula, plus the input validation that stops a silent wrong answer.

Run with: python3 tests/test_stats_tools.py
"""

from __future__ import annotations

import contextlib
import importlib.util
import io
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills" / "numbers-check" / "scripts" / "stats_tools.py"

spec = importlib.util.spec_from_file_location("stats_tools", SCRIPT)
assert spec and spec.loader, "cannot load stats tools at %s" % SCRIPT
stats_tools = importlib.util.module_from_spec(spec)
sys.modules["stats_tools"] = stats_tools
spec.loader.exec_module(stats_tools)

failures: list[str] = []


def check(condition: bool, message: str) -> None:
    if condition:
        print("  pass  %s" % message)
    else:
        print("  FAIL  %s" % message)
        failures.append(message)


def close(a: float, b: float, tol: float) -> bool:
    return abs(a - b) <= tol


def raises(func, *args) -> bool:
    try:
        func(*args)
    except stats_tools.InputError:
        return True
    return False


def run_cli(argv: list) -> tuple:
    out = io.StringIO()
    err = io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        rc = stats_tools.main(argv)
    return rc, out.getvalue(), err.getvalue()


print("\nwilson interval")
low, high = stats_tools.wilson_interval(8, 10)
check(close(low, 0.4902, 0.0005) and close(high, 0.9433, 0.0005),
      "8 of 10 at 95 percent is about 0.490 to 0.943")
low, high = stats_tools.wilson_interval(0, 10)
check(low == 0.0 and close(high, 0.2775, 0.0005), "0 of 10 gives a lower bound of 0")
low, high = stats_tools.wilson_interval(50, 100)
check(close(low + high, 1.0, 1e-9), "interval is symmetric at p = 0.5")
check(raises(stats_tools.wilson_interval, 11, 10), "rejects more successes than trials")
check(raises(stats_tools.wilson_interval, 0, 0), "rejects zero trials")

print("\ntwo-proportion z test")
diff, z, p = stats_tools.two_proportion_z(100, 1000, 130, 1000)
expected_z = 0.03 / math.sqrt(0.115 * 0.885 * (2 / 1000))
check(close(diff, 0.03, 1e-12), "difference is p_B minus p_A")
check(close(z, expected_z, 1e-9), "z uses the pooled standard error")
check(close(p, 0.0355, 0.0005), "two-sided p value is about 0.0355")
_, _, p_one = stats_tools.two_proportion_z(100, 1000, 130, 1000, two_sided=False)
check(close(p_one, p / 2, 1e-12), "one-sided p value is half the two-sided one here")
check(raises(stats_tools.two_proportion_z, 0, 10, 0, 10), "rejects an undefined z")

print("\nsample size")
n = stats_tools.sample_size_two_proportions(0.10, 0.02, 0.05, 0.8)
check(n == 3841, "10 percent baseline, 2 point lift, alpha 0.05 two-sided, power 0.8 is 3841 per arm")
n_one = stats_tools.sample_size_two_proportions(0.10, 0.02, 0.05, 0.8, two_sided=False)
check(n_one < n, "one-sided test needs fewer per arm")
n_small = stats_tools.sample_size_two_proportions(0.10, 0.01, 0.05, 0.8)
check(3.5 * n < n_small < 4.5 * n, "halving the effect roughly quadruples the sample")
check(raises(stats_tools.sample_size_two_proportions, 0.99, 0.02), "rejects a target above 1")
check(raises(stats_tools.sample_size_two_proportions, 0.10, 0.0), "rejects a zero effect")

print("\nBenjamini-Hochberg")
adj = stats_tools.benjamini_hochberg([0.01, 0.04, 0.03, 0.20])
check(all(close(a, b, 1e-9) for a, b in zip(adj, [0.04, 0.16 / 3, 0.16 / 3, 0.20])),
      "adjusted values are monotone step-up and returned in input order")
check(stats_tools.benjamini_hochberg([0.5]) == [0.5], "one test is unchanged")
check(max(stats_tools.benjamini_hochberg([0.9, 0.95, 0.99])) <= 1.0, "adjusted values cap at 1")
check(raises(stats_tools.benjamini_hochberg, [1.5]), "rejects a p value above 1")

print("\nmonte carlo product")
ranges = [(1e6, 5e6), (0.01, 0.05), (20.0, 40.0)]
res = stats_tools.monte_carlo_product(ranges, "loguniform", 20000, seed=1)
check(res["p05"] < res["p50"] < res["p95"], "percentiles are ordered")
check(res["naive_low"] < res["p05"] and res["p95"] < res["naive_high"],
      "90 percent range sits inside the product of the range ends")
check(close(res["p50"] / res["geometric_midpoint_product"], 1.0, 0.1),
      "log-uniform median is near the product of geometric midpoints")
again = stats_tools.monte_carlo_product(ranges, "loguniform", 20000, seed=1)
check(again == res, "a fixed seed is reproducible")
check(raises(stats_tools.parse_range, "0:10", "loguniform"), "log-uniform rejects a zero bound")
check(raises(stats_tools.parse_range, "5:1:10", "triangular"), "triangular rejects a mode below low")

print("\ncommand line")
rc, out, _ = run_cli(["samplesize", "0.10", "0.02"])
check(rc == 0 and out.startswith("3841 per arm"), "samplesize subcommand prints the per arm figure")
rc, out, _ = run_cli(["wilson", "8", "10"])
check(rc == 0 and "0.4902 to 0.9433" in out, "wilson subcommand prints the interval")
rc, _, err = run_cli(["wilson", "11", "10"])
check(rc == 2 and "error" in err, "invalid input exits 2 with a message")

print()
if failures:
    print("%d check(s) failed" % len(failures))
    sys.exit(1)
print("all checks passed")
