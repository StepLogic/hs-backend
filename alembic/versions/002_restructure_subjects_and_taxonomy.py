"""restructure subjects and taxonomy

Revision ID: 002
Revises: 001
Create Date: 2026-06-25 19:50:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Data migration: reading/comprehension -> english_language_arts
    op.execute("UPDATE questions SET subject = 'english_language_arts' WHERE subject IN ('reading', 'comprehension')")
    op.execute("UPDATE courses SET subject = 'english_language_arts' WHERE subject IN ('reading', 'comprehension')")
    op.execute("UPDATE test_results SET subject = 'english_language_arts' WHERE subject IN ('reading', 'comprehension')")

    # Recreate subject enum with new values
    op.execute("ALTER TABLE questions ALTER COLUMN subject TYPE VARCHAR")
    op.execute("ALTER TABLE courses ALTER COLUMN subject TYPE VARCHAR")
    op.execute("ALTER TABLE test_results ALTER COLUMN subject TYPE VARCHAR")
    op.execute("DROP TYPE IF EXISTS subject")
    subject_enum = sa.Enum(
        "math", "english_language_arts", "science", "social_studies",
        "world_languages", "test_prep", "college_readiness",
        name="subject",
    )
    subject_enum.create(op.get_bind(), checkfirst=False)
    op.execute("ALTER TABLE questions ALTER COLUMN subject TYPE subject USING subject::subject")
    op.execute("ALTER TABLE courses ALTER COLUMN subject TYPE subject USING subject::subject")
    op.execute("ALTER TABLE test_results ALTER COLUMN subject TYPE subject USING subject::subject")

    # Create new enums
    course_type_enum = sa.Enum("core", "test_prep", "college_readiness", name="coursetype")
    course_type_enum.create(op.get_bind(), checkfirst=True)

    review_status_enum = sa.Enum("draft", "in_review", "published", "rejected", name="reviewstatus")
    review_status_enum.create(op.get_bind(), checkfirst=True)

    # Add columns
    op.add_column("courses", sa.Column("course_type", course_type_enum, nullable=False, server_default="core"))
    op.add_column("questions", sa.Column("review_status", review_status_enum, nullable=False, server_default="published"))

    # Create skill_taxonomy table
    op.create_table(
        "skill_taxonomy",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("subject", subject_enum, nullable=False),
        sa.Column("skill", sa.String(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("subject", "skill"),
    )


def downgrade() -> None:
    op.drop_table("skill_taxonomy")
    op.drop_column("questions", "review_status")
    op.drop_column("courses", "course_type")
    op.execute("DROP TYPE IF EXISTS reviewstatus")
    op.execute("DROP TYPE IF EXISTS coursetype")

    # Restore old subject enum
    op.execute("ALTER TABLE questions ALTER COLUMN subject TYPE VARCHAR")
    op.execute("ALTER TABLE courses ALTER COLUMN subject TYPE VARCHAR")
    op.execute("ALTER TABLE test_results ALTER COLUMN subject TYPE VARCHAR")
    op.execute("DROP TYPE IF EXISTS subject")
    old_subject_enum = sa.Enum("math", "reading", "comprehension", name="subject")
    old_subject_enum.create(op.get_bind(), checkfirst=False)
    op.execute("ALTER TABLE questions ALTER COLUMN subject TYPE subject USING subject::subject")
    op.execute("ALTER TABLE courses ALTER COLUMN subject TYPE subject USING subject::subject")
    op.execute("ALTER TABLE test_results ALTER COLUMN subject TYPE subject USING subject::subject")

    # Data migration back (english_language_arts -> reading — lossy)
    op.execute("UPDATE questions SET subject = 'reading' WHERE subject = 'english_language_arts'")
    op.execute("UPDATE courses SET subject = 'reading' WHERE subject = 'english_language_arts'")
    op.execute("UPDATE test_results SET subject = 'reading' WHERE subject = 'english_language_arts'")
