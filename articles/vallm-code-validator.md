---
title: "vallm — LLM-Generated Code Validator"
slug: vallm-code-validator
date: 2026-03-27
author: Tom Sapletta
categories: [wronai, tools, validation]
tags: [vallm, validation, tree-sitter, llm-as-judge, code-quality, pypi]
excerpt: "Four-tier validation pipeline for LLM-generated code: syntax checks, static analysis, semantic LLM-as-judge, and behavioral testing."
featured_image: vallm-pipeline.png
status: publish
---

# vallm — LLM-Generated Code Validator

LLMs generate code that looks correct but often isn't. Import paths that don't exist, functions called with wrong signatures, subtle logic bugs masked by confident-sounding comments. vallm catches these problems before they reach your codebase.

## Four-Tier Validation

The validation pipeline is ordered by speed and cost:

**Tier 1: Fast syntax checks.** Tree-sitter parsing across multiple languages. Catches broken syntax, unresolved imports, undefined references. Runs in milliseconds.

**Tier 2: Static analysis.** Cyclomatic complexity, fan-in/fan-out metrics, code smell detection. Identifies structural problems that syntax checking misses.

**Tier 3: Semantic LLM-as-judge.** Ollama-powered evaluation using deepeval patterns. An LLM reviews the generated code for logical correctness, API misuse, and adherence to project patterns. More expensive but catches subtle bugs.

**Tier 4: Sandboxed behavioral testing.** Actually runs the code in isolation to verify it does what it claims. The most thorough tier, used selectively for high-risk changes.

## Multi-Language Support

vallm uses tree-sitter for parsing, which means it handles Python, JavaScript, TypeScript, Go, Rust, and other languages from the same CLI. Language-specific rules (import resolution, type checking) are implemented as pluggable validators.

## Project Metrics

vallm is the most mature tool in the ecosystem: 56 files, 8,604 lines of code, 91 functions, 19 classes, CC̄=3.5. It's published on PyPI and has 12 working examples. The CLI supports batch validation with recursive directory scanning.

Known issues being addressed: `imports.py` (653 lines, god module) and `cli.py` (401 lines, max CC=42 in the `batch` function). Both are targets for the next refactoring sprint.

## Integration with wronai

In the wronai pipeline, vallm sits at the validation step: after llx selects a model and proxym routes a coding task, vallm validates the result before marking the ticket as done. If validation fails, a follow-up ticket is automatically created with the specific errors.

## Getting Started

```bash
pip install vallm
vallm validate ./generated_code.py
vallm batch ./src/ --recursive --json
```

## Links

- **Repository**: [github.com/semcod/vallm](https://github.com/semcod/vallm)
- **PyPI**: [pypi.org/project/vallm](https://pypi.org/project/vallm/)
- **License**: Apache 2.0
- **Part of**: [wronai ecosystem](https://github.com/wronai)
