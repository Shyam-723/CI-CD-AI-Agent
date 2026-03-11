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

# 1. Get the list of jobs for this run
# We ignore the job if it's currently running (which is *this* CI Healer job)
# We only want to look at jobs that have already 'completed' and 'failed'
FAILED_JOB_IDS=$(gh api repos/$GITHUB_REPOSITORY/actions/runs/$GITHUB_RUN_ID/jobs --jq '.jobs[] | select(.status=="completed" and .conclusion=="failure") | .id')

if [ -z "$FAILED_JOB_IDS" ]; then
    echo "Warning: No completed and failed jobs found for this run yet."
    echo "This might happen if the Healer runs before the failing job finishes status updates."
    # We create an empty file so the pipeline doesn't completely crash, though AI will have nothing to do.
    touch "$LOG_FILE"
    exit 0
fi

# 2. Fetch logs for each failed job
for JOB_ID in $FAILED_JOB_IDS; do
    echo "Fetching log for failed job ID: $JOB_ID"
    # Download the log for this specific job
    # gh api handles the auth token automatically
    gh api repos/$GITHUB_REPOSITORY/actions/jobs/$JOB_ID/logs > "job_${JOB_ID}.log" || true
    cat "job_${JOB_ID}.log" >> "$LOG_FILE"
done

# Check if log file is empty
if [ ! -s "$LOG_FILE" ]; then
    echo "Warning: Failed log is empty or could not be fetched."
fi

echo "Log saved to $LOG_FILE"
# Print size of log
ls -lh "$LOG_FILE"
