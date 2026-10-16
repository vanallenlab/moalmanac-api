#!/bin/bash

SUBMODULE_PATH=moalmanac-db
COMMIT_HASH=$1
# The Python used to regenerate docs/openapi.json; it needs this repo's requirements.
PYTHON=${PYTHON:-python}

# docs/openapi.json is generated from the working tree, so uncommitted changes in
# app/ would end up in the committed spec without the code that produced them.
if [[ -n "$(git status --porcelain -- app/)" ]]; then
  echo "app/ has uncommitted changes. Commit or stash them first, so docs/openapi.json"
  echo "matches the committed code."
  exit 1
fi

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

# Regenerate the OpenAPI schema, whose response schemas and examples come from
# moalmanac-db, so it is committed together with the submodule update
"$PYTHON" utils/export_openapi.py || {
  echo "Failed to export docs/openapi.json; nothing was committed. $SUBMODULE_PATH is"
  echo "checked out at the new commit but not staged. Fix the error and rerun."
  exit 1
}

# Stage the submodule change and the regenerated schema
git add "$SUBMODULE_PATH" docs/openapi.json

# Commit the change
if [[ -n "$COMMIT_HASH" ]]; then
  git commit -m "Update submodule to commit $COMMIT_HASH"
  echo "Submodule updated to commit $COMMIT_HASH"
else
  LATEST_HASH=$(git -C "$SUBMODULE_PATH" rev-parse HEAD)
  git commit -m "Update submodule to latest commit on main ($LATEST_HASH)"
  echo "Submodule updated to latest commit on main ($LATEST_HASH)"
fi
