"""Initial login tables

Revision ID: 001
Revises: 
Create Date: 2025-08-29 15:50:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSON

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('avatar_url', sa.String(500), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('is_verified', sa.Boolean(), nullable=False, default=False),
        sa.Column('profile_data', JSON(), nullable=True, default={}),
        sa.Column('preferences', JSON(), nullable=True, default={}),
        sa.Column('oauth_data', JSON(), nullable=True, default={}),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('last_login_at', sa.DateTime(timezone=True), nullable=True),
    )
    
    # Create indexes for users table
    op.create_index('idx_users_email_active', 'users', ['email', 'is_active'])
    op.create_index('idx_users_created_at', 'users', ['created_at'])
    # Skip GIN index for now - can be added later if needed
    # op.create_index('idx_users_profile_data', 'users', ['profile_data'], postgresql_using='gin')
    op.create_unique_constraint('uq_users_email', 'users', ['email'])

    # Create auth_providers table
    op.create_table(
        'auth_providers',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', UUID(as_uuid=True), nullable=False),
        sa.Column('provider', sa.String(50), nullable=False),
        sa.Column('provider_user_id', sa.String(255), nullable=False),
        sa.Column('access_token', sa.Text(), nullable=True),
        sa.Column('refresh_token', sa.Text(), nullable=True),
        sa.Column('token_expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('provider_data', JSON(), nullable=True, default={}),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    
    # Create indexes for auth_providers table
    op.create_index('idx_auth_providers_user_provider', 'auth_providers', ['user_id', 'provider'])
    op.create_index('idx_auth_providers_provider_user_id', 'auth_providers', ['provider', 'provider_user_id'])

    # Create user_sessions table
    op.create_table(
        'user_sessions',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', UUID(as_uuid=True), nullable=False),
        sa.Column('session_token', sa.String(255), nullable=False),
        sa.Column('refresh_token', sa.String(255), nullable=False),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('device_info', JSON(), nullable=True, default={}),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('refresh_expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('last_accessed_at', sa.DateTime(timezone=True), nullable=False),
    )
    
    # Create indexes for user_sessions table
    op.create_index('idx_user_sessions_user_active', 'user_sessions', ['user_id', 'is_active'])
    op.create_index('idx_user_sessions_expires_at', 'user_sessions', ['expires_at'])
    # Skip GIN index for device_info - can be added later if needed
    # op.create_index('idx_user_sessions_device_info', 'user_sessions', ['device_info'], postgresql_using='gin')
    op.create_unique_constraint('uq_user_sessions_session_token', 'user_sessions', ['session_token'])
    op.create_unique_constraint('uq_user_sessions_refresh_token', 'user_sessions', ['refresh_token'])


def downgrade() -> None:
    op.drop_table('user_sessions')
    op.drop_table('auth_providers')
    op.drop_table('users')