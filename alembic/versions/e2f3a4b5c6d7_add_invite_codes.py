"""add invite codes: registration is gated on an admin-issued code

Revision ID: e2f3a4b5c6d7
Revises: d1e2f3a4b5c6
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "e2f3a4b5c6d7"
down_revision: Union[str, Sequence[str], None] = "d1e2f3a4b5c6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # app.migrations.run_safe_migrations() creates this at startup, so it may exist.
    if sa.inspect(op.get_bind()).has_table("invite_codes"):
        return
    op.create_table(
        "invite_codes",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("code", sa.String(), nullable=False, unique=True),
        sa.Column("note", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("used_at", sa.DateTime(), nullable=True),
        sa.Column("used_by_user_id", sa.String(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("invite_codes")
