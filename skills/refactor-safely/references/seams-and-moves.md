# Seams and moves

A seam is a place where behaviour can be substituted without editing the code under test. A move is a
named structural change. Both are refactors, so each lands as its own commit with the suite green.

## Seams by language family

### Object oriented with open classes (Java, C#, Kotlin open classes, Python, Ruby, TypeScript classes)

Subclass and override. Extract the call to the database, clock, or network into a protected method,
then override it in a test subclass. Works only when the class and method can be overridden.

Constructor injection. Add a constructor parameter typed as an interface, with an overload or default
that builds the current concrete dependency, so existing callers compile unchanged.

Extract interface. When a concrete class is passed around, extract the methods the caller uses into an
interface and depend on that.

### Final or sealed classes (Kotlin by default, C# sealed, Java final, Swift final)

Subclassing is unavailable, so wrap. Put the final class behind an interface you own, with one
production implementation that delegates, and a fake for tests. Inject the interface.

### Functional code (Haskell, Elixir, Clojure, F#, functional style JavaScript)

Pass the effect as an argument. A function that calls `now()` or `httpGet` directly takes that function
as a parameter instead, with the real one supplied by the caller or a default argument.

Push effects to the edge. Split into a pure core that takes data and returns data, and a thin shell
that performs effects. The core needs no seam at all.

### Go

Accept a small interface declared by the consumer, holding only the methods it calls. The production
type satisfies it implicitly, so no change is needed at the producer.

Function fields. A struct field such as `now func() time.Time`, set to `time.Now` in the constructor
and replaced in tests.

Package level function variables work but are global state, and they make parallel tests racy. Prefer
the two above.

### Rust

Generic over a trait: `fn run<C: Clock>(clock: &C)`. Zero runtime cost, and tests pass a fake that
implements the trait.

Trait objects (`&dyn Clock` or `Box<dyn Clock>`) when the type must be chosen at run time.

Closures: accept `impl Fn() -> Instant` for a single operation.

Conditional compilation with `#[cfg(test)]` to swap a module is a last resort, since the tested build
then differs from the shipped build.

### C and C++

Link seams (link a fake object file in the test build) and preprocessor seams exist, but the tested
binary is not the shipped binary. Prefer passing a function pointer or, in C++, a template parameter or
virtual interface.

## Moves: preconditions and what can silently change

Rename. Precondition: every reference is resolvable by tooling, or the string and reflective uses were
found by search. Can silently change: serialised field names, reflection, dependency injection by name,
route names, metric and log keys, anything in another repository.

Extract function. Precondition: the block has one entry and one exit, or the early returns are handled.
Can silently change: evaluation order if arguments now get evaluated before a condition that used to
short circuit; which exceptions escape if the block was inside a `try`; `this` binding in JavaScript
when the extracted function is a plain function rather than a method or arrow function; captured
variables that were mutated in the block and read after it; `defer` timing in Go, since deferred calls
now run when the extracted function returns.

Inline function. Precondition: the function has no overrides and is not part of a published interface.
Can silently change: an argument expression that used to be evaluated once may be evaluated several
times if it is substituted textually; stack traces and profiling names that alerts match on.

Move function. Precondition: no circular import results. Can silently change: module initialisation
order, and in Python or JavaScript, import time side effects now run at a different point.

Introduce parameter object. Can silently change: identity checks and mutation, since callers now share
an object where they had separate values.

Replace conditional with polymorphism. Precondition: the type test is exhaustive today. Can silently
change: the default branch, which often handled a case nobody listed, and dispatch on null.

Guard clauses. Can silently change: the order conditions are checked, which matters when a condition
has a side effect or throws.

Split loop, or replace loop with a pipeline. Can silently change: laziness (a lazy pipeline may never
run), iteration count over a generator that can be consumed once, and performance.

Replace magic value with constant. Can silently change: nothing if the value is identical, and a
floating point or string value that differs by one character changes behaviour, so compare exactly.

Delete dead code. Precondition: no caller found by tooling, by string search, or in production
telemetry. Can silently change: registration side effects, such as a module that registers a plugin
when imported.

## Published API checklist

Treat any interface consumed outside the repository as published: libraries, HTTP and RPC APIs,
message schemas, database tables read by other services, command line flags, configuration keys, and
event names.

1. Find the consumers. Search dependent repositories, check package registry dependents, and read access logs for endpoints.
2. Expand. Add the new name, field, or endpoint alongside the old. Both work.
3. Deprecate the old form in the way consumers will see it: the language's deprecation annotation, a response header, a changelog entry, and a log line or metric counting old form use.
4. Migrate callers you own. Tell owners of the rest, with a removal date.
5. Watch the old form usage metric reach zero, or the announced date pass.
6. Contract. Remove the old form in a release whose version number signals a breaking change under the project's versioning policy.

Each numbered step is a separate change. Steps 2 and 6 are never in the same release.
