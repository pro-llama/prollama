# devloop Articles — WordPress-Ready Markdown

Each `.md` file has YAML front-matter for WordPress import.

## Publishing

```bash
for f in articles/*.md; do wp post create "$f" --post_status=draft; done
```

## Suggested Order

1. `devloop-ecosystem-overview.md` — context + architecture
2. `progressive-algorithmization.md` — unique value proposition
3. `proxym-llm-gateway.md` — most devs start here
4. `code2llm-static-analysis.md` — analysis foundation
5. `vallm-code-validator.md` — validation story
6. `llx-model-router.md` — metric-driven routing
7. `redup-duplication-analyzer.md` — duplication detection
8. `planfile-sdlc-automation.md` — project management layer
9. `devloop-unified-toolchain.md` — the glue library (last, links to all)
