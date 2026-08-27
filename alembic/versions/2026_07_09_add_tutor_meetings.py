"""add tutor_meetings table

Revision ID: a1b2c3d4e5f6
Revises: bbf5ee13b496
Create Date: 2026-07-09 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = 'bbf5ee13b496'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'tutor_meetings',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('student_id', sa.String(), nullable=False),
        sa.Column('course_id', sa.String(), nullable=False),
        sa.Column('tutor_id', sa.String(), nullable=True),
        sa.Column('topic', sa.String(length=300), nullable=False),
        sa.Column('scheduled_at', sa.DateTime(), nullable=True),
        sa.Column('duration_min', sa.Integer(), nullable=False, server_default='30'),
        sa.Column('status', sa.Enum('requested', 'scheduled', 'completed', 'cancelled', 'declined', name='meetingstatus'), nullable=False, server_default='requested'),
        sa.Column('meeting_url', sa.String(length=500), nullable=True),
        sa.Column('student_notes', sa.Text(), nullable=True),
        sa.Column('tutor_notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['student_id'], ['students.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['course_id'], ['courses.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['tutor_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )


def downgrade() -> None:
    op.drop_table('tutor_meetings')
    op.execute("DROP TYPE IF EXISTS meetingstatus")
