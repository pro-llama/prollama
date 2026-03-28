---
title: "code2llm — Static Analysis That Speaks LLM"
slug: code2llm-static-analysis
date: 2026-03-27
author: Tom Sapletta
categories: [wronai, tools, analysis]
tags: [code2llm, static-analysis, toon, complexity, refactoring, code-health]
excerpt: "Generates health diagnostics, architectural maps, and refactoring recommendations in .toon format — structured output designed for LLM consumption."
featured_image: code2llm-analysis.png
status: publish
---

# code2llm — Static Analysis That Speaks LLM

Traditional static analysis tools produce reports meant for humans. code2llm produces structured output meant for LLMs. The `.toon` format captures everything an AI assistant needs to understand your codebase: complexity metrics, module dependencies, god function detection, data flow graphs, and prioritized refactoring queues.

## What It Generates

A single command produces a comprehensive suite of analysis files:

**analysis.toon** — health diagnostics with critical issues and refactoring priorities. Identifies god modules (files that do too much), god functions (high cyclomatic complexity), coupling problems, and layer complexity.

**evolution.toon** — a prioritized refactoring queue. Lists the highest-impact changes first, with risk assessments and success criteria. This is the file you feed to an LLM when asking "what should I fix next?"

**map.toon** — structural overview of all modules, their imports, and public API signatures. Gives an LLM the architectural context it needs to make informed suggestions.

**flow.toon** — data flow analysis showing pipelines, function contracts (input/output types), and side effects. Essential for understanding how data moves through the system.

**context.md** — a ready-to-paste narrative summary for AI assistants, with architecture overview, entry points, patterns, and key classes.

## The .toon Format

TOON is a structured, token-efficient representation of AST-based analysis. It's designed to maximize information density within LLM context windows. Where a full source dump might consume 120K tokens, a .toon analysis captures the essential structure in 5-10K tokens.

## Project Metrics

code2llm itself spans 102 modules with 820 functions and 104 classes. It supports Python analysis with features including NLP-based intent matching, type inference, data flow graph extraction, code smell detection, and large repo splitting.

## Current Status

The project is actively maintained with continuous dogfooding — code2llm analyzes itself using its own output, and refactoring decisions are driven by the tool's diagnostics.

Current focus: article view generator for publishable health reports, HTML dashboard export, and integration with the planfile ticket system via `--planfile` flag.

## Getting Started

```bash
pip install code2llm
code2llm ./ -f all -o ./analysis
# analysis.toon, evolution.toon, map.toon, flow.toon, context.md
```

## Links

- **Repository**: [github.com/wronai/code2llm](https://github.com/wronai/code2llm)
- **License**: Apache 2.0
- **Part of**: [wronai ecosystem](https://github.com/wronai)
