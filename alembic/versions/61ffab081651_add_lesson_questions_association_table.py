"""add_lesson_questions_association_table

Revision ID: 61ffab081651
Revises: 2026_07_27_add_question_scope
Create Date: 2026-08-08 08:03:20.959651

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '61ffab081651'
down_revision: Union[str, Sequence[str], None] = '2026_07_27_add_question_scope'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'lesson_questions',
        sa.Column('lesson_id', sa.String, sa.ForeignKey('lessons.id', ondelete='CASCADE'), primary_key=True, nullable=False),
        sa.Column('question_id', sa.String, sa.ForeignKey('questions.id', ondelete='CASCADE'), primary_key=True, nullable=False),
    )
    op.create_index('ix_lesson_questions_lesson_id', 'lesson_questions', ['lesson_id'])
    op.create_index('ix_lesson_questions_question_id', 'lesson_questions', ['question_id'])

    # Migrate existing lesson_id relationships into the new table
    op.execute(
        """
        INSERT INTO lesson_questions (lesson_id, question_id)
        SELECT lesson_id, id FROM questions
        WHERE lesson_id IS NOT NULL
        """
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('ix_lesson_questions_question_id', table_name='lesson_questions')
    op.drop_index('ix_lesson_questions_lesson_id', table_name='lesson_questions')
    op.drop_table('lesson_questions')
