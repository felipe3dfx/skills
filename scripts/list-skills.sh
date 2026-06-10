#!/usr/bin/env bash
set -euo pipefail

# Lists every skill in the repo and validates two invariants:
#   1. Every path in .claude-plugin/plugin.json resolves to a real SKILL.md.
#   2. Every SKILL.md on disk is registered in plugin.json (no orphans).
# Also flags any SKILL.md missing a `name:` frontmatter field.
# Exits non-zero if any invariant is broken — safe to run in CI.

REPO="$(cd "$(dirname "$0")/.." && pwd)"
PLUGIN="$REPO/.claude-plugin/plugin.json"
status=0

# Paths declared in plugin.json (strip ./ prefix, one per line).
declared="$(grep -oE '"\./skills/[^"]+"' "$PLUGIN" | tr -d '"' | sed 's|^\./||' | sort)"

# Skill dirs on disk (parent of each SKILL.md).
on_disk="$(find "$REPO/skills" -name SKILL.md -not -path '*/node_modules/*' \
  | sed "s|^$REPO/||;s|/SKILL.md$||" | sort)"

echo "== Declared in plugin.json =="
while IFS= read -r path; do
  [ -z "$path" ] && continue
  skill_md="$REPO/$path/SKILL.md"
  if [ ! -f "$skill_md" ]; then
    echo "  MISSING  $path  (declared but no SKILL.md)"
    status=1
    continue
  fi
  if ! grep -qE '^name:' "$skill_md"; then
    echo "  NO-NAME  $path  (SKILL.md has no 'name:' frontmatter)"
    status=1
    continue
  fi
  name="$(grep -m1 -E '^name:' "$skill_md" | sed 's/^name:[[:space:]]*//')"
  echo "  ok       $path  ->  $name"
done <<< "$declared"

echo
echo "== Orphans (SKILL.md on disk but not in plugin.json) =="
orphans="$(comm -23 <(echo "$on_disk") <(echo "$declared"))"
if [ -z "$orphans" ]; then
  echo "  none"
else
  echo "$orphans" | sed 's/^/  ORPHAN   /'
  status=1
fi

exit "$status"
