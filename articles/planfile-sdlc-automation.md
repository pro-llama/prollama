---
title: "Planfile — SDLC Automation with Sprint Strategy and Ticket Management"
slug: planfile-sdlc-automation
date: 2026-03-27
author: Tom Sapletta
categories: [wronai, tools, sdlc]
tags: [planfile, tickets, sprints, github, jira, ci-cd, automation]
excerpt: "Strategic project management platform with CI/CD integration, automated bug-fix loops, and multi-backend ticket sync to GitHub, Jira, and GitLab."
featured_image: planfile-workflow.png
status: publish
---

# Planfile — SDLC Automation with Sprint Strategy and Ticket Management

Managing development work across GitHub Issues, Jira boards, and CI/CD pipelines usually means context-switching between five different tools. Planfile unifies this into a single YAML-driven strategy file that generates tickets, tracks sprints, and automates the bug-fix lifecycle.

## What Planfile Does

You define a `strategy.yaml` describing your sprints, tasks, and quality gates. Planfile takes that file and pushes tickets to your preferred backend — GitHub Issues, Jira, GitLab, or a local store. It then tracks progress, runs automated CI/CD loops (test → ticket → fix → retest), and reports on sprint velocity.

The automated bug-fix loop is where it gets interesting: Planfile detects failing tests, generates detailed bug reports using LLMs, creates tickets, optionally auto-fixes the code, and re-runs tests. This loop continues until all tests pass or a configurable iteration limit is reached.

## Project Metrics

The codebase currently spans 56 modules with 395 functions. Cyclomatic complexity averages CC̄=4.1, with zero circular dependencies. The project supports Python 53 files, Shell 17, and JavaScript 3.

## Key Features

**Strategy-driven planning** — define sprints, tasks, and objectives in YAML. Quality gates let you set definition-of-done criteria like "coverage >= 80%".

**Multi-backend sync** — push and pull tickets from GitHub, Jira, GitLab, Linear, ClickUp, and Asana. Each backend has its own adapter and can be swapped without changing your workflow.

**CI/CD automation** — the `planfile auto loop` command runs the full test-fix-verify cycle with configurable iteration limits and LLM-powered bug reports.

**LLM integration** — AI-driven strategy generation, bug analysis, and auto-fix. Works with OpenAI, Anthropic, LiteLLM, and local models. Smart model routing via Proxym integration.

## Current Status

Planfile is published on PyPI (`pip install planfile`) and actively maintained. The CI/CD workflow on GitHub runs automated tests and includes an auto bug-fix loop.

The next phase focuses on implementing a standardized ticket format across all wronai tools, with a Python SDK, CLI, OpenAPI, and MCP server. This will let tools like code2llm and vallm create tickets directly from their analysis results.

## Getting Started

```bash
pip install planfile
planfile strategy generate ./my-project --sprints 3
planfile auto loop --strategy strategy.yaml --backend github
```

## Links

- **Repository**: [github.com/semcod/planfile](https://github.com/semcod/planfile)
- **PyPI**: [pypi.org/project/planfile](https://pypi.org/project/planfile/)
- **License**: Apache 2.0
- **Part of**: [wronai ecosystem](https://github.com/wronai)
