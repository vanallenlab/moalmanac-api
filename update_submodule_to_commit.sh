#!/bin/bash

SUBMODULE_PATH=moalmanac-db
COMMIT_HASH=$1

# Navigate to the submodule directory
cd "$SUBMODULE_PATH" || { echo "Submodule path not found"; exit 1; }

# Update to the latest version
git checkout main
git pull

# Checkout the specific commit, if provided
if [[ -n "$COMMIT_HASH" ]]; then
  git checkout "$COMMIT_HASH" || { echo "Failed to checkout commit"; exit 1; }
fi

# Navigate back to the main repository
cd - || exit

# Stage the submodule change
git add "$SUBMODULE_PATH"

# Commit the change
if [[ -n "$COMMIT_HASH" ]]; then
  git commit -m "Update submodule to commit $COMMIT_HASH"
  echo "Submodule updated to commit $COMMIT_HASH"
else
  LATEST_HASH=$(git -C "$SUBMODULE_PATH" rev-parse HEAD)
  git commit -m "Update submodule to latest commit on main ($LATEST_HASH)"
  echo "Submodule updated to latest commit on main ($LATEST_HASH)"
fi
