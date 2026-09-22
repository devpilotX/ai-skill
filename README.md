# ai-skill

Twenty nine agent skills built around one rule: say the true thing, in the user's own situation, without
the accent of machine writing.

They exist because of two failures that show up in almost every assistant. The first is flattery,
which produces agreement instead of assessment. The second is convergence, which hands every user the
same high probability answer. Fixing only the first gives you a confident, rude, generic answer, which
is not an improvement.

Works in [Kiro](https://kiro.dev/docs/skills.md) and in any tool that reads the open
[Agent Skills specification](https://agentskills.io/specification), including Claude Code.

## The skills

Twenty nine of them, in four groups.

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
| [frontend-build](skills/frontend-build/) | The five states most interfaces omit, state in the narrowest scope that works, accessibility during the build, bundle size budgeted in kilobytes. |
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
| [ship-audit](skills/ship-audit/) | Eleven gate production readiness audit. Every finding names a file, a line, the trigger, and what is lost. |
| [code-review](skills/code-review/) | Defects that cost something. Ignores anything a linter owns. Reports a clean change as clean. |
| [test-strategy](skills/test-strategy/) | Effort allocated by what a failure costs. Says plainly that coverage percentage measures execution, not correctness. |
| [debug-method](skills/debug-method/) | Reproduce, then one hypothesis at a time with a prediction that can be wrong. A symptom that stopped is not a fix. |
| [performance-tuning](skills/performance-tuning/) | Profile first, fix the dominant cost, report before and after from the same method. |
| [refactor-safely](skills/refactor-safely/) | Never mixes a refactor with a behaviour change. Safety net first, small reversible steps, suite green between each. |

### Judgement and communication

| Skill | What it does |
|---|---|
| [reality-check](skills/reality-check/) | Names the answer every other user got, bans it, then judges your idea against your own non-transferable advantages. BUILD, PIVOT or KILL with dated kill criteria. |
| [human-prose](skills/human-prose/) | Removes the stylistic residue of machine writing, then verifies with a working 23 rule detector rather than a judgement call. |
| [prompt-forge](skills/prompt-forge/) | Diagnoses which of six defects a prompt has and rewrites it. Refuses to invent a score out of ten. |
| [deep-research](skills/deep-research/) | Graded sources, reported contradictions, and an explicit list of what could not be established. |
| [numbers-check](skills/numbers-check/) | Recomputes with a script, carries units, cross-checks a second way, names the assumption that decides the result. |
| [doc-forge](skills/doc-forge/) | Documents chosen by what the reader does next, plus a zero dependency Markdown to print ready HTML and PDF converter. |
| [business-model](skills/business-model/) | Contribution margin, the working capital cycle, break-even, payback. Models cash rather than only profit. |
| [career-strategy](skills/career-strategy/) | Career decisions priced in years and money, anchored in your financial position and rare skill combinations. |
| [job-hunt](skills/job-hunt/) | Diagnoses which stage of the funnel is broken before rewriting anything. |
| [finance-books](skills/finance-books/) | Bookkeeping, reconciliation and statement checking. Stops at the line where a licensed accountant is required. |

### How they chain

`build-pilot` is the entry point for anything substantial. It calls the others in order: `deep-research`
to verify the facts, `reality-check` to test the premise, `arch-decide` to record the choice, the build
skills to implement, `test-strategy` and `code-review` while working, then `ship-audit` before release.
Each one also works alone.

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
bash tools/build_dist.sh          # writes dist/<skill>.zip and dist/ai-skill-all.zip
```

Per skill zips are attached to each [release](https://github.com/devpilotX/ai-skill/releases) by the
release workflow, alongside `SHA256SUMS.txt` for verification. The whole repository at a tag is also
downloadable directly:

```
https://github.com/devpilotX/ai-skill/archive/refs/tags/v1.0.0.zip
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
```

Every skill has an off switch. Saying "stop", "I've decided", or "just execute" ends it for the
session. Skills that nag get uninstalled.

## Two working scripts

Most skill collections are documentation. Two of these ship code.

`skills/human-prose/scripts/ai_tells.py` detects 23 classes of machine writing marker across three
severities, from leaked citation markup and tracking parameters through to overrepresented vocabulary
measured as a density. It skips fenced code and frontmatter, and supports per file per rule exemptions
that are printed in every report so no exemption stays hidden.

```
python3 skills/human-prose/scripts/ai_tells.py --strict docs/*.md
```

`skills/doc-forge/scripts/md2doc.py` converts Markdown to self contained HTML with embedded A4 print
rules, then to PDF using whichever of weasyprint, wkhtmltopdf, Chromium or pandoc is installed. With
none installed it says so and exits 3, and the HTML still prints correctly from a browser.

```
python3 skills/doc-forge/scripts/md2doc.py report.md --toc --pdf
```

Neither script needs a third party package.

## Verification

Nothing here is asserted without a check behind it.

```
python3 tools/validate_skills.py    # spec, references, scripts, style, hygiene, README
python3 tests/test_ai_tells.py      # 27 checks on the detector
python3 tests/test_md2doc.py        # 30 checks on the converter
```

The validator enforces the skill specification, confirms every referenced file exists and every
existing file is referenced, compiles every script, and runs the style detector across all Markdown in
the repository. CI runs all three on every push and pull request.

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
immigration, or financial advice. Both name the question to put to a professional instead of guessing.

## Why convergence is the real problem

Measured, not assumed.

Model responses cluster far more tightly with each other than independent human responses do
([arXiv 2501.19361](https://arxiv.org/html/2501.19361v1)).

In a 36 participant study, people using one assistant produced less semantically distinct ideas than
people using a different tool ([arXiv 2402.01536](https://arxiv.org/abs/2402.01536)).

Output diversity has fallen across three years of model releases
([arXiv 2608.19437](https://arxiv.org/html/2608.19437)), and the mechanisms behind low idea diversity
are documented ([arXiv 2602.20408](https://arxiv.org/html/2602.20408)).

Two mitigations are adapted here at the prompt level, with no embeddings and no extra API calls.
Semantic repulsion estimates the default response distribution and moves away from its repeated
concepts ([arXiv 2606.09587](https://arxiv.org/html/2606.09587v1)). Verbalized sampling asks for an
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
[CONTRIBUTING.md](CONTRIBUTING.md).

## Licence

MIT. See [LICENSE](LICENSE).
