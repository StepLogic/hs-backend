"""add testimonials

Revision ID: c9d1e2f3a4b5
Revises: 246f4ad9a700
"""
from typing import Sequence, Union
from datetime import datetime
import uuid

import sqlalchemy as sa
from alembic import op

revision: str = "c9d1e2f3a4b5"
down_revision: Union[str, Sequence[str], None] = "246f4ad9a700"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# The real quotes that replace the placeholder marketing copy. Attributed
# anonymously by role, as the families gave them.
SEED = [
    (
        "Student",
        "Thank you so much for your help. You came to my life at a time I needed you the "
        "most. I have learned so much from you in a short amount of time. I will continue "
        "to use what I have learned through the rest of my school year and in college as "
        "well. Will continue to keep in touch with you. Talk to you soon. God bless you.",
    ),
    (
        "Parent",
        "It's been an amazing 6 months journey with you. You came into my son's life at a "
        "very crucial moment when I was scared and frustrated because he needed help. With "
        "your help, he has learned a lot and has also built some confidence in himself. I "
        "know he will continue to use what he has learned through his final year in high "
        "school and hopefully in college as well. Thank you so much. This is not a goodbye, "
        "because his younger brother will be starting soon.",
    ),
    (
        "Parent",
        "He has done a great job teaching math to the kids, from middle school right through "
        "to the end of high school. He's very attentive to each student and does his best to "
        "push them to their limit. He focuses on building the kids' confidence in solving "
        "problems, and shows them how to break down complex problems step by step. He was "
        "always available when they needed more understanding, and he's patient with them. "
        "His passion for teaching is astounding and very uplifting. Everything he taught my "
        "child, and all the tips he gave, will carry into college math courses.",
    ),
    (
        "Parent",
        "Thank you so much for all your hard work and guidance with my son. Your remarkable "
        "ability to break down complex mathematical concepts into clear, digestible steps "
        "built his confidence tremendously. Math might never be his absolute favorite "
        "subject, but thanks to you, he is no longer afraid of it.",
    ),
    (
        "Parent",
        "“When an elder extends a hand, the young discover the strength to rise,” they "
        "say. Indeed, you have truly extended that hand to my son and so many of his peers — "
        "guiding, challenging, and inspiring them to reach their full potential. Your "
        "dedication, patience, and sacrifices have made a remarkable difference in his "
        "educational journey. We are deeply grateful for all you do to nurture young minds "
        "and help them aim higher. Thank you for investing in the next generation.",
    ),
]


def upgrade() -> None:
    # app.initial_data.init_db() runs create_all() at startup, so a deploy that lands
    # before this migration will already have built the table from the model. Bind to
    # the existing shape in that case rather than failing on a duplicate.
    testimonials = sa.table(
        "testimonials",
        sa.column("id", sa.String),
        sa.column("name", sa.String),
        sa.column("role", sa.String),
        sa.column("quote", sa.Text),
        sa.column("stars", sa.Integer),
        sa.column("published", sa.Boolean),
        sa.column("created_at", sa.DateTime),
    )
    if not sa.inspect(op.get_bind()).has_table("testimonials"):
        testimonials = op.create_table(
            "testimonials",
            sa.Column("id", sa.String(), primary_key=True),
            sa.Column("name", sa.String(), nullable=False, server_default="Anonymous"),
            sa.Column("role", sa.String(), nullable=False, server_default="Parent"),
            sa.Column("quote", sa.Text(), nullable=False),
            sa.Column("stars", sa.Integer(), nullable=False, server_default="5"),
            sa.Column("published", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        )

    # Seed only into an empty table, so this is safe however the table got here.
    if op.get_bind().execute(sa.text("SELECT COUNT(*) FROM testimonials")).scalar():
        return

    op.bulk_insert(
        testimonials,
        [
            {
                "id": str(uuid.uuid4()),
                "name": "Anonymous",
                "role": role,
                "quote": quote,
                "stars": 5,
                "published": True,
                "created_at": datetime.utcnow(),
            }
            for role, quote in SEED
        ],
    )


def downgrade() -> None:
    op.drop_table("testimonials")
