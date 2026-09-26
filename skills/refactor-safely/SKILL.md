---
name: refactor-safely
description: Change the structure of working code without changing what it does. Use when the user asks to refactor, clean up, restructure, modernise, simplify or untangle code, extract a method, rename across the codebase, remove dead code, reduce duplication, fix a code smell, work with legacy or inherited code, break up a large file, function or class, add tests to untestable code, or asks whether to rewrite. Keeps behaviour preserving changes apart from behaviour changes down to the pull request, needs a safety net first, prefers automated refactorings and codemods, works in small green steps, and argues against a full rewrite. To rewrite or replace a whole system use migration-plan instead. For test strategy use test-strategy. Triggers on refactor this, clean up this code, legacy code, technical debt, extract method, rename this everywhere, dead code, duplicated code, code smell, break up this function, this file is too big, should I rewrite, make this testable, untangle, modernise this codebase.
license: MIT
metadata:
  version: 1.1.0
  suite: ai-skill
---

# Refactoring safely

Cleanup breaks working systems when a behaviour change rides along inside a structural change, so
nobody can see it, review it, or revert it alone. This skill keeps the two apart and puts a safety net
under the code before anything moves.

## When to use and when to stay off

Run when the user wants to restructure existing code, make legacy code testable, or decide between
incremental change and a rewrite of one component.

Stay off, and route instead, when:

- The request is to replace or rewrite a whole system, move to a new platform, or run old and new side by side. Use `migration-plan`.
- The question is which tests to write, test pyramid shape, or coverage targets in general. Use `test-strategy`. This skill covers only the characterisation tests needed before a refactor.
- The user wants a review of a diff someone else wrote. Use `code-review`.
- The task is a feature or bug fix with no structural change. Just do it.

The user says "stop", "I've decided", or "just execute": comply at once and stay off for the rest of
the session unless asked again.

## Non-negotiables

These override everything else in this file.

1. Keep a refactor and a behaviour change apart at the unit that survives merge. Separate commits in that order, and where the repository squash merges, separate pull requests. A mixed change cannot be reviewed or reverted cleanly.
2. Get a safety net first: tests on the behaviour being preserved, even ones that only assert what the code does today. Restructuring untested code is editing blind.
3. Small steps with a green suite between each. The suite runs after every step, not at the end.
4. Preserve existing behaviour, including the parts that look wrong. Raise odd behaviour as a separate question rather than quietly fixing it.
5. Never refactor code you do not understand yet. Read it, characterise it with tests, then change it.
6. Stop when the change that prompted this is possible. If the user explicitly asks for cleanup with no pending change, state the risk once, then comply.
7. Do not claim the suite is green without running it and showing the output.

## What counts as behaviour

Behaviour is everything an outside caller or operator can observe, which is wider than return values:

- Return values and output, including ordering of collections and formatting of numbers and dates.
- Exception types, messages that callers parse, and which inputs raise.
- Side effects and their order: writes, network calls, events emitted, retries.
- Log lines and metric names that dashboards and alerts depend on.
- Performance characteristics a caller relies on, such as complexity, allocation, lock scope, or query count.
- Serialised and wire formats: JSON field names and order where parsed positionally, database columns, cache keys, file formats.
- The public API surface, including callers you cannot see: reflection, dependency injection by name, string keyed lookups, templates, configuration files, and other repositories.

If a move changes any of these, it is a behaviour change and gets its own commit and test.

## Procedure

### Step 1, state what and why

Name the change you want to make that the current structure makes hard. That target bounds the work.

"This file is long" is not a reason. Long is not a defect. The reason is something like: adding the
second payment provider requires editing five unrelated branches in one function.

If nothing is blocked, recommend leaving it alone, since restructuring with no pending change is risk
with no return. If the user asks for the cleanup anyway, say that once, agree a boundary (which files,
which smells), and proceed.

### Step 2, understand before touching

Read the code and the tests. Find the callers, including the indirect ones from the behaviour list
above: search for the name as a string, check reflection and configuration, and search other
repositories that consume the package. Check version control for why the code looks like this, since
strange code often encodes a bug fix nobody documented.

Write down the behaviour you believe it has, including edge cases and anything surprising. Verify a few
of those beliefs by running the code, because some will be wrong.

If the code is a published interface (a library, a public API, a schema other teams read), it cannot
be changed in one step. Use deprecation plus expand and contract: add the new form, migrate callers,
then remove the old form in a later release. Checklist in `references/seams-and-moves.md`.

### Step 3, get a net

Where tests exist for this behaviour, run them and confirm they pass now.

Where they do not, write characterisation tests. These assert what the code currently does, not what
it should do. Feed it real inputs and record the outputs as expectations, including outputs that look
wrong. For code with large or messy output (reports, rendered pages, serialised payloads), use
approval or golden master testing: capture the full output once, commit it, and fail on any diff.
Scrub timestamps and random identifiers before comparing so the test fails only on real change.

Where the code cannot be tested because dependencies are hardcoded, create a seam first. The smallest
safe seams:

- Add a parameter with a default equal to the current hardcoded value, so no caller changes.
- Pass the dependency as a function or interface value. In Go, accept a small interface or a function field. In Rust, take a trait bound or a closure. For final or sealed classes, and in functional code, this is the seam to use.
- Where inheritance is available and the class is open, extract the untestable part into a method and override it in a test subclass.
- Wrap a global or a direct constructor call behind a function you can substitute.

Seams by language family, with examples, are in `references/seams-and-moves.md`.

Creating a seam is itself a refactor, so make it a separate commit with the suite green.

### Step 4, small named moves, automated where possible

Prefer the automated refactorings in the IDE or language server (rename symbol, extract function,
inline, move) over hand edits. They update every reference the tooling can resolve, which a text
search cannot. They still miss string keyed and reflective callers, so search for those by hand.

For a change across many files, use a codemod: OpenRewrite for Java and Kotlin, jscodeshift for
JavaScript and TypeScript, comby for structural search and replace in most languages. Land the codemod
output as one mechanical commit containing nothing else, with the codemod script or command in the
message, so a reviewer checks the script rather than every line.

Each of these is one commit, and the suite runs after each:

- Rename for accuracy, since a wrong name misleads every future reader.
- Extract a function from a block with a single purpose, keeping the parameter list short.
- Inline a function that adds a name and no clarity.
- Replace a magic value with a named constant, defined once.
- Introduce a parameter object when the same arguments travel together everywhere.
- Split a function that does two things, then update the callers.
- Replace a conditional chain on a type with polymorphism, when the chain appears in more than one place.
- Guard clauses at the top instead of nested conditionals.
- Move a function to the module that owns its data.
- Separate the decision from the action, so the decision is testable without performing it.
- Delete dead code once a search, including string and reflective uses, finds no caller. Where usage is uncertain, log or count calls in production first.

Each move has preconditions and things it can silently change, such as evaluation order, which
exceptions escape, or `this` binding. Those are listed per move in `references/seams-and-moves.md`.

### Step 5, keep it reversible

Commit per step, with a message saying what moved. Never leave the tree broken between steps.

Check how the repository merges. Under squash merge, all commits in a pull request become one, so the
separation from non-negotiable 1 has to hold at pull request level: open the refactor as its own pull
request, or agree a merge strategy that keeps commits (merge commit or rebase merge).

When a step turns out badly, revert it rather than repairing forward. Reverting one small step is
cheap, and repairing an unclear half-change is not.

Rebuild and rerun after every step. The type checker catches many mechanical mistakes immediately.

### Step 6, then change the behaviour

Once the structure supports it, make the behaviour change as its own commit, or its own pull request
under squash merge, with its own test. The reviewer then sees the behaviour change apart from the
movement.

## Rewrite against incremental change

The default answer is incremental, because a rewrite restarts the accumulation of undocumented
behaviour while the original keeps changing underneath. The original encodes edge cases nobody wrote
down, the rewrite chases feature parity against a moving target, and both versions need maintaining
during the transition.

A rewrite of one component is justified when the platform or language is unsupported and cannot be
updated, when the architecture cannot meet a requirement that is not negotiable, or when the component
is small enough to rewrite in weeks rather than quarters.

Where a rewrite is right, do it incrementally with the strangler fig pattern
([Fowler](https://martinfowler.com/bliki/StranglerFigApplication.html)): put the new implementation
behind the same entry point, move one route or feature at a time, and let the old code keep serving
everything not yet moved. When the replacement is a whole system or platform, hand over to
`migration-plan`, which covers parallel running, data moves, and cutover.

## Self-audit

- The blocked change that motivated this is named, or the user explicitly asked for cleanup and the risk was stated once.
- Behaviour to be preserved is written down against the full behaviour list, and covered by tests that pass beforehand.
- String keyed, reflective, and cross repository callers were searched for.
- No commit mixes restructuring with behaviour change, and the separation survives the repository's merge strategy.
- Automated refactorings or a codemod were used where available, and a codemod landed as one mechanical commit.
- Published interfaces changed only through deprecation and expand and contract.
- Suite run after every step, with output shown.
- Surprising behaviour preserved and raised separately rather than fixed silently.
- Each step individually revertible.
- Work stopped once the motivating change became possible, or at the agreed boundary.

## What this cannot do

It cannot prove behaviour is unchanged. Tests show only that the checked behaviour held, and callers
outside the repository (reflection, other teams, external clients) can break without any test failing.
Where external consumers exist, the evidence that matters comes from their test suites, contract tests,
or a staged rollout with monitoring.

It cannot make a rewrite safe by planning alone. For a whole system replacement use `migration-plan`,
and for deciding which tests the codebase needs beyond characterisation use `test-strategy`. After the
refactor, `code-review` can check the diff with fresh eyes.
