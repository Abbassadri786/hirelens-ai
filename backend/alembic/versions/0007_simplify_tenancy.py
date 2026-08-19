"""simplify tenancy and drop the screening queue

Revision ID: 0007_simplify_tenancy
Revises: 0006_screening_fairness
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0007_simplify_tenancy"
down_revision = "0006_screening_fairness"
branch_labels = None
depends_on = None

ROLE_VALUES = (
    "ORGANIZATION_ADMIN",
    "RECRUITER",
    "HIRING_MANAGER",
    "CANDIDATE",
)


def upgrade() -> None:
    bind = op.get_bind()

    # ------------------------------------------------------------------
    # 1. Tenancy onto users
    # ------------------------------------------------------------------
    user_role = postgresql.ENUM(*ROLE_VALUES, name="user_role")
    user_role.create(bind, checkfirst=True)

    # Added nullable so existing rows can be backfilled before the constraint
    # is applied.
    op.add_column(
        "users",
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.add_column(
        "users",
        sa.Column(
            "role",
            postgresql.ENUM(*ROLE_VALUES, name="user_role", create_type=False),
            nullable=True,
        ),
    )

    # DISTINCT ON picks the earliest membership per user, matching the
    # behaviour the application used before this change.
    op.execute(
        """
        UPDATE users AS u
        SET organization_id = m.organization_id,
            role = m.role::text::user_role
        FROM (
            SELECT DISTINCT ON (user_id)
                user_id, organization_id, role
            FROM organization_members
            ORDER BY user_id, created_at ASC
        ) AS m
        WHERE u.id = m.user_id
        """
    )

    op.execute("DELETE FROM users WHERE organization_id IS NULL")

    op.alter_column("users", "organization_id", nullable=False)
    op.alter_column("users", "role", nullable=False)

    op.create_foreign_key(
        "fk_users_organization_id",
        "users",
        "organizations",
        ["organization_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_index("ix_users_organization_id", "users", ["organization_id"])

    # Superseded by users.organization_id / users.role.
    op.drop_table("organization_members")
    postgresql.ENUM(name="organization_role").drop(bind, checkfirst=True)

    # ------------------------------------------------------------------
    # 2. Screening queue
    # ------------------------------------------------------------------
    op.drop_table("screening_jobs")

    # ------------------------------------------------------------------
    # 3. Unused columns
    # ------------------------------------------------------------------
    op.drop_column("users", "is_verified")
    op.drop_column("audit_events", "request_id")


def downgrade() -> None:
    bind = op.get_bind()

    # ------------------------------------------------------------------
    # 3. Restore the dropped columns
    # ------------------------------------------------------------------
    op.add_column(
        "audit_events", sa.Column("request_id", sa.String(96), nullable=True)
    )
    op.add_column(
        "users",
        sa.Column(
            "is_verified", sa.Boolean(), nullable=False, server_default=sa.false()
        ),
    )

    # ------------------------------------------------------------------
    # 2. Recreate the screening queue
    # ------------------------------------------------------------------
    op.create_table(
        "screening_jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "organization_id", postgresql.UUID(as_uuid=True), nullable=False
        ),
        sa.Column("application_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("status", sa.String(24), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("available_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("locked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["organization_id"], ["organizations.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["application_id"], ["applications.id"], ondelete="CASCADE"
        ),
    )
    op.create_index(
        "ix_screening_jobs_org_status",
        "screening_jobs",
        ["organization_id", "status"],
    )
    op.create_index(
        "ix_screening_jobs_available_at",
        "screening_jobs",
        ["status", "available_at"],
    )

    # ------------------------------------------------------------------
    # 1. Recreate membership and move tenancy back
    # ------------------------------------------------------------------
    organization_role = postgresql.ENUM(
        *ROLE_VALUES, name="organization_role"
    )
    organization_role.create(bind, checkfirst=True)

    op.create_table(
        "organization_members",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "organization_id", postgresql.UUID(as_uuid=True), nullable=False
        ),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "role",
            postgresql.ENUM(
                *ROLE_VALUES, name="organization_role", create_type=False
            ),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["organization_id"], ["organizations.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], ondelete="CASCADE"
        ),
        sa.UniqueConstraint("organization_id", "user_id", name="uq_org_member"),
    )

    # Rebuild one membership per user from the columns being removed.
    op.execute(
        """
        INSERT INTO organization_members
            (id, organization_id, user_id, role, created_at)
        SELECT
            gen_random_uuid(),
            organization_id,
            user_id,
            role::text::organization_role,
            NOW()
        FROM users AS u
        WHERE u.organization_id IS NOT NULL
        """
    )

    op.drop_index("ix_users_organization_id", table_name="users")
    op.drop_constraint("fk_users_organization_id", "users", type_="foreignkey")
    op.drop_column("users", "role")
    op.drop_column("users", "organization_id")
    postgresql.ENUM(name="user_role").drop(bind, checkfirst=True)