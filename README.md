# ai-skill

[![ci](https://github.com/devpilotX/ai-skill/actions/workflows/ci.yml/badge.svg)](https://github.com/devpilotX/ai-skill/actions/workflows/ci.yml)
[![release](https://img.shields.io/github/v/release/devpilotX/ai-skill)](https://github.com/devpilotX/ai-skill/releases/latest)
[![licence](https://img.shields.io/badge/licence-MIT-blue)](LICENSE)

Thirty six agent skills and ten agents built around one rule: say the true thing, in the user's own situation, without
the accent of machine writing.

They exist because of two failures that show up in almost every assistant. The first is flattery,
which produces agreement instead of assessment. The second is convergence, which hands every user the
same high probability answer. Fixing only the first gives you a confident, rude, generic answer, which
is not an improvement.

Works in [Kiro](https://kiro.dev/docs/skills.md) and in any tool that reads the open
[Agent Skills specification](https://agentskills.io/specification), including Claude Code.

## The skills

Thirty six of them, in five groups. Every one has an activation section with an off switch, numbered
non-negotiables, a self-audit, and a statement of what it cannot do, and the validator fails the build if
any of those is missing.

### Running the work

| Skill | What it does |
|---|---|
| [build-pilot](skills/build-pilot/) | The whole build as seven staged phases: think, research, argue with itself, decide, plan, implement, verify. Gates where your input is needed. Writes no code before the deciding facts are verified. |
| [arch-decide](skills/arch-decide/) | Classifies a decision by what reversal costs, spends effort in proportion, and writes the decision record. Refuses complexity your team size cannot operate. |
| [release-manage](skills/release-manage/) | Separates deploying code from releasing behaviour, so a bad change is a toggle rather than an incident. |
| [migration-plan](skills/migration-plan/) | Incremental migration with both systems running and every step reversible. No cutover weekend. |
| [devex-tooling](skills/devex-tooling/) | One command from clean checkout to running, with pinned versions and a feedback loop short enough that nobody skips it. |

### Building software

| Skill | What it does |
|---|---|
| [frontend-build](skills/frontend-build/) | The six data states most interfaces omit, state in the narrowest scope that works, accessibility during the build, bundle size budgeted in kilobytes. |
| [backend-build](skills/backend-build/) | Object level authorisation, a stated concurrency assumption per write path, timeouts everywhere, idempotency before the retry arrives. |
| [data-layer](skills/data-layer/) | Schemas, indexes read from the query plan, and migrations treated as production operations with a lock estimate. |
| [mobile-build](skills/mobile-build/) | Offline behaviour decided before the screens, process death survived, store rejection causes covered. |
| [ml-build](skills/ml-build/) | Evaluation set and trivial baseline before the model. Treats a good score as leakage until proven otherwise. |
| [infra-deploy](skills/infra-deploy/) | Simplest hosting the requirements allow, rollback actually performed once, cost estimated from retrieved prices. |
| [observability-setup](skills/observability-setup/) | Works back from the questions you need answered at 3am. Every alert has an owner and an action. |
| [security-hardening](skills/security-hardening/) | Threat model first, findings ranked by reachability, advisories retrieved rather than recalled. |

### Keeping it working

| Skill | What it does |
|---|---|
| [ship-audit](skills/ship-audit/) | Twelve gate production readiness audit with a fixed severity to verdict rule. Every finding names a file, a line, the trigger, and what is lost. |
| [code-review](skills/code-review/) | Defects that cost something. Ignores anything a linter owns. Reports a clean change as clean. |
| [test-strategy](skills/test-strategy/) | Effort allocated by what a failure costs. Says plainly that coverage percentage measures execution, not correctness. |
| [debug-method](skills/debug-method/) | Reproduce, then one hypothesis at a time with a prediction that can be wrong. A symptom that stopped is not a fix. |
| [performance-tuning](skills/performance-tuning/) | Profile first, fix the dominant cost, report before and after from the same method. |
| [refactor-safely](skills/refactor-safely/) | Never mixes a refactor with a behaviour change. Safety net first, small reversible steps, suite green between each. |

### Judgement and communication

| Skill | What it does |
|---|---|
| [reality-check](skills/reality-check/) | Names the answer every other user got, bans it, then judges your idea against your own non-transferable advantages. BUILD, PIVOT or KILL with dated kill criteria. |
| [human-prose](skills/human-prose/) | Removes the stylistic residue of machine writing, then verifies with a tested 23 rule detector rather than a judgement call. |
| [prompt-forge](skills/prompt-forge/) | Diagnoses which of six defects a prompt has and rewrites it. Refuses to invent a score out of ten. |
| [deep-research](skills/deep-research/) | Graded sources, reported contradictions, and an explicit list of what could not be established. |
| [numbers-check](skills/numbers-check/) | Recomputes with a script, carries units, cross-checks a second way, names the assumption that decides the result. Ships interval, power and multiple testing calculators. |
| [doc-forge](skills/doc-forge/) | Documents chosen by what the reader does next, plus a zero dependency Markdown to print ready HTML and PDF converter. |
| [business-model](skills/business-model/) | Contribution margin, the working capital cycle, break-even, payback, LTV from a retention curve. Models cash rather than only profit, with a decimal calculator. |
| [career-strategy](skills/career-strategy/) | Career decisions priced in years and money, anchored in your financial position and rare skill combinations. |
| [job-hunt](skills/job-hunt/) | Diagnoses which stage of the funnel is broken before rewriting anything. |
| [finance-books](skills/finance-books/) | Bookkeeping, reconciliation, period close and statement checking, with a reconciliation script. Stops at the line where a licensed accountant is required. |

### Quantitative finance

Written to the standard of institutional quant research, trading and risk desks: every figure computed by
a tested script, every model assumption named, and every backtest treated as a false discovery until the
evidence says otherwise. None of it is investment advice.

| Skill | What it does |
|---|---|
| [quant-research](skills/quant-research/) | Falsifiable hypothesis, point-in-time data, a counted trial budget, purged validation, deflated Sharpe ratio, costs and capacity, dated kill criteria. |
| [portfolio-risk](skills/portfolio-risk/) | Shrunk and denoised covariance, risk budgeting, fractional Kelly, VaR and expected shortfall with backtests, stress and liquidity tests, limits with owners. |
| [execution-microstructure](skills/execution-microstructure/) | Implementation shortfall from the decision price, square root impact, Almgren-Chriss schedules, markouts, market structure and market making. |
| [derivatives-pricing](skills/derivatives-pricing/) | Forward and parity first, arbitrage-free surfaces, validated numerics, Greeks with units, P&L explained by realised against implied volatility. |
| [stat-arb](skills/stat-arb/) | Pairs and residual reversion with Engle-Granger critical values, search correction, rules from the fitted half-life, and a break rule. |
| [trading-systems](skills/trading-systems/) | Pre-trade checks with no bypass, tested kill switches, order state machines, backtest and live parity, reconciliation, atomic deploys. |
| [quant-reasoning](skills/quant-reasoning/) | Probability set up formally and checked twice, expected value with variance, Bayesian updating, Kelly and ruin, market making games, forecast scoring. |

### How they chain

`build-pilot` is the entry point for anything substantial. It calls the others in order: `deep-research`
to verify the facts, `reality-check` to test the premise, `arch-decide` to record the choice, the build
skills to implement, `test-strategy` and `code-review` while working, then `ship-audit` before release.
For trading work, `quant-research` tests the idea, `execution-microstructure` prices the trading,
`portfolio-risk` sizes it, and `trading-systems` carries it into production. Each one also works alone,
and each routes a request that belongs to a sibling skill to that skill.

## Agents

Ten agents in [agents/](agents/) combine the skills into roles: build-lead, code-reviewer,
release-auditor, incident-debugger, technical-writer, strategy-advisor, quant-researcher, risk-manager,
derivatives-desk and trading-systems-engineer. Each is written once and generated for Kiro and for
Claude Code, with read-only roles kept read-only. Install steps are in [agents/README.md](agents/README.md).

## Install

Pick the scope you want.

Project scope, shared through a repository:

```
git clone https://github.com/devpilotX/ai-skill.git
mkdir -p your-project/.kiro/skills
cp -r ai-skill/skills/* your-project/.kiro/skills/
```

Personal scope in the Kiro IDE or CLI:

```
mkdir -p ~/.kiro/skills
cp -r ai-skill/skills/* ~/.kiro/skills/
```

Kiro Web and Mobile do not read `~/.kiro/skills`. Use Settings, then Skills, and upload a skill as a
zip. There are three ways to get one:

```
bash tools/build_dist.sh          # dist/<skill>.zip, ai-skill-all.zip and ai-skill-agents.zip
```

Per skill zips are attached to each [release](https://github.com/devpilotX/ai-skill/releases) by the
release workflow, alongside `SHA256SUMS.txt` for verification. The zips are reproducible, so the same
tag always gives the same checksums. The whole repository at a tag is also downloadable directly:

```
https://github.com/devpilotX/ai-skill/archive/refs/tags/v1.2.0.zip
```

For Claude Code, copy a skill folder into `.claude/skills/`. The format is the same.

## Use

Each skill activates from its description when your request matches, or explicitly as a slash command
named after the folder:

```
/build-pilot build a booking system for a two person dental practice
/reality-check I want to start a timber company with 30,000
/ship-audit check the payments service before Friday
/debug-method it works locally but 500s in production
/human-prose clean up the launch post
/quant-research is this momentum backtest real or overfit
/derivatives-pricing check this option chain for arbitrage
```

Every skill has an off switch. Saying "stop", "I've decided", or "just execute" ends it for the
session. Skills that nag get uninstalled.

## Working scripts

Most skill collections are documentation. Twelve of these skills ship code, all standard library Python
3.9 or later, each with tests under `tests/`.

| Script | What it computes |
|---|---|
| `skills/human-prose/scripts/ai_tells.py` | 23 classes of machine writing marker across three severities, with per file exemptions printed in every report |
| `skills/doc-forge/scripts/md2doc.py` | Markdown to self contained print ready HTML with safe links, and PDF through whichever engine is installed |
| `skills/numbers-check/scripts/stats_tools.py` | Wilson intervals, two-proportion tests, sample size, Benjamini-Hochberg, Monte Carlo ranges |
| `skills/business-model/scripts/unit_economics.py` | Contribution, break-even, cash conversion cycle, payback, LTV and peak funding in decimal arithmetic |
| `skills/finance-books/scripts/reconcile.py` | Bank against ledger matching, with transposition, slide, sign and duplicate detection |
| `skills/quant-research/scripts/strategy_stats.py` | Sharpe with the Lo correction, probabilistic and deflated Sharpe, minimum track record, Newey-West t, drawdown |
| `skills/portfolio-risk/scripts/risk_lab.py` | Ledoit-Wolf covariance, Marchenko-Pastur spectrum, minimum variance, risk parity, risk contributions, VaR, ES, Kupiec, Kelly |
| `skills/execution-microstructure/scripts/execution_cost.py` | Almgren-Chriss schedules, square root impact, implementation shortfall, Avellaneda-Stoikov quotes |
| `skills/derivatives-pricing/scripts/options_lab.py` | BSM and Black-76 prices and Greeks, implied volatility, parity, chain and calendar arbitrage, Monte Carlo check |
| `skills/stat-arb/scripts/pairs_lab.py` | Hedge ratio, Engle-Granger test, Ornstein-Uhlenbeck fit, half-life, z-score |
| `skills/trading-systems/scripts/pretrade_check.py` | Replays orders through pre-trade limits and a kill switch, as a reference model for a risk gateway |
| `skills/quant-reasoning/scripts/edge_calc.py` | Expected value, Kelly and growth, Bayes, risk of ruin, Brier score and calibration |

The quantitative scripts are checked against published values where they exist: the deflated Sharpe
ratio against the Bailey and Lopez de Prado worked example, Black-Scholes prices and Greeks against
textbook values, and the Almgren-Chriss schedule against the parameters in the original paper.

```
python3 skills/human-prose/scripts/ai_tells.py --strict docs/*.md
python3 skills/quant-research/scripts/strategy_stats.py returns.csv --column net --periods 252 --trials 100 --trial-sr-var 0.4
```

## Verification

Nothing here is asserted without a check behind it.

```
python3 tools/run_tests.py            # every tests/test_*.py script
python3 tools/validate_skills.py      # spec, required sections, references, scripts, agents, style, hygiene, README
python3 tools/build_agents.py --check # generated agents match their sources
```

The validator enforces the skill specification and the section shape in CONTRIBUTING.md, confirms every
referenced file exists and every reference or script is reachable from its SKILL.md, compiles every
script, checks the agents, and runs the style detector across all Markdown in the repository. CI runs
all of it on Python 3.9, 3.12 and 3.14 on every push and pull request.

The repository holds itself to its own rules. Every Markdown file passes the detector at its strictest
level, and the files that have to enumerate the banned patterns declare per rule exemptions that the
report prints.

## What this does not claim

Stated plainly, because overselling would break the first rule.

No skill makes a model original. What these do is subtract the predictable answer and force the
reasoning through facts only you have. The differentiation comes from your inputs.

Removing the markers of machine writing does not make text human authored. It changes how it reads,
not where it came from. Detection is unreliable in both directions, human judgement performs near
chance, and classifier tools have error rates that matter, which is why Wikipedia tells its own editors
not to depend on them. Where authorship must be disclosed, disclose it.

There is no measurable score out of ten for a prompt, a document, or an idea. Any such number is
invented, so `prompt-forge` reports a defect count instead.

Verdicts are opinions with reasoning attached. Push back with evidence and they should change. Push
back with displeasure and they should not.

`finance-books` is not tax, audit, or regulatory advice, and `career-strategy` is not legal,
immigration, or financial advice. The quantitative skills are research and engineering tools, not
investment advice, and a backtest that passes every check here can still lose money live. Each skill
names the question to put to a professional instead of guessing.

## Why convergence is the real problem

Measured, not assumed.

Model responses cluster far more tightly with each other than independent human responses do
([arXiv 2501.19361](https://arxiv.org/html/2501.19361v1)).

In a 36 participant study, people using one assistant produced less semantically distinct ideas than
people using a different tool ([arXiv 2402.01536](https://arxiv.org/abs/2402.01536)).

Output diversity has fallen across three years of model releases ("Are LLMs becoming similarly
creative? Evidence from three years of models", [arXiv 2608.19437](https://arxiv.org/html/2608.19437)),
and the mechanisms behind low idea diversity are documented ("Examining and Addressing Barriers to
Diversity in LLM-Generated Ideas", [arXiv 2602.20408](https://arxiv.org/html/2602.20408)).

Two mitigations are adapted here at the prompt level, with no embeddings and no extra API calls.
Semantic repulsion estimates the default response distribution and moves away from its repeated
concepts ("A Consensus-Aware Interaction Technique for Mitigating AI Homogenization",
[arXiv 2606.09587](https://arxiv.org/html/2606.09587v1)). Verbalized sampling asks for an
explicit spread of candidates instead of one best answer
([arXiv 2510.01171](https://arxiv.org/html/2510.01171v3)).

The writing rules come from [Wikipedia:Signs of AI writing](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing),
CC BY-SA 4.0, paraphrased and reorganised, together with frequency studies on excess vocabulary
([Science Advances 2025](https://doi.org/10.1126/sciadv.adt3813)), style comparison
([PNAS 2025](https://doi.org/10.1073/pnas.2422455122)), and detection accuracy among frequent users
([ACL 2025](https://arxiv.org/abs/2501.15654)).

## Prior art

Good work exists on the parts this combines, and credit belongs with it.

[machinesoul11/anti-sycophant-ai-agent-skills](https://github.com/machinesoul11/anti-sycophant-ai-agent-skills)
for premise testing and for the explicit off switch pattern, which is borrowed here.
[Dimerin1/honest-audit](https://github.com/Dimerin1/honest-audit) named the manufactured filler
criticism failure. [acost1a/murderboard](https://github.com/acost1a/murderboard),
[zszendro/vc-teardown](https://github.com/zszendro/vc-teardown) and
[SanketSapkal/founder-skills](https://github.com/SanketSapkal/founder-skills) shaped the adversarial
teardown and the explicit verdict. [sirbuggington/no-bs](https://github.com/sirbuggington/no-bs) and
[hoodini/ai-agents-skills](https://github.com/hoodini/ai-agents-skills) cover anti-sycophancy tone.
[maxgoff/unslop](https://github.com/maxgoff/unslop) covers banned phrase discipline.

What none of them do is attack convergence directly. They fix tone, or they fix rigour. None names the
consensus answer and bans it, and none requires differentiation to be derived from the user's own non
transferable assets. That gap is the reason this repository exists.

## Contributing

Read [STYLE.md](STYLE.md) first, since the house style is enforced in CI, then
[CONTRIBUTING.md](CONTRIBUTING.md). Changes are recorded in [CHANGELOG.md](CHANGELOG.md), security
reports go through [SECURITY.md](SECURITY.md), and participation follows the
[code of conduct](CODE_OF_CONDUCT.md).

## Licence

MIT. See [LICENSE](LICENSE).
