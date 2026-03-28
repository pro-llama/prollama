"""devloop — Progressive algorithmization toolchain.

From LLM to deterministic code. From proxy to tickets. One loop.

    from devloop import Project, Loop, Workflow

    # Simple: 4 methods
    p = Project("./my-app")
    p.analyze()           # code2llm + vallm + redup
    p.plan()              # strategy → tickets
    p.execute()           # llx picks model, proxym routes
    p.status()            # health + tickets + budget + cost ledger

    # Progressive: extract patterns, replace LLM with rules
    loop = Loop("./my-app")
    loop.discover()       # LLM handles 100%, collect traces
    loop.extract()        # identify hot paths + patterns
    loop.generate_rules() # AI writes its own replacement
    loop.route()          # confidence-based: rules vs LLM
    loop.optimize()       # monitor, detect regressions

    # Workflow: Propact Markdown workflows
    wf = Workflow("./refactor-v1.md")
    wf.execute()          # run propact:rest, propact:shell blocks
    wf.status()           # step-by-step progress
"""

__version__ = "0.1.1"

from devloop.project import Project
from devloop.config import Config
from devloop.workflows.pipeline import Pipeline
from devloop.algo.loop import Loop
from devloop.propact.workflow import Workflow

__all__ = ["Project", "Config", "Pipeline", "Loop", "Workflow"]
