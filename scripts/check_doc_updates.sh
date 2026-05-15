#!/bin/bash
# Session-start hook for ROOPS doc protocol.
# Pulls origin/main and reports docs/ changes since last pull.
# Adopted from Aegis (moosjiny/dual_arms commit 13cea80).
set -u

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_DIR" || { echo "[check_doc_updates] cannot cd to repo root"; exit 1; }

# Warn (not block) on dirty tree — git pull will refuse if it'd clobber changes
if ! git diff --quiet || ! git diff --cached --quiet; then
    echo "[check_doc_updates] WARN: working tree has uncommitted changes."
    echo "  If pull fails: git stash && bash \"$0\" && git stash pop"
fi

if ! git pull origin main --quiet; then
    echo "[check_doc_updates] git pull failed — see error above."
    exit 1
fi

echo "[check_doc_updates] docs/ activity:"
if git rev-parse --verify ORIG_HEAD >/dev/null 2>&1 \
   && [ "$(git rev-parse ORIG_HEAD)" != "$(git rev-parse HEAD)" ]; then
    git log ORIG_HEAD..HEAD --pretty=format:"  %h %ad %s" --date=short -- docs/
    echo
    changed=$(git diff --name-only ORIG_HEAD..HEAD -- docs/)
    if [ -n "$changed" ]; then
        echo "  files:"
        printf "    %s\n" $changed
    fi
else
    echo "  (no new commits; showing last 3 doc commits)"
    git log -3 --pretty=format:"  %h %ad %s" --date=short -- docs/
    echo
fi
