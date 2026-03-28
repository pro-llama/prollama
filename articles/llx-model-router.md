---
title: "llx — Intelligent LLM Model Router Driven by Code Metrics"
slug: llx-model-router
date: 2026-03-27
author: Tom Sapletta
categories: [wronai, tools, llm]
tags: [llx, model-selection, mcp, code-metrics, routing]
excerpt: "Analyzes your codebase with code2llm, redup, and vallm, then selects the optimal LLM model based on actual project metrics — not abstract scores."
featured_image: llx-routing.png
status: publish
---

# llx — Intelligent LLM Model Router

When you use LLMs for coding, model selection matters. A simple refactoring task doesn't need Claude Opus at $15/M output tokens. A complex architecture decision shouldn't go to a free-tier model. llx automates this decision based on real metrics from your codebase.

## How It Works

llx runs the code2llm analysis pipeline on your project, collects metrics (file count, lines, cyclomatic complexity, fan-out, duplication groups, dependency cycles), and maps them to model tiers. Larger, more coupled, more complex projects get routed to stronger models.

The selection logic is transparent. A project with 50+ files, CC̄ above 6.0, and dependency cycles routes to premium (Claude Opus). A 5-file CLI with CC̄=3.0 routes to cheap (Haiku). A single script goes to free (Gemini).

## MCP Server

llx provides a complete MCP server exposing all wronai tools as endpoints. This means Claude Desktop, Claude Code, or any MCP-compatible agent can analyze projects, select models, and execute tasks through llx.

Seven MCP tools are available: `llx_analyze`, `llx_select`, `llx_chat`, `code2llm_analyze`, `redup_scan`, `vallm_validate`, and `llx_proxy_status`. Each wraps the corresponding CLI tool with proper input schemas.

## Successor to preLLM

llx is the modular rewrite of preLLM. Where preLLM had three god modules (cli.py at 999 lines, core.py at 893, trace.py at 509), llx splits into 12 modules, none exceeding 350 lines, with max CC at 10. The total codebase is about 1,600 lines.

## Current Status

llx is at v0.1.7 with MCP server, refactored high-CC functions, and enhanced test coverage. The active sprint (sprint 4) focuses on fixing 49 import errors, merging duplicate strategy code, and removing legacy preLLM modules to bring CC̄ from 3.9 to 3.5.

## Getting Started

```bash
pip install llx
llx analyze ./my-project
llx select . --task refactor
llx chat . --prompt "Refactor the god modules"
```

## Links

- **Repository**: [github.com/wronai/llx](https://github.com/wronai/llx)
- **License**: Apache 2.0
- **Part of**: [wronai ecosystem](https://github.com/wronai)
