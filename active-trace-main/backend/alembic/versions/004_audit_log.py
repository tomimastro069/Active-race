"""Create audit_log table.

Revision ID: 004_audit_log
Revises: 003_rbac
Create Date: 2026-06-02 23:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '004_audit_log'
down_revision = '003_rbac'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create audit_log table
    op.create_table(
        'audit_log',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('fecha_hora', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('actor_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('impersonado_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('materia_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('accion', sa.String(length=100), nullable=False),
        sa.Column('detalle', sa.JSON(), nullable=True),
        sa.Column('filas_afectadas', sa.Integer(), nullable=True),
        sa.Column('ip', sa.String(length=50), nullable=True),
        sa.Column('user_agent', sa.String(length=255), nullable=True),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenant.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['actor_id'], ['usuario.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['impersonado_id'], ['usuario.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for audit_log
    op.create_index('idx_audit_log_tenant', 'audit_log', ['tenant_id'])
    op.create_index('idx_audit_log_actor', 'audit_log', ['actor_id'])
    op.create_index('idx_audit_log_accion', 'audit_log', ['accion'])

    # PostgreSQL trigger to prevent UPDATE or DELETE (defense in depth)
    op.execute("""
        CREATE OR REPLACE FUNCTION prevent_audit_log_modification()
        RETURNS TRIGGER AS $$
        BEGIN
            RAISE EXCEPTION 'Audit logs are append-only. Modification or deletion is not allowed.';
        END;
        $$ LANGUAGE plpgsql;
    """)
    op.execute("""
        CREATE TRIGGER audit_log_no_update_delete
        BEFORE UPDATE OR DELETE ON audit_log
        FOR EACH ROW
        EXECUTE FUNCTION prevent_audit_log_modification();
    """)


def downgrade() -> None:
    # Drop trigger and function
    op.execute("DROP TRIGGER IF EXISTS audit_log_no_update_delete ON audit_log;")
    op.execute("DROP FUNCTION IF EXISTS prevent_audit_log_modification();")

    # Drop indexes and table
    op.drop_index('idx_audit_log_accion', table_name='audit_log')
    op.drop_index('idx_audit_log_actor', table_name='audit_log')
    op.drop_index('idx_audit_log_tenant', table_name='audit_log')
    op.drop_table('audit_log')
