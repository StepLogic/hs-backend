"""add lesson_id, unit_id, course_id, is_full_test to questions

Revision ID: 2026_07_27_add_question_scope
Revises: a1b2c3d4e5f6
Create Date: 2026-07-27 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2026_07_27_add_question_scope'
down_revision = 'a1b2c3d4e5f6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('questions', sa.Column('lesson_id', sa.String(), nullable=True))
    op.add_column('questions', sa.Column('unit_id', sa.String(), nullable=True))
    op.add_column('questions', sa.Column('course_id', sa.String(), nullable=True))
    op.add_column('questions', sa.Column('is_full_test', sa.Boolean(), nullable=False, server_default='false'))

    op.create_foreign_key('fk_questions_lesson', 'questions', 'lessons', ['lesson_id'], ['id'])
    op.create_foreign_key('fk_questions_unit', 'questions', 'units', ['unit_id'], ['id'])
    op.create_foreign_key('fk_questions_course', 'questions', 'courses', ['course_id'], ['id'])


def downgrade() -> None:
    op.drop_constraint('fk_questions_course', 'questions', type_='foreignkey')
    op.drop_constraint('fk_questions_unit', 'questions', type_='foreignkey')
    op.drop_constraint('fk_questions_lesson', 'questions', type_='foreignkey')

    op.drop_column('questions', 'is_full_test')
    op.drop_column('questions', 'course_id')
    op.drop_column('questions', 'unit_id')
    op.drop_column('questions', 'lesson_id')
