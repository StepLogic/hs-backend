"""add account profile fields

Revision ID: 7c3a91be04d2
Revises: 4114412c4a7f
Create Date: 2026-08-20 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "7c3a91be04d2"
down_revision: Union[str, Sequence[str], None] = "4114412c4a7f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Account identity + preferences live on the existing 1:1 user_profiles side-table.
    op.add_column("user_profiles", sa.Column("display_name", sa.String(length=80), nullable=True))
    op.add_column("user_profiles", sa.Column("bio", sa.Text(), nullable=True))
    op.add_column(
        "user_profiles",
        sa.Column("theme", sa.String(length=10), nullable=False, server_default="system"),
    )
    op.add_column(
        "user_profiles",
        sa.Column(
            "notify_weekly_email", sa.Boolean(), nullable=False, server_default=sa.true()
        ),
    )
    op.add_column(
        "user_profiles",
        sa.Column(
            "notify_practice_tips", sa.Boolean(), nullable=False, server_default=sa.false()
        ),
    )
    # Guardian is an address to notify, not an account. The email is the seam if
    # guardians ever need logins.
    op.add_column("students", sa.Column("guardian_name", sa.String(length=120), nullable=True))
    op.add_column("students", sa.Column("guardian_email", sa.String(length=255), nullable=True))


def downgrade() -> None:
    op.drop_column("students", "guardian_email")
    op.drop_column("students", "guardian_name")
    op.drop_column("user_profiles", "notify_practice_tips")
    op.drop_column("user_profiles", "notify_weekly_email")
    op.drop_column("user_profiles", "theme")
    op.drop_column("user_profiles", "bio")
    op.drop_column("user_profiles", "display_name")
