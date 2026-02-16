"""Add mining balance configuration tables

Revision ID: 20250217_000001
Revises: 20250128_000001
Create Date: 2025-02-17 00:00:01

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20250217_000001'
down_revision: Union[str, None] = '20250128_000001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create mining_balance_params table
    op.create_table(
        'mining_balance_params',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('version', sa.String(), nullable=False, server_default='default'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('coins_per_tap', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('exp_per_tap', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('energy_cost_per_tap', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('start_capacity_hits', sa.Integer(), nullable=False, server_default='1500'),
        sa.Column('cooldown_per_hit_sec', sa.Float(), nullable=False, server_default='2.0'),
        sa.Column('crit_multiplier', sa.Float(), nullable=False, server_default='1.2'),
        sa.Column('chance_crit_percent', sa.Float(), nullable=False, server_default='1.0'),
        sa.Column('avg_playtime_minutes', sa.Integer(), nullable=False, server_default='15'),
        sa.Column('taps_per_second', sa.Integer(), nullable=False, server_default='10'),
        sa.Column('profit_per_hour', sa.Integer(), nullable=False, server_default='500'),
        sa.Column('max_hours_offline', sa.Integer(), nullable=False, server_default='3'),
        sa.Column('sessions_per_day', sa.Integer(), nullable=False, server_default='2'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_mining_balance_params_id', 'mining_balance_params', ['id'])
    op.create_index('ix_mining_balance_params_version', 'mining_balance_params', ['version'], unique=True)

    # Create mining_balance_daily_progression table
    op.create_table(
        'mining_balance_daily_progression',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('balance_params_id', sa.Integer(), nullable=False),
        sa.Column('day', sa.Integer(), nullable=False),
        sa.Column('playtime_sec', sa.Integer(), nullable=False, server_default='900'),
        sa.Column('taps_per_session', sa.Integer(), nullable=False, server_default='1950'),
        sa.Column('taps_per_day', sa.Integer(), nullable=False, server_default='3900'),
        sa.Column('exp_per_day', sa.BigInteger(), nullable=False, server_default='3900'),
        sa.Column('coins_from_taps', sa.Float(), nullable=False, server_default='3946.8'),
        sa.Column('coins_from_offline_bonus', sa.Float(), nullable=False, server_default='3000.0'),
        sa.Column('profit_coins', sa.Float(), nullable=False, server_default='6946.8'),
        sa.Column('cumulative_profit_coins', sa.Float(), nullable=False, server_default='6946.8'),
        sa.Column('cumulative_exp', sa.BigInteger(), nullable=False, server_default='3900'),
        sa.ForeignKeyConstraint(['balance_params_id'], ['mining_balance_params.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_mining_balance_daily_progression_id', 'mining_balance_daily_progression', ['id'])


def downgrade() -> None:
    op.drop_table('mining_balance_daily_progression')
    op.drop_table('mining_balance_params')
