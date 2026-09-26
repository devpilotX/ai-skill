# Numerical methods and model validation

Every pricer gets three checks: a limit with a closed form, convergence as resolution increases, and
agreement with an independent method. Record all three.

## Monte Carlo

Error falls with the square root of the number of paths. Report the standard error with every price.
`scripts/options_lab.py mc` compares a Monte Carlo price with the closed form and fails if they differ by
more than three standard errors.

Variance reduction:

- Antithetic variates: pair each normal draw with its negative. Cheap, and effective for monotone payoffs.
- Control variates: price a related instrument with a known value on the same paths (a European with the Black-Scholes price, a geometric Asian for an arithmetic Asian) and correct by the observed error.
- Importance sampling: shift the drift toward the region that pays, for deep out of the money options and tail risk.
- Quasi Monte Carlo: low discrepancy sequences (Sobol) with Brownian bridge construction converge faster for smooth payoffs in moderate dimensions.

Discretisation: exact simulation of geometric Brownian motion needs no time steps for European payoffs.
Path dependent payoffs need steps; bias from discrete monitoring and from Euler steps in stochastic
volatility models must be measured by halving the step and comparing.

Seeds: fix and record them. A result that changes with the seed by more than the standard error suggests
a bug.

## Greeks by simulation

Bump and reprice with common random numbers (the same paths for the up and down bump), with a central
difference. Without common random numbers, the noise swamps the difference. Pathwise derivatives work for
payoffs differentiable almost everywhere (not digitals). Likelihood ratio estimators handle discontinuous
payoffs at the cost of variance. Adjoint algorithmic differentiation computes all sensitivities at a cost
of a few pricings.

## Finite differences

Solve the pricing PDE on a grid in the underlying (often in log space) and time.

- Explicit schemes are conditionally stable: the time step must be small relative to the square of the space step.
- Implicit schemes are stable and first order in time.
- Crank-Nicolson is second order but produces spurious oscillations in Greeks for non-smooth payoffs (the kink at the strike). Take a few fully implicit steps at the start (Rannacher smoothing), or smooth the payoff.
- Place grid nodes on the strike and barriers, and far enough out that boundary conditions do not distort the price. Test by moving the boundary.
- American exercise: projected successive over-relaxation, or a penalty method, at each step.

## Lattices

Binomial and trinomial trees converge to Black-Scholes with oscillation in the number of steps for vanilla
options; averaging two adjacent step counts or aligning a node with the strike reduces it. Good for
American options and teaching; slower than finite differences for the same accuracy.

## Least squares Monte Carlo

Longstaff and Schwartz (2001, "Valuing American Options by Simulation: A Simple Least-Squares Approach",
Review of Financial Studies): at each exercise date regress discounted future cash flows on basis functions
of the state, over in-the-money paths only, and exercise when intrinsic value exceeds the fitted
continuation value. Gives a low-biased estimate; a dual method (Andersen and Broadie) gives an upper bound.
Report both where the difference matters.

## Calibration

Least squares in implied volatility or vega-weighted price, with parameter bounds. Use several starting
points to detect local minima. Check identification: if two parameters can offset each other (vol of vol
and correlation in some regimes), the calibration will drift between equivalent fits and the Greeks will
jump. Regularise toward the previous day's parameters to stabilise, and report the cost in fit quality.

## Validation checklist

- Known limits: zero volatility gives the discounted intrinsic value of the forward; zero expiry gives the payoff; deep in the money call approaches the discounted forward minus the discounted strike.
- Parity: put-call parity holds to numerical precision for European pricers.
- Symmetries: for Black-Scholes, call delta minus put delta equals the dividend discount factor.
- Convergence: price and Greeks against grid size, time steps and paths, with the observed order.
- Independent method: a second pricer (analytic, PDE or Monte Carlo) agrees within tolerance.
- Stress: extreme but plausible inputs (very short expiry, very high volatility, deep wings) do not produce negative prices, NaN, or Greeks with the wrong sign.
- Regression tests: a fixed set of trades with stored prices, rerun on every code change.

In regulated banks, model risk management follows supervisory guidance such as the US Federal Reserve and
OCC SR 11-7, "Guidance on Model Risk Management" (2011): independent validation, documentation, ongoing
monitoring and an inventory of models. The checklist above is the technical core of that process.
