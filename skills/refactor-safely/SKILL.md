---
name: refactor-safely
description: Change the structure of working code without changing what it does. Use when the user asks to refactor, clean up, restructure, modernise, simplify or untangle code, asks how to work with legacy or inherited code, asks how to break up a large file, function or class, asks how to add tests to untestable code, or asks whether to rewrite. Separates behaviour preserving changes from behaviour changing ones and never mixes them in one commit, requires a safety net before restructuring, works in small reversible steps that keep the suite green, and argues against a full rewrite unless a specific condition justifies it. Triggers on refactor this, clean up this code, legacy code, technical debt, break up this function, this file is too big, should I rewrite, make this testable, untangle, modernise this codebase.
license: MIT
metadata:
  version: 1.0.0
  suite: ai-skill
---

# Refactoring safely

Refactoring means changing structure while behaviour stays identical. The moment behaviour changes it is
no longer a refactor, and pretending otherwise is how working systems break during cleanup.

## Non-negotiables

1. Never mix a refactor with a behaviour change in one commit. Separate commits, in that order, always. A mixed commit cannot be reviewed and cannot be reverted cleanly when something breaks.
2. Get a safety net first. Tests on the behaviour being preserved, even bad ones that just assert what the code currently does. Restructuring untested code is editing blind.
3. Small steps with a green suite between each. The suite runs after every step, not at the end. A twenty file change that breaks something gives you no information about which step did it.
4. Preserve existing behaviour including the parts that look wrong. Odd behaviour is often relied upon. Raise it as a separate question rather than quietly fixing it.
5. Never refactor code you do not understand yet. Read it, characterise it with tests, then change it.
6. Stop when the change that prompted this is possible. Refactoring is preparation for a change, and without one it is unbounded.
7. Do not claim the suite is green without running it and showing the output.

## Procedure

### Step 1, state what and why

Name the change you want to make that the current structure makes hard. That target bounds the work.

"This file is long" is not a reason. Long is not a defect. The reason is something like: adding the second
payment provider requires editing five unrelated branches in one function.

If nothing is blocked, leave it alone. Restructuring working code with no pending change is risk with no
return.

### Step 2, understand before touching

Read the code and the tests. Find the callers. Check version control for why it looks like this, since
strange code often encodes a bug fix nobody documented.

Write down the behaviour you believe it has, including edge cases and anything surprising. Verify a few of
those beliefs by running the code, because some will be wrong.

### Step 3, get a net

Where tests exist for this behaviour, run them and confirm they pass now.

Where they do not, write characterisation tests. These assert what the code currently does, not what it
should do. Feed it real inputs and record the outputs as expectations, including outputs that look wrong.
Their purpose is detecting change, not judging correctness.

Where the code cannot be tested because dependencies are hardcoded, create a seam first. The smallest safe
seams:

Add a parameter with a default equal to the current hardcoded value, so no caller changes.

Extract the untestable part into a separate method, leaving the original calling it, then override it in a
test subclass.

Wrap a global or a direct constructor call behind a function you can substitute.

Creating a seam is itself a refactor, so make it a separate commit with the suite green.

### Step 4, small named moves

Each of these is one commit, run the suite after each.

Rename for accuracy. The cheapest improvement available, and the one that most reduces future defects,
because a name that states the wrong thing misleads every future reader.

Extract a function from a block that has a single purpose, keeping the parameter list short.

Inline a function that adds a name and no clarity.

Replace a magic value with a named constant, defined once.

Introduce a parameter object when the same three arguments travel together everywhere.

Split a function that does two things into two functions, then update the callers.

Replace a conditional chain on a type with polymorphism, when the chain appears in more than one place.

Guard clauses at the top instead of nested conditionals, which flattens the code without changing it.

Move a function to the module that owns its data.

Separate the decision from the action, so the decision becomes testable without performing the action.

### Step 5, keep it reversible

Commit per step, with a message saying what moved.

Never leave the tree broken between steps.

When a step turns out badly, revert it rather than repairing forward. Reverting one small step is cheap,
and repairing an unclear half-change is not.

Rebuild and rerun after every step. The type checker catches most mechanical mistakes immediately.

### Step 6, then change the behaviour

Once the structure supports it, make the behaviour change as its own commit, with its own test.

Now the review is straightforward, because the reviewer can see the behaviour change separately from
several hundred lines of movement.

## Rewrite against incremental change

The default answer is incremental, because a rewrite restarts the accumulation of undocumented behaviour
while the original keeps changing underneath.

What is usually underestimated: the original encodes years of edge cases nobody wrote down, the rewrite has
to maintain feature parity against a moving target, and both versions need maintaining during the
transition.

A rewrite is justified when the platform or language is unsupported and cannot be updated, when the
architecture cannot meet a requirement that is not negotiable, or when the system is small enough to
rewrite in weeks rather than quarters.

Where a rewrite is genuinely right, do it incrementally anyway. Put the new system in front of the old
one and move one route or one feature at a time, so each move is small and reversible, and the old system
keeps serving everything not yet moved.

## Self-audit

- The blocked change that motivated this is named.
- Behaviour to be preserved is written down and covered by tests that pass beforehand.
- No commit mixes restructuring with behaviour change.
- Suite run after every step, with output shown.
- Surprising behaviour preserved and raised separately rather than fixed silently.
- Each step individually revertible.
- Work stopped once the motivating change became possible.
