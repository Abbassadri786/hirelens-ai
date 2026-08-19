"""Deterministic orchestration graph. Pipelines compose pure-function nodes
over a shared ScreeningState. 'scorer' is critical because callers expect an
explanation as well as the score; 'redaction' precedes everything that consumes
text, which is what makes the PII boundary structural.
"""

from __future__ import annotations

import logging
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Final

from app.agents.nodes import (
    bias_check_node,
    feedback_node,
    matcher_node,
    parser_node,
    redaction_node,
    scorer_node,
)
from app.agents.state import NodeOutcome, ScreeningState

logger = logging.getLogger(__name__)

NodeFn = Callable[[ScreeningState], ScreeningState]


class PipelineError(RuntimeError):
    """A critical node failed; the run produced no usable result."""


@dataclass(frozen=True, slots=True)
class Node:
    """One pipeline stage."""

    name: str
    run: NodeFn
    # When true, a failure aborts the run instead of being recorded and skipped.
    critical: bool
    # Optional predicate; when it returns False the node is skipped.
    should_run: Callable[[ScreeningState], bool] | None = None


def _has_text(state: ScreeningState) -> bool:
    """Text-dependent nodes are pointless on an empty resume."""
    return state.has_resume_text


# The graph. Order is the execution order; edges are implicit and linear.
PIPELINE: Final[tuple[Node, ...]] = (
    Node(parser_node.NODE_NAME, parser_node.run, critical=True),
    Node(redaction_node.NODE_NAME, redaction_node.run, critical=True),
    Node(
        matcher_node.NODE_NAME,
        matcher_node.run,
        critical=False,
        should_run=_has_text,
    ),
    Node(scorer_node.NODE_NAME, scorer_node.run, critical=True),
    Node(
        feedback_node.NODE_NAME,
        feedback_node.run,
        critical=False,
        should_run=_has_text,
    ),
    Node(bias_check_node.NODE_NAME, bias_check_node.run, critical=False),
)


def run_pipeline(
    state: ScreeningState,
    pipeline: tuple[Node, ...] = PIPELINE,
) -> ScreeningState:
    """Execute every node in order, returning the completed state.

    Raises 'PipelineError' when a critical node fails.
    """
    logger.debug(
        "Screening pipeline started for application %s", state.application_id
    )

    for node in pipeline:
        if node.should_run is not None and not node.should_run(state):
            state.record(
                NodeOutcome(
                    name=node.name,
                    succeeded=True,
                    duration_ms=0,
                    details="skipped: no resume text",
                )
            )
            continue

        started = time.perf_counter()
        try:
            state = node.run(state)
        except Exception as exc:
            duration_ms = int((time.perf_counter() - started) * 1000)
            state.record(
                NodeOutcome(
                    name=node.name,
                    succeeded=False,
                    duration_ms=duration_ms,
                    details=str(exc)[:500],
                )
            )
            if node.critical:
                logger.exception(
                    "Critical node %r failed; aborting run", node.name
                )
                raise PipelineError(
                    f"Screening failed in the {node.name} stage: {exc}"
                ) from exc

            logger.warning(
                "Advisory node %r failed; continuing with a reduced result",
                node.name,
                exc_info=True,
            )
            continue

        state.record(
            NodeOutcome(
                name=node.name,
                succeeded=True,
                duration_ms=int((time.perf_counter() - started) * 1000),
            )
        )

    if state.ats is None:
        # The scorer is critical, so reaching here means a contract was broken.
        raise PipelineError("Pipeline completed without producing a score")

    # A run that produced no explanation is not shippable -- the explanation is
    # the artefact a candidate is entitled to.
    if not state.explanation:
        state.explanation = (
            f"The screening score is {state.ats.overall_score:.1f}/100. "
            "It is a screening aid computed by deterministic rules, not a "
            "hiring decision."
        )

    logger.info(
        "Pipeline completed for %s in %dms (provider=%s)",
        state.application_id,
        state.total_duration_ms,
        state.provider,
    )
    return state


def replace_node(
    name: str, run: NodeFn, pipeline: tuple[Node, ...] = PIPELINE
) -> tuple[Node, ...]:
    """Return 'pipeline' with the named node's implementation swapped out.

    Keeps the node's critical/conditional classification intact, so a test can
    verify how the graph reacts to a specific stage failing without restating the
    rest of the graph.
    """
    return tuple(
        Node(node.name, run, node.critical, node.should_run)
        if node.name == name
        else node
        for node in pipeline
    )