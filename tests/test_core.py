"""Tests for devloop — including algo loop and propact."""

import pytest
from pathlib import Path

from devloop.config import Config, ProxyConfig
from devloop.tools import discover_tools, TOOL_REGISTRY
from devloop.tools.tickets import Tickets
from devloop.tools.analysis import HealthReport
from devloop.algo import Loop, TraceEntry, Pattern
from devloop.propact import Workflow


class TestConfig:
    def test_default(self):
        cfg = Config()
        assert cfg.proxy.url == "http://localhost:4000"

    def test_env_override(self, monkeypatch):
        monkeypatch.setenv("PROXYM_URL", "http://custom:5000")
        cfg = ProxyConfig.from_env()
        assert cfg.url == "http://custom:5000"

    def test_save_load(self, tmp_path):
        cfg = Config()
        cfg.proxy.default_tier = "cheap"
        saved = cfg.save(str(tmp_path / "devloop.yaml"))
        assert saved.exists()


class TestToolDiscovery:
    def test_all_tools_registered(self):
        assert set(TOOL_REGISTRY.keys()) == {"proxym", "planfile", "llx", "code2llm", "vallm", "redup"}

    def test_discover(self):
        tools = discover_tools()
        for name, status in tools.items():
            assert hasattr(status, "installed")


class TestTickets:
    def test_add(self, tmp_path):
        t = Tickets(str(tmp_path))
        ticket = t.add("Fix bug", priority="high", type="bug")
        assert ticket.id == "DLP-0001"
        assert ticket.priority == "high"

    def test_from_analysis(self, tmp_path):
        t = Tickets(str(tmp_path))
        report = HealthReport(
            god_modules=["cli.py"],
            god_functions=["_dispatch"],
            dup_groups=3, dup_lines=500,
            vallm_pass_rate=0.75,
        )
        created = t.from_analysis(report)
        assert len(created) >= 4

    def test_persistence(self, tmp_path):
        Tickets(str(tmp_path)).add("Persist me", priority="critical")
        assert len(Tickets(str(tmp_path)).list()) == 1

    def test_board(self, tmp_path):
        t = Tickets(str(tmp_path))
        t.add("Open"); t.add("Done")
        t.update("DLP-0002", status="done")
        board = t.board()
        assert len(board["open"]) == 1
        assert len(board["done"]) == 1


class TestHealthReport:
    def test_grades(self):
        assert HealthReport(cc_avg=2.0, vallm_pass_rate=0.96).grade == "A"
        assert HealthReport(cc_avg=3.5, vallm_pass_rate=0.91).grade == "B"
        assert HealthReport(cc_avg=5.5, vallm_pass_rate=0.5).grade == "D"

    def test_passed(self):
        assert HealthReport(cc_avg=3.0, vallm_pass_rate=0.95).passed is True
        assert HealthReport(cc_avg=4.0, vallm_pass_rate=0.80).passed is False


class TestAlgoLoop:
    def test_init(self, tmp_path):
        loop = Loop(str(tmp_path))
        assert loop._state.stage == 0

    def test_discover(self, tmp_path):
        loop = Loop(str(tmp_path))
        loop.discover()
        assert loop._state.stage >= 1

    def test_add_trace(self, tmp_path):
        loop = Loop(str(tmp_path))
        entry = loop.add_trace("What is X?", "X is Y", model="haiku", cost_usd=0.001)
        assert entry.prompt_hash
        assert loop._state.total_requests == 1
        assert loop._state.llm_requests == 1

    def test_extract_patterns(self, tmp_path):
        loop = Loop(str(tmp_path))
        # Add same prompt 5 times → should form a pattern
        for _ in range(5):
            loop.add_trace("What is a for loop?", "A for loop iterates...", cost_usd=0.01)
        patterns = loop.extract(min_frequency=3)
        assert len(patterns) >= 1
        assert patterns[0].frequency == 5

    def test_report(self, tmp_path):
        loop = Loop(str(tmp_path))
        loop.add_trace("test", "reply", cost_usd=0.05)
        report = loop.report()
        assert report["total_requests"] == 1
        assert report["total_cost_usd"] == 0.05

    def test_persistence(self, tmp_path):
        loop1 = Loop(str(tmp_path))
        loop1.add_trace("test", "reply")
        loop1.discover()

        loop2 = Loop(str(tmp_path))
        assert loop2._state.stage >= 1
        assert loop2._state.total_requests == 1


class TestPropactWorkflow:
    def test_parse(self, tmp_path):
        wf_file = tmp_path / "test.md"
        wf_file.write_text("""# Test Workflow

## Step 1

```propact:shell
echo "hello"
```

## Step 2

```propact:rest
GET http://localhost:4000/health
```
""")
        wf = Workflow(str(wf_file))
        steps = wf.parse()
        assert len(steps) == 2
        assert steps[0].type == "shell"
        assert steps[1].type == "rest"

    def test_validate_good(self, tmp_path):
        wf_file = tmp_path / "good.md"
        wf_file.write_text("""# Good
```propact:shell
echo hi
```
```propact:rest
GET http://example.com
```
""")
        wf = Workflow(str(wf_file))
        errors = wf.validate()
        assert errors == []

    def test_validate_bad(self, tmp_path):
        wf_file = tmp_path / "bad.md"
        wf_file.write_text("""# Bad
```propact:rest

```
""")
        wf = Workflow(str(wf_file))
        errors = wf.validate()
        assert len(errors) > 0

    def test_execute_shell(self, tmp_path):
        wf_file = tmp_path / "shell.md"
        wf_file.write_text("""# Shell test
```propact:shell
echo "hello from propact"
```
""")
        wf = Workflow(str(wf_file))
        result = wf.execute()
        assert result.steps_done == 1
        assert result.success
        assert "hello from propact" in result.steps[0].result

    def test_dry_run(self, tmp_path):
        wf_file = tmp_path / "dry.md"
        wf_file.write_text("""# Dry
```propact:shell
rm -rf /
```
""")
        wf = Workflow(str(wf_file))
        result = wf.execute(dry_run=True)
        assert result.steps[0].status == "skipped"


class TestProject:
    def test_init(self, tmp_path):
        from devloop.project import Project
        p = Project(str(tmp_path))
        assert p.path == tmp_path

    def test_algo_accessible(self, tmp_path):
        from devloop.project import Project
        p = Project(str(tmp_path))
        assert isinstance(p.algo, Loop)

    def test_add_ticket(self, tmp_path):
        from devloop.project import Project
        p = Project(str(tmp_path))
        t = p.add_ticket("Test", priority="high")
        assert t.id == "DLP-0001"
