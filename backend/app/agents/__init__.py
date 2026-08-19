# backend/app/agents/__init__.py

"""Multi-agent screening pipeline.

Public surface:

* `ScreeningState` - the typed state every node reads and writes.
* `run_pipeline` - execute the full graph over a state.
* `router` - the Gemini -> Groq -> Ollama fallback chain.

Persistence deliberately lives outside this package: nodes are pure functions of
the state, which is what makes each one independently testable and the whole
pipeline reproducible.
"""

from app.agents.graph import PIPELINE, Node, PipelineError, replace_node, run_pipeline
from app.agents.llm_router import AllProvidersFailed, LLMRouter, router
from app.agents.state import PIPELINE_VERSION, NodeOutcome, ScreeningState

__all__ = [
    "PIPELINE",
    "PIPELINE_VERSION",
    "AllProvidersFailed",
    "LLMRouter",
    "Node",
    "NodeOutcome",
    "PipelineError",
    "ScreeningState",
    "replace_node",
    "router",
    "run_pipeline",
]