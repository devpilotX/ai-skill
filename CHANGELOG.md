# Changelog

All notable changes to this repository. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and versions follow
[Semantic Versioning](https://semver.org/). Each skill also carries its own version in its frontmatter.

## [1.2.0] - 2026-09-26

Thirty six skills and ten agents. This release adds seven quantitative finance skills, ships the suite's
first agents for Kiro and Claude Code, and brings every existing skill up to the shape CONTRIBUTING.md
asks for, with the validator now enforcing it.

### Added

- `quant-research`: systematic signal and strategy research with point-in-time data, a trial registry, purged and embargoed validation, the probabilistic and deflated Sharpe ratio, costs and capacity, and dated kill criteria. Ships `scripts/strategy_stats.py`, checked against the published deflated Sharpe ratio example.
- `portfolio-risk`: covariance shrinkage and random matrix denoising, factor models, minimum variance, risk parity and fractional Kelly construction, Euler risk contributions, VaR and expected shortfall with Kupiec backtests, stress and liquidity testing, and limit design. Ships `scripts/risk_lab.py`.
- `execution-microstructure`: implementation shortfall, the square root impact law, Almgren-Chriss schedules, markouts and adverse selection, market structure, and market making after Avellaneda and Stoikov. Ships `scripts/execution_cost.py`.
- `derivatives-pricing`: forwards and parity, static and calendar arbitrage checks, surface models (SVI, SABR, Heston, local volatility), numerical validation, and P&L attribution by Greeks. Ships `scripts/options_lab.py`.
- `stat-arb`: pairs, baskets and residual mean reversion with Engle-Granger critical values, Ornstein-Uhlenbeck fits, search correction, out-of-sample rules and break detection. Ships `scripts/pairs_lab.py`.
- `trading-systems`: pre-trade controls, kill switches, order state machines, market data recovery, backtest and live parity, reconciliation and atomic deployment. Ships `scripts/pretrade_check.py`, a reference model for testing a risk gateway.
- `quant-reasoning`: formal probability, expected value, Bayesian updating, Kelly sizing, ruin, market making games and forecast scoring. Ships `scripts/edge_calc.py`.
- Ten agents in `agents/`, written once in `agents/src/` and generated for Kiro and Claude Code by `tools/build_agents.py`: build-lead, code-reviewer, release-auditor, incident-debugger, technical-writer, strategy-advisor, quant-researcher, risk-manager, derivatives-desk and trading-systems-engineer.
- New scripts in existing skills: `numbers-check/scripts/stats_tools.py` (Wilson intervals, two-proportion tests, sample size, Benjamini-Hochberg, Monte Carlo ranges), `business-model/scripts/unit_economics.py` (decimal unit economics, cash cycle, LTV, peak funding) and `finance-books/scripts/reconcile.py` (bank reconciliation with transposition and sign error detection).
- Twenty nine new reference files across the existing skills, and seventeen for the quantitative skills, including online DDL by engine, LLM and agent security, rollout playbooks, SLO burn rate alerting, web security controls, store review, accessibility, Web Vitals, measurement, and techniques by symptom.
- `tools/run_tests.py`, `tools/release_notes.py`, `CHANGELOG.md`, `SECURITY.md`, `CODE_OF_CONDUCT.md`, issue and pull request templates, `CODEOWNERS` and Dependabot configuration for workflow actions.

### Changed

- Every skill now has an activation section with an off switch, numbered non-negotiables, a self-audit and a statement of what it cannot do, and routes overlapping requests to the sibling skill that owns them. All 29 existing skills moved to version 1.1.0.
- `tools/validate_skills.py` enforces the required sections, the off switch, semantic versions in metadata, reachability of every reference and script from SKILL.md, typo detection for skill names, agent validity, CRLF and UTF-8 hygiene, and exact README links.
- `tools/build_dist.sh` builds reproducible zips (sorted entries, fixed timestamps), adds `ai-skill-agents.zip`, no longer deletes caches from the source tree, and works on macOS.
- CI runs on Python 3.9, 3.12 and 3.14 with pinned action SHAs, concurrency and timeouts. The release workflow has a single trigger, builds from the tag, takes its notes from this changelog, and grants write permission only to the publishing job.

### Fixed

- `md2doc.py`: attribute injection through image alt text and link text, `javascript:` and `data:` links, double escaping of `&` in URLs, nested anchors, indented code, list nesting and continuation, table pipes inside code, CRLF frontmatter, stale PDF detection, missing subprocess timeouts, and a path that could overwrite an input file.
- `ai_tells.py`: high severity false positives on "todo", links whose text starts with "your", "not widely available", and email sign-offs; dead patterns for "Certainly!" and "Overall,"; unclosed frontmatter hiding a whole file; tilde fences; setext underlines; the trade mark sign as emoji; phrase matching without word boundaries; density on very short files; and a mistyped path exiting 0.
- Technical corrections in the existing skills, among them: composite index column order (equality, sort, range), per engine isolation defaults, `EXPLAIN ANALYZE` executing its statement, liveness probes that check dependencies, variance used where spread was meant, the induction rule and the p-value definition in `numbers-check`, the working capital unit error in `business-model`, the retained earnings identity in `finance-books`, pay transparency law in `job-hunt`, and several unsourced figures that are now retrieved, cited or labelled as assumptions.

## [1.1.0] - 2026-09-22

### Added

- Seventeen engineering skills and the `build-pilot` orchestrator, which runs a build as seven stages with gates: think, research, discuss, decide, plan, build, verify.

## [1.0.0] - 2026-09-22

### Added

- Twelve skills, the style detector, the Markdown converter, the validator, CI and the release workflow.

[1.2.0]: https://github.com/devpilotX/ai-skill/compare/v1.1.0...v1.2.0
[1.1.0]: https://github.com/devpilotX/ai-skill/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/devpilotX/ai-skill/releases/tag/v1.0.0
