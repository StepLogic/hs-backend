"""add image url columns

Revision ID: 4114412c4a7f
Revises: 61ffab081651
Create Date: 2026-08-19 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "4114412c4a7f"
down_revision: Union[str, Sequence[str], None] = "61ffab081651"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("students", sa.Column("profile_image_url", sa.String(), nullable=True))
    op.add_column("courses", sa.Column("banner_image_url", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column("courses", "banner_image_url")
    op.drop_column("students", "profile_image_url")