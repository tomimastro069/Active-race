"""create_programas_materia

Revision ID: b2d3f4a5c6e7
Revises: a1c2e3f4d5b6
Create Date: 2026-06-17 00:10:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b2d3f4a5c6e7'
down_revision: Union[str, Sequence[str], None] = 'a1c2e3f4d5b6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'programas_materia',
        sa.Column('materia_id', sa.UUID(), nullable=False),
        sa.Column('carrera_id', sa.UUID(), nullable=False),
        sa.Column('cohorte_id', sa.UUID(), nullable=False),
        sa.Column('titulo', sa.String(length=255), nullable=False),
        sa.Column('filename', sa.String(length=255), nullable=False),
        sa.Column('content_type', sa.String(length=100), nullable=False),
        sa.Column('file_size', sa.Integer(), nullable=False),
        sa.Column('contenido', sa.LargeBinary(), nullable=False),
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['carrera_id'], ['carreras.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['cohorte_id'], ['cohortes.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['materia_id'], ['materias.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_programa_tenant_materia', 'programas_materia', ['tenant_id', 'materia_id'])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('idx_programa_tenant_materia', table_name='programas_materia')
    op.drop_table('programas_materia')
