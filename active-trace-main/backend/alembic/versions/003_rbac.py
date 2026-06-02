"""RBAC tables creation and seeding.

Revision ID: 003_rbac
Revises: 002_auth
Create Date: 2026-06-02 22:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import uuid
from datetime import datetime

# revision identifiers, used by Alembic.
revision = '003_rbac'
down_revision = '002_auth'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Create tables
    op.create_table(
        'rol',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('nombre', sa.String(length=100), nullable=False),
        sa.Column('descripcion', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('tenant_id', 'nombre', name='uq_rol_tenant_nombre')
    )
    op.create_index('idx_rol_tenant_deleted_at', 'rol', ['tenant_id', 'deleted_at'])

    op.create_table(
        'permiso',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('nombre', sa.String(length=100), nullable=False),
        sa.Column('descripcion', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('tenant_id', 'nombre', name='uq_permiso_tenant_nombre')
    )
    op.create_index('idx_permiso_tenant_deleted_at', 'permiso', ['tenant_id', 'deleted_at'])

    op.create_table(
        'rol_permiso',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('rol_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('permiso_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['permiso_id'], ['permiso.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['rol_id'], ['rol.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('tenant_id', 'rol_id', 'permiso_id', name='uq_rol_permiso_unique')
    )
    op.create_index('idx_rol_permiso_tenant_deleted_at', 'rol_permiso', ['tenant_id', 'deleted_at'])

    op.create_table(
        'asignacion',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('usuario_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('rol_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('materia_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('carrera_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('cohorte_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('comisiones', sa.JSON(), nullable=True),
        sa.Column('responsable_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('desde', sa.DateTime(), nullable=False),
        sa.Column('hasta', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['rol_id'], ['rol.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['responsable_id'], ['usuario.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['usuario_id'], ['usuario.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_asignacion_tenant_deleted_at', 'asignacion', ['tenant_id', 'deleted_at'])
    op.create_index('idx_asignacion_usuario_vigencia', 'asignacion', ['usuario_id', 'desde', 'hasta'])

    # 2. Seed default roles and permissions
    # Bind connection
    connection = op.get_bind()

    # MetaData for table operations
    metadata = sa.MetaData()
    rol_table = sa.Table('rol', metadata,
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('nombre', sa.String),
        sa.Column('descripcion', sa.String)
    )
    permiso_table = sa.Table('permiso', metadata,
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('nombre', sa.String),
        sa.Column('descripcion', sa.String)
    )
    rol_permiso_table = sa.Table('rol_permiso', metadata,
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True)),
        sa.Column('rol_id', postgresql.UUID(as_uuid=True)),
        sa.Column('permiso_id', postgresql.UUID(as_uuid=True))
    )

    # Insert default system-wide roles (tenant_id is NULL)
    roles_seed = [
        {"id": uuid.uuid4(), "tenant_id": None, "nombre": "ALUMNO", "descripcion": "Estudiante del sistema"},
        {"id": uuid.uuid4(), "tenant_id": None, "nombre": "TUTOR", "descripcion": "Ayudante / Tutor académico"},
        {"id": uuid.uuid4(), "tenant_id": None, "nombre": "PROFESOR", "descripcion": "Profesor a cargo de comisiones"},
        {"id": uuid.uuid4(), "tenant_id": None, "nombre": "COORDINADOR", "descripcion": "Coordinador de carrera/materias"},
        {"id": uuid.uuid4(), "tenant_id": None, "nombre": "NEXO", "descripcion": "Articulador transversal"},
        {"id": uuid.uuid4(), "tenant_id": None, "nombre": "ADMIN", "descripcion": "Administrador del tenant"},
        {"id": uuid.uuid4(), "tenant_id": None, "nombre": "FINANZAS", "descripcion": "Responsable de liquidaciones y honorarios"}
    ]
    for r in roles_seed:
        connection.execute(rol_table.insert().values(r))

    # Insert default system-wide permissions (tenant_id is NULL)
    permissions_seed = [
        {"id": uuid.uuid4(), "tenant_id": None, "nombre": "calificaciones:ver_propio", "descripcion": "Ver su propio estado académico"},
        {"id": uuid.uuid4(), "tenant_id": None, "nombre": "evaluaciones:reservar", "descripcion": "Reservar turno de examen"},
        {"id": uuid.uuid4(), "tenant_id": None, "nombre": "avisos:ack", "descripcion": "Confirmar avisos del sistema"},
        {"id": uuid.uuid4(), "tenant_id": None, "nombre": "calificaciones:importar", "descripcion": "Importar planilla de notas global"},
        {"id": uuid.uuid4(), "tenant_id": None, "nombre": "calificaciones:importar_propio", "descripcion": "Importar planilla de notas en sus materias"},
        {"id": uuid.uuid4(), "tenant_id": None, "nombre": "atrasados:ver", "descripcion": "Ver lista de alumnos atrasados"},
        {"id": uuid.uuid4(), "tenant_id": None, "nombre": "atrasados:ver_propio", "descripcion": "Ver alumnos atrasados de sus materias"},
        {"id": uuid.uuid4(), "tenant_id": None, "nombre": "entregas:detectar", "descripcion": "Detectar entregas sin corregir"},
        {"id": uuid.uuid4(), "tenant_id": None, "nombre": "entregas:detectar_propio", "descripcion": "Detectar entregas sin corregir propias"},
        {"id": uuid.uuid4(), "tenant_id": None, "nombre": "comunicacion:enviar", "descripcion": "Enviar emails a alumnos"},
        {"id": uuid.uuid4(), "tenant_id": None, "nombre": "comunicacion:enviar_propio", "descripcion": "Enviar emails a sus propios alumnos"},
        {"id": uuid.uuid4(), "tenant_id": None, "nombre": "comunicacion:aprobar", "descripcion": "Aprobar envíos masivos de emails"},
        {"id": uuid.uuid4(), "tenant_id": None, "nombre": "encuentros:gestionar", "descripcion": "Gestionar encuentros presenciales/virtuales"},
        {"id": uuid.uuid4(), "tenant_id": None, "nombre": "encuentros:gestionar_propio", "descripcion": "Gestionar sus propios encuentros"},
        {"id": uuid.uuid4(), "tenant_id": None, "nombre": "guardias:registrar", "descripcion": "Registrar guardias de tutoría"},
        {"id": uuid.uuid4(), "tenant_id": None, "nombre": "guardias:registrar_propio", "descripcion": "Registrar sus propias guardias"},
        {"id": uuid.uuid4(), "tenant_id": None, "nombre": "tareas:gestionar", "descripcion": "Gestionar tareas internas"},
        {"id": uuid.uuid4(), "tenant_id": None, "nombre": "tareas:gestionar_propio", "descripcion": "Gestionar sus tareas internas asignadas"},
        {"id": uuid.uuid4(), "tenant_id": None, "nombre": "avisos:publicar", "descripcion": "Crear avisos institucionales"},
        {"id": uuid.uuid4(), "tenant_id": None, "nombre": "equipos:gestionar", "descripcion": "Asignar docentes y equipos"},
        {"id": uuid.uuid4(), "tenant_id": None, "nombre": "estructura:gestionar", "descripcion": "Configurar carreras, materias, cohortes"},
        {"id": uuid.uuid4(), "tenant_id": None, "nombre": "usuarios:gestionar", "descripcion": "Alta, baja y mod de usuarios del tenant"},
        {"id": uuid.uuid4(), "tenant_id": None, "nombre": "auditoria:ver", "descripcion": "Ver el log de auditoría completo"},
        {"id": uuid.uuid4(), "tenant_id": None, "nombre": "auditoria:ver_propio", "descripcion": "Ver log de auditoría de su ámbito"},
        {"id": uuid.uuid4(), "tenant_id": None, "nombre": "salarios:operar", "descripcion": "Configurar grilla salarial"},
        {"id": uuid.uuid4(), "tenant_id": None, "nombre": "liquidaciones:gestionar", "descripcion": "Calcular y cerrar liquidaciones"},
        {"id": uuid.uuid4(), "tenant_id": None, "nombre": "facturas:gestionar", "descripcion": "Gestionar facturas docentes"},
        {"id": uuid.uuid4(), "tenant_id": None, "nombre": "tenant:configurar", "descripcion": "Configurar branding e idioma de institución"}
    ]
    for p in permissions_seed:
        connection.execute(permiso_table.insert().values(p))

    # Helper mapping to easily match roles to permission names
    role_ids = {r["nombre"]: r["id"] for r in roles_seed}
    perm_ids = {p["nombre"]: p["id"] for p in permissions_seed}

    # Define matrix relationships
    matrix = {
        "ALUMNO": [
            "calificaciones:ver_propio",
            "evaluaciones:reservar",
            "avisos:ack"
        ],
        "TUTOR": [
            "avisos:ack",
            "atrasados:ver",
            "entregas:detectar",
            "encuentros:gestionar",
            "guardias:registrar_propio"
        ],
        "PROFESOR": [
            "avisos:ack",
            "calificaciones:importar_propio",
            "atrasados:ver_propio",
            "entregas:detectar_propio",
            "comunicacion:enviar_propio",
            "encuentros:gestionar_propio",
            "guardias:registrar_propio",
            "tareas:gestionar_propio"
        ],
        "COORDINADOR": [
            "avisos:ack",
            "calificaciones:importar",
            "atrasados:ver",
            "entregas:detectar",
            "comunicacion:enviar",
            "comunicacion:aprobar",
            "encuentros:gestionar",
            "guardias:registrar",
            "tareas:gestionar",
            "avisos:publicar",
            "equipos:gestionar",
            "auditoria:ver_propio"
        ],
        "NEXO": [
            "avisos:ack"
            # ADR-008: semántica pendiente
        ],
        "ADMIN": [
            # Herencia de todos los permisos del COORDINADOR + los suyos
            "avisos:ack",
            "calificaciones:importar",
            "atrasados:ver",
            "entregas:detectar",
            "comunicacion:enviar",
            "comunicacion:aprobar",
            "encuentros:gestionar",
            "guardias:registrar",
            "tareas:gestionar",
            "avisos:publicar",
            "equipos:gestionar",
            "estructura:gestionar",
            "usuarios:gestionar",
            "auditoria:ver",
            "tenant:configurar"
        ],
        "FINANZAS": [
            "avisos:ack",
            "auditoria:ver",
            "salarios:operar",
            "liquidaciones:gestionar",
            "facturas:gestionar"
        ]
    }

    # As associate entries must carry a valid tenant_id, and we do default settings seeding,
    # we can use a dummy UUID '00000000-0000-0000-0000-000000000000' representing the global tenant
    # or just use a default fallback. Since RolPermiso requires a non-null tenant_id,
    # we use a constant system-wide dummy UUID for default seed values.
    # Tenants will duplicate these associations upon creation or we can check with NULL tenant.
    # To keep it completely compliant with `nullable=False` for tenant_id in intermediate table,
    # we use the nil UUID ('00000000-0000-0000-0000-000000000000') as the global system tenant marker.
    system_tenant_id = uuid.UUID('00000000-0000-0000-0000-000000000000')

    for role_name, perm_names in matrix.items():
        role_uuid = role_ids[role_name]
        for p_name in perm_names:
            perm_uuid = perm_ids[p_name]
            connection.execute(rol_permiso_table.insert().values({
                "id": uuid.uuid4(),
                "tenant_id": system_tenant_id,
                "rol_id": role_uuid,
                "permiso_id": perm_uuid
            }))


def downgrade() -> None:
    op.drop_index('idx_asignacion_usuario_vigencia', table_name='asignacion')
    op.drop_index('idx_asignacion_tenant_deleted_at', table_name='asignacion')
    op.drop_table('asignacion')

    op.drop_index('idx_rol_permiso_tenant_deleted_at', table_name='rol_permiso')
    op.drop_table('rol_permiso')

    op.drop_index('idx_permiso_tenant_deleted_at', table_name='permiso')
    op.drop_table('permiso')

    op.drop_index('idx_rol_tenant_deleted_at', table_name='rol')
    op.drop_table('rol')
