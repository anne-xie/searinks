#!/usr/bin/env bash
# Copy the data branch's files into site/data/ and print its commit, or nothing if the branch doesn't exist yet.
set -euo pipefail

mkdir -p site/data
if git ls-remote --exit-code --heads origin data >/dev/null; then
  git fetch --quiet --no-tags --depth=1 origin data
  git archive FETCH_HEAD | tar -x -C site/data
  git rev-parse FETCH_HEAD
fi
