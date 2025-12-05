"""Initial migration - create users and friendships tables

Revision ID: 20241204_000001
Revises: 
Create Date: 2024-12-04 00:00:01

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20241204_000001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('telegram_id', sa.BigInteger(), nullable=False),
        sa.Column('username', sa.String(length=255), nullable=True),
        sa.Column('first_name', sa.String(length=255), nullable=False),
        sa.Column('last_name', sa.String(length=255), nullable=True),
        sa.Column('photo_url', sa.String(length=512), nullable=True),
        sa.Column('language_code', sa.String(length=10), nullable=False, server_default='en'),
        sa.Column('is_premium', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('level', sa.BigInteger(), nullable=False, server_default='1'),
        sa.Column('watts', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('referral_code', sa.String(length=16), nullable=False),
        sa.Column('referred_by_id', sa.BigInteger(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_login_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['referred_by_id'], ['users.id'], name='fk_users_referred_by'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes on users table
    op.create_index('ix_users_telegram_id', 'users', ['telegram_id'], unique=True)
    op.create_index('ix_users_referral_code', 'users', ['referral_code'], unique=True)
    
    # Create friendships table
    op.create_table(
        'friendships',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.BigInteger(), nullable=False),
        sa.Column('friend_id', sa.BigInteger(), nullable=False),
        sa.Column('source', sa.String(length=50), nullable=False, server_default='referral'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['friend_id'], ['users.id'], name='fk_friendships_friend', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name='fk_friendships_user', ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'friend_id', name='uq_friendship_user_friend')
    )
    
    # Create indexes on friendships table
    op.create_index('ix_friendships_user_id', 'friendships', ['user_id'])
    op.create_index('ix_friendships_friend_id', 'friendships', ['friend_id'])


def downgrade() -> None:
    # Drop friendships table
    op.drop_index('ix_friendships_friend_id', table_name='friendships')
    op.drop_index('ix_friendships_user_id', table_name='friendships')
    op.drop_table('friendships')
    
    # Drop users table
    op.drop_index('ix_users_referral_code', table_name='users')
    op.drop_index('ix_users_telegram_id', table_name='users')
    op.drop_table('users')


