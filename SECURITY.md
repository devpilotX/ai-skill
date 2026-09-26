# Security policy

## Supported versions

Security fixes go into the latest release. Older tags are not patched; upgrade to the newest release.

## Reporting a vulnerability

Report privately through GitHub's
[private vulnerability reporting](https://github.com/devpilotX/ai-skill/security/advisories/new) for this
repository. Do not open a public issue for a vulnerability.

Include the file and line, the input that triggers the problem, and what an attacker gains. Expect an
acknowledgement within seven days and a fix or a decision within thirty days for confirmed issues.

## What is in scope

The Python scripts under `skills/*/scripts/` and `tools/`, for example HTML injection in the Markdown
converter or a path handling flaw in a command line tool.

Skill or agent instructions that would lead an assistant to take a harmful action, such as running a
destructive command without asking, leaking secrets, or following instructions embedded in untrusted
content.

The release workflow and the integrity of published zips.

## What is out of scope

The advice in a skill being wrong on a subject matter question. Open an ordinary issue for that.

Vulnerabilities in the tools that load these skills (Kiro, Claude Code or others). Report those to their
vendors.

## Verifying a download

Every release includes `SHA256SUMS.txt`, and the zips are built reproducibly from the tagged commit by
the release workflow. To check a download:

```
sha256sum -c SHA256SUMS.txt
```

On macOS use `shasum -a 256 -c SHA256SUMS.txt`.
