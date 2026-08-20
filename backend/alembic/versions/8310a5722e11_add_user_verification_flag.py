"""add user verification flag

Revision ID: 8310a5722e11
Revises: 0007_simplify_tenancy
Create Date: 2026-08-20 00:36:57.306724

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '8310a5722e11'
down_revision: Union[str, Sequence[str], None] = '0007_simplify_tenancy'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "is_verified",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )


def downgrade() -> None:
    op.drop_column("users", "is_verified")
