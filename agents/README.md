# Agents

Ten agents that combine the skills into roles. Each one is written once in `src/` and generated for two
tools by `tools/build_agents.py`:

- `kiro/` holds Kiro custom agents in the Markdown format: frontmatter with `tools` and one `skill://` resource per skill, and the body as the prompt.
- `claude/` holds Claude Code subagents: frontmatter with `tools` and the `skills` to preload, and the body as the system prompt.

Agents only work when the skills they name are installed too.

## The agents

| Agent | Access | Delegate to it when |
|---|---|---|
| build-lead | read-write | A build spans several components or starts from a vague idea. Runs the staged build with gates. |
| code-reviewer | read-only | A diff, pull request or commit needs a verdict before merge. |
| release-auditor | read-only | A whole product needs a ship or do not ship verdict before launch. |
| incident-debugger | read-write | Something is broken in production or a bug resists guessing. Mitigates first, then narrows the cause. |
| technical-writer | read-write | A README, runbook, decision record or report has to be written or cleaned up. |
| strategy-advisor | read-only | An idea, business plan or career decision needs honest judgement and real numbers. |
| quant-researcher | read-write | A trading idea needs a hypothesis, point-in-time data, a backtest and a verdict that survives multiple testing. |
| risk-manager | read-only | A portfolio or book needs an independent risk review, stress tests and limits. |
| derivatives-desk | read-write | Options need pricing, arbitrage checks, surface fitting, hedging or P&L explanation. |
| trading-systems-engineer | read-write | Order gateways, risk checks, kill switches or market data code are being built or reviewed. |

Read-only agents read files and the web and do not edit. Read-write agents may edit files and run
commands, and each prompt says where it must stop and ask first.

## Install for Kiro

Copy the skills and the agents into the workspace, or into `~/.kiro/` for every project:

```
mkdir -p .kiro/skills .kiro/agents
cp -r ai-skill/skills/* .kiro/skills/
cp ai-skill/agents/kiro/*.md .kiro/agents/
```

The `skill://<name>` resources resolve to `.kiro/skills/<name>/SKILL.md` in the workspace. If the skills
live only in `~/.kiro/skills`, change the resources to `skill://~/.kiro/skills/<name>/SKILL.md`.

In the Kiro CLI, start a session with one of them: `kiro-cli --agent quant-researcher`.

## Install the Claude Code subagents

```
mkdir -p .claude/skills .claude/agents
cp -r ai-skill/skills/* .claude/skills/
cp ai-skill/agents/claude/*.md .claude/agents/
```

Claude Code delegates to a subagent when a request matches its description, or when asked by name.

## Changing an agent

Edit `src/<name>.md` and run `python3 tools/build_agents.py`. The validator fails if a generated file is
out of date, names a skill that does not exist, or lists a skill the prompt never says when to use.
