"""initial schema with users

Revision ID: 001
Revises:
Create Date: 2026-06-25 19:40:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # enums
    role_enum = sa.Enum("student", "parent", "teacher", "admin", name="role")
    subject_enum = sa.Enum(
        "math", "english_language_arts", "science", "social_studies",
        "world_languages", "test_prep", "college_readiness",
        name="subject",
    )
    question_type_enum = sa.Enum("multiple-choice", "fill-in", "ordering", "matching", name="questiontype")
    mastery_level_enum = sa.Enum("beginner", "developing", "proficient", "advanced", name="masterylevel")

    role_enum.create(op.get_bind(), checkfirst=True)
    subject_enum.create(op.get_bind(), checkfirst=True)
    question_type_enum.create(op.get_bind(), checkfirst=True)
    mastery_level_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "users",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("password_hash", sa.String(), nullable=False),
        sa.Column("role", sa.Enum("student", "parent", "teacher", "admin", name="role"), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )

    op.create_table(
        "courses",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("subject", subject_enum, nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("short_title", sa.String(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("icon", sa.String(), nullable=False),
        sa.Column("color", sa.String(), nullable=False),
        sa.Column("price", sa.Float(), nullable=False),
        sa.Column("original_price", sa.Float(), nullable=True),
        sa.Column("skills", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("grade_range", sa.String(), nullable=False),
        sa.Column("lesson_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("student_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("rating", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("review_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("features", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("image_emoji", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "students",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("email", sa.String(), nullable=True),
        sa.Column("grade_level", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("owner_user_id", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(["owner_user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "questions",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("subject", subject_enum, nullable=False),
        sa.Column("grade_level", sa.Integer(), nullable=False),
        sa.Column("type", question_type_enum, nullable=False),
        sa.Column("prompt", sa.Text(), nullable=False),
        sa.Column("context", sa.Text(), nullable=True),
        sa.Column("options", sa.JSON(), nullable=True),
        sa.Column("pairs", sa.JSON(), nullable=True),
        sa.Column("items", sa.JSON(), nullable=True),
        sa.Column("correct_answer", sa.JSON(), nullable=False),
        sa.Column("skill", sa.String(), nullable=False),
        sa.Column("explanation", sa.Text(), nullable=False),
        sa.Column("hint", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "test_results",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("student_id", sa.String(), nullable=False),
        sa.Column("subject", subject_enum, nullable=False),
        sa.Column("score", sa.Integer(), nullable=False),
        sa.Column("grade_equivalent", sa.Integer(), nullable=False),
        sa.Column("percentile", sa.Integer(), nullable=False),
        sa.Column("correct_count", sa.Integer(), nullable=False),
        sa.Column("total_questions", sa.Integer(), nullable=False),
        sa.Column("skill_breakdown", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("mastery_level", mastery_level_enum, nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["student_id"], ["students.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "user_answers",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("test_result_id", sa.String(), nullable=False),
        sa.Column("question_id", sa.String(), nullable=False),
        sa.Column("answer", sa.JSON(), nullable=False),
        sa.Column("is_correct", sa.Boolean(), nullable=False),
        sa.Column("time_spent", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["test_result_id"], ["test_results.id"]),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("user_answers")
    op.drop_table("test_results")
    op.drop_table("questions")
    op.drop_table("students")
    op.drop_table("courses")
    op.drop_table("users")
    op.execute("DROP TYPE IF EXISTS role")
    op.execute("DROP TYPE IF EXISTS subject")
    op.execute("DROP TYPE IF EXISTS questiontype")
    op.execute("DROP TYPE IF EXISTS masterylevel")
