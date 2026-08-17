# diff-msg

A lightweight CLI tool that reads your branch diff and suggests five
commit titles, using a local LLM.

## Why

Your editor already writes the small ones. Three lines changed, one
intent, and its suggestion is fine.

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

`diff-msg` pipes your branch diff into a locally running LLM via Ollama
and returns five one-line suggestions. Nothing is pinned, so every ask
gives you a fresh set. No internet required, no API keys.

## Usage

```bash
diff-msg --ask
```

`diff-msg` calls `git diff main...` itself and prints five suggestions.
Bare `diff-msg` prints the usage banner; the generation is an explicit
`--ask`.

example output:

```text
1. simplify the conversion logic and clean up the comments
2. rewrite conversion to drop the intermediate step
3. tidy the converter and its comments
4. collapse the conversion branches into one path
5. clean up conversion and remove stale comments
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
