# diff-msg DESIGN

## Scope

One person develops this, on one machine. No CI, no support matrix, no
other users to break. That is a standing licence to take the simpler
path: the model is a constant in the source rather than a configuration
surface, the install path assumes a current pip, releases are internal,
and this file doubles as the bug tracker.

## Architecture

`diff-msg` requires Python 3.9 or newer and has one runtime dependency,
`requests`, for talking to the local Ollama HTTP API. Everything runs
against `localhost:11434`. No cloud calls, no API keys, and no code
leaves the machine.

The whole implementation is one module, `src/diff_msg/cli.py`: pure
functions with one job each, plus a `main()` that wires them into a
pipeline. Data is plain strings; the only state read is the git
repository in the current directory, and the only external service is
the local model.

The module carries no shebang. It is reached through the console script
or `python -m diff_msg.cli`, never by executing the file directly.

## Dependencies

`pyproject.toml` is the single source of truth. Runtime needs live in
`[project.dependencies]`. The tools for working on the code, `black`,
`pytest`, `pytest-cov`, and `ruff`, form a PEP 735 dependency group named
`dev`.

A group rather than an optional extra, because those tools are not a
feature of the package. An extra would publish them in the package
metadata, where a stranger could install them alongside the tool itself.

```bash
pip install -e . --group dev
```

`--group` landed in pip 25.1, so the dev install needs a pip at least
that new.

Ruff lints and black formats. Ruff has a formatter too, and the two
disagree, so only `ruff check` runs here. Ruff gets no configuration in
this project, because the pinned version is the rule set. That is what
the exact pin buys.

## File Tree

Trimmed view of the layout

```text
.
├── src/
│   └── diff_msg/
│       ├── __init__.py
│       └── cli.py
├── tests/
│   ├── conftest.py
│   ├── test_cli_integration.py
│   └── test_prompt.py
├── CHANGELOG.md
├── DESIGN.md
├── LICENSE
├── pyproject.toml
└── README.md
```

## CLI Grammar

`diff-msg [--ask]`.

Bare `diff-msg` on a TTY prints the module docstring (the usage banner)
and exits 0. Generating a commit title costs one explicit flag:
`diff-msg --ask`. That is the same posture as sibling project `docmap`,
where the harmless invocation is the default and the action that does
real work (here, shelling out to git and querying a model) is asked for
by name.

`diff-msg` takes no piped input yet. Reading a diff from stdin
(`git diff main.. | diff-msg`) is a documented future feature, not
current behaviour. Bare `diff-msg` with stdin attached to a pipe is
therefore a usage error (exit 1), not a help dump: printing help to
stdout in the middle of a pipeline would silently pollute it with exit
0, and an error is the honest signal that the piped grammar does not
exist yet.

Exit codes:

- `0`: success (a title was printed, "no changes" was reported, or
        bare-on-TTY printed help).
- `1`: every error diff-msg raises itself: usage errors, a git failure, and
        an unreachable Ollama.
- `2`: argparse's own errors (unknown flag), argparse's convention, left
        untouched.

All self-raised errors go to stderr as `diff-msg: <message>`; usage
errors additionally print the usage line.

## Determinism

The same diff should always produce the same title. The Ollama request
pins `temperature: 0.0` and `seed: 42`, and the model is fixed at
`qwen2.5-coder:3b`, small enough to run anywhere and deterministic
enough to trust in a script. There is no configuration surface yet;
changing the model means editing one constant.

## The Pipeline

`main()` runs: parse args -> grammar guards (bare invocation, stdin)
-> `get_branch` -> `get_diff` -> empty-diff early exit ->
`build_prompt` -> `ask_ollama` -> print one title.

- `run_git` runs one git command via `subprocess` and hands back its
    stdout. See Git Failures for what it does when git fails.
- `get_branch` and `get_diff` are thin wrappers over it, for
    `git branch --show-current` and `git diff main...`.
- `build_prompt` wraps the branch name and diff in a fixed prompt instructing
    the model to output exactly one conventional-commit-style title line.
- `ask_ollama` POSTs to the local `/api/generate` endpoint. An unreachable
    Ollama is reported as `diff-msg: cannot reach Ollama ...` on stderr
    (exit 1), not a `requests` traceback.

## Git Failures

Git is shelled out to twice, and either call can fail. There is no
repository, or no `main` branch to diff against.

The return code decides, not the output. Any non-zero exit from git is a
diff-msg error: exit 1, with the first line of git's own message passed
through behind the `diff-msg:` prefix. Git's `fatal:` is stripped first,
so only one prefix survives, and one line matches the rest of the output
discipline. Reading stdout alone cannot tell a failure from an empty
result, and a tool that claims success when it never ran is worse than
one that stops. Git already words each case well, so restating that
classification in Python would only let the two drift apart.

Two git outcomes are not failures, and both exit 0. An empty diff means
there is nothing to commit, so `--ask` says "No changes vs main." without
ever contacting the model. A detached HEAD has no branch name to print,
so the branch name is simply empty and the diff carries the signal on its
own.

## Output Shape

Exactly one commit title line on stdout:

```text
refactor: simplify conversion logic and clean up comments
```

Prefix from `feat fix docs refactor test chore`, lowercase after
the colon, 100 characters maximum, no body. The prompt enforces this;
nothing post-processes the model output yet (see Open Questions).

## Open Questions

- `--style` flag (`conventional` / `simple` / `bracket`)
- Piped input (`git diff main.. | diff-msg`)

```bash
git diff main.. | diff-msg --style conventional
git diff main.. | diff-msg --style simple
git diff main.. | diff-msg --style bracket
```

- Configurable model and base branch (`main` is hardcoded in
  `git diff main...`).
- Model output is trusted verbatim, with no validation that the reply is
  actually one line, one prefix, under 100 chars.
- `-t` / `-m` / `-tm` flags for title, body, or both
- `-v` verbose mode showing the full prompt
- A giant diff goes into the prompt whole. Nothing truncates it, so a
  large branch can overrun the model's context.

## Known Bugs

Confirmed defects, recorded here until fixed.

None currently open.

## Use of AI

Both the use of AI and its disclosure are deliberate. Code and
documentation in this project are written in collaboration with
Artificial Intelligence (AI). The division of labor: the AI explores,
challenges assumptions and edge cases, and drafts; the human
initiates, drafts the designs, explores alongside the AI, reviews
every change, and decides what gets committed.

---

**East Van AI** · AI for the rest of us! · Vancouver, BC, Canada

[github.com/east-van-ai](https://github.com/east-van-ai) · <east-van-ai@proton.me>

Copyright (c) 2026 Go Nakamaru
