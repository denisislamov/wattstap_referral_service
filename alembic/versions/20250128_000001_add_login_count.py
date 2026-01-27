"""Add login_count field to users table

Revision ID: 20250128_000001
Revises: 20250119_000001
Create Date: 2025-01-28 00:00:01

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20250128_000001'
down_revision: Union[str, None] = '20250119_000001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add login_count column with default 0
    op.add_column(
        'users',
        sa.Column('login_count', sa.BigInteger(), nullable=False, server_default='0')
    )


def downgrade() -> None:
    # Drop login_count column
    op.drop_column('users', 'login_count')
