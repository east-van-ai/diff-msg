# diff-msg CLI

## Grammar

`diff-msg ask PATH`.

The command word sits at `argv[1]` and its argument at `argv[2]`, and both
are read off those slots directly. Since Python 3.12 argparse back-fills a
trailing positional from a token appearing after any number of flags. That
makes `diff-msg ask --flag PATH` parse happily, and the accepted grammar
drifts away from the documented one. Reading the slots decides the shape
instead of inferring it. A second bare word after PATH is a stray, named by
diff-msg itself at exit 1 rather than left to argparse.

A bare word is a question, and documentation is the answer. Bare
`diff-msg` prints the module docstring and exits 0. Bare `diff-msg ask`
prints the ask documentation and exits 0. The token count alone decides
that. Once any other token is present the user asked for something
specific, and answering with help would hide the mistake, so a missing PATH
there is an error at exit 1.

Doing the work costs a command word. A bare invocation is harmless, and
shelling out to git and querying a model is asked for by name.

`ask` takes the directory to work in, and `diff-msg ask .` is the current
one. Git's answer depends on which repository it is standing in, so that
choice is stated on the command line rather than left ambient. A PATH that
is not a directory is a readiness failure: exit 1, and no usage line,
because the grammar was fine and what the run needed was not there. A
directory that is not a checkout is git's own message passed through.

## version

`diff-msg version` and `diff-msg --version` both print the installed
version and exit 0. The command word and the flag do the same thing,
because a reader arriving from either convention should not have to guess
which one this tool took.

Neither appears in the banner or the README. This is the one document
that explains them. A version number answers a question a first-time
reader does not have yet, and the banner has room for the one command that
does the work.

## No piped input

`diff-msg` reads nothing from stdin. Its input is git, in the directory it
was pointed at, and there is no second source. `ask PATH` already covers
working on a checkout you are not standing in, which is the reach a piped
diff would have bought.

Any run with piped stdin is therefore a usage error, exit 1, whatever the
command word. A diff sent down a pipe was sent to be read. Printing help at
exit 0 instead would drop it in silence and report success.

The usage line under that error is `version`'s after `version`, and `ask`'s
after anything else, a bare `diff-msg` included. `ask` is the only command
that reads input, so its line is the one that says where input goes.

Piped is decided by stdin's file type, never by `isatty()`. A pipe, a
redirect, and a socket carry content. A character device does not, and that
is where `isatty()` goes wrong: it is false for `/dev/null` too, which
cron, systemd, `nohup`, and CI hand a process. Deciding on `isatty()` alone
would make one command line answer two ways depending on how it was
launched, and a test for it would then pass or fail with the launch context
rather than with the code.

## No flags

`ask` takes no flags at all. PATH is the whole of its input.

The model is fixed in the source. The prompt is tuned to the model in front
of it, so a different model wants different wording, and that is a code
change rather than a setting. See DESIGN's Sampling section for which model
and why.

The base branch is fixed too. `ask` diffs against `main`, and a checkout
that calls its trunk something else is not covered yet.

## Exit codes

- `0`: success. Suggestions printed, "no changes" reported, or
        documentation printed.
- `1`: every error diff-msg raises itself: usage errors, a PATH that is not
        a directory, a git failure, and an unreachable Ollama.
- `2`: argparse's own errors (unknown command, unknown flag), argparse's
        convention, left untouched.

All self-raised errors go to stderr as `diff-msg: <message>`. Usage errors
additionally print the usage line of the command that failed, so a stray
after `version` shows `version`'s grammar rather than `ask`'s. Readiness
failures print no usage line.

A git failure carries git's own message behind that prefix. DESIGN's Git
Failures section has the reasoning.

## What ask prints

Five numbered suggestions on stdout, and nothing else:

```text
1. Simplify the conversion logic and remove the comments that no longer apply
2. Rewrite the converter to drop the intermediate representation entirely
3. Collapse the three conversion branches into a single code path
4. Tidy the converter and bring its comments back in line with the code
5. Remove the stale conversion comments and shorten the surrounding logic
```

One line each, between 60 and 120 characters, all guaranteed by the schema
the request carries. See DESIGN's Enforced Shape section. No prefix and no
scope, since a suggestion is a plain sentence. Casing is not enforced,
though the prompt's imperative examples tend to draw a capital.

A body is not part of this shape. The whole reply is titles.

The set changes on every run, deliberately. Asking twice about the same
diff gives two different sets.

Two cases print something else, and both exit 0. An empty diff prints "No
changes vs main. Nothing to commit." without ever contacting the model. A
detached HEAD has no branch name, and the diff carries the signal on its
own.

## Use of AI

Both the use of AI and its disclosure are deliberate. Code and
documentation in this project are written in collaboration with
Artificial Intelligence (AI). The division of labour: the AI explores,
challenges assumptions and edge cases, and drafts; the human
initiates, drafts the designs, explores alongside the AI, reviews
every change, and decides what gets committed.

---

**East Van AI** · AI for the rest of us! · Vancouver, BC, Canada

[github.com/east-van-ai](https://github.com/east-van-ai) · <east-van-ai@proton.me>

Copyright (c) 2026 Go Nakamaru
