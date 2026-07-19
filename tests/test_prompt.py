"""
Unit tests for the prompt-building layer and the local-only constants.
"""

from diffmsg.cli import MODEL, OLLAMA_URL, build_prompt

# ---------- build_prompt ----------


def test_prompt_contains_branch_and_diff():
    """The branch name and diff text appear verbatim in the prompt."""
    prompt = build_prompt("feat/x", "diff --git a/foo.py b/foo.py")
    assert "feat/x" in prompt
    assert "diff --git a/foo.py b/foo.py" in prompt


def test_prompt_ends_with_commit_title_cue():
    """The prompt ends by cueing the model for the title line."""
    prompt = build_prompt("main", "some diff")
    assert prompt.endswith("Commit title:")


def test_prompt_states_the_rules():
    """The prefix list and the 100-character ceiling are in the rules."""
    prompt = build_prompt("main", "some diff")
    assert "feat fix docs refactor test chore style" in prompt
    assert "100 characters" in prompt


# ---------- constants ----------


def test_ollama_url_is_local():
    """The endpoint must be localhost -- no accidental cloud calls."""
    assert OLLAMA_URL.startswith("http://localhost")


def test_model_is_pinned():
    """A concrete model is pinned for deterministic output."""
    assert MODEL
