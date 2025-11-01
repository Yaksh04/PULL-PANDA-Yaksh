"""
GitHub Pull Request Review Tool.

This script fetches pull request diffs from GitHub and sends them to a local
Ollama instance for AI-powered code review.
"""

import os
import json

import requests
from dotenv import load_dotenv


def fetch_pr_diff(owner: str, repo: str, pr_number: int, token: str, timeout: int = 10) -> str:
    """Fetch a pull request diff from GitHub."""
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3.diff"
    }

    try:
        resp = requests.get(url, headers=headers, timeout=timeout)
        resp.raise_for_status()
        return resp.text
    except requests.exceptions.RequestException as exc:
        raise SystemExit(f"Failed to fetch PR diff: {exc}") from exc


def call_ollama(prompt: str, timeout: int = 15) -> str:
    """Send the prompt to the local Ollama API and return the streaming response."""
    endpoint = "http://localhost:11434/api/generate"
    payload = {"model": "codellama", "prompt": prompt}

    try:
        resp = requests.post(endpoint, json=payload, stream=True, timeout=timeout)
        resp.raise_for_status()
    except requests.exceptions.RequestException as exc:
        raise SystemExit(f"Failed to call Ollama endpoint: {exc}") from exc

    review_text = ""
    for line in resp.iter_lines(decode_unicode=True):
        if not line:
            continue
        try:
            obj = json.loads(line)
            if "response" in obj:
                review_text += obj["response"]
        except json.JSONDecodeError:
            review_text += line
    return review_text.strip()


def main():
    """Main entry point: load token, fetch diff, send to LLM, and display review."""
    load_dotenv()

    github_token = os.getenv("GITHUB_TOKEN")
    if not github_token:
        raise SystemExit("❌ GITHUB_TOKEN not found. Add it to your .env file.")

    owner = "prince-chovatiya01"
    repo = "nutrition-diet-planner"
    pr_number = 2

    print("=== Fetching PR Diff ===")
    diff = fetch_pr_diff(owner, repo, pr_number, github_token)

    print("=== DIFF FETCHED (Preview) ===")
    print(diff[:500], "...", "\n")

    prompt = f"""
You are a strict GitHub code reviewer. Review the following pull request diff.

Return your feedback **in Markdown format** with the following sections:

## Summary
- Brief explanation of what the PR changes.

## Strengths
- Positive aspects in bullet points.

## Issues / Suggestions
- Potential bugs or improvements.

## Final Verdict
- e.g., LGTM ✅ or Needs Work ❌

Here is the diff:
{diff}
"""

    print("=== Requesting AI Review ===")
    review_text = call_ollama(prompt)

    print("\n=== AI REVIEW ===\n")
    print(review_text)


if __name__ == "__main__":
    main()

    