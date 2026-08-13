"""AI screening results

Revision ID: 0003_ai_screening
Revises: 0002_recruitment_domain
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0003_ai_screening"
down_revision = "0002_recruitment_domain"
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        "screening_results",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("application_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("overall_score", sa.Float(), nullable=False),
        sa.Column("keyword_score", sa.Float(), nullable=False),
        sa.Column("semantic_score", sa.Float(), nullable=False),
        sa.Column("experience_score", sa.Float(), nullable=False),
        sa.Column("completeness_score", sa.Float(), nullable=False),
        sa.Column("recommendation", sa.String(40), nullable=False),
        sa.Column("provider", sa.String(40), nullable=False),
        sa.Column("model_name", sa.String(120), nullable=False),
        sa.Column("matched_skills", postgresql.JSONB(), nullable=False),
        sa.Column("missing_required_skills", postgresql.JSONB(), nullable=False),
        sa.Column("matched_preferred_skills", postgresql.JSONB(), nullable=False),
        sa.Column("strengths", postgresql.JSONB(), nullable=False),
        sa.Column("concerns", postgresql.JSONB(), nullable=False),
        sa.Column("improvement_suggestions", postgresql.JSONB(), nullable=False),
        sa.Column("explanation", sa.Text(), nullable=False),
        sa.Column("resume_sections", postgresql.JSONB(), nullable=False),
        sa.Column("redacted_text", sa.Text(), nullable=True),
        sa.Column("processing_ms", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["application_id"], ["applications.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("application_id", name="uq_screening_results_application_id"),
    )
    op.create_index("ix_screening_results_organization_id", "screening_results", ["organization_id"])

def downgrade():
    op.drop_index("ix_screening_results_organization_id", table_name="screening_results")
    op.drop_table("screening_results")
