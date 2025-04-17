#!/bin/bash

# Check if the correct number of arguments is provided
if [ "$#" -ne 2 ]; then
    echo "Usage: $0 <submodule-path> <commit-hash>"
    exit 1
fi

SUBMODULE_PATH=$1
COMMIT_HASH=$2

# Navigate to the submodule directory
cd "$SUBMODULE_PATH" || { echo "Submodule path not found"; exit 1; }

# Update to the latest version
git pull

# Checkout the specific commit
git checkout "$COMMIT_HASH" || { echo "Failed to checkout commit"; exit 1; }

# Navigate back to the main repository
cd - || exit

# Stage the submodule change
git add "$SUBMODULE_PATH"

# Commit the change
git commit -m "Update submodule to commit $COMMIT_HASH"

echo "Submodule updated to commit $COMMIT_HASH"