"""c12_comunicacion

Revision ID: bc500c50d1fd
Revises: fbbfb2cc45f9
Create Date: 2026-06-03 22:18:23.829127

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'bc500c50d1fd'
down_revision: Union[str, Sequence[str], None] = 'fbbfb2cc45f9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema: add aprobacion_comunicaciones_masivas to tenant, create comunicacion table."""

    # 1. Add flag to tenant (safe with server_default for existing rows)
    op.add_column(
        'tenant',
        sa.Column(
            'aprobacion_comunicaciones_masivas',
            sa.Boolean(),
            nullable=False,
            server_default='false',
        ),
    )

    # 2. Create the enum type (checkfirst=True is idempotent)
    estadocomunicacion = postgresql.ENUM(
        'Pendiente', 'Enviando', 'Enviado', 'Error', 'Cancelado',
        name='estadocomunicacion',
        create_type=True,
    )
    estadocomunicacion.create(op.get_bind(), checkfirst=True)

    # 3. Create the comunicacion table
    op.create_table(
        'comunicacion',
        sa.Column('enviado_por', sa.UUID(), nullable=False),
        sa.Column('materia_id', sa.UUID(), nullable=False),
        sa.Column('destinatario', sa.String(), nullable=False),
        sa.Column('destinatario_hash', sa.String(length=64), nullable=False),
        sa.Column('asunto', sa.String(length=500), nullable=False),
        sa.Column('cuerpo', sa.Text(), nullable=False),
        sa.Column(
            'estado',
            postgresql.ENUM(
                'Pendiente', 'Enviando', 'Enviado', 'Error', 'Cancelado',
                name='estadocomunicacion',
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column('lote_id', sa.UUID(), nullable=True),
        sa.Column('aprobado', sa.Boolean(), nullable=False),
        sa.Column('enviado_at', sa.DateTime(), nullable=True),
        sa.Column('intentos', sa.Integer(), nullable=False),
        sa.Column('max_intentos', sa.Integer(), nullable=False),
        # TimestampedTenant mixin columns
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['enviado_por'], ['usuario.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['materia_id'], ['materias.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )

    # 4. Create indexes
    op.create_index('idx_comunicacion_tenant_estado', 'comunicacion', ['tenant_id', 'estado'], unique=False)
    op.create_index('idx_comunicacion_lote_id', 'comunicacion', ['lote_id'], unique=False)
    op.create_index('idx_comunicacion_tenant_enviado_por', 'comunicacion', ['tenant_id', 'enviado_por'], unique=False)
    op.create_index('idx_comunicacion_destinatario_hash', 'comunicacion', ['destinatario_hash'], unique=False)


def downgrade() -> None:
    """Downgrade schema: undo comunicacion table, enum, and tenant flag."""

    # Drop indexes first
    op.drop_index('idx_comunicacion_destinatario_hash', table_name='comunicacion')
    op.drop_index('idx_comunicacion_tenant_enviado_por', table_name='comunicacion')
    op.drop_index('idx_comunicacion_lote_id', table_name='comunicacion')
    op.drop_index('idx_comunicacion_tenant_estado', table_name='comunicacion')

    # Drop table
    op.drop_table('comunicacion')

    # Drop enum type
    op.execute('DROP TYPE IF EXISTS estadocomunicacion')

    # Drop column from tenant
    op.drop_column('tenant', 'aprobacion_comunicaciones_masivas')
