"""Add experience fields to users table

Revision ID: 20250119_000001
Revises: 20241204_000001
Create Date: 2025-01-19 00:00:01

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20250119_000001'
down_revision: Union[str, None] = '20241204_000001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add current_xp column
    op.add_column(
        'users',
        sa.Column('current_xp', sa.BigInteger(), nullable=False, server_default='0')
    )
    
    # Add total_xp column
    op.add_column(
        'users',
        sa.Column('total_xp', sa.BigInteger(), nullable=False, server_default='0')
    )


def downgrade() -> None:
    # Drop total_xp column
    op.drop_column('users', 'total_xp')
    
    # Drop current_xp column
    op.drop_column('users', 'current_xp')

