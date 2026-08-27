"""add rich lesson fields

Revision ID: 005
Revises: 9629b6d554e1
Create Date: 2025-06-25 20:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '005'
down_revision = '9629b6d554e1'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('lessons', sa.Column('content_blocks', sa.JSON(), nullable=False, server_default='[]'))
    op.add_column('lessons', sa.Column('resources', sa.JSON(), nullable=False, server_default='[]'))
    op.add_column('lessons', sa.Column('objectives', sa.JSON(), nullable=False, server_default='[]'))
    op.add_column('lessons', sa.Column('homework', sa.JSON(), nullable=False, server_default='[]'))
    op.add_column('lessons', sa.Column('difficulty', sa.Enum('easy', 'medium', 'hard', name='difficulty'), nullable=False, server_default='medium'))


def downgrade():
    op.drop_column('lessons', 'difficulty')
    op.drop_column('lessons', 'homework')
    op.drop_column('lessons', 'objectives')
    op.drop_column('lessons', 'resources')
    op.drop_column('lessons', 'content_blocks')
