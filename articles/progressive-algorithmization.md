---
title: "Progressive Algorithmization — From LLM Calls to Deterministic Code"
slug: progressive-algorithmization
date: 2026-03-27
author: Tom Sapletta
categories: [wronai, strategy, llm]
tags: [progressive-algorithmization, llm, optimization, cost-reduction, dspy, deterministic, eu-funding]
excerpt: "Start with LLM for everything. Measure patterns. Replace hot paths with deterministic code. A 5-stage pipeline no existing framework automates."
featured_image: progressive-algorithmization-stages.png
status: publish
---

# Progressive Algorithmization — From LLM Calls to Deterministic Code

Every team using LLMs in production hits the same wall: costs grow linearly with usage, latency is unpredictable, and you're paying $3/M tokens for decisions a lookup table could make in microseconds.

The concept is simple: start with LLM for everything, then systematically replace predictable patterns with deterministic code. "Progressive algorithmization" describes this five-stage journey.

## The Five Stages

### Stage 1 — Discovery

LLM handles 100% of requests. This is intentional. You're not optimizing yet — you're collecting data. Full trace monitoring (Langfuse, Helicone) captures every request, response, and decision path. The goal is to understand what the LLM is actually doing with your traffic.

### Stage 2 — Pattern Extraction

With enough traces, patterns emerge. DSPy-style optimization compiles and tunes prompts automatically, shrinking model requirements. BootstrapFinetune distills behavior into smaller models. The critical output: identifying "hot paths" — requests that repeat with predictable inputs and outputs.

### Stage 3 — Rule Generation

This is where it gets interesting. The "Rule Maker Pattern" uses AI to generate its own replacement: deterministic rules, decision trees, lookup tables, OpenRewrite recipes. Each generated rule is validated against historical data before deployment. The AI literally writes the code that makes itself unnecessary for that pattern.

### Stage 4 — Hybrid Routing

Confidence-based routing splits traffic. Requests matching known patterns go to deterministic handlers (microseconds, zero cost). Uncertain requests still go to the LLM. The split is measurable — you can track exactly how much money and latency you're saving.

### Stage 5 — Optimization

Most traffic runs deterministically. The LLM handles only edge cases and genuinely novel requests. Continuous monitoring detects when new patterns emerge (back to Stage 1 for those) or when existing rules start regressing.

## Why Nobody Else Does This

The current LLM framework landscape is fragmented:

- **LangChain/LangGraph** (100K+ stars) dominates but frustrates with API instability
- **LlamaIndex** (38K+) is strong for RAG, limited beyond retrieval
- **DSPy** (20K+) goes from LLM to smaller LLM, not LLM to algorithm
- **CrewAI** (34.7K+) focuses on multi-agent roles, limited observability
- **AutoGen** (39K+) centers on chat-style agents

None of them automate the path from LLM to deterministic code. DSPy comes closest but stops at model-to-model distillation. Proxis.ai attempted it and pivoted. Logic Distillation remains purely academic. The five-stage pipeline described above has no commercial implementation.

## How wronai Implements It

The wronai ecosystem maps to these stages:

**Discovery**: proxym captures every LLM request with full cost/latency metadata. code2llm generates structured analysis of the codebase state.

**Pattern Extraction**: llx analyzes code metrics to classify request complexity. Repeated patterns (tier classification, model selection, routing decisions) become candidates for extraction.

**Rule Generation**: proxym's DSL parser handles known command patterns with zero LLM tokens. The `dsl.yaml` config file contains regex patterns that intercept requests before they reach any model.

**Hybrid Routing**: proxym's confidence-based router sends known patterns to deterministic handlers and novel requests to LLMs. The split is visible in the dashboard.

**Optimization**: vallm validates that deterministic replacements maintain quality. code2llm tracks complexity trends. planfile manages the iterative improvement cycle.

## The Market Opportunity

66% of developers report frustration with AI-generated code quality. LLM API spending doubles annually. Yet no commercial tool helps teams systematically reduce their LLM dependency for predictable workloads.

This positions the concept for EU deep-tech funding. Poland qualifies as a "widening country" with access to dedicated programs:

- **Space3ac / Poland Prize** (€65K, Gdańsk)
- **PARP Startup Booster** (PLN 400K)
- **EIC Pre-Accelerator** (€300-500K)
- **EIC Accelerator GenAI4EU Challenge** (€2.5M grant + up to €10M equity)
- **NCBR Seal of Excellence** (PLN 14M pool for high-scoring EIC applications)

The first public demonstrations are planned for InfoShare Gdańsk (May 2026) and Devoxx Poland (June 2026).

## Getting Started

```bash
pip install wronai[all]
wronai init ./my-project
wronai go  # full pipeline: analyze → plan → execute → validate
```

## Links

- **Organization**: [github.com/wronai](https://github.com/wronai) / [github.com/semcod](https://github.com/semcod)
- **License**: Apache 2.0
- **Author**: Tom Sapletta, Gdańsk
