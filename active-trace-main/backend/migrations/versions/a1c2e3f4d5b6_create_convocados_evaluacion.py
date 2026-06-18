"""create_convocados_evaluacion

Revision ID: a1c2e3f4d5b6
Revises: 0e9339c786f7
Create Date: 2026-06-17 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1c2e3f4d5b6'
down_revision: Union[str, Sequence[str], None] = '0e9339c786f7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'convocados_evaluacion',
        sa.Column('evaluacion_id', sa.UUID(), nullable=False),
        sa.Column('alumno_id', sa.UUID(), nullable=False),
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['alumno_id'], ['usuario.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['evaluacion_id'], ['evaluaciones.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('evaluacion_id', 'alumno_id', name='uq_convocado_alumno_evaluacion'),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('convocados_evaluacion')
