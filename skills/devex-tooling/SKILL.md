---
name: devex-tooling
description: Make a clean checkout run with one command, CI install exactly what the lockfile says, and the feedback loop fast enough to be used. Use when the user asks how to set up a project, write a setup script or onboarding steps, choose a build tool, bundler or package manager, structure a monorepo, manage dependencies or lockfiles, pin runtime versions, configure linting, formatting, type checking, pre-commit hooks or a devcontainer, set up Renovate or Dependabot, or reports that it works on my machine only. Triggers on project setup, onboarding, setup script, monorepo, build tool, bundler, Vite, Webpack, Turborepo, Nx, npm, pnpm, yarn, uv, poetry, pip, Cargo, Makefile, .nvmrc, lockfile, eslint, prettier, Biome, Ruff, husky, pre-commit, devcontainer, Renovate, Dependabot, CI is slow, slow build. For slow application code use performance-tuning. For a supply chain security audit use security-hardening. For the deploy pipeline use infra-deploy.
license: MIT
metadata:
  version: 1.1.0
  suite: ai-skill
---

# Development tooling

Tooling fails quietly. The build resolves different dependency versions on each laptop and in CI, the
setup notes were last followed by the person who wrote them, a hook takes long enough that everyone
passes `--no-verify`, and a flaky test teaches the team to merge on red. Nobody notices until a release
breaks on a machine that is not the author's. This skill makes the checkout reproducible, the installs
exact, and the feedback loop short enough to be used.

## When to use and when to stay off

Run when the user is setting up or repairing the local and CI tooling of a project: runtime and package
manager pins, lockfiles, setup scripts, formatters, linters, type checkers, hooks, CI caching, monorepo
structure, dependency update automation, or a "works on my machine" report.

Stay off when:

- The question is a one line command lookup. Answer it.
- The problem is slow application code at runtime. That belongs to `performance-tuning`.
- The request is a supply chain or vulnerability audit of the dependencies. That belongs to `security-hardening`.
- The request is about building images, environments or the deploy pipeline. That belongs to `infra-deploy`.
- The request is about which tests to write or how to structure the suite. That belongs to `test-strategy`.
- The user wants the onboarding document written up. `doc-forge` writes it, using the commands this skill verified.

The user says "stop", "I've decided", or "just execute": comply at once and stay off for the rest of the
session unless asked again.

## Non-negotiables

These override everything else in this file.

1. A clean checkout runs with one documented command, verified from a fresh clone. Unfollowed setup instructions are assumed wrong.
2. Pin everything that changes the build: runtime version in a file, package manager version, a committed lockfile, container base images by digest, and third party CI actions by full length commit SHA.
3. CI installs with the frozen form of the install command, so a lockfile that disagrees with the manifest fails the build instead of being rewritten.
4. Versions are retrieved from the official release source at the time of writing, never recalled from memory.
5. Never commit secrets or generated output. Secret scanning runs in pre-commit and again in CI.
6. Formatting is automated and never discussed in review.
7. Every tool earns its configuration, and its cost in time and concepts is stated.

## Procedure

### Step 1, declare the runtime and the manager

Put the runtime version in the file the tooling reads, and declare the package manager and its version,
because different managers and versions resolve and lock differently. One package manager per
repository. Two lockfiles in one project produce failures that appear only in CI.

The pin file, lockfile, frozen install command and usual formatter and linter for each ecosystem are in
`references/ecosystem-pins.md`. Retrieve current version numbers from the sources named there.

### Step 2, make machines agree

Declare which operating systems and CPU architectures are supported, and check each one. The usual
breaks are native dependencies built for amd64 on an arm64 laptop (or the reverse), container images
pulled for the wrong platform, CRLF line endings from Windows checkouts breaking shell scripts (fix with
a `.gitattributes` rule), and Windows path separators or path length limits in scripts.

When the toolchain is heavy or the team spans operating systems, offer a devcontainer
([containers.dev](https://containers.dev/)) so the editor, runtime and local services come from one
definition. Pin its base image by digest like any other image.

### Step 3, one command to get running

A script or a make target that installs with the frozen command, starts local services, seeds data, and
starts the application. Local services such as a database run in containers, at the engine version used
in production.

Check in an example environment file listing every variable with a description and a safe default.

Verify from a fresh clone in a clean directory, and record how long it takes.

### Step 4, formatting, linting, types

One formatter, running on save and in CI, with one configuration for the repository.

A linter configured for correctness rules. Style belongs to the formatter. Turn off rules the team
disagrees with in configuration, since a wall of inline suppressions means the configuration is wrong.

Type checking: on a new project, start in strict mode. On an existing codebase, strictness arrives
incrementally, one rule or one directory at a time, with a recorded baseline that may only shrink.
Turning on every strict flag at once in a large codebase produces thousands of errors and gets reverted.

All of these run in CI, so a local skip is caught.

### Step 5, hooks and secret scanning

Split the checks by cost. Pre-commit runs only fast checks on staged files: format, quick lint, and a
secret scan with a tool such as [gitleaks](https://github.com/gitleaks/gitleaks) or
[trufflehog](https://github.com/trufflesecurity/trufflehog). Pre-push can run the type check and the
affected tests. CI runs everything and is the authority, including a secret scan of the full diff,
because hooks are optional on every developer machine. The split is in `references/ecosystem-pins.md`.

A leaked secret is revoked and rotated. Deleting it from history does not undo the exposure.

### Step 6, measure the feedback loop

Measure time from saving a file to seeing the result, and time for the test suite. Write both numbers
down. When the loop is slow, fix it before adding checks, because checks people skip catch nothing.

Split the suite so a change runs its relevant tests quickly, with the full suite in CI.

### Step 7, monorepo, decided by coupling

Package count is not the test. A workspace pays off when packages change together, share types, or need
atomic cross package changes. A frontend and a backend sharing API types qualify, even as two packages,
and a plain package manager workspace may be all they need. Many unrelated packages with separate
release cycles may not qualify.

In a monorepo: declare dependencies between packages explicitly, build only what changed and what
depends on it, keep one version of each shared external dependency, and let the task runner cache
results by input hash.

### Step 8, dependency discipline

Before adding a dependency: check whether the platform already does it, how many transitive
dependencies arrive with it, maintenance activity, licence, and any install scripts, which run with your
permissions. Keep runtime and development dependencies separate.

Automate updates with Renovate or Dependabot on a schedule, with minor updates batched. The same tool
bumps the SHA pinned CI actions and the digest pinned images, which keeps pinning from turning into
staleness.

### Step 9, CI guard rails

Frozen install, format check, lint, type check, test, build, secret scan. Fail on any.

Cache keys differ by what is cached. The dependency cache keys on the lockfile hash plus OS, architecture
and runtime version. Build output keys on the source files, build configuration and toolchain version,
since a lockfile hash says nothing about whether the code changed. Recipes are in
`references/ecosystem-pins.md`.

Pin third party actions by full length commit SHA with the version in a trailing comment, following the
GitHub Docs guide "Security hardening for GitHub Actions". A tag can be moved to different code, and a
digest applies to container images only.

Flaky tests get a written quarantine policy: a flaky test is moved out of the required checks with a
named owner and a fix-by date, tracked in an issue, and deleted or fixed when the date passes. A
quarantine with no owner or date becomes a permanent hole in coverage.

## Self-audit

- Fresh clone to running verified, with the command documented and the time recorded.
- Runtime, package manager, lockfile, image digests and action SHAs all pinned, and every version number retrieved from a named source.
- CI uses the frozen install command for the ecosystem.
- Supported OS and architecture listed, line endings fixed in `.gitattributes`, and each platform checked.
- Pre-commit contains only fast checks, and secret scanning runs in both pre-commit and CI.
- Type checker strict on new code, or an incremental plan with a shrinking baseline on existing code.
- Dependency cache and build cache use different keys, as described in Step 9.
- Renovate or Dependabot configured, covering actions and images.
- Every quarantined test has an owner and a date.
- Feedback loop and suite duration measured and written down.
- No generated output or secrets committed.

## What this cannot do

It cannot see the user's CI runner, network, or machines. Timings and platform checks are only real
when the user runs them and reports the output.

It cannot know current tool versions or current flags without retrieving them. Flags for frozen installs
and secret scanners change between major versions, so check the tool's documentation for the version in
use.

Secret scanning finds patterns. It misses secrets that look like ordinary strings, and it does nothing
about a secret that already leaked.

Licence compatibility of dependencies is a legal question. Ask a software licensing lawyer: "Given that
we distribute this product as a hosted service and as a downloadable binary, do the licences of these
dependencies, listed with versions, impose obligations on our own code, and which of them must we
remove or replace?"
