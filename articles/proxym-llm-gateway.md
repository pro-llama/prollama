---
title: "Proxym — Intelligent Multi-Provider LLM Gateway"
slug: proxym-llm-gateway
date: 2026-03-27
author: Tom Sapletta
categories: [wronai, tools, llm]
tags: [proxym, llm, gateway, proxy, openai, anthropic, cost-optimization]
excerpt: "Local proxy connecting 10 providers, 15 models, and intelligent routing in one OpenAI-compatible API. Budget $20–60/month instead of $150+."
featured_image: proxym-architecture.png
status: publish
---

# Proxym — Intelligent Multi-Provider LLM Gateway

Modern AI-assisted development means juggling multiple LLM providers — Anthropic for architecture decisions, DeepSeek for bulk coding, Ollama for offline work. Each has its own API, pricing, and rate limits. Proxym solves this by acting as a single, local gateway.

## What Proxym Does

Proxym sits between your IDE and all LLM providers. You point your tools (Roo Code, Cline, Aider, Cursor) at `localhost:4000` and let Proxym figure out which model handles each request. It analyzes the complexity of your prompt and routes it to the cheapest model that can handle the task.

A typo fix goes to Cerebras Llama 70B at $0.27/M tokens. An architecture refactoring goes to Claude Opus 4.6 at $5/M tokens. You don't need to manually switch models — Proxym does it based on what you're actually asking.

## Key Features

**Content-based routing** picks the optimal model per-request. The system classifies tasks into five tiers (trivial, operational, standard, complex, deep) and maps each to the cheapest capable model.

**Delta context buffer** watches your `code2llm` output and sends only file diffs to the LLM, not the full context every time. This saves 60–80% on tokens — a request that costs $0.36 with full context drops to $0.015 with deltas.

**Budget enforcement** caps spending at daily and monthly limits. When your $3/day budget runs out, requests fall back to free or local models instead of failing.

**Fallback chains** handle provider outages gracefully. If Anthropic is rate-limited, Proxym automatically tries OpenAI, then DeepSeek, then local Ollama.

## Current Status

Proxym is functional and self-hosted. The dashboard UI has 16 tabs covering projects, tickets, tools, environments, users, and observability. SQLite persistence means all data survives restarts.

The project supports three deployment modes: local Python, Docker Compose, and NVIDIA Jetson Orin for edge deployments.

Integration with the broader wronai ecosystem is underway — Proxym will consume tickets from planfile and use llx for metric-driven model selection.

## Getting Started

```bash
pip install proxym
proxym serve
# Point your IDE at http://localhost:4000
```

## Links

- **Repository**: [github.com/wronai/proxym](https://github.com/wronai/proxym)
- **License**: Apache 2.0
- **Part of**: [wronai ecosystem](https://github.com/wronai)
