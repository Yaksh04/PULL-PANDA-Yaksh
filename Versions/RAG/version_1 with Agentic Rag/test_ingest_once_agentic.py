"""
Pytest suite for ingest_once_agentic.py

Each test is unique and covers a distinct normal flow, edge case, or boundary condition:
- missing token -> ValueError
- insufficient CLI args -> prints usage and exits (SystemExit)
- successful invocation -> build_index_for_repo called with expected args (force_rebuild=True)
- build_index_for_repo raising -> exception propagates
- owner/repo contain special characters -> passed through unchanged

Tests import the module fresh per test and inject a fake rag_loader_agentic module
so the real index-building code is not executed.
"""
import importlib.util
import sys
import os
import types
import pytest

MODULE_PATH = os.path.join(os.path.dirname(__file__), "ingest_once_agentic.py")


def _load_module_fresh(name="ingest_once_agentic"):
    """Load the target module from file path under the given module name."""
    # ensure fresh import
    if name in sys.modules:
        del sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _make_fake_rag_module(build_fn):
    """Create a fake rag_loader_agentic module object with build_index_for_repo = build_fn."""
    mod = types.ModuleType("rag_loader_agentic")
    mod.build_index_for_repo = build_fn
    return mod


def test_missing_github_token_raises_value_error(monkeypatch):
    """No GITHUB_TOKEN in environment should raise ValueError at import time."""
    # Ensure env var absent
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    # Provide a harmless fake rag_loader_agentic to avoid import errors unrelated to the token
    fake_mod = _make_fake_rag_module(lambda *a, **k: None)
    sys.modules["rag_loader_agentic"] = fake_mod
    # Clear argv to avoid other exit branches
    monkeypatch.setattr(sys, "argv", ["ingest_once_agentic.py"])
    with pytest.raises(ValueError):
        _load_module_fresh("ingest_missing_token")
    # cleanup
    del sys.modules["rag_loader_agentic"]


def test_insufficient_cli_arguments_prints_usage_and_exits(monkeypatch, capsys):
    """If fewer than 2 CLI args provided (owner, repo), module should print usage and exit with code 1."""
    # Ensure token exists so token check passes
    monkeypatch.setenv("GITHUB_TOKEN", "ghp_testtoken")
    # Inject fake rag module (should not be called because sys.exit runs first)
    fake_mod = _make_fake_rag_module(lambda *a, **k: (_ for _ in ()).throw(RuntimeError("should not be called")))
    sys.modules["rag_loader_agentic"] = fake_mod
    # Simulate insufficient args (only script name)
    monkeypatch.setattr(sys, "argv", ["ingest_once_agentic.py"])
    with pytest.raises(SystemExit) as se:
        _load_module_fresh("ingest_insufficient_args")
    # sys.exit(1) expected
    assert se.value.code == 1
    out = capsys.readouterr().out
    assert "Usage: python" in out and "<owner> <repo>" in out
    del sys.modules["rag_loader_agentic"]


def test_calls_build_index_for_repo_with_owner_repo_and_force_rebuild_true(monkeypatch):
    """When valid token and CLI args given, build_index_for_repo must be called with (owner, repo, token, force_rebuild=True)."""
    monkeypatch.setenv("GITHUB_TOKEN", "ghp_token_ABC")
    called = {}
    def fake_build_index_for_repo(owner, repo, token, force_rebuild=False):
        called["args"] = (owner, repo, token, force_rebuild)
        # simulate normal completion
        return "ok"
    # inject fake module before importing target
    sys.modules["rag_loader_agentic"] = _make_fake_rag_module(fake_build_index_for_repo)
    monkeypatch.setattr(sys, "argv", ["ingest_once_agentic.py", "some-owner", "some-repo"])
    mod = _load_module_fresh("ingest_success_call")
    # ensure fake was invoked and args match
    assert "args" in called
    owner, repo, token, fr = called["args"]
    assert owner == "some-owner"
    assert repo == "some-repo"
    assert token == "ghp_token_ABC"
    assert fr is True
    # cleanup
    del sys.modules["rag_loader_agentic"]


def test_build_index_for_repo_exception_propagates_during_import(monkeypatch):
    """If build_index_for_repo raises an exception, it should propagate when importing the script."""
    monkeypatch.setenv("GITHUB_TOKEN", "ghp_token_ERR")
    def raising_build(owner, repo, token, force_rebuild=False):
        raise RuntimeError("indexing failed")
    sys.modules["rag_loader_agentic"] = _make_fake_rag_module(raising_build)
    monkeypatch.setattr(sys, "argv", ["ingest_once_agentic.py", "o", "r"])
    with pytest.raises(RuntimeError) as exc:
        _load_module_fresh("ingest_build_raises")
    assert "indexing failed" in str(exc.value)
    del sys.modules["rag_loader_agentic"]


def test_owner_repo_with_special_characters_are_passed_through(monkeypatch):
    """Owner and repo names containing special characters should be passed unchanged to build_index_for_repo."""
    monkeypatch.setenv("GITHUB_TOKEN", "ghp_token_SPEC")
    captured = {}
    def capture_build(owner, repo, token, force_rebuild=False):
        captured["owner"] = owner
        captured["repo"] = repo
        captured["token"] = token
        captured["force_rebuild"] = force_rebuild
    sys.modules["rag_loader_agentic"] = _make_fake_rag_module(capture_build)
    special_owner = "user-name_123.@"
    special_repo = "repo.name-with+chars~"
    monkeypatch.setattr(sys, "argv", ["ingest_once_agentic.py", special_owner, special_repo])
    _load_module_fresh("ingest_special_chars")
    assert captured.get("owner") == special_owner
    assert captured.get("repo") == special_repo
    assert captured.get("token") == "ghp_token_SPEC"
    assert captured.get("force_rebuild") is True
    del sys.modules["rag_loader_agentic"]