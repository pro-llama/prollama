---
title: "devloop — Three Objects, One CLI, Zero Learning Curve"
slug: devloop-unified-toolchain
date: 2026-03-28
author: Tom Sapletta
categories: [devloop, ecosystem]
tags: [devloop, devtools, llm, mcp, docker, propact, progressive-algorithmization]
excerpt: "Project for code quality. Loop for cost optimization. Workflow for Markdown automation. All tools optional, everything composable."
featured_image: devloop-architecture.png
status: publish
---

# devloop — Three Objects, One CLI, Zero Learning Curve

Modern LLM-assisted development involves a dozen moving parts. Learning each tool separately is a barrier few developers want to cross. devloop wraps the entire semcod/wronai ecosystem into three Python objects and a CLI that works with whatever tools you have installed.

## Three Objects

**Project** — the code quality loop. Four methods: `analyze()`, `plan()`, `execute()`, `status()`. Runs code2llm for health diagnostics, vallm for validation, redup for duplication. Auto-generates tickets from analysis. Sends work to proxym for LLM routing. Tracks cost per ticket.

**Loop** — the progressive algorithmization engine. Five stages: `discover()`, `extract()`, `generate_rules()`, `route()`, `optimize()`. Collects LLM traces, finds repeating patterns, generates deterministic replacements, routes by confidence. The ratio of deterministic-to-LLM requests grows over time.

**Workflow** — the Propact Markdown executor. Parses `.md` files with embedded `propact:shell`, `propact:rest`, `propact:mcp`, `propact:llm` blocks. Executes them sequentially. Failed steps create tickets automatically. No YAML, no custom DSL — just Markdown.

## What's New vs. wronai

devloop expands the original wronai library with three major additions:

**Progressive algorithmization** — the `Loop` class implements the 5-stage pipeline that no other framework offers. Every LLM call through devloop feeds the trace collector. Over time, the system identifies patterns worth replacing with deterministic code.

**Propact workflow engine** — the `Workflow` class turns Markdown into executable pipelines. This aligns with the broader trend of Markdown as API (Cloudflare content negotiation, Fern, llms.txt). Propact is an original concept with no direct competitor.

**Planfile-aware proxy headers** — every request carries `X-Planfile-Ref` and `X-Workflow-Ref`. Proxym logs cost/model/latency per-ticket, building a cost ledger that connects LLM spending to actual work items.

## The CLI

```bash
devloop init ./my-app           # setup
devloop go                      # full pipeline
devloop status                  # dashboard with algo progress

devloop algo discover           # start collecting traces
devloop algo extract            # find patterns
devloop algo rules              # generate replacements
devloop algo report             # % deterministic, $ saved

devloop workflow run fix.md     # execute Markdown workflow
devloop ask "question"          # quick LLM query
devloop ticket add "Fix auth"   # manual ticket
```

## Graceful Degradation

Every tool is optional. devloop discovers what's installed and uses it:

- No proxym? `ask()` returns an error, but `analyze()` and `plan()` work fine.
- No code2llm? Health reports are empty, but tickets and workflows still work.
- No planfile? Tickets store locally in `.devloop/tickets.yaml`.

The `devloop tools` command shows exactly what's available and what's missing.

## Links

- **Repository**: [github.com/semcod/devloop](https://github.com/semcod/devloop)
- **License**: Apache 2.0
