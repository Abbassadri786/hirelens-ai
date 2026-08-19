"""screening fairness and provenance columns

Adds the columns that make a screening decision auditable: the flags raised by
the fairness node, and provenance for which semantic backend and pipeline
version produced the score.

Revision ID: 0006_screening_fairness
Revises: 0005_screening_indexes
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0006_screening_fairness"
down_revision = "0005_screening_indexes"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # server_default on each column so existing rows get a valid value without a
    # separate backfill step.
    op.add_column(
        "screening_results",
        sa.Column(
            "bias_flags",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
    )
    op.add_column(
        "screening_results",
        sa.Column(
            "bias_review_required",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )
    op.add_column(
        "screening_results",
        sa.Column(
            "semantic_backend",
            sa.String(40),
            nullable=False,
            server_default="lexical",
        ),
    )
    op.add_column(
        "screening_results",
        sa.Column(
            "pipeline_version",
            sa.String(20),
            nullable=False,
            server_default="1",
        ),
    )

    # 'Which decisions need a fairness review' is a dashboard query, so it gets
    # an index rather than a sequential scan over every result.
    op.create_index(
        "ix_screening_results_bias_review",
        "screening_results",
        ["organization_id", "bias_review_required"],
    )


def downgrade() -> None:
    op.drop_index("ix_screening_results_bias_review", table_name="screening_results")
    op.drop_column("screening_results", "pipeline_version")
    op.drop_column("screening_results", "semantic_backend")
    op.drop_column("screening_results", "bias_review_required")
    op.drop_column("screening_results", "bias_flags")