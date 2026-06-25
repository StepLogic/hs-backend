"""skill mastery and difficulty

Revision ID: 004
Revises: 003
Create Date: 2026-06-25 20:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "004"
down_revision: Union[str, None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    difficulty_enum = sa.Enum("easy", "medium", "hard", name="difficulty")
    difficulty_enum.create(op.get_bind(), checkfirst=True)

    op.add_column(
        "questions",
        sa.Column("difficulty", difficulty_enum, nullable=False, server_default="medium"),
    )

    op.create_table(
        "skill_mastery",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("student_id", sa.String(), sa.ForeignKey("students.id"), nullable=False),
        sa.Column("subject", sa.Enum(
            "math", "english_language_arts", "science", "social_studies",
            "world_languages", "test_prep", "college_readiness",
            name="subject",
        ), nullable=False),
        sa.Column("skill", sa.String(), nullable=False),
        sa.Column("mastery_level", sa.Enum(
            "beginner", "developing", "proficient", "advanced",
            name="masterylevel",
        ), nullable=False),
        sa.Column("mastery_score", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("repetitions", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("easiness", sa.Float(), nullable=False, server_default="2.5"),
        sa.Column("interval_days", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("due_date", sa.Date(), nullable=False),
        sa.Column("last_practiced", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("student_id", "subject", "skill"),
    )

    op.create_table(
        "user_profiles",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("user_id", sa.String(), sa.ForeignKey("users.id"), nullable=False, unique=True),
        sa.Column("xp", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("level", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("streak_days", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_active", sa.Date(), nullable=True),
        sa.Column("badges", sa.JSON(), nullable=False, server_default="[]"),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("user_profiles")
    op.drop_table("skill_mastery")
    op.drop_column("questions", "difficulty")
    op.execute("DROP TYPE IF EXISTS difficulty")
