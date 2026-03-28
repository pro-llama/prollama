"""Propact Workflow Engine — execute Markdown with embedded actions.

Propact treats Markdown as a workflow format. Code blocks tagged with
`propact:rest`, `propact:shell`, `propact:mcp` are executable steps.

Usage:
    from devloop.propact import Workflow

    wf = Workflow("./refactor-v1.md")
    wf.validate()       # check syntax
    wf.execute()         # run all steps
    wf.status()          # step-by-step progress

Workflow format:
    # Fix Imports

    First, analyze the module structure.

    ```propact:shell
    code2llm ./src -f toon --json
    ```

    Then call the fix endpoint:

    ```propact:rest
    POST http://localhost:4000/v1/chat/completions
    {"model": "balanced", "messages": [{"role": "user", "content": "Fix imports"}]}
    ```

    Finally, validate:

    ```propact:shell
    vallm batch ./src --recursive
    ```
"""

from __future__ import annotations

import json
import re
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional


@dataclass
class WorkflowStep:
    """Single executable step in a Propact workflow."""

    index: int
    type: str  # rest | shell | mcp | llm
    title: str = ""
    content: str = ""
    status: str = "pending"  # pending | running | done | failed | skipped
    result: str = ""
    elapsed_ms: float = 0.0
    cost_usd: float = 0.0

    def to_dict(self) -> dict:
        return {
            "index": self.index,
            "type": self.type,
            "title": self.title,
            "status": self.status,
            "elapsed_ms": self.elapsed_ms,
        }


@dataclass
class WorkflowResult:
    """Result of workflow execution."""

    workflow_path: str
    title: str
    steps_total: int = 0
    steps_done: int = 0
    steps_failed: int = 0
    total_elapsed_ms: float = 0.0
    total_cost_usd: float = 0.0
    steps: list[WorkflowStep] = field(default_factory=list)

    @property
    def success(self) -> bool:
        return self.steps_failed == 0 and self.steps_done == self.steps_total


STEP_PATTERN = re.compile(
    r"```propact:(rest|shell|mcp|llm)\s*\n(.*?)```",
    re.DOTALL,
)
HEADING_PATTERN = re.compile(r"^#+\s+(.+)$", re.MULTILINE)


class Workflow:
    """Parse and execute Propact Markdown workflows."""

    def __init__(self, path: str):
        self.path = Path(path)
        self._steps: list[WorkflowStep] = []
        self._title: str = ""
        self._parsed = False

    def parse(self) -> list[WorkflowStep]:
        """Parse Markdown into executable steps."""
        if not self.path.exists():
            raise FileNotFoundError(f"Workflow not found: {self.path}")

        content = self.path.read_text()

        # Extract title
        heading = HEADING_PATTERN.search(content)
        self._title = heading.group(1) if heading else self.path.stem

        # Extract steps
        self._steps = []
        last_heading = self._title
        for i, match in enumerate(STEP_PATTERN.finditer(content)):
            step_type = match.group(1)
            step_content = match.group(2).strip()

            # Find nearest preceding heading for step title
            before = content[: match.start()]
            headings = HEADING_PATTERN.findall(before)
            if headings:
                last_heading = headings[-1]

            self._steps.append(
                WorkflowStep(
                    index=i,
                    type=step_type,
                    title=last_heading,
                    content=step_content,
                )
            )

        self._parsed = True
        return self._steps

    def validate(self) -> list[str]:
        """Check workflow for errors without executing."""
        if not self._parsed:
            self.parse()

        errors = []
        for step in self._steps:
            if step.type == "rest":
                lines = step.content.strip().split("\n", 1)
                if not lines or not lines[0].strip():
                    errors.append(f"Step {step.index}: empty REST block")
                elif not any(lines[0].startswith(m) for m in ("GET", "POST", "PUT", "DELETE", "PATCH")):
                    errors.append(f"Step {step.index}: REST block must start with HTTP method")

            elif step.type == "shell":
                if not step.content.strip():
                    errors.append(f"Step {step.index}: empty shell block")

        return errors

    def execute(
        self,
        *,
        dry_run: bool = False,
        stop_on_error: bool = True,
        proxy_url: str = "http://localhost:4000",
    ) -> WorkflowResult:
        """Execute all steps in the workflow."""
        if not self._parsed:
            self.parse()

        result = WorkflowResult(
            workflow_path=str(self.path),
            title=self._title,
            steps_total=len(self._steps),
        )

        for step in self._steps:
            if dry_run:
                step.status = "skipped"
                result.steps.append(step)
                continue

            step.status = "running"
            start = time.time()

            try:
                if step.type == "shell":
                    step = self._exec_shell(step)
                elif step.type == "rest":
                    step = self._exec_rest(step, proxy_url)
                elif step.type == "mcp":
                    step = self._exec_mcp(step, proxy_url)
                elif step.type == "llm":
                    step = self._exec_llm(step, proxy_url)
            except Exception as e:
                step.status = "failed"
                step.result = str(e)

            step.elapsed_ms = (time.time() - start) * 1000
            result.total_elapsed_ms += step.elapsed_ms
            result.total_cost_usd += step.cost_usd

            if step.status == "done":
                result.steps_done += 1
            elif step.status == "failed":
                result.steps_failed += 1
                if stop_on_error:
                    # Mark remaining as skipped
                    for remaining in self._steps[step.index + 1 :]:
                        remaining.status = "skipped"
                    break

            result.steps.append(step)

        result.steps = self._steps
        return result

    def status(self) -> dict:
        """Current workflow status."""
        return {
            "title": self._title,
            "path": str(self.path),
            "steps": [s.to_dict() for s in self._steps],
            "progress": f"{sum(1 for s in self._steps if s.status == 'done')}/{len(self._steps)}",
        }

    # ── Step executors ────────────────────────────────────

    def _exec_shell(self, step: WorkflowStep) -> WorkflowStep:
        """Execute a shell command."""
        proc = subprocess.run(
            step.content,
            shell=True,
            capture_output=True,
            text=True,
            timeout=300,
            cwd=str(self.path.parent),
        )
        step.result = proc.stdout + proc.stderr
        step.status = "done" if proc.returncode == 0 else "failed"
        return step

    def _exec_rest(self, step: WorkflowStep, proxy_url: str) -> WorkflowStep:
        """Execute a REST API call."""
        import httpx

        lines = step.content.strip().split("\n", 1)
        method_line = lines[0].strip()
        body = lines[1].strip() if len(lines) > 1 else ""

        parts = method_line.split(None, 1)
        method = parts[0].upper()
        url = parts[1] if len(parts) > 1 else ""

        # Replace relative URLs with proxy
        if url.startswith("/"):
            url = proxy_url + url

        with httpx.Client(timeout=120) as client:
            kwargs: dict[str, Any] = {}
            if body:
                try:
                    kwargs["json"] = json.loads(body)
                except json.JSONDecodeError:
                    kwargs["content"] = body

            resp = client.request(method, url, **kwargs)

        step.result = resp.text[:2000]
        step.status = "done" if resp.status_code < 400 else "failed"

        # Extract cost from proxym metadata
        try:
            data = resp.json()
            meta = data.get("_proxy", {})
            step.cost_usd = meta.get("cost_usd", 0.0)
        except Exception:
            pass

        return step

    def _exec_mcp(self, step: WorkflowStep, proxy_url: str) -> WorkflowStep:
        """Execute an MCP tool call."""
        try:
            data = json.loads(step.content)
            server = data.get("server", "")
            tool = data.get("tool", "")
            args = data.get("args", {})

            import httpx
            with httpx.Client(timeout=60) as client:
                resp = client.post(
                    f"{proxy_url}/mcp/self/tools/{tool}",
                    json=args,
                )
            step.result = resp.text[:2000]
            step.status = "done" if resp.status_code < 400 else "failed"
        except Exception as e:
            step.status = "failed"
            step.result = str(e)
        return step

    def _exec_llm(self, step: WorkflowStep, proxy_url: str) -> WorkflowStep:
        """Send prompt to LLM via proxym."""
        from devloop.tools.proxy import Proxy

        try:
            with Proxy() as proxy:
                resp = proxy.ask(step.content, context=True)
            step.result = resp.content[:2000]
            step.cost_usd = resp.cost_usd
            step.status = "done"
        except Exception as e:
            step.status = "failed"
            step.result = str(e)
        return step
