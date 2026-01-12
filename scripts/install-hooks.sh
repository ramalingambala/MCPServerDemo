#!/usr/bin/env sh
# Install repository git hooks for local development.
# This creates/overwrites .git/hooks/pre-commit to run the scanner in scripts/precommit_check.py

set -e

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
HOOKS_DIR="$ROOT_DIR/.git/hooks"
SCRIPT_DIR="$ROOT_DIR/scripts"
PRECOMMIT_PY="$SCRIPT_DIR/precommit_check.py"
PRECOMMIT_HOOK="$HOOKS_DIR/pre-commit"

if [ ! -d "$ROOT_DIR/.git" ]; then
  echo "No .git directory found. Initialize git repo first (git init) or run this from a working repo." >&2
  exit 1
fi

mkdir -p "$HOOKS_DIR"

cat > "$PRECOMMIT_HOOK" <<'HOOK'
#!/bin/sh
python3 "$(dirname "$0")/../scripts/precommit_check.py"
RESULT=$?
if [ $RESULT -ne 0 ]; then
  echo "Pre-commit check blocked the commit. See output above." >&2
  exit $RESULT
fi
exit 0
HOOK

chmod +x "$PRECOMMIT_HOOK" || true
chmod +x "$PRECOMMIT_PY" || true

echo "Installed pre-commit hook to $PRECOMMIT_HOOK"

exit 0
