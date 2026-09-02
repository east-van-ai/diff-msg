# diff-msg

A lightweight CLI tool that reads your branch diff and suggests five
commit titles, using a local LLM.

## Why

Nobody calls a sommelier for a Tuesday sandwich. Your editor already
writes the small commits: three lines changed, one intent, and its
suggestion is fine.

Then the branch ends. Twenty files, three days, four half-related ideas,
and now it wants a single title. That is a harder question, and it gets
harder the bigger the branch grows. You commit `wip` like a normal person,
but the squash merge deserves better.

`diff-msg` will not write the message for you. At that size there is
rarely one right answer, and the call is yours to make. It hands you five
and lets you pick one, or disagree with all five and write your own.
Either way you are no longer staring at an empty line. Ask again and five
more turn up.

## Overview

`diff-msg` feeds your branch diff to a locally running LLM via Ollama
and returns five one-line suggestions. Nothing is pinned, so every ask
gives you a fresh set. No internet required, no API keys.

## Usage

```bash
diff-msg ask .
```

`diff-msg` calls `git diff main...` and prints five suggestions.
`ask` takes the checkout to read, and `.` is the one you are standing in.
Any other checkout works the same way. Bare `diff-msg` prints the usage
banner, and `diff-msg ask` explains the command.

example output:

```text
1. simplify the conversion logic and remove the comments that no longer apply
2. rewrite the converter to drop the intermediate representation entirely
3. collapse the three conversion branches into a single code path
4. tidy the converter and bring its comments back in line with the code
5. remove the stale conversion comments and shorten the surrounding logic
```

## Requirements

- [Ollama](https://ollama.com) running locally

## Setup

```bash
ollama pull qwen2.5-coder:3b
```

## Install

- Python 3.9 or newer
- pipx

```bash
pipx install "git+https://github.com/east-van-ai/diff-msg.git"
```

## Model

default: `qwen2.5-coder:3b` (Apache 2.0)

## Privacy

Runs entirely on your machine. Your code never leaves it.
No API keys. No cloud. Nothing for your manager to worry about.

## Use of AI

This project is built with Artificial Intelligence (AI), deliberately
and in the open. Code and documentation are written in collaboration
with remote and local AI; design decisions, code review, and final
judgement stay human.

---

**East Van AI** · AI for the rest of us! · Vancouver, BC, Canada

[github.com/east-van-ai](https://github.com/east-van-ai) · <east-van-ai@proton.me>

Copyright (c) 2026 Go Nakamaru
