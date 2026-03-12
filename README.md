# CI Healer Action 
The CI Healer Action is an intelligent GitHub Actions agent that automatically detects build failures, extracts the relevant error logs, analyzes them using a Llama 3 LLM (via Groq), and opens a Pull Request with the correct fix!

This repository provides the **Dockerized version** of the action, meaning it runs in a clean, isolated environment with all required dependencies pre-installed. It works beautifully on both GitHub-hosted and self-hosted runners.

## How it Works

1. **The Log Miner:** When a job fails, the action uses the GitHub API to fetch the specific log for the failed job.
2. **The Agent Brain:** A Python script prunes the log to fit the LLM token window and queries Groq's `llama-3.1-8b-instant` model to find the root cause, identify the broken file, and generate an exact search-and-replace fix.
3. **The PR Creator:** The action dynamically resolves the file path, applies the text replacement, creates a new branch, and uses the GitHub CLI to open a Pull Request with the AI's explanation.

---

## Quick Start Guide

To use the Dockerized CI Healer Action in your own repository, follow these steps:

### 1. Repository Settings (CRITICAL)
By default, GitHub prevents Actions from opening Pull Requests. You **must** enable this setting for the agent to work:
1. Go to your repository **Settings**.
2. Click **Actions** -> **General** on the left sidebar.
3. Scroll down to **Workflow permissions**.
4. Check the box for **"Allow GitHub Actions to create and approve pull requests"**.
5. Click **Save**.

### 2. Add the Groq API Key
The agent needs a Groq API key to power the LLM.
1. Get a free API key from [Groq Console](https://console.groq.com/).
2. Go to your repository **Settings** -> **Secrets and variables** -> **Actions**.
3. Create a new repository secret named `GROQ_API_KEY` and paste your key.

### 3. Setup the Workflow
Create or update a workflow file (e.g., `.github/workflows/ci.yml`) in your repository. You must add the CI Healer as a **separate job** that runs `if: failure()` and `needs:` the job that might fail. 

It also requires specific `permissions` to read the logs and write the PR.

Here is a complete example:

```yaml
name: Example CI Pipeline

on:
  push:
    branches: [ "master", "main" ]
  pull_request:

jobs:
  # Your normal build/test job
  build_and_test:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Run Tests (that might fail)
        run: |
          make test
          # or pytest, npm test, etc.

  # The AI Healer Job
  heal:
    needs: [build_and_test]
    if: failure() # Only run if the build fails!
    runs-on: ubuntu-latest
    # REQUIRED PERMISSIONS
    permissions:
      contents: write       # To push the new branch
      pull-requests: write  # To create the PR
      actions: read         # To download the failed job logs
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Run CI Healer Action
        # Point to the docker branch of this repository!
        uses: Shyam-723/CI-CD-AI-Agent@docker
        with:
          groq_api_key: ${{ secrets.GROQ_API_KEY }}
          github_token: ${{ secrets.GITHUB_TOKEN }}
```

## Inputs

| Parameter | Required | Description |
| --- | --- | --- |
| `groq_api_key` | **Yes** | Your Groq API key (pass via secrets). |
| `github_token` | **Yes** | The default `${{ secrets.GITHUB_TOKEN }}` for the runner. |

## Troubleshooting

* **`pull request create failed: GraphQL: ... Base ref must be a branch`**: The action dynamically targets the repository's default branch (e.g., `main` or `master`). Ensure your repository has a valid default branch set.
* **`pull request create failed: GraphQL: GitHub Actions is not permitted to create or approve pull requests`**: You forgot to enable "Allow GitHub Actions to create and approve pull requests" in your repository Settings -> Actions -> General.
* **The fix wasn't applied or `git add` failed**: The LLM might have heavily hallucinated a file path that doesn't exist, or requested a string replacement for code that isn't exactly matched in the file. Re-running the job often yields a better LLM response.
