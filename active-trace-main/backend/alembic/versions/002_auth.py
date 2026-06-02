"""Auth tables creation.

Revision ID: 002_auth
Revises: 001_tenant
Create Date: 2026-06-02 22:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '002_auth'
down_revision = '001_tenant'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create usuario table
    op.create_table(
        'usuario',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('estado', sa.String(length=50), nullable=False, server_default='Activo'),
        sa.Column('two_factor_secret', sa.String(length=255), nullable=True),
        sa.Column('two_factor_enabled', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('tenant_id', 'email', name='uq_usuario_tenant_email')
    )
    
    # Create indexes for usuario
    op.create_index('idx_usuario_tenant_email', 'usuario', ['tenant_id', 'email'])
    op.create_index('idx_usuario_deleted_at', 'usuario', ['deleted_at'])

    # Create token_refresco table
    op.create_table(
        'token_refresco',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('usuario_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('token', sa.String(length=500), nullable=False),
        sa.Column('expira_el', sa.DateTime(), nullable=False),
        sa.Column('familia_id', sa.String(length=255), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['usuario_id'], ['usuario.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('token')
    )
    
    # Create indexes for token_refresco
    op.create_index('idx_token_refresco_usuario', 'token_refresco', ['usuario_id'])
    op.create_index('idx_token_refresco_familia', 'token_refresco', ['familia_id'])
    op.create_index('idx_token_refresco_deleted_at', 'token_refresco', ['deleted_at'])


def downgrade() -> None:
    op.drop_index('idx_token_refresco_deleted_at', table_name='token_refresco')
    op.drop_index('idx_token_refresco_familia', table_name='token_refresco')
    op.drop_index('idx_token_refresco_usuario', table_name='token_refresco')
    op.drop_table('token_refresco')
    
    op.drop_index('idx_usuario_deleted_at', table_name='usuario')
    op.drop_index('idx_usuario_tenant_email', table_name='usuario')
    op.drop_table('usuario')
