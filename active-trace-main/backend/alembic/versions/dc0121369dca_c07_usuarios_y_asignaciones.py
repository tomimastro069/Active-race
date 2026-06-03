"""c07_usuarios_y_asignaciones

Revision ID: dc0121369dca
Revises: 6f2bdeffd594
Create Date: 2026-06-03 03:33:19.429501

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'dc0121369dca'
down_revision: Union[str, Sequence[str], None] = '6f2bdeffd594'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Drop existing uniqueness constraints and indexes on email first
    op.drop_constraint('uq_usuario_tenant_email', 'usuario', type_='unique')
    op.drop_index('idx_usuario_tenant_email', table_name='usuario')

    # 2. Add email_hash and other profile/PII columns as nullable
    op.add_column('usuario', sa.Column('email_hash', sa.String(length=64), nullable=True))
    op.add_column('usuario', sa.Column('nombre', sa.String(length=100), nullable=True))
    op.add_column('usuario', sa.Column('apellidos', sa.String(length=100), nullable=True))
    op.add_column('usuario', sa.Column('dni', sa.String(length=255), nullable=True))
    op.add_column('usuario', sa.Column('cuil', sa.String(length=255), nullable=True))
    op.add_column('usuario', sa.Column('cbu', sa.String(length=255), nullable=True))
    op.add_column('usuario', sa.Column('alias_cbu', sa.String(length=255), nullable=True))
    op.add_column('usuario', sa.Column('banco', sa.String(length=100), nullable=True))
    op.add_column('usuario', sa.Column('regional', sa.String(length=100), nullable=True))
    op.add_column('usuario', sa.Column('legajo', sa.String(length=50), nullable=True))
    op.add_column('usuario', sa.Column('legajo_profesional', sa.String(length=50), nullable=True))
    op.add_column('usuario', sa.Column('facturador', sa.Boolean(), nullable=False, server_default=sa.text('false')))

    # 3. Data migration for existing users
    connection = op.get_bind()
    users = connection.execute(sa.text("SELECT id, email FROM usuario")).fetchall()
    
    from app.core.security import encrypt_attr, generate_email_hash
    
    for row in users:
        user_id = row[0]
        plain_email = row[1]
        
        # Check if email is already encrypted
        if '@' in plain_email:
            encrypted_email = encrypt_attr(plain_email)
            email_hash = generate_email_hash(plain_email)
            connection.execute(
                sa.text("UPDATE usuario SET email = :email, email_hash = :email_hash WHERE id = :id"),
                {"email": encrypted_email, "email_hash": email_hash, "id": user_id}
            )
        else:
            from app.core.config import Settings
            import hmac
            import hashlib
            settings = Settings()
            key = settings.ENCRYPTION_KEY.encode('utf-8') if isinstance(settings.ENCRYPTION_KEY, str) else settings.ENCRYPTION_KEY
            fallback_hash = hmac.new(key, plain_email.lower().strip().encode('utf-8'), hashlib.sha256).hexdigest()
            connection.execute(
                sa.text("UPDATE usuario SET email_hash = :email_hash WHERE id = :id"),
                {"email_hash": fallback_hash, "id": user_id}
            )

    # 4. Alter email_hash to be NOT NULL
    op.alter_column('usuario', 'email_hash', nullable=False)

    # 5. Create new unique constraints and indexes using email_hash
    op.create_unique_constraint('uq_usuario_tenant_email', 'usuario', ['tenant_id', 'email_hash'])
    op.create_index('idx_usuario_tenant_email', 'usuario', ['tenant_id', 'email_hash'], unique=False)


def downgrade() -> None:
    # 1. Drop new constraints and indexes
    op.drop_constraint('uq_usuario_tenant_email', 'usuario', type_='unique')
    op.drop_index('idx_usuario_tenant_email', table_name='usuario')

    # 2. Data rollback: decrypt email back to plain text
    connection = op.get_bind()
    users = connection.execute(sa.text("SELECT id, email FROM usuario")).fetchall()
    
    from app.core.security import decrypt_attr
    
    for row in users:
        user_id = row[0]
        encrypted_email = row[1]
        try:
            plain_email = decrypt_attr(encrypted_email)
            connection.execute(
                sa.text("UPDATE usuario SET email = :email WHERE id = :id"),
                {"email": plain_email, "id": user_id}
            )
        except Exception:
            pass

    # 3. Drop columns
    op.drop_column('usuario', 'facturador')
    op.drop_column('usuario', 'legajo_profesional')
    op.drop_column('usuario', 'legajo')
    op.drop_column('usuario', 'regional')
    op.drop_column('usuario', 'banco')
    op.drop_column('usuario', 'alias_cbu')
    op.drop_column('usuario', 'cbu')
    op.drop_column('usuario', 'cuil')
    op.drop_column('usuario', 'dni')
    op.drop_column('usuario', 'apellidos')
    op.drop_column('usuario', 'nombre')
    op.drop_column('usuario', 'email_hash')

    # 4. Restore original unique constraint and index on email
    op.create_unique_constraint('uq_usuario_tenant_email', 'usuario', ['tenant_id', 'email'])
    op.create_index('idx_usuario_tenant_email', 'usuario', ['tenant_id', 'email'], unique=False)
