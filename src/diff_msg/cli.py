"""
# ==============================================
# East Van AI -- AI for the rest of us!
# https://github.com/east-van-ai
# contact: east-van-ai@proton.me
# ==============================================
#
# ~~~ ~~~ ~~~ ~~~ ~~~ diff-msg ~~~ ~~~ ~~~ ~~~ ~~~
#
# Suggest five commit titles for the current branch by feeding
# `git diff main...` to a locally running Ollama model. No cloud calls, no
# API keys -- everything talks to localhost:11434, and your code never
# leaves the machine.
#
# diff-msg does not write the commit message for you. It offers five
# suggestions, and five more every time it is asked again.
#
# Usage:
#    diff-msg [--ask]
#
#    --ask    Read the branch name and `git diff main...`, ask the local
#             model, print five suggestions. Bare `diff-msg` prints this
#             help; generating suggestions is an explicit `diff-msg --ask`
#
# Requires: Ollama running locally with qwen2.5-coder:3b pulled
# (`ollama pull qwen2.5-coder:3b`).
#
# Exit codes:
#    0: success (suggestions printed, or nothing to commit, or bare-on-TTY
#        printed help)
#    1: any diff-msg-raised error (usage, git failure, unreachable Ollama,
#        unusable reply)
#    2: argparse's own errors
#
# License: MIT
# ==============================================
"""

import argparse
import json
import subprocess
import sys

import requests

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "qwen2.5-coder:3b"

# Hot, because the point is a different set of ideas each run.
# See DESIGN.md, Sampling.
TEMPERATURE = 0.8

SUGGESTION_COUNT = 5
MIN_LENGTH = 60
MAX_LENGTH = 120

USAGE = "Usage: diff-msg [--ask]"

# The output contract, enforced by Ollama rather than requested in prose.
# See DESIGN.md, Enforced Shape.
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
# shortens and minLength cannot be met by clipping at all. See DESIGN.md,
# Enforced Shape.
RULES = f"""Rules:
- Write one line, between {MIN_LENGTH} and {MAX_LENGTH} characters.
- A full sentence naming what changed, not a label or a branch name.
- Each suggestion names the whole change, not one file within it.
- Make them genuinely different from each other, not rewordings."""


def run_git(args):
    """Run a git command and return its stdout, or exit 1 if git failed.

    The return code decides, not the output: stdout alone cannot tell a
    failure from an empty result. The first line of git's own message is
    passed through, with its `fatal: ` stripped so only one prefix survives.
    """
    result = subprocess.run(["git", *args], capture_output=True, text=True, check=False)
    if result.returncode != 0:
        stderr = result.stderr.strip()
        first_line = stderr.splitlines()[0] if stderr else ""
        message = first_line.removeprefix("fatal: ") or f"git {args[0]} failed"
        print(f"diff-msg: {message}", file=sys.stderr)
        sys.exit(1)
    return result.stdout.strip()


def get_branch():
    """Return the current git branch name, empty on a detached HEAD."""
    return run_git(["branch", "--show-current"])


def get_diff():
    """Return the diff of the current branch against main."""
    return run_git(["diff", "main..."])


def ask_ollama(prompt):
    """Send the prompt to the local model and return the five suggestions.

    The request carries SCHEMA, so the reply is constrained to an array of
    five capped strings. No seed is sent, so the same diff gives a different
    set every run. An unreachable Ollama, or a reply that somehow escapes
    the schema, is a diff-msg error (exit 1), not a traceback.
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
        print(f"diff-msg: cannot reach Ollama at {OLLAMA_URL}: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        return json.loads(response.json()["response"])["suggestions"]
    except (json.JSONDecodeError, KeyError, TypeError) as e:
        print(f"diff-msg: the model returned an unusable reply: {e}", file=sys.stderr)
        sys.exit(1)


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


def main():
    """Parse arguments, enforce the CLI grammar, and run the pipeline."""
    parser = argparse.ArgumentParser(
        prog="diff-msg",
        description="Suggest five commit titles from your branch diff.",
    )
    parser.add_argument(
        "--ask",
        action="store_true",
        help="suggest five commit titles for the current branch diff",
    )
    parser.parse_args()

    if len(sys.argv) == 1:

        # a human typed bare `diff-msg`
        if sys.stdin.isatty():
            print(__doc__, file=sys.stdout)
            sys.exit(0)

        # piped input, real usage error -- stdin piping is not built yet
        print(
            "diff-msg: missing --ask; diff-msg takes no piped input yet.",
            file=sys.stderr,
        )
        print(USAGE, file=sys.stderr)
        sys.exit(1)

    branch = get_branch()
    diff = get_diff()

    if not diff:
        print("No changes vs main. Nothing to commit.")
        sys.exit(0)

    suggestions = ask_ollama(build_prompt(branch, diff))

    print(format_suggestions(suggestions))


if __name__ == "__main__":
    main()
