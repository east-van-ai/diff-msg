"""
# ==============================================
# East Van AI -- AI for the rest of us!
# https://github.com/east-van-ai
# contact: east-van-ai@proton.me
# ==============================================
#
# ~~~ ~~~ ~~~ ~~~ ~~~ diff-msg ~~~ ~~~ ~~~ ~~~ ~~~
#
# Generate one conventional commit title for the current branch by feeding
# `git diff main...` to a locally running Ollama model. No cloud calls, no
# API keys -- everything talks to localhost:11434, and your code never
# leaves the machine.
#
# Usage:
#    diff-msg [--ask]
#
#    --ask    Read the branch name and `git diff main...`, ask the local
#             model, print one commit title. Bare `diff-msg` prints this
#             help; generating a title is an explicit `diff-msg --ask`
#
# Requires: Ollama running locally with qwen2.5-coder:3b pulled
# (`ollama pull qwen2.5-coder:3b`).
#
# Exit codes:
#    0: success (title printed, or nothing to commit, or bare-on-TTY
#        printed help)
#    1: any diff-msg-raised error (usage, git failure, unreachable Ollama)
#    2: argparse's own errors
#
# License: MIT
# ==============================================
"""

import argparse
import subprocess
import sys

import requests

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "qwen2.5-coder:3b"

USAGE = "Usage: diff-msg [--ask]"


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
    """Send the prompt to the local Ollama model and return its reply.

    The request pins temperature 0.0 and seed 42 so the same diff always
    produces the same title. An unreachable Ollama is a diff-msg error
    (exit 1), not a requests traceback.
    """
    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0.0, "seed": 42},
            },
        )
    except requests.RequestException as e:
        print(f"diff-msg: cannot reach Ollama at {OLLAMA_URL}: {e}", file=sys.stderr)
        sys.exit(1)
    return response.json()["response"].strip()


def build_prompt(branch, diff):
    """Wrap the branch name and diff in the fixed commit-title prompt."""
    return f"""You are a git commit message writer.

Branch name : {branch}
Git diff    :
{diff}

Rules:
- Pick ONE prefix from: feat fix docs refactor test chore
- Write ONE commit title only. No body. No explanation.
- Max 100 characters including the prefix.
- Use Conventional Commit format without scope in parentheses
- Format: prefix: short description
- No code fences
- No code blocks
- Use lowercase after the colon.
- Do not wrap the output in triple backticks (```), under any circumstance.

Commit title:"""


def main():
    """Parse arguments, enforce the CLI grammar, and run the pipeline."""
    parser = argparse.ArgumentParser(
        prog="diff-msg",
        description="Generate a conventional commit title from your branch diff.",
    )
    parser.add_argument(
        "--ask",
        action="store_true",
        help="generate a commit title for the current branch diff",
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

    prompt = build_prompt(branch, diff)
    message = ask_ollama(prompt)

    print(message)


if __name__ == "__main__":
    main()
