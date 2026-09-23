"""
# ~~~ ~~~ ~~~ ~~~ ~~~ ~~~ ~~~ ~~~ diff-msg ask ~~~ ~~~ ~~~ ~~~ ~~~ ~~~ ~~~ ~~~
#
# https://github.com/east-van-ai/diff-msg
#
# Read the branch name and `git diff main...` in the checkout at PATH, ask
# the local model, and print five one-line commit-title suggestions.
#
# Usage:
#    diff-msg ask PATH
#
#    PATH   The git checkout to read. `.` is the current directory.
#
# Requires: Ollama running locally with tiny-aya-global pulled
# (`ollama pull hf.co/CohereLabs/tiny-aya-global-GGUF:Q4_K_M`).
"""

import json
import os
import subprocess

import requests

from diff_msg import errors

HELP = "Suggest five commit titles."
USAGE = "diff-msg ask PATH"
SLOTS = ("PATH",)

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "hf.co/CohereLabs/tiny-aya-global-GGUF:Q4_K_M"

# Hot, because the point is a different set of ideas each run.
TEMPERATURE = 0.8

SUGGESTION_COUNT = 5
MIN_LENGTH = 60
MAX_LENGTH = 120

# The output contract, enforced by Ollama rather than requested in prose.
SCHEMA = {
    "type": "object",
    "properties": {
        "suggestions": {
            "type": "array",
            "items": {
                "type": "string",
                "minLength": MIN_LENGTH,
                "maxLength": MAX_LENGTH,
            },
            "minItems": SUGGESTION_COUNT,
            "maxItems": SUGGESTION_COUNT,
        }
    },
    "required": ["suggestions"],
}

# The count and the absence of fences are the schema's job. Both ends of the
# length range appear here as well, since maxLength clips rather than
# shortens and minLength cannot be met by clipping at all.
RULES = f"""Rules:
- Write one line, between {MIN_LENGTH} and {MAX_LENGTH} characters.
- A full sentence naming what changed, not a label or a branch name.
- Start with a verb in the imperative: "Add", "Rename", "Collapse".
  Not "Adding", not "Addition of", not "Changes to".
- Each suggestion names the whole change, not one file within it.
- Make them genuinely different from each other, not rewordings."""


def run_git(args, cwd):
    """Run a git command in cwd and return its stdout, or raise if git failed.

    The return code decides, not the output: stdout alone cannot tell a
    failure from an empty result. The first line of git's own message is
    passed through, with its `fatal: ` stripped so only one prefix survives.
    """
    result = subprocess.run(
        ["git", *args], cwd=cwd, capture_output=True, text=True, check=False
    )
    if result.returncode != 0:
        stderr = result.stderr.strip()
        first_line = stderr.splitlines()[0] if stderr else ""
        message = first_line.removeprefix("fatal: ") or f"git {args[0]} failed"
        raise errors.ReadinessError(message)
    return result.stdout.strip()


def get_branch(cwd):
    """Return the current git branch name, empty on a detached HEAD."""
    return run_git(["branch", "--show-current"], cwd)


def get_diff(cwd):
    """Return the diff of the current branch against main."""
    return run_git(["diff", "main..."], cwd)


def ask_ollama(prompt):
    """Send the prompt to the local model and return the five suggestions.

    The request carries SCHEMA, so the reply is constrained to an array of
    five capped strings. No seed is sent, so the same diff gives a different
    set every run. An unreachable Ollama, or a reply that somehow escapes
    the schema, raises for main to report, not a traceback.
    """
    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": MODEL,
                "prompt": prompt,
                "stream": False,
                "format": SCHEMA,
                "options": {"temperature": TEMPERATURE},
            },
        )
    except requests.RequestException as e:
        raise errors.ReadinessError(f"cannot reach Ollama at {OLLAMA_URL}: {e}") from e

    try:
        return json.loads(response.json()["response"])["suggestions"]
    except (json.JSONDecodeError, KeyError, TypeError) as e:
        raise errors.RuntimeFailure(f"the model returned an unusable reply: {e}") from e


def build_prompt(branch, diff):
    """Wrap the branch name and diff in the five-suggestion prompt."""
    return f"""You are a git commit message writer.

Branch name : {branch}
Git diff    :
{diff}

{RULES}

Write {SUGGESTION_COUNT} alternative one-line names for this change."""


def format_suggestions(suggestions):
    """Number the suggestions for printing.

    Numbering happens here rather than in the prompt, because a model that
    cannot be relied on to count to five should not be asked to.
    """
    return "\n".join(f"{n}. {text}" for n, text in enumerate(suggestions, 1))


def run(path):
    """Print five suggestions for the checkout at path.

    A path that is not a directory is a readiness failure, reported with no
    usage line: the grammar was fine and the run's ground was not.
    """
    if not os.path.isdir(path):
        raise errors.ReadinessError(f"not a directory: {path}")

    branch = get_branch(path)
    diff = get_diff(path)

    if not diff:
        print("No changes vs main. Nothing to commit.")
        return

    print(format_suggestions(ask_ollama(build_prompt(branch, diff))))
