# Ecosystem pins, frozen installs, caches and hooks

Every version number that goes into a pin file is retrieved from the official release source at the
time of writing: the runtime's download or release page, the package manager's changelog, or the
registry. Never write a version from memory, because the one you remember may be end of life or may not
exist. The same applies to command flags, which change between major versions of a tool. Confirm them
against the documentation for the version the project uses.

## Per ecosystem

### Node.js

Runtime pin: `.nvmrc` or `.node-version`, plus `engines.node` in `package.json` for tools that read it.

Package manager pin: the `packageManager` field in `package.json`, read by Corepack. Check whether
Corepack ships with the Node version in use, since its bundling has been changing.

Lockfile: `package-lock.json`, `pnpm-lock.yaml`, or `yarn.lock`. Exactly one.

Frozen install in CI:

```
npm ci
pnpm install --frozen-lockfile
yarn install --immutable            # Yarn 2 and later
yarn install --frozen-lockfile      # Yarn 1
```

Formatter and linter: Prettier plus ESLint, or Biome for both. TypeScript's `tsc --noEmit` for types.

### Python

Runtime pin: `.python-version` (read by pyenv and uv), plus `project.requires-python` in `pyproject.toml`.

Lockfile: `uv.lock`, `poetry.lock`, or a `requirements.txt` compiled with hashes by pip-tools or
`uv pip compile --generate-hashes`.

Frozen install in CI:

```
uv sync --locked                    # fails if uv.lock is out of date
poetry check --lock && poetry install
pip install --require-hashes -r requirements.txt
```

`uv sync --frozen` installs from the lockfile without checking it against `pyproject.toml`. Use
`--locked` in CI so a stale lockfile fails.

Formatter and linter: Ruff for both. mypy or pyright for types.

### Rust

Runtime pin: `rust-toolchain.toml`, read by rustup
([toolchain overrides](https://rust-lang.github.io/rustup/overrides.html)). List the components
(`rustfmt`, `clippy`) and targets there too.

Lockfile: `Cargo.lock`, committed for applications. For libraries, follow the current Cargo FAQ in
the Cargo Book, since that guidance has changed.

Frozen install in CI: `cargo build --locked` and `cargo test --locked`. `--frozen` also forbids network
access.

Formatter and linter: `cargo fmt --check` and `cargo clippy` with warnings denied.

### Go

Runtime pin: the `go` and `toolchain` directives in `go.mod`
([Go toolchains](https://go.dev/doc/toolchain)).

Lockfile: `go.sum`, committed.

Frozen install in CI: `go mod download` then `go mod verify`, and build with module mode read only (the
default for `go build` outside vendoring). Add a CI check that `go mod tidy` leaves no diff.

Formatter and linter: `gofmt` (or `gofumpt`), `go vet`, and golangci-lint if the team wants more.

### Several runtimes in one repository

A single `.tool-versions` file (asdf) or `mise.toml` ([mise](https://mise.jdx.dev/)) pins every runtime
in one place. mise can also read the per language files above. Pick one mechanism and remove the others,
or they drift apart.

## CI cache key recipes

A dependency cache and a build output cache answer different questions, so they get different keys.

Dependency cache. Cache the package manager's download store, then run the frozen install. Key on the
lockfile hash, the OS, the CPU architecture and the runtime version, because native modules differ
across all four. A GitHub Actions example, with the action pinned by commit SHA:

```yaml
- uses: actions/cache@FULL_LENGTH_COMMIT_SHA  # version retrieved from the actions/cache releases page
  with:
    path: ~/.cache/uv
    key: deps-${{ runner.os }}-${{ runner.arch }}-py${{ steps.py.outputs.python-version }}-${{ hashFiles('uv.lock') }}
    restore-keys: |
      deps-${{ runner.os }}-${{ runner.arch }}-py${{ steps.py.outputs.python-version }}-
```

The setup actions for Node, Python and Go offer built in dependency caching keyed on the lockfile. Use
them where they fit, and check which store path they cache.

Build output cache. Key on the source files, the build configuration files, and the toolchain version,
for example `hashFiles('src/**', 'tsconfig.json', 'vite.config.*')` plus the Node version. A lockfile
hash alone would restore stale output after a source change. Task runners such as Turborepo and Nx
compute this input hash themselves, so prefer their remote or local cache to a hand built key.

Restore keys, the prefix fallbacks above, are safe for dependency stores because the frozen install
corrects any difference. For build output they are safe only when the tool does its own invalidation,
as Cargo's `target` directory and TypeScript's incremental build info do. Never restore a partial match
of build output that is then shipped as is.

## What runs where

Pre-commit, on staged files only, fast enough that nobody bypasses it:

- formatter
- quick lint on changed files
- secret scan of the staged diff (gitleaks or trufflehog)
- lockfile consistency check when the manifest changed

Pre-push, slower but still local:

- type check
- tests affected by the change

CI, authoritative, because hooks can be skipped or never installed:

- frozen install
- format check, full lint, type check
- full test suite and build
- secret scan of every commit in the pull request
- dependency update pull requests from Renovate or Dependabot, covering packages, CI actions and image digests

Hook managers: husky or lefthook in JavaScript projects, the pre-commit framework for Python and mixed
repositories. Whichever is used, install it from the one setup command, so new clones get hooks without
a separate step.
