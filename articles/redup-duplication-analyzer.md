---
title: "reDUP — Code Duplication Analyzer and Refactoring Planner"
slug: redup-duplication-analyzer
date: 2026-03-27
author: Tom Sapletta
categories: [wronai, tools, analysis]
tags: [redup, duplication, refactoring, codebert, semantic-similarity]
excerpt: "Detects exact, fuzzy, and semantic code duplications across your codebase. Plans refactoring to eliminate them with library-grade performance."
featured_image: redup-scan.png
status: publish
---

# reDUP — Code Duplication Analyzer

Duplication is the silent complexity multiplier. Every duplicated block means every future bug fix has to be applied in multiple places. reDUP finds these duplications — not just exact copies, but fuzzy matches and semantic equivalents — and generates refactoring plans to eliminate them.

## Three Detection Levels

**Exact duplicates.** Hash-based detection using xxhash for line-level and block-level matching. Fast enough for CI pipelines.

**Fuzzy duplicates.** Uses rapidfuzz for approximate string matching. Catches renamed variables, reordered statements, and minor variations that exact matching misses.

**Semantic duplicates** (planned). CodeBERT embeddings for detecting code blocks that do the same thing with completely different implementations. Two sorting functions using different algorithms would be flagged as semantic duplicates.

## Project Metrics

reDUP currently spans 52 files with 8,772 lines of code. The codebase has its own complexity challenges being addressed: scanner sprawl (4 scanners), pipeline sprawl (3 `analyze()` variants), 2 `HashCache` classes, and a god function `_apply_fuzzy_similarity` at CC=19.

## Performance Libraries

The project adopts high-performance libraries with optional-dependency patterns: xxhash for hashing, rapidfuzz for fuzzy matching, libcst for concrete syntax tree manipulation, pybloom-live for Bloom filter pre-screening, and sentence-transformers for embedding-based similarity. All are optional — base installs fall back to stdlib implementations.

## Integration with wronai

In the wronai pipeline, reDUP contributes duplication metrics that inform model selection (more duplication = more complex task = stronger model) and automatically generates tickets for the worst duplication groups.

## Getting Started

```bash
pip install redup
redup scan ./src/ --json
redup analyze ./src/ --fuzzy --threshold 0.85
```

## Links

- **Repository**: [github.com/semcod/redup](https://github.com/semcod/redup)
- **License**: Apache 2.0
- **Part of**: [wronai ecosystem](https://github.com/wronai)
