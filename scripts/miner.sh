#!/bin/bash
set -e

echo "Starting Phase A: Log Miner..."

# Ensure we have the run ID
if [ -z "$GITHUB_RUN_ID" ]; then
    echo "Error: GITHUB_RUN_ID is not set."
    exit 1
fi

LOG_FILE="failed_job.log"

echo "Fetching logs for run ID: $GITHUB_RUN_ID"
# Using GitHub CLI to fetch only the failed logs
gh run view "$GITHUB_RUN_ID" --log-failed > "$LOG_FILE"

# Check if log file is empty
if [ ! -s "$LOG_FILE" ]; then
    echo "Warning: Failed log is empty or could not be fetched."
    # We could optionally fallback to fetching all logs, but usually log-failed is better
    # gh run view "$GITHUB_RUN_ID" --log > "$LOG_FILE"
fi

echo "Log saved to $LOG_FILE"
# Print size of log
ls -lh "$LOG_FILE"
