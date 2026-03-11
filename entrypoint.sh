#!/bin/bash
set -e

# When GitHub Actions runs a Docker container, it mounts the repository code
# into the /github/workspace directory inside the container.
# We need to change into that directory so our git and gh commands work!
cd "$GITHUB_WORKSPACE"

# GitHub Actions passes inputs as environment variables with the prefix INPUT_
# We'll map those to the expected variables in our scripts
export GROQ_API_KEY="$INPUT_GROQ_API_KEY"
export GH_TOKEN="$INPUT_GITHUB_TOKEN"

# Now we run our 3 phases sequentially exactly as before
/app/scripts/miner.sh
python3 /app/scripts/analyzer.py
/app/scripts/pr_creator.sh
