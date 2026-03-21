"""add subscribers table

Revision ID: a1b2c3d4e5f6
Revises: adf9c42cc985
Create Date: 2026-03-21 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = '4edff6f3ba5d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('subscribers',
        sa.Column('chat_id', sa.BigInteger(), nullable=False),
        sa.PrimaryKeyConstraint('chat_id')
    )


def downgrade() -> None:
    op.drop_table('subscribers')
