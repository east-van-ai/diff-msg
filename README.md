# diffmsg

A lightweight CLI tool that generates conventional commit messages from `git diff` output using a local LLM.

## why

You commit `wip` like a normal person.
But squash merge deserves better.
Pipe your branch diff into `diffmsg` and get a clean conventional commit message, ready to paste.

## overview

`diffmsg` pipes your staged or branch diff into a locally running LLM via Ollama and returns a formatted commit title and message body. No internet required, no API keys.

## usage

```bash
git diff main.. | diffmsg
```

or just run it and let it call `git diff` itself:

```bash
diffmsg
```

example output:

```text
refactor(conversion): simplify logic and clean up comments

* remove dead code from conversion logic
* replace lengthy comment with concise bullet list
* apply bulkification logic to trigger
```

optionally specify a title style:

```bash
git diff main.. | diffmsg --style conventional  # default
git diff main.. | diffmsg --style simple
git diff main.. | diffmsg --style bracket
```

## requirements

- macOS
- [Ollama](https://ollama.com) running locally
- Python 3.x

## setup

```bash
brew install ollama
ollama pull qwen2.5-coder:3b
pip install diffmsg
```

## model

default: `qwen2.5-coder:3b` (Apache 2.0)
Smaller is better. Swap via config if needed.

## privacy

Runs ethically local. Your code never leaves your machine.
No API keys. No cloud. Nothing for your manager to worry about.

## license

MIT
