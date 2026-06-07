"""C20 perfil y mensajeria interna

Revision ID: e21b72dc6345
Revises: b6fc5b16d6f1
Create Date: 2026-06-07 20:25:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'e21b72dc6345'
down_revision: Union[str, Sequence[str], None] = 'b6fc5b16d6f1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add column modalidad_cobro to usuario table
    op.add_column('usuario', sa.Column('modalidad_cobro', sa.String(length=100), nullable=True))

    # Create thread table
    op.create_table(
        'thread',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('asunto', sa.String(length=255), nullable=False),
        sa.Column('creador_id', sa.UUID(), nullable=False),
        sa.Column('is_closed', sa.Boolean(), nullable=False, default=False),
        sa.ForeignKeyConstraint(['creador_id'], ['usuario.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_thread_tenant_id', 'thread', ['tenant_id'], unique=False)
    op.create_index('idx_thread_creador_id', 'thread', ['creador_id'], unique=False)

    # Create thread_member association table
    op.create_table(
        'thread_member',
        sa.Column('thread_id', sa.UUID(), nullable=False),
        sa.Column('usuario_id', sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(['thread_id'], ['thread.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['usuario_id'], ['usuario.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('thread_id', 'usuario_id')
    )

    # Create message table
    op.create_table(
        'message',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('thread_id', sa.UUID(), nullable=False),
        sa.Column('remitente_id', sa.UUID(), nullable=False),
        sa.Column('contenido', sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(['remitente_id'], ['usuario.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['thread_id'], ['thread.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_message_tenant_id', 'message', ['tenant_id'], unique=False)
    op.create_index('idx_message_thread_id', 'message', ['thread_id'], unique=False)
    op.create_index('idx_message_remitente_id', 'message', ['remitente_id'], unique=False)


def downgrade() -> None:
    # Drop indices and tables
    op.drop_index('idx_message_remitente_id', table_name='message')
    op.drop_index('idx_message_thread_id', table_name='message')
    op.drop_index('idx_message_tenant_id', table_name='message')
    op.drop_table('message')

    op.drop_table('thread_member')

    op.drop_index('idx_thread_creador_id', table_name='thread')
    op.drop_index('idx_thread_tenant_id', table_name='thread')
    op.drop_table('thread')

    op.drop_column('usuario', 'modalidad_cobro')
