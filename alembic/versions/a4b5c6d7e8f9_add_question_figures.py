"""questions: the figure a question depends on (image + description, or a data table)

Revision ID: a4b5c6d7e8f9
Revises: f3a4b5c6d7e8
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "a4b5c6d7e8f9"
down_revision: Union[str, Sequence[str], None] = "f3a4b5c6d7e8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # app.migrations.run_safe_migrations() adds these at startup, so they may exist.
    existing = {c["name"] for c in sa.inspect(op.get_bind()).get_columns("questions")}
    with op.batch_alter_table("questions") as batch:
        if "image_url" not in existing:
            batch.add_column(sa.Column("image_url", sa.String(), nullable=True))
        if "image_alt" not in existing:
            batch.add_column(sa.Column("image_alt", sa.Text(), nullable=True))
        if "figure_table" not in existing:
            batch.add_column(sa.Column("figure_table", sa.JSON(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("questions") as batch:
        batch.drop_column("figure_table")
        batch.drop_column("image_alt")
        batch.drop_column("image_url")
