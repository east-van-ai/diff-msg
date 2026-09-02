"""
# ==============================================
# East Van AI -- AI for the rest of us!
# https://github.com/east-van-ai
# contact: east-van-ai@proton.me
# ==============================================
#
# ~~~ ~~~ ~~~ ~~~ ~~~ diff-msg ~~~ ~~~ ~~~ ~~~ ~~~
#
# Suggest five commit titles for a branch by feeding `git diff main...` to a
# locally running Ollama model. No cloud calls, no API keys -- everything
# talks to localhost:11434, and your code never leaves the machine.
#
# diff-msg does not write the commit message for you. It offers five
# suggestions, and five more every time it is asked again.
#
# Usage:
#    ASK
#       diff-msg ask PATH   Suggest five commit titles for the checkout
#                           at PATH. `.` is the current directory
#       diff-msg ask        Explain the ask command
#
#    diff-msg               Print this help
#
# diff-msg reads no piped input. PATH says which repository to read.
#
# Requires: Ollama running locally with qwen2.5-coder:3b pulled
# (`ollama pull qwen2.5-coder:3b`).
#
# Exit codes:
#    0: success (suggestions printed, nothing to commit, or documentation
#        printed)
#    1: any diff-msg-raised error (usage, a PATH that is not a directory, a
#        git failure, unreachable Ollama, unusable reply)
#    2: argparse's own errors
#
# License: MIT
# ==============================================
"""

import os
import stat
import sys

from . import args, cli_ask

USAGE = "Usage: diff-msg ask PATH"


def leading_paths(tokens):
    """Return the tokens ahead of the first flag."""
    paths = []
    for token in tokens:
        if token.startswith("-"):
            break
        paths.append(token)
    return paths


def piped_stdin():
    """Return True when stdin carries content the user sent.

    Deliberately narrower than `not isatty()`, which is also false for the
    /dev/null that cron, nohup, and CI hand a process. See DESIGN.md, No
    piped input.
    """
    if sys.stdin is None:
        return False
    try:
        if sys.stdin.isatty():
            return False
        mode = os.fstat(sys.stdin.fileno()).st_mode
    except (AttributeError, OSError, ValueError):
        return False
    return stat.S_ISFIFO(mode) or stat.S_ISREG(mode) or stat.S_ISSOCK(mode)


def usage_error(message):
    """Report a command line the tool could not read, with its usage."""
    print(f"diff-msg: {message}", file=sys.stderr)
    print(USAGE, file=sys.stderr)
    return args.EXIT_ERROR


def main():
    """Read the command slots, enforce the grammar, and run the command."""
    if piped_stdin():
        return usage_error("diff-msg reads no piped input")

    if len(sys.argv) == 1:
        print(__doc__)
        return args.EXIT_OK

    command = sys.argv[1]
    paths = leading_paths(sys.argv[2:])

    # Strays are named here, ahead of the parser, so they stay diff-msg's own
    # error at exit 1 rather than argparse's "unrecognized arguments" at 2.
    if command == "ask" and len(paths) > 1:
        return usage_error(f"unexpected argument: {paths[1]}")
    if command == "version" and paths:
        return usage_error(f"version takes no arguments: {paths[0]}")

    # Rejects an unknown command or flag at exit 2, and answers --version on
    # the way past. What it resolved is discarded: the slots decide.
    args.build_parser().parse_args()

    if command == "version":
        print(args.version_line())
        return args.EXIT_OK

    # A command word and nothing else is a question, and its own docs answer.
    if len(sys.argv) == 2:
        print(cli_ask.__doc__)
        return args.EXIT_OK

    if not paths:
        return usage_error("ask needs a PATH")

    return cli_ask.run(paths[0])


if __name__ == "__main__":
    sys.exit(main())
