"""curriculum hierarchy

Revision ID: 003
Revises: 002
Create Date: 2026-06-25 20:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    enrollment_status_enum = sa.Enum("active", "completed", "dropped", name="enrollmentstatus")
    enrollment_status_enum.create(op.get_bind(), checkfirst=True)

    lesson_progress_status_enum = sa.Enum("not_started", "in_progress", "completed", name="lessonprogressstatus")
    lesson_progress_status_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "units",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("course_id", sa.String(), sa.ForeignKey("courses.id"), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("slug", sa.String(), nullable=False),
        sa.Column("order_index", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("description", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "lessons",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("unit_id", sa.String(), sa.ForeignKey("units.id"), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("slug", sa.String(), nullable=False),
        sa.Column("order_index", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("duration_min", sa.Integer(), nullable=False, server_default="10"),
        sa.Column("skills", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("review_status", sa.Enum("draft", "in_review", "published", "rejected", name="reviewstatus"), nullable=False),
        sa.Column("prerequisite_lesson_id", sa.String(), sa.ForeignKey("lessons.id"), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "enrollments",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("student_id", sa.String(), sa.ForeignKey("students.id"), nullable=False),
        sa.Column("course_id", sa.String(), sa.ForeignKey("courses.id"), nullable=False),
        sa.Column("enrolled_at", sa.DateTime(), nullable=False),
        sa.Column("status", enrollment_status_enum, nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("student_id", "course_id"),
    )

    op.create_table(
        "lesson_progress",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("student_id", sa.String(), sa.ForeignKey("students.id"), nullable=False),
        sa.Column("lesson_id", sa.String(), sa.ForeignKey("lessons.id"), nullable=False),
        sa.Column("status", lesson_progress_status_enum, nullable=False),
        sa.Column("mastery_score", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_accessed", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("student_id", "lesson_id"),
    )


def downgrade() -> None:
    op.drop_table("lesson_progress")
    op.drop_table("enrollments")
    op.drop_table("lessons")
    op.drop_table("units")
    op.execute("DROP TYPE IF EXISTS lessonprogressstatus")
    op.execute("DROP TYPE IF EXISTS enrollmentstatus")
