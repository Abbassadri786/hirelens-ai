"""screening operational indexes

Revision ID: 0005_screening_indexes
Revises: 0004_screening_operations
"""
from alembic import op

revision = "0005_screening_indexes"
down_revision = "0004_screening_operations"
branch_labels = None
depends_on = None

def upgrade():
    op.create_index(
        "ix_screening_results_org_score",
        "screening_results",
        ["organization_id", "overall_score"],
    )
    op.create_index(
        "ix_applications_org_submitted",
        "applications",
        ["organization_id", "submitted_at"],
    )

def downgrade():
    op.drop_index("ix_applications_org_submitted", table_name="applications")
    op.drop_index("ix_screening_results_org_score", table_name="screening_results")
