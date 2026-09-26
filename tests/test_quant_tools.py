#!/usr/bin/env python3
"""Tests for the scripts shipped with the quantitative skills.

Each function is checked against a published worked example, a closed form, or an
identity that must hold, plus the input validation and exit codes.

Run with: python3 tests/test_quant_tools.py
"""

from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import math
import random
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = {
    "strategy_stats": ROOT / "skills" / "quant-research" / "scripts" / "strategy_stats.py",
    "risk_lab": ROOT / "skills" / "portfolio-risk" / "scripts" / "risk_lab.py",
    "execution_cost": ROOT / "skills" / "execution-microstructure" / "scripts" / "execution_cost.py",
    "options_lab": ROOT / "skills" / "derivatives-pricing" / "scripts" / "options_lab.py",
    "pairs_lab": ROOT / "skills" / "stat-arb" / "scripts" / "pairs_lab.py",
    "pretrade_check": ROOT / "skills" / "trading-systems" / "scripts" / "pretrade_check.py",
    "edge_calc": ROOT / "skills" / "quant-reasoning" / "scripts" / "edge_calc.py",
}


def load(name: str):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS[name])
    assert spec and spec.loader, "cannot load %s" % SCRIPTS[name]
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


ss = load("strategy_stats")
rl = load("risk_lab")
ec = load("execution_cost")
ol = load("options_lab")
pl = load("pairs_lab")
pt = load("pretrade_check")
eg = load("edge_calc")

failures: list = []


def check(condition: bool, message: str) -> None:
    if condition:
        print("  pass  %s" % message)
    else:
        print("  FAIL  %s" % message)
        failures.append(message)


def close(a: float, b: float, tol: float) -> bool:
    return abs(a - b) <= tol


def cli(module, argv: list) -> tuple:
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        rc = module.main(argv)
    return rc, out.getvalue(), err.getvalue()


def raises(func, *args, **kwargs) -> bool:
    try:
        func(*args, **kwargs)
    except ValueError:
        return True
    return False


tmp_dir = tempfile.TemporaryDirectory()
TMP = Path(tmp_dir.name)

print("\nstrategy_stats: deflated Sharpe ratio")
# Bailey and Lopez de Prado (2014) worked example: annual SR 2.5 over 1250 daily
# observations, skew -3, kurtosis 10, 100 trials with annualised SR variance 0.5.
sr0 = ss.expected_max_sharpe(100, 0.5)
check(close(sr0, 1.789, 0.002), "expected max Sharpe of 100 null trials is about 1.79")
dsr = ss.psr(2.5 / math.sqrt(250), sr0 / math.sqrt(250), 1250, -3, 10)
check(close(dsr, 0.9004, 0.0005), "DSR matches the published 0.9004")
check(ss.min_track_record(0.1, 0.2, 0, 3) == math.inf, "no track record suffices below the benchmark")
check(close(ss.psr(0.1, 0.1, 100, 0, 3), 0.5, 1e-12), "PSR at its own benchmark is one half")

print("\nstrategy_stats: moments, drawdown, Lo correction")
m = ss.moments([0.01, -0.02, 0.03, 0.0])
check(close(m["mean"], 0.005, 1e-12) and close(m["sd"], math.sqrt(0.0013 / 3), 1e-12),
      "mean and sample sd")
dd = ss.drawdown([0.1, -0.5, 0.2, 0.5])
check(close(dd["max_drawdown"], 0.5, 1e-12), "drawdown of a 50 percent fall is 0.5")
check(close(dd["total_return"], 1.1 * 0.5 * 1.2 * 1.5 - 1, 1e-12), "compounded total return")
rng = random.Random(3)
iid = [rng.gauss(0.001, 0.01) for _ in range(2000)]
lo = ss.lo_adjusted_annual_sharpe(0.1, iid, 12)
check(close(lo, 0.1 * math.sqrt(12), 0.05), "Lo correction is close to sqrt(q) for iid returns")
ar = [0.0]
for _ in range(3000):
    ar.append(0.5 * ar[-1] + rng.gauss(0.001, 0.01))
check(ss.lo_adjusted_annual_sharpe(0.1, ar, 12) < 0.1 * math.sqrt(12),
      "positive autocorrelation lowers the annualised Sharpe")
nw = ss.newey_west_t(iid)
check(nw["lags"] == int(4 * (2000 / 100) ** (2 / 9)), "Newey-West default lag rule")
check(raises(ss.moments, [0.1, 0.1, 0.1]), "zero variance is rejected")
series = TMP / "r.csv"
series.write_text("date,pnl\n" + "".join("d%d,%.6f\n" % (i, v) for i, v in enumerate(iid)),
                  encoding="utf-8")
rc, out, _ = cli(ss, [str(series), "--column", "pnl", "--periods", "252", "--trials", "50",
                      "--trial-sr-var", "0.3", "--json"])
data = json.loads(out) if rc == 0 else {}
check(rc == 0 and 0 <= data.get("dsr", -1) <= 1 and data["n"] == 2000, "CLI reports DSR as JSON")
rc, _, err = cli(ss, [str(series), "--column", "nope", "--periods", "252"])
check(rc == 2 and "not found" in err, "missing column exits 2")

print("\nrisk_lab")
cov = [[0.04, 0.0, 0.0], [0.0, 0.01, 0.0], [0.0, 0.0, 0.09]]
w = rl.risk_parity(cov)
check(all(close(a, b, 1e-8) for a, b in zip(w, [3 / 11, 6 / 11, 2 / 11])),
      "risk parity with no correlation is inverse volatility")
cov2 = [[0.04, 0.006, 0.012], [0.006, 0.01, 0.003], [0.012, 0.003, 0.09]]
w2 = rl.risk_parity(cov2)
sigma, rc_ = rl.risk_contributions(cov2, w2)
check(all(close(c / sigma, 1 / 3, 1e-6) for c in rc_), "risk parity equalises contributions")
check(close(math.fsum(rc_), sigma, 1e-12), "Euler contributions sum to portfolio sd")
mv = rl.min_variance(cov)
check(all(close(a, b, 1e-12) for a, b in zip(mv, [9 / 49, 36 / 49, 4 / 49])),
      "minimum variance with a diagonal covariance is inverse variance")
check(all(close(a, b, 1e-9) for a, b in zip(rl.jacobi_eigenvalues([[2, 1], [1, 2]]), [3, 1])),
      "Jacobi eigenvalues of a 2x2")
check(close(rl.marchenko_pastur_edge(50, 200), (1 + math.sqrt(0.25)) ** 2, 1e-12),
      "Marchenko-Pastur edge")
lr, p = rl.kupiec(9, 250, 0.99)
check(close(lr, 10.229, 0.01) and p < 0.01, "Kupiec rejects 9 exceptions in 250 at 99 percent")
lr, p = rl.kupiec(2, 250, 0.99)
check(p > 0.5, "Kupiec does not reject 2 exceptions in 250")
var, es = rl.historical_var_es([-0.05, -0.01, 0.0, 0.01, 0.02] * 20, 0.95)
check(close(var, 0.05, 1e-12) and es >= var, "historical VaR and ES ordering")
rows = [[rng.gauss(0, 0.01) for _ in range(4)] for _ in range(60)]
lw, shrink = rl.ledoit_wolf(rows)
check(0 <= shrink <= 1, "Ledoit-Wolf intensity lies in [0, 1]")
check(all(close(lw[i][j], lw[j][i], 1e-15) for i in range(4) for j in range(4)), "shrunk matrix is symmetric")
returns_csv = TMP / "assets.csv"
returns_csv.write_text("A,B,C,D\n" + "".join(",".join("%.6f" % v for v in r) + "\n" for r in rows),
                       encoding="utf-8")
rc, out, _ = cli(rl, ["contrib", str(returns_csv), "--weights", "A=0.25", "B=0.25", "C=0.25", "D=0.25"])
check(rc == 0 and "risk contribution" in out, "contrib CLI")
rc, _, err = cli(rl, ["contrib", str(returns_csv), "--weights", "Z=1"])
check(rc == 2 and "unknown asset" in err, "unknown asset exits 2")

print("\nexecution_cost")
r = ec.almgren_chriss(1e6, 5, 5, 0.95, 2.5e-6, 2.5e-7, 0.0625, 1e-6)
check(close(r["kappa"], 0.607, 0.002), "Almgren-Chriss kappa for the paper's parameters is about 0.6 per day")
check(r["holdings"][0] == 1e6 and r["holdings"][-1] == 0.0, "schedule starts full and ends flat")
check(all(a > b for a, b in zip(r["holdings"], r["holdings"][1:])), "holdings fall monotonically")
twap = ec.almgren_chriss(1e6, 5, 5, 0.95, 2.5e-6, 2.5e-7, 0.0625, 0.0)
eta_t = 2.5e-6 - 2.5e-7 / 2
check(close(twap["expected_cost"], 0.5 * 2.5e-7 * 1e12 + 0.0625 * 1e6 + eta_t * 1e12 / 5, 1e-6),
      "zero risk aversion gives the TWAP cost formula")
check(r["std_cost"] < twap["std_cost"] and r["expected_cost"] > twap["expected_cost"],
      "risk aversion trades expected cost for lower variance")
sq = ec.sqrt_impact(250000, 5e6, 0.02, 40, 1.0, 4)
check(close(sq["impact_bps"], 200 * math.sqrt(0.05), 1e-9), "square root impact in bps")
sf = ec.shortfall("buy", 50, 50.1, [(3000, 50.15), (5000, 50.22)], 10000, 50.4, 12.5)
check(close(sf["delay"], 800, 1e-6) and close(sf["execution"], 750, 1e-6)
      and close(sf["opportunity"], 800, 1e-6), "Perold shortfall components")
check(close(sf["total"], sf["delay"] + sf["execution"] + sf["opportunity"] + sf["fees"], 1e-9),
      "shortfall components add up")
sell = ec.shortfall("sell", 50, 49.9, [(1000, 49.8)], 1000, 49.0)
check(sell["delay"] > 0 and sell["execution"] > 0, "a falling price is a cost for a seller")
av = ec.avellaneda_stoikov(100, 5, 0.1, 2, 0.5, 1.5)
check(close(av["reservation"], 99.0, 1e-12) and close(av["ask"] - av["bid"], av["spread"], 1e-12),
      "Avellaneda-Stoikov reservation price skews against inventory")
check(raises(ec.shortfall, "buy", 50, 50, [(20000, 50)], 10000, 50), "overfill is rejected")

print("\noptions_lab")
c = ol.bsm(100, 100, 0.05, 0.2, 1)
p = ol.bsm(100, 100, 0.05, 0.2, 1, call=False)
check(close(c["price"], 10.4506, 1e-4) and close(p["price"], 5.5735, 1e-4), "textbook BSM prices")
check(close(c["delta"], 0.6368, 1e-4) and close(c["gamma"], 0.018762, 1e-6)
      and close(c["vega"], 37.524, 1e-3), "textbook Greeks")
check(close(ol.parity_gap(c["price"], p["price"], 100, 100, 0.05, 1), 0.0, 1e-12), "put-call parity holds")
bump = 1e-4
num_delta = (ol.bsm(100 + bump, 100, 0.05, 0.2, 1, 0.02)["price"]
             - ol.bsm(100 - bump, 100, 0.05, 0.2, 1, 0.02)["price"]) / (2 * bump)
check(close(num_delta, ol.bsm(100, 100, 0.05, 0.2, 1, 0.02)["delta"], 1e-6),
      "analytic delta matches a central difference with dividends")
num_theta = -(ol.bsm(100, 100, 0.05, 0.2, 1 + bump)["price"] - ol.bsm(100, 100, 0.05, 0.2, 1 - bump)["price"]) / (2 * bump)
check(close(num_theta, c["theta"], 1e-5), "analytic theta matches a central difference")
check(close(ol.implied_vol(c["price"], 100, 100, 0.05, 1), 0.2, 1e-8), "implied vol round trip")
check(close(ol.implied_vol(ol.bsm(100, 150, 0.05, 0.6, 0.25)["price"], 100, 150, 0.05, 0.25), 0.6, 1e-7),
      "implied vol far out of the money")
check(raises(ol.implied_vol, 0.01, 100, 50, 0.05, 1), "price below intrinsic has no implied vol")
check(close(ol.black(100, 100, 0.05, 0.2, 1)["price"], math.exp(-0.05) * 7.9656, 1e-3), "Black-76")
est, se = ol.monte_carlo(100, 100, 0.05, 0.2, 1, paths=40000, seed=7)
check(abs(est - c["price"]) < 4 * se, "Monte Carlo agrees with the closed form")
check(ol.check_chain([(90, 15), (100, 8), (110, 4)], 0.0, 0.25) == [], "clean chain passes")
check(any("convexity" in m for m in ol.check_chain([(90, 15), (100, 9.9), (110, 4)], 0.0, 0.25)),
      "negative butterfly detected")
check(any("slope" in m for m in ol.check_chain([(90, 5), (100, 8)], 0.0, 0.25)),
      "call price rising with strike detected")
check(ol.check_calendar([(0.25, 0.30), (0.5, 0.25)]) == [], "total variance increasing passes")
check(len(ol.check_calendar([(0.25, 0.40), (0.5, 0.25)])) == 1, "calendar arbitrage detected")
chain = TMP / "chain.csv"
chain.write_text("strike,call\n90,15\n100,9.9\n110,4\n", encoding="utf-8")
rc, out, _ = cli(ol, ["chain", str(chain), "--expiry", "0.25"])
check(rc == 1 and "ARBITRAGE" in out, "chain CLI exits 1 on arbitrage")

print("\npairs_lab")
rng = random.Random(11)
s = [0.0]
for _ in range(1500):
    s.append(0.9 * s[-1] + rng.gauss(0, 1))
ou = pl.ou_fit(s)
check(close(ou["half_life"], math.log(2) / -math.log(0.9), 1.0), "OU half-life recovered near 6.6")
check(pl.adf(s, 1)["stat"] < pl.ADF_CRITICAL["1%"], "ADF rejects a unit root for AR(1) 0.9")
walk = [0.0]
for _ in range(1500):
    walk.append(walk[-1] + rng.gauss(0, 1))
check(pl.adf(walk, 1)["stat"] > pl.ADF_CRITICAL["5%"], "ADF does not reject for a random walk")
x = [100.0]
for _ in range(1500):
    x.append(x[-1] + rng.gauss(0, 1))
y = [2.0 * xi + 5 + si for xi, si in zip(x, s)]
alpha, beta, resid = pl.hedge_ratio(y, x)
check(close(beta, 2.0, 0.05), "hedge ratio recovered")
check(pl.adf(resid, 1)["stat"] < pl.EG_CRITICAL["1%"], "Engle-Granger finds the cointegrated pair")
check(close(pl.zscore([1, 2, 3, 4, 5]), (5 - 3) / math.sqrt(2.5), 1e-12), "z-score of the last value")
check(pl.verdict(-3.5, pl.EG_CRITICAL) == "rejects a unit root at 5%", "verdict uses the strictest level passed")

print("\npretrade_check")
limits = {"max_order_qty": 1000, "max_order_notional": 50000, "price_collar_pct": 5,
          "max_position": {"*": 1500}, "max_orders_per_second": 2, "restricted": ["BAD"],
          "kill_after_rejects": 3, "kill_window_seconds": 10}
orders = [
    pt.Order(2, 0.0, "a", "XYZ", "buy", 500, 50, 50),
    pt.Order(3, 0.1, "b", "XYZ", "buy", 2000, 50, 50),
    pt.Order(4, 0.2, "a", "XYZ", "buy", 10, 50, 50),
    pt.Order(5, 2.0, "c", "XYZ", "buy", 10, 60, 50),
    pt.Order(6, 3.0, "d", "BAD", "buy", 10, 10, 10),
    pt.Order(7, 4.0, "e", "XYZ", "sell", 10, 50, 50),
]
res = pt.check_orders(orders, limits)
reasons = [r for _, r in res]
check(reasons[0] == [], "a clean order is accepted")
check(any("max_order_qty" in m for m in reasons[1]), "oversize order rejected")
check(any("duplicate" in m for m in reasons[2]), "duplicate client order id rejected")
check(any("collar" in m for m in reasons[3]) and any("kill switch tripped" in m for m in reasons[3]),
      "collar breach rejected and the kill switch trips on the third reject")
check(any("kill switch active" in m for m in reasons[5]), "orders after the kill switch are rejected")
burst = [pt.Order(i, 0.1 * i, "o%d" % i, "XYZ", "buy", 1, 50, 50) for i in range(4)]
rate = [r for _, r in pt.check_orders(burst, {"max_orders_per_second": 2})]
check(rate[0] == [] and rate[1] == [] and any("rate" in m for m in rate[2]), "order rate limit")
pos = [pt.Order(2, 0, "p1", "XYZ", "buy", 1000, 1, None), pt.Order(3, 1, "p2", "XYZ", "buy", 600, 1, None)]
check(any("position" in m for m in pt.check_orders(pos, {"max_position": {"XYZ": 1500}})[1][1]),
      "position limit counts accepted orders as filled")
check(any("reference" in m for m in pt.check_orders(pos[:1], {"price_collar_pct": 5})[0][1]),
      "a missing reference price is a reject, not a pass")
lim_path = TMP / "limits.json"
lim_path.write_text(json.dumps({"max_order_qty": 5, "typo_key": 1}), encoding="utf-8")
ord_path = TMP / "orders.csv"
ord_path.write_text("ts,id,symbol,side,qty,price\n0,a,XYZ,buy,1,10\n", encoding="utf-8")
rc, _, err = cli(pt, [str(ord_path), str(lim_path)])
check(rc == 2 and "unknown limit" in err, "an unknown limit key is an error, not ignored")

print("\nedge_calc")
check(close(eg.kelly_fraction(0.55, 1), 0.10, 1e-12), "Kelly for 55 percent at even odds is 10 percent")
check(eg.kelly_fraction(0.4, 1) < 0, "negative edge gives a negative Kelly fraction")
f = eg.kelly_fraction(0.6, 2)
check(eg.log_growth(0.6, 2, f) > eg.log_growth(0.6, 2, f * 0.5) > 0, "growth peaks at Kelly")
check(eg.log_growth(0.55, 1, 0.2) < 0.001, "twice Kelly gives roughly zero growth")
post = eg.bayes(0.001, [0.99 / 0.02])
check(close(post, 0.0472, 0.0005), "rare condition with a good test stays unlikely")
ev = eg.expected_value([(100, 0.2), (-20, 0.8)])
check(close(ev["ev"], 4.0, 1e-12), "expected value")
check(raises(eg.expected_value, [(1, 0.5), (2, 0.4)]), "probabilities that do not sum to 1 are rejected")
lo_risk = eg.ruin_probability(0.55, 1, 0.05, 300, 0.5, 2000, seed=1)["probability"]
hi_risk = eg.ruin_probability(0.55, 1, 0.3, 300, 0.5, 2000, seed=1)["probability"]
check(lo_risk < hi_risk, "over-betting raises the chance of halving the bankroll")
sc = eg.score([(0.9, 1), (0.1, 0), (0.8, 1), (0.3, 0)])
check(close(sc["brier"], (0.01 + 0.01 + 0.04 + 0.09) / 4, 1e-12), "Brier score")
rc, out, _ = cli(eg, ["kelly", "--p", "0.45", "--odds", "1"])
check(rc == 0 and "do not bet" in out, "CLI refuses to size a negative edge")

print("\nregressions from review")
check(any("collar" in m or "reference" in m
          for m in pt.check_orders([pt.Order(2, 0, "n", "XYZ", "buy", 1, 50, float("nan"))],
                                   {"price_collar_pct": 5})[0][1]),
      "a non-finite reference price fails the collar")
check(raises(pt.validate_limits, {"restricted": "ABC"}), "a string restricted list is rejected")
check(raises(pt.validate_limits, {"max_order_qty": None}), "a null limit is rejected")
check(raises(pt.validate_limits, {"max_position": 100}), "max_position must be a mapping")
flat = [pt.Order(2, 0, "g1", "XYZ", "buy", 100, 10, None), pt.Order(3, 1, "g2", "XYZ", "sell", 100, 10, None),
        pt.Order(4, 2, "g3", "XYZ", "buy", 100, 10, None)]
check(all(r == [] for _, r in pt.check_orders(flat, {"max_gross_notional": 1500})),
      "gross exposure nets a round trip instead of accumulating traded notional")
bad_limits = TMP / "bad.json"
bad_limits.write_text(json.dumps({"max_position": 5}), encoding="utf-8")
rc, _, _ = cli(pt, [str(ord_path), str(bad_limits)])
check(rc == 2, "malformed limits exit 2, not the rejection code 1")
wide = TMP / "wide.csv"
wide.write_text("ts,id,symbol,side,qty,price\n0,a,XYZ,buy,1,10,extra\n", encoding="utf-8")
rc, _, _ = cli(pt, [str(wide), str(lim_path)])
check(rc == 2, "a row with extra fields is an input error")
indexed = TMP / "indexed.csv"
indexed.write_text(",pnl\n0,0.01\n1,-0.02\n2,0.03\n3,0.0\n", encoding="utf-8")
rc, _, err = cli(ss, [str(indexed), "--periods", "252"])
check(rc == 2 and "--column" in err, "a multi-column file needs --column")
short = [rng.gauss(0.001, 0.01) for _ in range(40)]
check(isinstance(ss.analyse(short, 252), dict), "a short daily series still gives a full report")
tw = ec.almgren_chriss(1e6, 1, 10, 0.95, 2.5e-6, 0.0, 0.0, 1e-20)
check(tw["holdings"][-1] == 0.0, "negligible risk aversion does not divide by zero")
fast = ec.almgren_chriss(1e6, 23400, 100, 0.01, 2.5e-6, 0.0, 0.0, 1e-2)
check(fast["holdings"][0] == 1e6 and all(math.isfinite(h) for h in fast["holdings"]),
      "large kappa T does not overflow")
deep = ol.implied_vol(ol.bsm(100, 300, 0.0, 0.5, 0.1)["price"], 100, 300, 0.0, 0.1)
check(close(deep, 0.5, 1e-4), "implied vol of a tiny deep out of the money price is found, not the start guess")
check(raises(eg.expected_value, [(1, float("nan"))]), "NaN probabilities are rejected")

tmp_dir.cleanup()
print()
if failures:
    print("%d check(s) failed" % len(failures))
    sys.exit(1)
print("all checks passed")
