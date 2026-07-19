# diffmsg DESIGN

## Table of Contents

- L1: [diffmsg DESIGN](#diffmsg-design)
  - L3: [Table of Contents](#table-of-contents)
  - L17: [Architecture](#architecture)
  - L30: [File Tree](#file-tree)
  - L53: [CLI Grammar](#cli-grammar)
  - L84: [Determinism](#determinism)
  - L96: [The Pipeline](#the-pipeline)
  - L111: [Output Shape](#output-shape)
  - L123: [Open Questions](#open-questions)
  - L137: [Known Bugs](#known-bugs)
  - L144: [Use of AI](#use-of-ai)

## Architecture

`diffmsg` requires Python 3.9 or newer and has one runtime dependency,
`requests`, for talking to the local Ollama HTTP API. Everything runs
against `localhost:11434` -- no cloud calls, no API keys, and no code
leaves the machine.

The whole implementation is one module, `src/diffmsg/cli.py`: pure
functions with one job each, plus a `main()` that wires them into a
pipeline. Data is plain strings; the only state read is the git
repository in the current directory, and the only external service is
the local model.

## File Tree

Trimmed view of the layout

```text
.
├── src/
│   └── diffmsg/
│       ├── __init__.py
│       └── cli.py
├── tests/
│   ├── conftest.py
│   ├── test_cli_integration.py
│   └── test_prompt.py
├── CHANGELOG.md
├── CLAUDE.md
├── DESIGN.md
├── LICENSE
├── pyproject.toml
├── README.md
└── RELEASING.md
```

## CLI Grammar

`diffmsg [--ask]`.

Bare `diffmsg` on a TTY prints the module docstring (the usage banner)
and exits 0. Generating a commit title costs one explicit flag:
`diffmsg --ask` -- the same posture as sibling project `docmap`, where
the harmless invocation is the default and the action that does real
work (here, shelling out to git and querying a model) is asked for by
name.

`diffmsg` takes no piped input yet -- reading a diff from stdin
(`git diff main.. | diffmsg`) is a documented future feature, not
current behavior. Bare `diffmsg` with stdin attached to a pipe is
therefore a usage error (exit 1), not a help dump: printing help to
stdout in the middle of a pipeline would silently pollute it with exit
0, and an error is the honest signal that the piped grammar does not
exist yet.

Exit codes:

- `0` -- success (a title was printed, "no changes" was reported, or
  bare-on-TTY printed help).
- `1` -- every error diffmsg raises itself: usage errors and an
  unreachable Ollama.
- `2` -- argparse's own errors (unknown flag), argparse's convention,
  left untouched.

All self-raised errors go to stderr as `diffmsg: <message>`; usage
errors additionally print the usage line.

## Determinism

The same diff should always produce the same title. The Ollama request
pins `temperature: 0.0` and `seed: 42`, and the model is fixed at
`qwen2.5-coder:3b` -- small enough to run anywhere, deterministic
enough to trust in a script. There is no configuration surface yet;
changing the model means editing one constant.

An empty diff (`git diff main...` returns nothing) is the harmless
default: `--ask` reports "No changes vs main." and exits 0 without
ever contacting the model.

## The Pipeline

`main()` runs: parse args -> grammar guards (bare invocation, stdin)
-> `get_branch` -> `get_diff` -> empty-diff early exit ->
`build_prompt` -> `ask_ollama` -> print one title.

- `get_branch` / `get_diff` shell out to git (`git branch
  --show-current`, `git diff main...`) via `subprocess`.
- `build_prompt` wraps the branch name and diff in a fixed prompt
  instructing the model to output exactly one
  conventional-commit-style title line.
- `ask_ollama` POSTs to the local `/api/generate` endpoint. An
  unreachable Ollama is reported as `diffmsg: cannot reach Ollama ...`
  on stderr (exit 1), not a `requests` traceback.

## Output Shape

Exactly one commit title line on stdout:

```text
refactor: simplify conversion logic and clean up comments
```

Prefix from `feat fix docs refactor test chore style`, lowercase after
the colon, 100 characters maximum, no body. The prompt enforces this;
nothing post-processes the model output yet (see Open Questions).

## Open Questions

- `--style` flag (`conventional` / `simple` / `bracket`) -- README
  advertises it; not built.
- Piped input (`git diff main.. | diffmsg`) -- README advertises it;
  the grammar above reserves the pipe as an error until it exists.
- Configurable model and base branch (`main` is hardcoded in
  `git diff main...`).
- git failures (not a repo, no `main` branch) currently look like an
  empty diff and exit 0 as "no changes" -- honest error reporting
  would need to check the subprocess return code.
- Model output is trusted verbatim -- no validation that the reply is
  actually one line, one prefix, under 100 chars.

## Known Bugs

Confirmed defects, recorded here until fixed (this file is the bug
tracker -- a solo project doesn't need GitHub Issues).

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
