#!/usr/bin/env bash
# Build one zip per skill, a bundle of all skills, and a bundle of the agents, into dist/.
#
# Each per skill zip contains the skill folder at its root, so it can be dropped
# straight into .kiro/skills/ or uploaded through Settings, then Skills, in Kiro
# Web. The skills bundle contains every skill folder side by side. The agents
# bundle contains agents/kiro and agents/claude.
#
# Zips are reproducible: files are added in sorted order with a fixed timestamp
# taken from SOURCE_DATE_EPOCH, or from the last commit when that is unset, and zip
# runs in UTC, so the same commit gives the same checksums on any machine.
#
# Usage: bash tools/build_dist.sh

set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$root"

command -v zip >/dev/null 2>&1 || { echo "zip is not installed" >&2; exit 1; }
command -v python3 >/dev/null 2>&1 || { echo "python3 is not installed" >&2; exit 1; }
[ -d skills ] || { echo "no skills directory found in $root" >&2; exit 1; }

if [ -z "${SOURCE_DATE_EPOCH:-}" ]; then
  SOURCE_DATE_EPOCH="$(git log -1 --format=%ct 2>/dev/null || echo 315532800)"
fi
export SOURCE_DATE_EPOCH

rm -rf dist
mkdir -p dist
stage="$(mktemp -d)"
trap 'rm -rf "$stage"' EXIT

# Copy the tracked content into a staging area without caches, then normalise
# timestamps and permissions there, so the source tree is never modified.
copy() {
  local src="$1" dest="$2"
  mkdir -p "$dest"
  (cd "$src" && find . -type f ! -name '*.pyc' ! -path '*/__pycache__/*' ! -name '.DS_Store' -print0) |
    while IFS= read -r -d '' f; do
      mkdir -p "$dest/$(dirname "$f")"
      cp "$src/$f" "$dest/$f"
    done
}

normalise() {
  find "$1" -type d -exec chmod 755 {} +
  find "$1" -type f -exec chmod 644 {} +
  find "$1" -path '*/scripts/*.py' -exec chmod 755 {} +
  python3 - "$1" <<'PY'
import os, sys
stamp = int(os.environ["SOURCE_DATE_EPOCH"])
for base, dirs, files in os.walk(sys.argv[1]):
    for name in dirs + files:
        os.utime(os.path.join(base, name), (stamp, stamp))
PY
}

zipdir() {
  # zipdir <working dir> <output zip> <paths...>
  local cwd="$1" out="$2"
  shift 2
  (cd "$cwd" && find "$@" -print | LC_ALL=C sort | TZ=UTC zip -q -X -D "$out" -@)
}

count=0
for dir in skills/*/; do
  name="$(basename "$dir")"
  [ -f "$dir/SKILL.md" ] || { echo "skipping $name, no SKILL.md" >&2; continue; }
  copy "skills/$name" "$stage/skills/$name"
  count=$((count + 1))
done
[ "$count" -gt 0 ] || { echo "no skills packaged" >&2; exit 1; }

copy agents/kiro "$stage/agents/kiro"
copy agents/claude "$stage/agents/claude"
normalise "$stage"

for dir in "$stage"/skills/*/; do
  name="$(basename "$dir")"
  zipdir "$stage/skills" "$root/dist/${name}.zip" "$name"
  printf 'built dist/%-32s %8s bytes\n' "${name}.zip" "$(wc -c < "dist/${name}.zip" | tr -d ' ')"
done

zipdir "$stage/skills" "$root/dist/ai-skill-all.zip" .
printf 'built dist/%-32s %8s bytes\n' "ai-skill-all.zip" "$(wc -c < dist/ai-skill-all.zip | tr -d ' ')"
zipdir "$stage" "$root/dist/ai-skill-agents.zip" agents
printf 'built dist/%-32s %8s bytes\n' "ai-skill-agents.zip" "$(wc -c < dist/ai-skill-agents.zip | tr -d ' ')"

# A checksum file so a download can be verified. sha256sum on Linux, shasum on macOS.
if command -v sha256sum >/dev/null 2>&1; then
  (cd dist && sha256sum ./*.zip > SHA256SUMS.txt)
else
  (cd dist && shasum -a 256 ./*.zip > SHA256SUMS.txt)
fi

echo
echo "packaged $count skills and the agents into dist/"
echo "verify a download with: sha256sum -c SHA256SUMS.txt   (or shasum -a 256 -c on macOS)"
