"""recruitment domain

Revision ID: 0002_recruitment_domain
Revises: 0001_initial
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0002_recruitment_domain"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


# ---------------------------------------------------------------------------
# PostgreSQL ENUM definitions
# ---------------------------------------------------------------------------

job_status_enum = postgresql.ENUM(
    "DRAFT",
    "PUBLISHED",
    "CLOSED",
    "ARCHIVED",
    name="job_status",
    create_type=False,
)

resume_file_type_enum = postgresql.ENUM(
    "PDF",
    "DOCX",
    name="resume_file_type",
    create_type=False,
)

resume_status_enum = postgresql.ENUM(
    "UPLOADED",
    "PARSED",
    "PARSE_FAILED",
    name="resume_status",
    create_type=False,
)

application_status_enum = postgresql.ENUM(
    "SUBMITTED",
    "UNDER_REVIEW",
    "SHORTLISTED",
    "REJECTED",
    "WITHDRAWN",
    name="application_status",
    create_type=False,
)


def upgrade():
    bind = op.get_bind()

    # -----------------------------------------------------------------------
    # Create PostgreSQL ENUM types exactly once.
    #
    # -----------------------------------------------------------------------

    postgresql.ENUM(
        "DRAFT",
        "PUBLISHED",
        "CLOSED",
        "ARCHIVED",
        name="job_status",
    ).create(bind, checkfirst=True)

    postgresql.ENUM(
        "PDF",
        "DOCX",
        name="resume_file_type",
    ).create(bind, checkfirst=True)

    postgresql.ENUM(
        "UPLOADED",
        "PARSED",
        "PARSE_FAILED",
        name="resume_status",
    ).create(bind, checkfirst=True)

    postgresql.ENUM(
        "SUBMITTED",
        "UNDER_REVIEW",
        "SHORTLISTED",
        "REJECTED",
        "WITHDRAWN",
        name="application_status",
    ).create(bind, checkfirst=True)

    # -----------------------------------------------------------------------
    # JOBS
    # -----------------------------------------------------------------------

    op.create_table(
        "jobs",

        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
        ),

        sa.Column(
            "organization_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),

        sa.Column(
            "created_by",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),

        sa.Column(
            "title",
            sa.String(180),
            nullable=False,
        ),

        sa.Column(
            "description",
            sa.Text(),
            nullable=False,
        ),

        sa.Column(
            "location",
            sa.String(180),
            nullable=True,
        ),

        sa.Column(
            "employment_type",
            sa.String(80),
            nullable=True,
        ),

        sa.Column(
            "status",
            job_status_enum,
            nullable=False,
        ),

        sa.Column(
            "min_experience_years",
            sa.Integer(),
            nullable=True,
        ),

        sa.Column(
            "is_public",
            sa.Boolean(),
            nullable=False,
        ),

        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),

        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),

        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            ondelete="CASCADE",
        ),

        sa.ForeignKeyConstraint(
            ["created_by"],
            ["users.id"],
            ondelete="RESTRICT",
        ),
    )

    op.create_index(
        "ix_jobs_organization_id",
        "jobs",
        ["organization_id"],
    )

    op.create_index(
        "ix_jobs_status",
        "jobs",
        ["status"],
    )

    # -----------------------------------------------------------------------
    # JOB REQUIREMENTS
    # -----------------------------------------------------------------------

    op.create_table(
        "job_requirements",

        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
        ),

        sa.Column(
            "job_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),

        sa.Column(
            "skill",
            sa.String(120),
            nullable=False,
        ),

        sa.Column(
            "is_required",
            sa.Boolean(),
            nullable=False,
        ),

        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),

        sa.ForeignKeyConstraint(
            ["job_id"],
            ["jobs.id"],
            ondelete="CASCADE",
        ),
    )

    op.create_index(
        "ix_job_requirements_job_id",
        "job_requirements",
        ["job_id"],
    )

    # -----------------------------------------------------------------------
    # CANDIDATES
    # -----------------------------------------------------------------------

    op.create_table(
        "candidates",

        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
        ),

        sa.Column(
            "organization_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),

        sa.Column(
            "full_name",
            sa.String(160),
            nullable=False,
        ),

        sa.Column(
            "email",
            sa.String(320),
            nullable=False,
        ),

        sa.Column(
            "phone",
            sa.String(40),
            nullable=True,
        ),

        sa.Column(
            "location",
            sa.String(180),
            nullable=True,
        ),

        sa.Column(
            "summary",
            sa.Text(),
            nullable=True,
        ),

        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),

        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),

        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            ondelete="CASCADE",
        ),
    )

    op.create_index(
        "ix_candidates_organization_id",
        "candidates",
        ["organization_id"],
    )

    op.create_index(
        "ix_candidates_email",
        "candidates",
        ["email"],
    )

    # -----------------------------------------------------------------------
    # RESUMES
    # -----------------------------------------------------------------------

    op.create_table(
        "resumes",

        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
        ),

        sa.Column(
            "organization_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),

        sa.Column(
            "candidate_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),

        sa.Column(
            "original_filename",
            sa.String(255),
            nullable=False,
        ),

        sa.Column(
            "stored_filename",
            sa.String(255),
            nullable=False,
        ),

        sa.Column(
            "file_type",
            resume_file_type_enum,
            nullable=False,
        ),

        sa.Column(
            "mime_type",
            sa.String(120),
            nullable=False,
        ),

        sa.Column(
            "file_size",
            sa.Integer(),
            nullable=False,
        ),

        sa.Column(
            "sha256",
            sa.String(64),
            nullable=False,
        ),

        sa.Column(
            "status",
            resume_status_enum,
            nullable=False,
        ),

        sa.Column(
            "extracted_text",
            sa.Text(),
            nullable=True,
        ),

        sa.Column(
            "parsed_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),

        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),

        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            ondelete="CASCADE",
        ),

        sa.ForeignKeyConstraint(
            ["candidate_id"],
            ["candidates.id"],
            ondelete="CASCADE",
        ),

        sa.UniqueConstraint(
            "stored_filename",
            name="uq_resumes_stored_filename",
        ),
    )

    op.create_index(
        "ix_resumes_organization_id",
        "resumes",
        ["organization_id"],
    )

    op.create_index(
        "ix_resumes_candidate_id",
        "resumes",
        ["candidate_id"],
    )

    op.create_index(
        "ix_resumes_sha256",
        "resumes",
        ["sha256"],
    )

    # -----------------------------------------------------------------------
    # APPLICATIONS
    # -----------------------------------------------------------------------

    op.create_table(
        "applications",

        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
        ),

        sa.Column(
            "organization_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),

        sa.Column(
            "job_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),

        sa.Column(
            "candidate_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),

        sa.Column(
            "resume_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),

        sa.Column(
            "cover_letter",
            sa.Text(),
            nullable=True,
        ),

        sa.Column(
            "status",
            application_status_enum,
            nullable=False,
        ),

        sa.Column(
            "submitted_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),

        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),

        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            ondelete="CASCADE",
        ),

        sa.ForeignKeyConstraint(
            ["job_id"],
            ["jobs.id"],
            ondelete="CASCADE",
        ),

        sa.ForeignKeyConstraint(
            ["candidate_id"],
            ["candidates.id"],
            ondelete="CASCADE",
        ),

        sa.ForeignKeyConstraint(
            ["resume_id"],
            ["resumes.id"],
            ondelete="RESTRICT",
        ),

        sa.UniqueConstraint(
            "job_id",
            "candidate_id",
            name="uq_job_candidate_application",
        ),
    )

    op.create_index(
        "ix_applications_organization_id",
        "applications",
        ["organization_id"],
    )

    op.create_index(
        "ix_applications_job_id",
        "applications",
        ["job_id"],
    )

    op.create_index(
        "ix_applications_candidate_id",
        "applications",
        ["candidate_id"],
    )

    op.create_index(
        "ix_applications_status",
        "applications",
        ["status"],
    )


def downgrade():
    # Drop tables first because they depend on the ENUM types.
    op.drop_table("applications")
    op.drop_table("resumes")
    op.drop_table("candidates")
    op.drop_table("job_requirements")
    op.drop_table("jobs")

    bind = op.get_bind()

    # Drop ENUM types after dependent tables are gone.
    postgresql.ENUM(
        "SUBMITTED",
        "UNDER_REVIEW",
        "SHORTLISTED",
        "REJECTED",
        "WITHDRAWN",
        name="application_status",
    ).drop(bind, checkfirst=True)

    postgresql.ENUM(
        "UPLOADED",
        "PARSED",
        "PARSE_FAILED",
        name="resume_status",
    ).drop(bind, checkfirst=True)

    postgresql.ENUM(
        "PDF",
        "DOCX",
        name="resume_file_type",
    ).drop(bind, checkfirst=True)

    postgresql.ENUM(
        "DRAFT",
        "PUBLISHED",
        "CLOSED",
        "ARCHIVED",
        name="job_status",
    ).drop(bind, checkfirst=True)