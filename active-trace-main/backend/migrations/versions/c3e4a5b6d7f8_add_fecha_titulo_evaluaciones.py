"""add_fecha_titulo_evaluaciones

Revision ID: c3e4a5b6d7f8
Revises: b2d3f4a5c6e7
Create Date: 2026-06-17 00:20:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c3e4a5b6d7f8'
down_revision: Union[str, Sequence[str], None] = 'b2d3f4a5c6e7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('evaluaciones', sa.Column('titulo', sa.String(length=255), nullable=True))
    op.add_column('evaluaciones', sa.Column('fecha', sa.Date(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('evaluaciones', 'fecha')
    op.drop_column('evaluaciones', 'titulo')
