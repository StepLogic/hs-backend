"""questions.wrong_feedback, students.study_tip(+_at), test_results.source

Revision ID: b5c6d7e8f9a0
Revises: a4b5c6d7e8f9
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "b5c6d7e8f9a0"
down_revision: Union[str, Sequence[str], None] = "a4b5c6d7e8f9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("questions", sa.Column("wrong_feedback", sa.JSON(), nullable=True))
    op.add_column("students", sa.Column("study_tip", sa.Text(), nullable=True))
    op.add_column("students", sa.Column("study_tip_at", sa.DateTime(), nullable=True))
    op.add_column("test_results", sa.Column("source", sa.String(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("test_results") as batch:
        batch.drop_column("source")
    with op.batch_alter_table("students") as batch:
        batch.drop_column("study_tip_at")
        batch.drop_column("study_tip")
    with op.batch_alter_table("questions") as batch:
        batch.drop_column("wrong_feedback")
