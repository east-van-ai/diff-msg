# diff-msg DESIGN

## Role

`diff-msg` is not the primary commit-message writer, and will not become
one. The message is written by hand. This tool is for the moment that
message will not come: it offers another suggestion, then another, until
one of them knocks the right phrasing loose.

That moment has a shape. It is the squash merge at the end of a branch
that touched twenty files over three days. Naming that is a problem of
summary, and it grows harder as the file count and the line count grow.
Editor autocomplete solves the opposite case, a handful of lines just
typed, one intent, with the whole editing session as context. Small
commits are well served already, and there is nothing to add to them here.

At that size there is also no single right answer. Which thread of a
branch counts as the headline is a judgement call, and it belongs to
whoever did the work. So the tool suggests, and never decides.

The rest of the design follows from that. Five suggestions rather than
one, because a single answer invites acceptance while a list invites
choosing. Fresh sampling on every run, because a tool asked for another
idea has to have one. No commit-format rules in the prompt, because the
output is raw material and shaping it into a commit is the reader's job.

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

## Sampling

The same diff should produce a different set of suggestions on every run.
It follows from Role: a second opinion pinned to one answer is not a
second opinion.

The request sets `temperature: 0.8` and sends no seed, so Ollama picks its
own each time and the five titles move from run to run. The output is not
reproducible, and for this tool that is the point.

The model stays fixed at `qwen2.5-coder:3b`. A 3b model on an 8 GB machine
answers in seconds, where an 8b model against a large diff spends its time
swapping. Comprehension is genuinely better at 8b, and it is still the
wrong trade when a whole diff has to fit in memory beside it. There is no
configuration surface yet; changing the model means editing one constant.

## The Pipeline

`main()` runs: parse args -> grammar guards (bare invocation, stdin)
-> `get_branch` -> `get_diff` -> empty-diff early exit ->
`build_prompt` -> `ask_ollama` -> `format_suggestions` -> print.

- `run_git` runs one git command via `subprocess` and hands back its
    stdout. See Git Failures for what it does when git fails.
- `get_branch` and `get_diff` are thin wrappers over it, for
    `git branch --show-current` and `git diff main...`.
- `build_prompt` wraps the branch name and diff in a fixed prompt asking the
    model for five one-line suggestions.
- `ask_ollama` POSTs to the local `/api/generate` endpoint and returns the
    five strings. An unreachable Ollama is reported as `diff-msg: cannot
    reach Ollama ...` on stderr (exit 1), not a `requests` traceback.
- `format_suggestions` numbers the list for printing.

## Enforced Shape

The request carries a JSON schema, so the reply is an object holding an
array of exactly five strings, each between 60 and 120 characters. Ollama
constrains generation to fit it.

That moves the output contract out of the prompt and into the request. A
rule written in prose is a request the model may decline, and it declined
often: replies arrived wrapped in code fences, prefaced with "Here are
five suggestions", closed with an offer of further assistance, or as one
commit message with a body instead of five lines. None of those are
expressible under the schema.

The numbering is done in Python, not asked for. A model that cannot be
relied on to count to five is not the right thing to ask for `1.` through
`5.`.

Length is pinned at both ends, 60 characters to 120, and both ends are
stated in the prompt as well as in the schema. A `maxLength` clips a long
line mid-word rather than shortening it, and a `minLength` cannot be
satisfied by clipping at all, so neither survives as a schema entry alone.
The schema is the backstop, not the instruction.

The floor exists because asking for brevity worked far too well. Told to
keep each suggestion "short, well under" the cap, the model answered at
half the budget, and sometimes collapsed into kebab-case slugs echoing the
branch name, `ls-sql-modularization` in place of a sentence. Inviting it to
use the room helped a little, and unreliably. A `minLength` ended the
argument, since nothing shorter can be generated. The squash merge this
tool is for describes a long branch, and a long branch rarely fits in five
words.

The prompt also carries the rules that shape *content* rather than form:
genuinely different suggestions, each naming the whole change rather than
one file. Those cannot be schema-enforced, and they are the ones the model
still gets wrong.

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

Five numbered suggestions on stdout, and nothing else:

```text
1. simplify the conversion logic and remove the comments that no longer apply
2. rewrite the converter to drop the intermediate representation entirely
3. collapse the three conversion branches into a single code path
4. tidy the converter and bring its comments back in line with the code
5. remove the stale conversion comments and shorten the surrounding logic
```

One line each, between 60 and 120 characters, all guaranteed by the schema.
See Enforced Shape. No prefix, no scope, and no particular casing, since a
suggestion is a plain sentence.

A body is not part of this shape. The whole reply is titles.

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
- A body suggestion, and the `-t` / `-m` / `-tm` flags for title, body, or
  both. Titles only for now.
- `-v` verbose mode showing the full prompt
- A giant diff goes into the prompt whole. Nothing truncates it, so a
  large branch can overrun the model's context.
- Choosing the input by the kind of change. Full diff content suits code,
  where the meaning is in the lines. File-level input (`git diff --numstat`,
  paths and line counts only) suits prose, where the meaning is in which
  files moved and by how much, and it carries no text for the model to
  mistake for instructions. Deciding automatically, by file extension or by
  diff size, is undesigned.

## Known Bugs

Confirmed defects, recorded here until fixed.

### A prose-heavy diff hijacks the model

A diff whose content reads as instructions gets followed instead of
described. The model stops naming the change and starts answering the text
it found inside it.

Reproduced on a documentation branch whose diff edits a rules file: the
five suggestions came back as advice about em-dashes, because the diff
contained rules about em-dashes. Filenames get corrupted in the process,
`CLAUDE.md` arriving as `CLAIDE.md` and `CLAUS.md`, which is the dangerous
part. A wrong filename in a commit title looks right at a glance.

Delimiting the diff and instructing the model to treat it as data does not
fix it at 3b. It helps at 8b, which suggests the boundary is a capability
the small model lacks rather than a prompt that needs rewording.

This tool cannot describe its own repository, or any repository whose
diffs are mostly prose. File-level input sidesteps it entirely, since a
list of paths carries nothing to obey. See Open Questions.

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
