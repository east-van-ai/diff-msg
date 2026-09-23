"""
Unit tests for the prompt-building layer, the output shape, and the
local-only constants.

These cover what diff-msg builds and prints, which is its own and
deterministic. Nothing here checks the model's judgment.
"""

import json

import pytest
import requests

from diff_msg import cli_ask, errors
from diff_msg.cli_ask import (
    MAX_LENGTH,
    MIN_LENGTH,
    MODEL,
    OLLAMA_URL,
    SCHEMA,
    SUGGESTION_COUNT,
    build_prompt,
    format_suggestions,
)

# ---------- build_prompt ----------


def test_prompt_contains_branch_and_diff():
    """The branch name and diff text appear verbatim in the prompt."""
    prompt = build_prompt("feat/x", "diff --git a/foo.py b/foo.py")
    assert "feat/x" in prompt
    assert "diff --git a/foo.py b/foo.py" in prompt


def test_prompt_asks_for_the_count():
    """The prompt names how many suggestions it wants."""
    assert str(SUGGESTION_COUNT) in build_prompt("main", "some diff")


def test_prompt_carries_the_content_rules():
    """The rules the schema cannot express are stated in the prompt."""
    prompt = build_prompt("main", "some diff")
    assert "genuinely different" in prompt
    assert "names the whole change" in prompt
    assert "code fence" not in prompt


def test_prompt_states_the_length_range():
    """Both ends are asked for, not only enforced."""
    prompt = build_prompt("main", "some diff")
    assert str(MIN_LENGTH) in prompt
    assert str(MAX_LENGTH) in prompt


# ---------- the schema ----------


def test_schema_pins_the_count_and_the_length():
    """Exactly five items, each inside the range, enforced by the request."""
    items = SCHEMA["properties"]["suggestions"]
    assert items["minItems"] == SUGGESTION_COUNT
    assert items["maxItems"] == SUGGESTION_COUNT
    assert items["items"]["minLength"] == MIN_LENGTH
    assert items["items"]["maxLength"] == MAX_LENGTH


def test_the_floor_is_below_the_ceiling():
    """A floor above the cap would make every reply impossible."""
    assert MIN_LENGTH < MAX_LENGTH


# ---------- format_suggestions ----------


def test_format_suggestions_numbers_from_one():
    """Numbering is diff-msg's own, not the model's."""
    assert format_suggestions(["one", "two"]) == "1. one\n2. two"


def test_format_suggestions_leaves_the_text_alone():
    """The suggestion text is printed as the model wrote it."""
    assert "rename the package" in format_suggestions(["rename the package"])


# ---------- the request ----------


class _FakeResponse:
    """Stands in for a requests response carrying an Ollama reply."""

    def __init__(self, payload):
        self._payload = payload

    def json(self):
        """Return the outer Ollama envelope."""
        return {"response": self._payload}


def test_request_sends_the_schema_and_no_seed(monkeypatch):
    """The schema rides the request, and nothing pins the sampling."""
    sent = {}

    def fake_post(url, json):
        """Capture the payload instead of reaching Ollama."""
        sent.update(json)
        return _FakeResponse('{"suggestions": ["one"]}')

    monkeypatch.setattr(cli_ask.requests, "post", fake_post)
    cli_ask.ask_ollama("a prompt")

    assert sent["format"] == SCHEMA
    assert sent["options"]["temperature"] > 0
    assert "seed" not in sent["options"]


def test_unusable_reply_raises_a_runtime_failure(monkeypatch):
    """A reply that escapes the schema raises for main to report, not a traceback."""
    monkeypatch.setattr(
        cli_ask.requests, "post", lambda url, json: _FakeResponse("not json at all")
    )
    with pytest.raises(errors.RuntimeFailure, match="the model returned an unusable"):
        cli_ask.ask_ollama("a prompt")


def test_unreachable_ollama_raises_readiness(monkeypatch):
    """A refused connection is a missing prerequisite, raised for main to report."""

    def refuse(url, json):
        """Fail the way requests does when nothing listens on the port."""
        raise requests.ConnectionError("refused")

    monkeypatch.setattr(cli_ask.requests, "post", refuse)
    with pytest.raises(errors.ReadinessError, match="cannot reach Ollama"):
        cli_ask.ask_ollama("a prompt")


def test_reply_is_parsed_into_a_list(monkeypatch):
    """The suggestions array comes back as a plain list of strings."""
    payload = json.dumps({"suggestions": ["one", "two"]})
    monkeypatch.setattr(
        cli_ask.requests, "post", lambda url, json: _FakeResponse(payload)
    )
    assert cli_ask.ask_ollama("a prompt") == ["one", "two"]


# ---------- constants ----------


def test_ollama_url_is_local():
    """The endpoint must be localhost -- no accidental cloud calls."""
    assert OLLAMA_URL.startswith("http://localhost")


def test_model_is_pinned():
    """A concrete model is named in the source."""
    assert MODEL
