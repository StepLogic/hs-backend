"""questions: record where a question sits in a full mock (module + position)

Revision ID: f3a4b5c6d7e8
Revises: e2f3a4b5c6d7
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "f3a4b5c6d7e8"
down_revision: Union[str, Sequence[str], None] = "e2f3a4b5c6d7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # app.migrations.run_safe_migrations() adds these at startup, so they may exist.
    existing = {c["name"] for c in sa.inspect(op.get_bind()).get_columns("questions")}
    with op.batch_alter_table("questions") as batch:
        if "mock_module" not in existing:
            batch.add_column(sa.Column("mock_module", sa.String(), nullable=True))
        if "mock_position" not in existing:
            batch.add_column(sa.Column("mock_position", sa.Integer(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("questions") as batch:
        batch.drop_column("mock_position")
        batch.drop_column("mock_module")
