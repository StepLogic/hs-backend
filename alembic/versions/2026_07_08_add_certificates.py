"""add certificate_enabled, certificate_passing_score to courses; create final_exams, final_exam_attempts, certificates

Revision ID: bbf5ee13b496
Revises: 005
Create Date: 2026-07-08 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'bbf5ee13b496'
down_revision = '005'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('courses', sa.Column('certificate_enabled', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('courses', sa.Column('certificate_passing_score', sa.Integer(), nullable=False, server_default='70'))

    op.create_table(
        'final_exams',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('course_id', sa.String(), nullable=False),
        sa.Column('prompt', sa.Text(), nullable=False),
        sa.Column('question_type', sa.Enum('multiple-choice', 'fill-in', 'ordering', 'matching', name='questiontype', create_type=False), nullable=False),
        sa.Column('options', sa.JSON(), nullable=True),
        sa.Column('correct_answer', sa.JSON(), nullable=False),
        sa.Column('skill', sa.String(), nullable=False),
        sa.Column('difficulty', sa.Enum('easy', 'medium', 'hard', name='difficulty', create_type=False), nullable=False, server_default='medium'),
        sa.Column('order_index', sa.Integer(), nullable=False, server_default='0'),
        sa.ForeignKeyConstraint(['course_id'], ['courses.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )

    op.create_table(
        'final_exam_attempts',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('student_id', sa.String(), nullable=False),
        sa.Column('course_id', sa.String(), nullable=False),
        sa.Column('score', sa.Integer(), nullable=False),
        sa.Column('passed', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['student_id'], ['students.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['course_id'], ['courses.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )

    op.create_table(
        'certificates',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('student_id', sa.String(), nullable=False),
        sa.Column('course_id', sa.String(), nullable=False),
        sa.Column('earned_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('final_score', sa.Integer(), nullable=False),
        sa.Column('status', sa.Enum('earned', 'revoked', name='certificatestatus'), nullable=False, server_default='earned'),
        sa.Column('certificate_hash', sa.String(), nullable=False),
        sa.ForeignKeyConstraint(['student_id'], ['students.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['course_id'], ['courses.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('student_id', 'course_id'),
    )


def downgrade() -> None:
    op.drop_table('certificates')
    op.drop_table('final_exam_attempts')
    op.drop_table('final_exams')
    op.drop_column('courses', 'certificate_passing_score')
    op.drop_column('courses', 'certificate_enabled')
