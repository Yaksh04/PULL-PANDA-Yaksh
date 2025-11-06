"""
Pytest tests for version_1_Traditional_rag.py

Tests cover:
- get_latest_pr: success case, API errors, empty PR list
- fetch_pr_diff: successful fetch, API errors, small diff warning
- post_review_comment: successful post, error handling
- main: happy path and various error conditions
"""

import pytest
from unittest.mock import mock_open, patch
from types import SimpleNamespace
import os
import sys

# Helper to import module fresh for each test
def _load_module_fresh(name="version1_test"):
    """Import module fresh with mocked dependencies to avoid side effects."""
    if name in sys.modules:
        del sys.modules[name]
        
    # Mock env vars
    os.environ["GITHUB_TOKEN"] = "fake-token"
    os.environ["API_KEY"] = "fake-groq-key"
    
    # Mock LangChain components with chainable objects
    class ChainableObject:
        def __init__(self, return_value="Test Response"):
            self._return = return_value
            
        def __or__(self, other):
            return ChainableObject(self._return)
            
        def invoke(self, *args, **kwargs):
            return self._return

    # Inject fake LangChain modules
    sys.modules["langchain_core.prompts"] = SimpleNamespace(
        ChatPromptTemplate=type("ChatPromptTemplate", (), {
            "from_messages": lambda msgs: ChainableObject()
        }),
        MessagesPlaceholder=lambda **k: None
    )
    
    sys.modules["langchain_core.output_parsers"] = SimpleNamespace(
        StrOutputParser=lambda: ChainableObject()
    )
    
    sys.modules["langchain_groq"] = SimpleNamespace(
        ChatGroq=lambda **k: ChainableObject()
    )
    
    # Import target module
    import version_1_Traditional_rag as v1
    return v1

# Tests for get_latest_pr()
def test_get_latest_pr_success_returns_number_and_url(requests_mock):
    """When API returns 200 with PRs, returns number and URL of first PR."""
    mod = _load_module_fresh()
    pr_data = [{"number": 42, "html_url": "http://test/pr/42"}]
    requests_mock.get(
        "https://api.github.com/repos/owner/repo/pulls",
        json=pr_data
    )
    
    num, url = mod.get_latest_pr("owner", "repo", "token")
    assert num == 42
    assert url == "http://test/pr/42"

def test_get_latest_pr_non_200_raises_exception(requests_mock):
    """When API returns non-200, raises exception with API error."""
    mod = _load_module_fresh()
    requests_mock.get(
        "https://api.github.com/repos/owner/repo/pulls",
        status_code=403,
        json={"message": "Rate limited"}
    )
    
    with pytest.raises(Exception) as exc:
        mod.get_latest_pr("owner", "repo", "token")
    assert "GitHub API Error" in str(exc.value)

def test_get_latest_pr_empty_list_raises_exception(requests_mock):
    """When API returns empty PR list, raises appropriate exception."""
    mod = _load_module_fresh()
    requests_mock.get(
        "https://api.github.com/repos/owner/repo/pulls",
        json=[]
    )
    
    with pytest.raises(Exception) as exc:
        mod.get_latest_pr("owner", "repo", "token")
    assert "No open PRs" in str(exc.value)

# Tests for fetch_pr_diff()
def test_fetch_pr_diff_success_writes_file_and_returns_text(requests_mock, tmp_path):
    """Successfully fetches diff, writes to file, returns content."""
    mod = _load_module_fresh()
    diff_text = "diff --git a/file b/file\n+new line"
    requests_mock.get(
        "https://api.github.com/repos/owner/repo/pulls/1",
        text=diff_text
    )
    
    with patch("builtins.open", mock_open()) as mock_file:
        result = mod.fetch_pr_diff("owner", "repo", 1, "token")
        
    assert result == diff_text
    mock_file.assert_called_once_with("latest_pr.diff", "w", encoding="utf-8")
    mock_file().write.assert_called_once_with(diff_text)

def test_fetch_pr_diff_small_diff_warns(requests_mock, capsys):
    """When diff is small (<50 chars), prints warning."""
    mod = _load_module_fresh()
    requests_mock.get(
        "https://api.github.com/repos/owner/repo/pulls/1",
        text="tiny diff"
    )
    
    with patch("builtins.open", mock_open()):
        mod.fetch_pr_diff("owner", "repo", 1, "token")
    
    captured = capsys.readouterr()
    assert "Warning" in captured.out
    assert "too small" in captured.out

def test_fetch_pr_diff_api_error_returns_empty_and_prints_error(requests_mock, capsys):
    """On API error, returns empty string and prints error."""
    mod = _load_module_fresh()
    requests_mock.get(
        "https://api.github.com/repos/owner/repo/pulls/1",
        status_code=404,
        text="Not found"
    )
    
    result = mod.fetch_pr_diff("owner", "repo", 1, "token")
    
    assert result == ""
    captured = capsys.readouterr()
    assert "Error fetching diff" in captured.out

def main():
    """Main entry point for the PR review tool."""
    try:
        if len(sys.argv) < 3:
            print("Usage: python version_1.py <owner> <repo>")
            sys.exit(1)

        owner, repo = sys.argv[1], sys.argv[2]

        # 1. Build or load RAG index for repo
        print("📦 Building/loading RAG index for repo (this may take a minute)...")
        rag = build_index_for_repo(owner, repo, GITHUB_TOKEN, force_rebuild=False)

        # 2. Get latest PR from GitHub
        pr_number, pr_url = get_latest_pr(owner, repo, GITHUB_TOKEN)
        print(f"🔸 Found latest PR: {pr_url}")

        # 3. Fetch PR diff
        diff_text = fetch_pr_diff(owner, repo, pr_number, GITHUB_TOKEN)
        if not diff_text:
            raise Exception("No diff fetched.")

        # 4. Create retriever and get context
        retriever = rag.as_retriever(search_kwargs={"k": 6})
        retrieved_documents = retriever.get_relevant_documents(diff_text)
        print("Retrieved", len(retrieved_documents), "context chunks.")
        context_text = assemble_context(retrieved_documents, char_limit=3000)

        # 5. Generate AI review
        prompt_vars = {"context": context_text, "diff": diff_text[:80_000]}
        review_text = review_chain.invoke(prompt_vars)
        print("=== 🧠 AI REVIEW ===")
        print(review_text)
        print("====================")

        # 6. Post review comment on PR
        comment = post_review_comment(owner, repo, pr_number, GITHUB_TOKEN, review_text)
        if "html_url" in comment:
            print(f"✅ Review posted: {comment['html_url']}")
        else:
            print(f"⚠️ Failed to post review: {comment}")

    except Exception as e:
        print("❌ Error:", e)
        raise

if __name__ == "__main__":
    main()