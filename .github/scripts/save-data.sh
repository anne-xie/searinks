#!/usr/bin/env bash
# Replace the data branch with a single commit holding site/data/, so its history doesn't grow.
# Pass the commit load-data.sh printed (empty for a new branch): the push fails rather than
# overwrite a data branch that changed since it was loaded.
set -euo pipefail

expected=${1:-}
root=$(git rev-parse --show-toplevel)
GIT_INDEX_FILE="$(mktemp -d)/index"
export GIT_INDEX_FILE

git -C site/data --git-dir="$root/.git" --work-tree=. add --all .
tree=$(git write-tree)
commit=$(git commit-tree "$tree" -m "Data export $(date -u +%Y-%m-%dT%H:%M:%SZ)")
git push --quiet --force-with-lease="refs/heads/data:$expected" origin "$commit:refs/heads/data"
echo "$commit"
