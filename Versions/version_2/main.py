import requests
import os
import subprocess
import tempfile
from dotenv import load_dotenv
from langchain.prompts import ChatPromptTemplate
from langchain.schema.output_parser import StrOutputParser
from langchain_groq import ChatGroq

# 1. Load API Keys
load_dotenv()
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GROQ_API_KEY = os.getenv("API_KEY")
owner = os.getenv("OWNER")
repo = os.getenv("REPO")
pr_number = os.getenv("PR_NUMBER")

if not GROQ_API_KEY:
    raise ValueError("❌ GROQ_API_KEY not found. Please set it in .env file.")

# 2. Fetch PR Diff
def fetch_pr_diff(owner, repo, pr_number, token):
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}"
    headers = {"Authorization": f"token {token}"}
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        raise Exception(f"GitHub API Error: {response.json()}")
    diff_url = response.json()["diff_url"]
    diff = requests.get(diff_url, headers=headers).text
    return diff

# 3. Run static analysis (example: pylint)
def run_static_analysis(diff_text):
    """Run pylint on changed files (extracted from diff)."""
    static_results = []

    # Create temporary folder for analysis
    with tempfile.TemporaryDirectory() as tmpdir:
        # Save the diff text to a temporary file for reference
        diff_path = os.path.join(tmpdir, "pr_diff.patch")
        with open(diff_path, "w", encoding="utf-8") as f:
            f.write(diff_text)

        # (Optional) If you have repo checked out locally, you can run:
        # pylint_output = subprocess.getoutput(f"pylint path/to/changed/files")

        # For demonstration, we run pylint on the temporary folder
        try:
            pylint_result = subprocess.getoutput("pylint --exit-zero .")
            static_results.append("Pylint Results:\n" + pylint_result)
        except Exception as e:
            static_results.append(f"Error running pylint: {e}")

    return "\n\n".join(static_results)

# 4. Post review to GitHub
def post_review_comment(owner, repo, pr_number, token, review_body):
    url = f"https://api.github.com/repos/{owner}/{repo}/issues/{pr_number}/comments"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github+json"
    }
    payload = {"body": review_body}
    response = requests.post(url, headers=headers, json=payload)
    if response.status_code not in [200, 201]:
        raise Exception(f"❌ Failed to post comment: {response.json()}")
    return response.json()

# 5. Initialize Groq LLM
llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    temperature=0.3,
    api_key=GROQ_API_KEY,
)
parser = StrOutputParser()

review_prompt = ChatPromptTemplate.from_messages([
    ("system",
     "You are a senior software engineer reviewing a GitHub Pull Request. "
     "Use both the static analysis evidence and the diff to produce precise, "
     "constructive comments."),
    ("human",
     "Here is the PR diff:\n\n{diff}\n\n"
     "And here are static analysis results:\n\n{static}\n\n"
     "Combine these insights to produce a high-quality review. "
     "Mention file names, potential issues, and improvements clearly.")
])

review_chain = review_prompt | llm | parser

# 6. Main
if __name__ == "__main__":
    try:
        diff_text = fetch_pr_diff(owner, repo, pr_number, GITHUB_TOKEN)
        print("✅ Diff fetched successfully.\n")

        print("🔍 Running static analysis...")
        static_output = run_static_analysis(diff_text)

        print("🤖 Sending diff + analyzer output to AI reviewer...\n")
        review = review_chain.invoke({
            "diff": diff_text[:4000],
            "static": static_output[:4000]  # avoid token overflow
        })

        print("=== AI REVIEW RESULT ===")
        print(review)
        print("========================")

        print("📌 Posting review comment to GitHub...")
        comment = post_review_comment(owner, repo, pr_number, GITHUB_TOKEN, review)
        print(f"✅ Review posted at: {comment['html_url']}")

    except Exception as e:
        print("Error:", str(e))
