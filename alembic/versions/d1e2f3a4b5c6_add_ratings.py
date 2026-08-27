"""add student ratings, drop the stored course rating

Revision ID: d1e2f3a4b5c6
Revises: c9d1e2f3a4b5
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "d1e2f3a4b5c6"
down_revision: Union[str, Sequence[str], None] = "c9d1e2f3a4b5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # app.migrations.run_safe_migrations() creates this at startup to keep the deploy
    # window safe, so this may legitimately already exist.
    if sa.inspect(op.get_bind()).has_table("ratings"):
        _drop_stored_course_rating()
        return

    op.create_table(
        "ratings",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("student_id", sa.String(), sa.ForeignKey("students.id", ondelete="CASCADE"), nullable=False),
        sa.Column("target_type", sa.String(length=10), nullable=False),
        sa.Column("target_id", sa.String(), nullable=False),
        sa.Column("stars", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("student_id", "target_type", "target_id", name="uq_rating_student_target"),
    )
    op.create_index("ix_ratings_target", "ratings", ["target_type", "target_id"])

    _drop_stored_course_rating()


def _drop_stored_course_rating() -> None:
    """These held hand-typed marketing numbers. Ratings are averaged from `ratings`
    now, so these columns are the only place a fake score could come back."""
    existing = {c["name"] for c in sa.inspect(op.get_bind()).get_columns("courses")}
    doomed = [c for c in ("rating", "review_count") if c in existing]
    if not doomed:
        return
    with op.batch_alter_table("courses") as batch:
        for column in doomed:
            batch.drop_column(column)


def downgrade() -> None:
    with op.batch_alter_table("courses") as batch:
        batch.add_column(sa.Column("rating", sa.Float(), nullable=False, server_default="0"))
        batch.add_column(sa.Column("review_count", sa.Integer(), nullable=False, server_default="0"))
    op.drop_index("ix_ratings_target", table_name="ratings")
    op.drop_table("ratings")
