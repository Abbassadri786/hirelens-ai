"""Pipeline nodes.

Each module exposes `NODE_NAME` and a `run(state) -> state` function and does
exactly one thing. Nodes never construct their own inputs or persist anything;
the graph supplies the state and the service layer owns the transaction.
"""

from app.agents.nodes import (
    bias_check_node,
    feedback_node,
    matcher_node,
    parser_node,
    redaction_node,
    scorer_node,
)

__all__ = [
    "bias_check_node",
    "feedback_node",
    "matcher_node",
    "parser_node",
    "redaction_node",
    "scorer_node",
]