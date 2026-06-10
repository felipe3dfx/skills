#!/usr/bin/env bash
set -euo pipefail

# Symlinks every skill in this repo into ~/.claude/skills so the local Claude
# CLI loads your in-progress edits live — change a SKILL.md, use it immediately,
# no reinstall.
#
# Non-destructive by design: this machine's ~/.claude/skills already holds real
# installs (plugins and copied skills). We NEVER delete a real directory. We only
# create new symlinks or re-point symlinks we previously made. Anything else is
# skipped with a warning so you can resolve it by hand.

REPO="$(cd "$(dirname "$0")/.." && pwd)"
DEST="$HOME/.claude/skills"

# If ~/.claude/skills is itself a symlink into this repo, per-skill links would
# write back into the repo's own tree. Bail instead of polluting the working copy.
if [ -L "$DEST" ]; then
  resolved="$(readlink -f "$DEST")"
  case "$resolved" in
    "$REPO" | "$REPO"/*)
      echo "error: $DEST is a symlink into this repo ($resolved)." >&2
      echo "Remove it (rm \"$DEST\") and re-run; it will be recreated as a real dir." >&2
      exit 1
      ;;
  esac
fi

mkdir -p "$DEST"

linked=0 skipped=0
find "$REPO/skills" -name SKILL.md -not -path '*/node_modules/*' -print0 \
  | while IFS= read -r -d '' skill_md; do
  src="$(dirname "$skill_md")"
  name="$(basename "$src")"
  target="$DEST/$name"

  if [ -e "$target" ] && [ ! -L "$target" ]; then
    echo "SKIP  $name  (a real directory already exists at $target — remove it yourself if you want the repo version)"
    skipped=$((skipped + 1))
    continue
  fi
  # Re-point existing symlinks freely; create new ones otherwise.
  ln -sfn "$src" "$target"
  echo "link  $name -> $src"
  linked=$((linked + 1))
done
