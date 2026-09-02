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
surface, the install path assumes a current pip, and releases are
internal.

One limit is worth stating here rather than leaving a reader to find it.
A diff that is mostly prose is outside what this can do. The model
follows the text it finds inside the diff instead of describing it, and
no prompt wording fixes that at the size of model this runs on.

## Architecture

`diff-msg` requires Python 3.9 or newer and has one runtime dependency,
`requests`, for talking to the local Ollama HTTP API. Everything runs
against `localhost:11434`. No cloud calls, no API keys, and no code
leaves the machine.

The implementation is three modules under `src/diff_msg/`. `args.py`
holds the command line's vocabulary, `cli_ask.py` holds the `ask` command
and the pipeline it runs, and `cli.py` is the entry point that reads the
command line and hands off. Pure functions with one job each, and data
that is plain strings. The only state read is the git repository `ask`
was pointed at, and the only external service is the local model.

The split keeps the entry point small. An entry point that also holds a
command's work grows without bound, and the command line is the part that
has to stay readable.

No module carries a shebang. They are reached through the console script
or `python -m diff_msg.cli`, never by executing a file directly.

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

## CLI Grammar

`diff-msg ask PATH`.

The command word sits at `argv[1]` and its argument at `argv[2]`, and both
are read off those slots directly. Since Python 3.12 argparse back-fills a
trailing positional from a token appearing after any number of flags.
That makes `diff-msg ask --flag PATH` parse happily, and the accepted
grammar drifts away from the documented one. Reading the slots decides the shape instead
of inferring it. A second bare word after PATH is a stray, named by
diff-msg itself at exit 1 rather than left to argparse.

A bare word is a question, and documentation is the answer. Bare
`diff-msg` prints the module docstring and exits 0. Bare `diff-msg ask`
prints the ask documentation and exits 0. The token count alone decides
that. Once any other token is present the user asked for something
specific, and answering with help would hide the mistake, so a missing
PATH there is an error at exit 1.

Doing the work costs a command word. A bare invocation is harmless, and
shelling out to git and querying a model is asked for by name.

`ask` takes the directory to work in, and `diff-msg ask .` is the current
one. Git's answer depends on which repository it is standing in, so that
choice is stated on the command line rather than left ambient. A PATH that
is not a directory is a readiness failure: exit 1, and no usage line,
because the grammar was fine and what the run needed was not there. A
directory that is not a checkout is git's own message passed through. See
Git Failures.

### No piped input

`diff-msg` reads nothing from stdin. Its input is git, in the directory it
was pointed at, and there is no second source. `ask PATH` already covers
working on a checkout you are not standing in, which is the reach a piped
diff would have bought.

Any run with piped stdin is therefore a usage error, exit 1, whatever the
command word. A diff sent down a pipe was sent to be read. Printing help
at exit 0 instead would drop it in silence and report success.

Piped is decided by stdin's file type, never by `isatty()`. A pipe, a
redirect, and a socket carry content. A character device does not, and
that is where `isatty()` goes wrong: it is false for `/dev/null` too,
which cron, systemd, `nohup`, and CI hand a process. Deciding on
`isatty()` alone would make one command line answer two ways depending on
how it was launched, and a test for it would then pass or fail with the
launch context rather than with the code.

Exit codes:

- `0`: success. Suggestions printed, "no changes" reported, or documentation
        printed.
- `1`: every error diff-msg raises itself: usage errors, a PATH that is
        not a directory, a git failure, and an unreachable Ollama.
- `2`: argparse's own errors (unknown command, unknown flag), argparse's
        convention, left untouched.

All self-raised errors go to stderr as `diff-msg: <message>`. Usage errors
additionally print the usage line. Readiness failures do not.

## Sampling

The same diff should produce a different set of suggestions on every run.
It follows from Role: a second opinion pinned to one answer is not a
second opinion.

The request sets `temperature: 0.8` and sends no seed, so Ollama picks its
own each time and the five titles move from run to run. The output is not
reproducible, and for this tool that is the point.

The model stays fixed at `tiny-aya-global`, Cohere's 3.35b, at Q4_K_M. A
3b model on an 8 GB machine answers in seconds, where an 8b model against a
large diff spends its time swapping. Comprehension is genuinely better at
8b, and it is still the wrong trade when a whole diff has to fit in memory
beside it. There is no configuration surface yet; changing the model means
editing one constant.

Several 3b models clear that bar, so the size class does not settle which
one. Cohere is Canadian, and a tool that runs entirely on the machine in
front of it may as well run a model from home. That is the reason.

What the swap gives up and gains is worth recording next to it. The code
model reads code better. Against that, on the branch both were asked about,
`tiny-aya-global` carried the repository's name correctly through all five
suggestions where the code model never named the project at all. A small
model can return an identifier subtly misspelled, close enough to read as
correct at a glance, and the suggestions here are read by someone who knows
the branch. A wrong name is the one error that survives that reading. One
branch is thin evidence, so this is an observation, not the deciding
argument.

The cost is voice. `tiny-aya-global` writes noun phrases by default,
"Refactoring the converter" where the log wants "Refactor the converter",
so the prompt now asks for the imperative.

## The Pipeline

`main()` runs: read the command slots -> grammar guards (bare word,
stdin, PATH) -> `get_branch` -> `get_diff` -> empty-diff early exit ->
`build_prompt` -> `ask_ollama` -> `format_suggestions` -> print.

- `run_git` runs one git command via `subprocess` and hands back its stdout.
  See Git Failures for what it does when git fails.
- `get_branch` and `get_diff` are thin wrappers over it, for
  `git branch --show-current` and `git diff main...`. Both run in the directory
  `ask` was given, handed to `subprocess` as its working directory.
- `build_prompt` wraps the branch name and diff in a fixed prompt asking the
  model for five one-line suggestions.
- `ask_ollama` POSTs to the local `/api/generate` endpoint and returns the five
  strings. An unreachable Ollama is reported as
  `diff-msg: cannot reach Ollama ...` on stderr (exit 1), not a `requests`
  traceback.
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
one file, each in the imperative mood. Those cannot be schema-enforced, and
they are the ones the model still gets wrong.

Mood is the borderline one, since it looks like form. A `pattern` could ban
the handful of openings a noun phrase tends to use, but only those, and a
model steered off "Refactoring" reaches for "Changes to" rather than for a
verb. Recognizing a verb is not something a regular expression does.
So the imperative is asked for, and nothing enforces it.

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
there is nothing to commit, so `ask` says "No changes vs main." without
ever contacting the model. A detached HEAD has no branch name to print,
so the branch name is simply empty and the diff carries the signal on its
own.

## Output Shape

Five numbered suggestions on stdout, and nothing else:

```text
1. Simplify the conversion logic and remove the comments that no longer apply
2. Rewrite the converter to drop the intermediate representation entirely
3. Collapse the three conversion branches into a single code path
4. Tidy the converter and bring its comments back in line with the code
5. Remove the stale conversion comments and shorten the surrounding logic
```

One line each, between 60 and 120 characters, all guaranteed by the schema.
See Enforced Shape. No prefix and no scope, since a suggestion is a plain
sentence. Casing is not enforced, though the prompt's imperative examples
tend to draw a capital.

A body is not part of this shape. The whole reply is titles.

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
