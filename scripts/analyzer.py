import os
import json
import sys
import tiktoken
from groq import Groq

# Constants
MAX_TOKENS = 6000 # Adjust based on model limits (giving buffer for prompt and output)
ANCHORS = ["error", "fail", "exception", "traceback", "fatal"]
LOG_FILE = "failed_job.log"
OUTPUT_FILE = "analysis_result.json"

def count_tokens(text: str, model="gpt-3.5-turbo") -> int:
    """Estimate token count using tiktoken. Since Groq uses Llama 3, 
    cl100k_base is a reasonable proxy if exact Llama tokenizer isn't locally available."""
    encoding = tiktoken.get_encoding("cl100k_base")
    return len(encoding.encode(text))

def prune_log(filepath: str) -> str:
    """Extracts windows of lines around relevant anchor keywords."""
    if not os.path.exists(filepath):
        print(f"Error: {filepath} not found.")
        sys.exit(1)

    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()

    relevant_indices = set()
    for i, line in enumerate(lines):
        line_lower = line.lower()
        if any(anchor in line_lower for anchor in ANCHORS):
            # Window: 30 lines before, 70 lines after
            start = max(0, i - 30)
            end = min(len(lines), i + 70)
            for j in range(start, end):
                relevant_indices.add(j)

    if not relevant_indices:
        print("No anchors found, using the last 200 lines as a fallback.")
        relevant_indices = set(range(max(0, len(lines) - 200), len(lines)))

    pruned_lines = [lines[i] for i in sorted(relevant_indices)]
    pruned_text = "".join(pruned_lines)

    # Iteratively reduce if token budget is exceeded
    while count_tokens(pruned_text) > MAX_TOKENS and len(pruned_lines) > 50:
        # Cut 10% from the beginning (assuming errors are usually towards the end)
        cut_index = int(len(pruned_lines) * 0.1)
        pruned_lines = pruned_lines[cut_index:]
        pruned_text = "".join(pruned_lines)
    
    return pruned_text

def analyze_log(api_key: str, log_content: str, workspace_files: str):
    """Calls Groq API to analyze the structured log."""
    client = Groq(api_key=api_key)
    
    prompt = f"""You are a CI Healer agent. Analyze the following failed build log and suggest a fix.
You must return your response STRICTLY as a JSON object with no markdown formatting around it.
The JSON must have the following keys:
- "root_cause": A short string explaining what broke.
- "file_to_fix": The filepath of the file that needs changing.
- "search_content": The exact string in the file to be replaced. Must be an exact match of existing lines.
- "replace_content": The new string that should replace the search_content.

CRITICAL INSTRUCTION:
The log might contain references to temporary GitHub Actions runner scripts (e.g., /home/runner/work/_temp/...sh). 
DO NOT suggest fixes for these temporary files, as they are non-existent in the repository. 
If the error happens in a temporary script, the actual fix must be applied to the `.github/workflows/*.yml` file that generated it, or a script tracked in the repository.

Here is a list of all tracked files in the repository to help you identify the correct `file_to_fix`:
{workspace_files}

Log content:
{log_content}
"""

    print("Sending request to Groq...")
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": "You are an expert software engineer and debugger."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.2, # Low temperature for more deterministic output
        response_format={"type": "json_object"} # Ensure structure
    )

    try:
        content = response.choices[0].message.content
        result = json.loads(content)
        return result
    except json.JSONDecodeError as e:
        print(f"Failed to parse JSON response: {e}")
        print("Raw response:", content)
        sys.exit(1)
    except Exception as e:
        print(f"Error communicating with Groq: {e}")
        sys.exit(1)

def main():
    print("Starting Phase B: Agent Brain...")
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        print("Error: GROQ_API_KEY environment variable is missing.")
        sys.exit(1)

    print("Pruning logs...")
    pruned_log = prune_log(LOG_FILE)
    tokens = count_tokens(pruned_log)
    print(f"Pruned log size: {tokens} tokens.")

    print("Gathering workspace context...")
    # Get a tree or list of files to help the LLM know the real structure
    try:
        workspace_files = os.popen('find . -type f -not -path "*/\.git/*" | sort').read()
    except Exception as e:
        print(f"Warning: Could not list workspace files: {e}")
        workspace_files = ""

    result = analyze_log(api_key, pruned_log, workspace_files)

    print("Analysis complete. Saving result...")
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2)

    print(f"Result saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
