"""merge heads

Revision ID: 9629b6d554e1
Revises: ab3badd360aa, 004
Create Date: 2026-06-25 19:52:26.624626

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9629b6d554e1'
down_revision: Union[str, Sequence[str], None] = ('ab3badd360aa', '004')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
