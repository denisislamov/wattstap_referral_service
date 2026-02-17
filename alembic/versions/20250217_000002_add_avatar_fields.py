"""Add avatar fields to users table

Revision ID: 20250217_000002
Revises: 20250217_000001
Create Date: 2025-02-17 18:00:01

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20250217_000002'
down_revision: Union[str, None] = '20250217_000001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add unlocked_avatars column (comma-separated list of unlocked avatar IDs)
    op.add_column(
        'users',
        sa.Column('unlocked_avatars', sa.String(4096), nullable=False, server_default='')
    )
    # Add current_avatar column (currently equipped avatar ID)
    op.add_column(
        'users',
        sa.Column('current_avatar', sa.String(255), nullable=False, server_default='telegram_avatar')
    )


def downgrade() -> None:
    op.drop_column('users', 'current_avatar')
    op.drop_column('users', 'unlocked_avatars')
