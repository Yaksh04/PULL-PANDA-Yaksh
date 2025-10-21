import requests
import os
import subprocess
import tempfile
import re
from dotenv import load_dotenv
from langchain.prompts import ChatPromptTemplate
from langchain.schema.output_parser import StrOutputParser
from langchain_groq import ChatGroq

# =====================================================
# 1. Load API Keys & GitHub Config
# =====================================================
load_dotenv()
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GROQ_API_KEY = os.getenv("API_KEY")
owner = os.getenv("OWNER")
repo = os.getenv("REPO")
pr_number = os.getenv("PR_NUMBER")

if not GROQ_API_KEY:
    raise ValueError("❌ GROQ_API_KEY not found. Please set it in .env file.")


# =====================================================
# 2. Fetch PR Diff from GitHub
# =====================================================
def fetch_pr_diff(owner, repo, pr_number, token):
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}"
    headers = {"Authorization": f"token {token}"}
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        raise Exception(f"GitHub API Error: {response.json()}")
    diff_url = response.json()["diff_url"]
    diff = requests.get(diff_url, headers=headers).text
    return diff


# =====================================================
# 3. Detect Languages from Diff
# =====================================================
def detect_languages_from_diff(diff_text):
    """Infer file types/languages from PR diff."""
    extensions = re.findall(r'\+\+\+ b/.*\.(\w+)', diff_text)
    languages = set()
    for ext in extensions:
        ext = ext.lower()
        if ext in ["py"]:
            languages.add("python")
        elif ext in ["js", "jsx", "ts", "tsx"]:
            languages.add("javascript")
        elif ext in ["java"]:
            languages.add("java")
        elif ext in ["cpp", "cc", "cxx", "h", "hpp"]:
            languages.add("cpp")
        elif ext in ["go"]:
            languages.add("go")
        elif ext in ["kt"]:
            languages.add("kotlin")
        elif ext in ["rs"]:
            languages.add("rust")
    return list(languages)


# =====================================================
# 4. Run Static Analysis by Language
# =====================================================
def run_static_analysis(diff_text):
    """Run appropriate static analyzers depending on language."""
    languages = detect_languages_from_diff(diff_text)
    if not languages:
        return "⚠️ No recognizable programming language found in PR diff."

    results = []
    with tempfile.TemporaryDirectory() as tmpdir:
        # Save diff for context (optional)
        diff_path = os.path.join(tmpdir, "pr_diff.patch")
        with open(diff_path, "w", encoding="utf-8") as f:
            f.write(diff_text)

        # Loop through each detected language
        for lang in languages:
            results.append(f"=== 🔍 Static Analysis for {lang.upper()} ===")

            try:
                if lang == "python":
                    pylint_output = subprocess.getoutput("pylint --exit-zero .")
                    flake8_output = subprocess.getoutput("flake8 . --exit-zero")
                    bandit_output = subprocess.getoutput("bandit -r . --exit-zero")
                    mypy_output = subprocess.getoutput("mypy --ignore-missing-imports .")
                    results.extend([
                        "🧩 Pylint:\n" + pylint_output,
                        "🎯 Flake8:\n" + flake8_output,
                        "🔒 Bandit:\n" + bandit_output,
                        "🧠 Mypy:\n" + mypy_output
                    ])

                elif lang == "java":
                    results.append(subprocess.getoutput("checkstyle -c /google_checks.xml ."))

                elif lang == "javascript":
                    results.append(subprocess.getoutput("eslint . --max-warnings=0"))

                elif lang == "cpp":
                    results.append(subprocess.getoutput("cppcheck --enable=all ."))

                elif lang == "go":
                    results.append(subprocess.getoutput("staticcheck ./..."))

                elif lang == "kotlin":
                    results.append(subprocess.getoutput("detekt --input ."))

                elif lang == "rust":
                    results.append(subprocess.getoutput("cargo clippy -- -D warnings"))

                else:
                    results.append(f"No analyzer configured for {lang}")

            except Exception as e:
                results.append(f"Error running analyzer for {lang}: {e}")

    return "\n\n".join(results)


# =====================================================
# 5. Post Review Comment to GitHub
# =====================================================
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


# =====================================================
# 6. Initialize Groq LLM (AI Reviewer)
# =====================================================
llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    temperature=0.3,
    api_key=GROQ_API_KEY,
)
parser = StrOutputParser()

review_prompt = ChatPromptTemplate.from_messages([
    ("system",
     "You are a senior software engineer reviewing a GitHub Pull Request. "
     "You will receive the PR diff and static analysis results. "
     "Provide clear, concise, and technically correct review comments. "
     "Focus on correctness, maintainability, security, and readability."),
    ("human",
     "Here is the PR diff:\n\n{diff}\n\n"
     "And here are static analysis results:\n\n{static}\n\n"
     "Now provide a professional GitHub PR review. Include actionable feedback, "
     "specific file references, and improvement suggestions.")
])

review_chain = review_prompt | llm | parser


# =====================================================
# 7. Main Logic
# =====================================================
if __name__ == "__main__":
    try:
        diff_text = fetch_pr_diff(owner, repo, pr_number, GITHUB_TOKEN)
        print("✅ Diff fetched successfully.\n")

        print("🔍 Detecting language and running static analysis...")
        static_output = run_static_analysis(diff_text)

        print("🤖 Sending diff + analyzer results to AI reviewer...\n")
        review = review_chain.invoke({
            "diff": diff_text[:4000],
            "static": static_output[:4000]
        })

        print("=== 🧠 AI REVIEW RESULT ===")
        print(review)
        print("===========================")

        print("📌 Posting review comment to GitHub...")
        comment = post_review_comment(owner, repo, pr_number, GITHUB_TOKEN, review)
        print(f"✅ Review posted at: {comment['html_url']}")

    except Exception as e:
        print("Error:", str(e))
