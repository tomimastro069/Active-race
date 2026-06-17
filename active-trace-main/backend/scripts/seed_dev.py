"""
Seed de desarrollo para Active Trace.

Crea:
  Tenant : Demo University
  Roles  : ADMIN, COORDINADOR, PROFESOR, ALUMNO  (globales y por tenant)
  Permisos y relaciones RolPermiso
  Entidades académicas de prueba: Carrera (TUPAD), Cohortes, Materias
  Usuarios y Asignaciones iniciales de comisiones de prueba
"""

import asyncio
import sys
import uuid
from datetime import datetime, timezone

# Asegura que /app esté en el path cuando se corre fuera de Docker
sys.path.insert(0, "/app") if "/app" not in sys.path else None

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import SessionLocal
from app.core.security import generate_email_hash, hash_password
from app.models.asignacion import Asignacion
from app.models.rol import Rol
from app.models.tenant import Tenant
from app.models.usuario import Usuario
from app.models.permiso import Permiso
from app.models.rol_permiso import RolPermiso
from app.models.carrera import Carrera
from app.models.cohorte import Cohorte
from app.models.materia import Materia

# ---------------------------------------------------------------------------
# Datos
# ---------------------------------------------------------------------------

TENANT_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")

ROLES = [
    {"nombre": "ADMIN",        "descripcion": "Administrador de tenant"},
    {"nombre": "COORDINADOR",  "descripcion": "Coordinador académico"},
    {"nombre": "PROFESOR",     "descripcion": "Docente / Profesor"},
    {"nombre": "ALUMNO",       "descripcion": "Estudiante"},
]

PERMISOS = [
    {"nombre": "usuarios:gestionar", "descripcion": "Crear, editar o desactivar usuarios del tenant"},
    {"nombre": "tareas:gestionar", "descripcion": "Crear y gestionar tareas internas"},
    {"nombre": "estructura:gestionar", "descripcion": "Crear y gestionar carreras, cohortes y materias"},
    {"nombre": "encuentros:gestionar", "descripcion": "Crear y editar encuentros y slots de disponibilidad"},
    {"nombre": "equipos:asignar", "descripcion": "Asignar docentes a materias/cohortes (equipos)"},
    {"nombre": "comunicacion:enviar", "descripcion": "Redactar y encolar envíos de emails"},
    {"nombre": "comunicacion:aprobar", "descripcion": "Aprobar o rechazar envíos de emails masivos"},
    {"nombre": "calificaciones:importar", "descripcion": "Importar calificaciones desde CSV o Moodle"},
    {"nombre": "avisos:publicar", "descripcion": "Publicar avisos institucionales (tablón)"},
    {"nombre": "auditoria:ver", "descripcion": "Visualizar logs de auditoría"},
    {"nombre": "atrasados:ver", "descripcion": "Visualizar listado y monitor de alumnos atrasados"},
]

MAPEO_ROL_PERMISO = {
    "ADMIN": [p["nombre"] for p in PERMISOS],
    "COORDINADOR": [
        "usuarios:gestionar",
        "tareas:gestionar",
        "estructura:gestionar",
        "encuentros:gestionar",
        "equipos:asignar",
        "comunicacion:enviar",
        "comunicacion:aprobar",
        "calificaciones:importar",
        "avisos:publicar",
        "atrasados:ver",
    ],
    "PROFESOR": [
        "tareas:gestionar",
        "encuentros:gestionar",
        "calificaciones:importar",
        "atrasados:ver",
    ],
    "ALUMNO": []
}

USUARIOS = [
    {
        "nombre":   "Admin",
        "apellidos": "Demo",
        "email":    "admin@demo.com",
        "password": "admin1234",
        "rol":      "ADMIN",
    },
    {
        "nombre":   "Coordinador",
        "apellidos": "Demo",
        "email":    "coordinador@demo.com",
        "password": "coord1234",
        "rol":      "COORDINADOR",
    },
    {
        "nombre":   "Docente",
        "apellidos": "Demo",
        "email":    "docente@demo.com",
        "password": "docente1234",
        "rol":      "PROFESOR",
    },
]

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def get_or_create_tenant(session: AsyncSession) -> Tenant:
    result = await session.execute(select(Tenant).where(Tenant.id == TENANT_ID))
    tenant = result.scalar_one_or_none()
    if tenant is None:
        tenant = Tenant(id=TENANT_ID, name="Demo University")
        session.add(tenant)
        await session.flush()
        print(f"  [+] Tenant creado: {tenant.name}")
    else:
        print(f"  [~] Tenant ya existe: {tenant.name}")
    return tenant


async def get_or_create_roles(session: AsyncSession) -> dict[str, Rol]:
    roles: dict[str, Rol] = {}
    for r in ROLES:
        result = await session.execute(
            select(Rol).where(Rol.nombre == r["nombre"], Rol.tenant_id == TENANT_ID)
        )
        rol = result.scalar_one_or_none()
        if rol is None:
            rol = Rol(tenant_id=TENANT_ID, nombre=r["nombre"], descripcion=r["descripcion"])
            session.add(rol)
            await session.flush()
            print(f"  [+] Rol creado: {rol.nombre}")
        else:
            print(f"  [~] Rol ya existe: {rol.nombre}")
        roles[rol.nombre] = rol
    return roles


async def get_or_create_permisos(session: AsyncSession) -> dict[str, Permiso]:
    permisos: dict[str, Permiso] = {}
    for p in PERMISOS:
        result = await session.execute(
            select(Permiso).where(Permiso.nombre == p["nombre"], Permiso.tenant_id == TENANT_ID)
        )
        permiso = result.scalar_one_or_none()
        if permiso is None:
            permiso = Permiso(tenant_id=TENANT_ID, nombre=p["nombre"], descripcion=p["descripcion"])
            session.add(permiso)
            await session.flush()
            print(f"  [+] Permiso creado: {permiso.nombre}")
        else:
            print(f"  [~] Permiso ya existe: {permiso.nombre}")
        permisos[permiso.nombre] = permiso
    return permisos


async def sync_rol_permisos(session: AsyncSession, roles: dict[str, Rol], permisos: dict[str, Permiso]) -> None:
    for rol_nombre, permisos_lista in MAPEO_ROL_PERMISO.items():
        rol = roles[rol_nombre]
        for p_nombre in permisos_lista:
            permiso = permisos[p_nombre]
            result = await session.execute(
                select(RolPermiso).where(
                    RolPermiso.rol_id == rol.id,
                    RolPermiso.permiso_id == permiso.id,
                    RolPermiso.tenant_id == TENANT_ID
                )
            )
            rp = result.scalar_one_or_none()
            if rp is None:
                rp = RolPermiso(tenant_id=TENANT_ID, rol_id=rol.id, permiso_id=permiso.id)
                session.add(rp)
                print(f"     → Rol {rol_nombre} vinculado con Permiso {p_nombre}")


async def get_or_create_usuario(
    session: AsyncSession, data: dict, tenant_id: uuid.UUID
) -> Usuario:
    email_hash = generate_email_hash(data["email"])
    result = await session.execute(
        select(Usuario).where(
            Usuario.tenant_id == tenant_id,
            Usuario.email_hash == email_hash,
        )
    )
    usuario = result.scalar_one_or_none()
    if usuario is None:
        usuario = Usuario(
            tenant_id=tenant_id,
            email=data["email"],
            hashed_password=hash_password(data["password"]),
            nombre=data["nombre"],
            apellidos=data["apellidos"],
            estado="Activo",
        )
        session.add(usuario)
        await session.flush()
        print(f"  [+] Usuario creado: {data['email']}")
    else:
        print(f"  [~] Usuario ya existe: {data['email']}")
    return usuario


async def assign_rol(
    session: AsyncSession, usuario: Usuario, rol: Rol, materia_id = None, cohorte_id = None, comisiones = None
) -> Asignacion:
    result = await session.execute(
        select(Asignacion).where(
            Asignacion.usuario_id == usuario.id,
            Asignacion.rol_id == rol.id,
            Asignacion.materia_id == materia_id,
            Asignacion.cohorte_id == cohorte_id
        )
    )
    asig = result.scalar_one_or_none()
    if asig is None:
        asig = Asignacion(
            tenant_id=usuario.tenant_id,
            usuario_id=usuario.id,
            rol_id=rol.id,
            materia_id=materia_id,
            cohorte_id=cohorte_id,
            comisiones=comisiones,
            desde=datetime.now(timezone.utc).replace(tzinfo=None),
        )
        session.add(asig)
        await session.flush()
        print(f"     → asignado rol {rol.nombre} (materia: {materia_id}, cohorte: {cohorte_id})")
    return asig

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

async def seed() -> None:
    print("\n=== Seed de desarrollo ===\n")
    async with SessionLocal() as session:
        async with session.begin():
            tenant = await get_or_create_tenant(session)
            roles = await get_or_create_roles(session)
            permisos = await get_or_create_permisos(session)
            await sync_rol_permisos(session, roles, permisos)

            # Estructura Académica Básica
            print("\n--- Estructura Académica ---")
            # 1. Carrera
            result_carrera = await session.execute(
                select(Carrera).where(Carrera.codigo == "TUPAD", Carrera.tenant_id == TENANT_ID)
            )
            carrera = result_carrera.scalar_one_or_none()
            if not carrera:
                carrera = Carrera(tenant_id=TENANT_ID, codigo="TUPAD", nombre="Tecnicatura Universitaria en Programación a Distancia")
                session.add(carrera)
                await session.flush()
                print(f"  [+] Carrera creada: {carrera.nombre}")
            else:
                print(f"  [~] Carrera ya existe: {carrera.nombre}")

            # 2. Cohortes
            cohortes_nombres = ["2026-1", "2026-2"]
            cohortes_dict: dict[str, Cohorte] = {}
            for cn in cohortes_nombres:
                result_cohorte = await session.execute(
                    select(Cohorte).where(Cohorte.nombre == cn, Cohorte.tenant_id == TENANT_ID)
                )
                coh = result_cohorte.scalar_one_or_none()
                if not coh:
                    coh = Cohorte(
                        tenant_id=TENANT_ID,
                        carrera_id=carrera.id,
                        nombre=cn,
                        anio=2026,
                        vig_desde=datetime.now(timezone.utc).date()
                    )
                    session.add(coh)
                    await session.flush()
                    print(f"  [+] Cohorte creada: {coh.nombre}")
                else:
                    print(f"  [~] Cohorte ya existe: {coh.nombre}")
                cohortes_dict[cn] = coh

            # 3. Materias
            materias_datos = [
                {"codigo": "PROG1", "nombre": "Programación I"},
                {"codigo": "PROG2", "nombre": "Programación II"},
                {"codigo": "BDD", "nombre": "Bases de Datos"},
            ]
            materias_dict: dict[str, Materia] = {}
            for md in materias_datos:
                result_materia = await session.execute(
                    select(Materia).where(Materia.codigo == md["codigo"], Materia.tenant_id == TENANT_ID)
                )
                mat = result_materia.scalar_one_or_none()
                if not mat:
                    mat = Materia(tenant_id=TENANT_ID, codigo=md["codigo"], nombre=md["nombre"])
                    session.add(mat)
                    await session.flush()
                    print(f"  [+] Materia creada: {mat.nombre}")
                else:
                    print(f"  [~] Materia ya existe: {mat.nombre}")
                materias_dict[md["codigo"]] = mat

            print("\n--- Usuarios y Asignaciones ---")
            usuarios_creados = {}
            for data in USUARIOS:
                usuario = await get_or_create_usuario(session, data, tenant.id)
                usuarios_creados[data["email"]] = usuario
                
                # Asignación global inicial
                await assign_rol(session, usuario, roles[data["rol"]])

            # Asignaciones académicas específicas para simular equipos / comisiones
            docente_user = usuarios_creados["docente@demo.com"]
            coord_user = usuarios_creados["coordinador@demo.com"]
            
            # Asignar Docente a PROG1 en 2026-1 con Comisión A
            await assign_rol(
                session, 
                docente_user, 
                roles["PROFESOR"], 
                materia_id=materias_dict["PROG1"].id, 
                cohorte_id=cohortes_dict["2026-1"].id,
                comisiones=["A"]
            )
            # Asignar Coordinador a PROG1 en 2026-1
            await assign_rol(
                session, 
                coord_user, 
                roles["COORDINADOR"], 
                materia_id=materias_dict["PROG1"].id, 
                cohorte_id=cohortes_dict["2026-1"].id
            )

    print("\n=== Seed completado ===")
    print("\nCuentas disponibles:")
    print("  admin@demo.com       / admin1234")
    print("  coordinador@demo.com / coord1234")
    print("  docente@demo.com     / docente1234")
    print()


if __name__ == "__main__":
    asyncio.run(seed())
