---
title: "devloop — Progressive Algorithmization for LLM-Assisted Development"
slug: devloop-ecosystem-overview
date: 2026-03-28
author: Tom Sapletta
categories: [devloop, ecosystem, strategy]
tags: [devloop, progressive-algorithmization, llm, devtools, mcp, propact, toon]
excerpt: "The only framework that automates the 5-stage path from 'LLM handles everything' to 'most traffic runs deterministically.' Seven tools, one loop."
featured_image: devloop-ecosystem.png
status: publish
---

# devloop — Progressive Algorithmization for LLM-Assisted Development

## The Problem Nobody Else Is Solving

LLM frameworks help you build things. None of them help you stop paying for the same LLM call over and over.

LangChain dominates by stars but frustrates with unstable APIs. DSPy takes an academic approach and goes from LLM to smaller LLM — not from LLM to algorithm. CrewAI lacks observability. AutoGen centers on chat-style agents. None of them answer the question every production team hits after month three: "We're spending $150/month on requests that a lookup table could handle. How do we fix that?"

devloop answers it with a 5-stage pipeline called **progressive algorithmization**: start with LLM for everything, collect traces, extract patterns, generate deterministic rules, route by confidence, optimize until most traffic runs without touching an LLM at all.

## The 5-Stage Loop

**Discovery** — LLM handles 100% of requests. Full trace monitoring captures every interaction: prompt hash, response, model, cost, latency. You're not optimizing yet — you're building the dataset.

**Pattern Extraction** — With enough traces, repeating patterns emerge. The `devloop algo extract` command groups by prompt similarity, ranks by frequency times cost. The top 10 patterns are your biggest savings opportunities.

**Rule Generation** — The "Rule Maker Pattern" — AI generates its own deterministic replacement. Decision trees, lookup tables, regex matchers, Python functions. Each rule is validated against historical data before activation.

**Hybrid Routing** — Confidence-based split. Known patterns hit deterministic handlers (microseconds, zero cost). Unknown or ambiguous requests go to the LLM. The ratio is tracked in real-time.

**Optimization** — Most traffic runs deterministically. The LLM handles edge cases and genuinely novel requests. Continuous monitoring detects when new patterns emerge (cycling back to Discovery) or when existing rules regress.

## Seven Tools, Clear Boundaries

**code2llm** generates structured analysis in `.toon` format — health diagnostics, architectural maps, refactoring queues. Token-efficient: 5-10K tokens instead of 120K for raw source.

**vallm** validates LLM-generated code through four tiers: syntax (tree-sitter), static analysis, semantic LLM-as-judge (Ollama), and sandboxed behavioral testing.

**reDUP** detects exact, fuzzy, and semantic duplications. Plans refactoring to eliminate them.

**llx** uses metrics from all three analysis tools to select the optimal LLM model per task. Higher complexity routes to stronger models.

**proxym** sits between IDE and LLM providers. Content-based routing, budget enforcement, fallback chains, delta context buffer (96% token savings). Ten providers, 15 models, one API endpoint.

**planfile** manages sprints, strategies, and tickets. Syncs bidirectionally with GitHub, Jira, and GitLab. Automated CI/CD loops.

**devloop** (this library) wraps everything into three objects — `Project`, `Loop`, `Workflow` — and a CLI that treats the whole stack as one tool.

## Propact: Markdown as Workflow

Propact treats Markdown files as executable workflows. Code blocks tagged `propact:shell`, `propact:rest`, `propact:mcp`, `propact:llm` are steps that devloop runs sequentially. Failed steps automatically create tickets. No YAML pipeline files, no custom DSLs — just Markdown your team already reads.

## Planfile-Aware Everything

Every LLM request carries structured metadata: `X-Planfile-Ref` (which ticket this request serves), `X-Workflow-Ref` (which Propact workflow triggered it), `X-Task-Tier` (complexity class). Proxym logs cost and latency per-ticket, building a cost ledger that tells you exactly what each piece of work cost in LLM tokens.

## Current State

| Tool | Maturity | LOC | CC̄ | PyPI |
|------|----------|-----|-----|------|
| **vallm** | Published | 8,604 | 3.5 | yes |
| **code2llm** | Active | 21,128 | 4.6 | planned |
| **reDUP** | Active | 8,772 | — | planned |
| **llx** | Active | 1,600 | 3.9 | yes |
| **planfile** | Active | ~15K | 4.1 | yes |
| **proxym** | Active | 68,692 | 4.6 | planned |
| **devloop** | New | ~2,500 | — | planned |

## Getting Started

```bash
pip install devloop[all]
devloop init ./my-project
devloop go                    # analyze → plan → execute → validate
devloop algo discover         # start collecting traces
```

## Links

- **Organization**: [github.com/semcod](https://github.com/semcod) / [github.com/wronai](https://github.com/wronai)
- **License**: Apache 2.0
- **Author**: Tom Sapletta, Gdańsk
