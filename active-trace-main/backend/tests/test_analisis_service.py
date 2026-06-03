import pytest
import uuid
from datetime import date, datetime, timedelta, timezone
from app.models.tenant import Tenant
from app.models.carrera import Carrera
from app.models.cohorte import Cohorte
from app.models.materia import Materia
from app.models.usuario import Usuario
from app.models.asignacion import Asignacion
from app.models.rol import Rol
from app.models.rol_permiso import RolPermiso
from app.models.permiso import Permiso
from app.models.padron import VersionPadron, EntradaPadron
from app.models.calificacion import Calificacion
from app.models.umbral import UmbralMateria
from app.services.analisis_service import AnalisisService
from app.schemas.auth import CurrentUser

@pytest.fixture
async def setup_data(db_session):
    tenant_id = uuid.uuid4()
    tenant = Tenant(id=tenant_id, name="Test Analytics Tenant")
    
    rol_docente = Rol(id=uuid.uuid4(), tenant_id=tenant_id, nombre="PROFESOR")
    rol_admin = Rol(id=uuid.uuid4(), tenant_id=tenant_id, nombre="ADMIN")
    
    perm_ver_propio = Permiso(id=uuid.uuid4(), tenant_id=tenant_id, nombre="atrasados:ver_propio")
    perm_ver_todos = Permiso(id=uuid.uuid4(), tenant_id=tenant_id, nombre="atrasados:ver")
    
    rp1 = RolPermiso(tenant_id=tenant_id, rol_id=rol_docente.id, permiso_id=perm_ver_propio.id)
    rp2 = RolPermiso(tenant_id=tenant_id, rol_id=rol_admin.id, permiso_id=perm_ver_todos.id)
    
    docente_user = Usuario(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        email="teacher@example.com",
        hashed_password="pwd",
        nombre="Teacher",
        apellidos="One"
    )
    admin_user = Usuario(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        email="admin@example.com",
        hashed_password="pwd",
        nombre="Admin",
        apellidos="One"
    )
    student_user_1 = Usuario(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        email="stu1@example.com",
        hashed_password="pwd",
        nombre="Student",
        apellidos="One"
    )
    student_user_2 = Usuario(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        email="stu2@example.com",
        hashed_password="pwd",
        nombre="Student",
        apellidos="Two"
    )
    
    carrera = Carrera(id=uuid.uuid4(), tenant_id=tenant_id, codigo="ISI", nombre="Sistemas", estado="Activa")
    
    db_session.add_all([tenant, rol_docente, rol_admin, perm_ver_propio, perm_ver_todos, rp1, rp2, docente_user, admin_user, student_user_1, student_user_2, carrera])
    await db_session.commit()
    
    cohorte = Cohorte(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        carrera_id=carrera.id,
        nombre="Cohorte 2026",
        anio=2026,
        vig_desde=datetime.now(timezone.utc).date(),
        estado="Activa"
    )
    materia = Materia(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        codigo="AED",
        nombre="Algoritmos",
        estado="Activa"
    )
    db_session.add_all([cohorte, materia])
    await db_session.commit()
    
    asignacion_docente = Asignacion(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        usuario_id=docente_user.id,
        rol_id=rol_docente.id,
        materia_id=materia.id,
        desde=(datetime.now(timezone.utc) - timedelta(days=1)).replace(tzinfo=None)
    )
    asignacion_admin = Asignacion(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        usuario_id=admin_user.id,
        rol_id=rol_admin.id,
        materia_id=None,
        desde=(datetime.now(timezone.utc) - timedelta(days=1)).replace(tzinfo=None)
    )
    db_session.add_all([asignacion_docente, asignacion_admin])
    await db_session.commit()
    
    # Configure threshold for teacher
    umbral = UmbralMateria(

        id=uuid.uuid4(),
        tenant_id=tenant_id,
        asignacion_id=asignacion_docente.id,
        materia_id=materia.id,
        umbral_pct=60,
        valores_aprobatorios=["Satisfactorio"]
    )
    db_session.add(umbral)
    await db_session.commit()
    
    version_padron = VersionPadron(
        tenant_id=tenant_id,
        materia_id=materia.id,
        cohorte_id=cohorte.id,
        activa=True
    )
    db_session.add(version_padron)
    await db_session.commit()
    
    entrada1 = EntradaPadron(
        tenant_id=tenant_id,
        version_id=version_padron.id,
        usuario_id=student_user_1.id,
        email="stu1@example.com",
        nombre="Student",
        apellidos="One",
        comision="Comision A"
    )
    entrada2 = EntradaPadron(
        tenant_id=tenant_id,
        version_id=version_padron.id,
        usuario_id=student_user_2.id,
        email="stu2@example.com",
        nombre="Student",
        apellidos="Two",
        comision="Comision B"
    )
    db_session.add_all([entrada1, entrada2])
    await db_session.commit()
    
    return {
        "tenant_id": tenant_id,
        "docente_id": docente_user.id,
        "admin_id": admin_user.id,
        "materia_id": materia.id,
        "cohorte_id": cohorte.id,
        "entrada1": entrada1,
        "entrada2": entrada2,
        "docente_user": docente_user,
        "admin_user": admin_user
    }

@pytest.mark.asyncio
async def test_analisis_service_alumnos_atrasados(db_session, setup_data):
    data = setup_data
    tenant_id = data["tenant_id"]
    materia_id = data["materia_id"]
    cohorte_id = data["cohorte_id"]
    
    # Setup qualifications
    # Student 1: TP1 numeric 70 (approved), TP2 missing (not in DB)
    # Student 2: TP1 numeric 50 (below threshold 60)
    c1 = Calificacion(
        tenant_id=tenant_id,
        entrada_padron_id=data["entrada1"].id,
        materia_id=materia_id,
        docente_id=data["docente_id"],
        actividad="TP1",
        nota_numerica=70.0,
        aprobado=True,
        finalizado=True,
        es_numerica=True
    )
    c2 = Calificacion(
        tenant_id=tenant_id,
        entrada_padron_id=data["entrada2"].id,
        materia_id=materia_id,
        docente_id=data["docente_id"],
        actividad="TP1",
        nota_numerica=50.0,
        aprobado=False,
        finalizado=True,
        es_numerica=True
    )
    db_session.add_all([c1, c2])
    await db_session.commit()
    
    service = AnalisisService(db_session, tenant_id)
    curr_user = CurrentUser(id=data["docente_id"], tenant_id=tenant_id, email="teacher@example.com")
    
    # We call obtener_alumnos_atrasados. For activities, we get the list of unique activities from the DB.
    # The unique activities in DB are "TP1" only. Student 1 has TP1 approved, so not delayed.
    # Student 2 has TP1 below threshold (50 < 60), so delayed.
    atrasados = await service.obtener_alumnos_atrasados(materia_id, cohorte_id, curr_user)
    
    assert len(atrasados) == 1
    assert atrasados[0]["padron_id"] == data["entrada2"].id
    assert atrasados[0]["motivo"] == "Nota menor al umbral"
    assert atrasados[0]["actividad"] == "TP1"

@pytest.mark.asyncio
async def test_analisis_service_ranking_aprobados(db_session, setup_data):
    data = setup_data
    tenant_id = data["tenant_id"]
    materia_id = data["materia_id"]
    cohorte_id = data["cohorte_id"]
    
    # Student 1: 2 approved
    # Student 2: 0 approved
    c1 = Calificacion(
        tenant_id=tenant_id,
        entrada_padron_id=data["entrada1"].id,
        materia_id=materia_id,
        docente_id=data["docente_id"],
        actividad="TP1",
        nota_numerica=80.0,
        aprobado=True,
        finalizado=True
    )
    c2 = Calificacion(
        tenant_id=tenant_id,
        entrada_padron_id=data["entrada1"].id,
        materia_id=materia_id,
        docente_id=data["docente_id"],
        actividad="TP2",
        nota_numerica=90.0,
        aprobado=True,
        finalizado=True
    )
    c3 = Calificacion(
        tenant_id=tenant_id,
        entrada_padron_id=data["entrada2"].id,
        materia_id=materia_id,
        docente_id=data["docente_id"],
        actividad="TP1",
        nota_numerica=40.0,
        aprobado=False,
        finalizado=True
    )
    db_session.add_all([c1, c2, c3])
    await db_session.commit()
    
    service = AnalisisService(db_session, tenant_id)
    curr_user = CurrentUser(id=data["docente_id"], tenant_id=tenant_id, email="teacher@example.com")
    
    ranking = await service.obtener_ranking_aprobados(materia_id, cohorte_id, curr_user)
    
    # Student 2 should be excluded because approved count is 0 (RN-09)
    assert len(ranking) == 1
    assert ranking[0]["padron_id"] == data["entrada1"].id
    assert ranking[0]["actividades_aprobadas"] == 2

@pytest.mark.asyncio
async def test_analisis_service_tps_sin_corregir(db_session, setup_data):
    data = setup_data
    tenant_id = data["tenant_id"]
    materia_id = data["materia_id"]
    cohorte_id = data["cohorte_id"]
    
    # qualitative TP, finalizado=True, but ungraded (nota_textual and nota_numerica are None, es_numerica=False)
    c1 = Calificacion(
        tenant_id=tenant_id,
        entrada_padron_id=data["entrada1"].id,
        materia_id=materia_id,
        docente_id=data["docente_id"],
        actividad="TP_Qual",
        nota_numerica=None,
        nota_textual=None,
        aprobado=False,
        finalizado=True,
        es_numerica=False
    )
    db_session.add(c1)
    await db_session.commit()
    
    service = AnalisisService(db_session, tenant_id)
    curr_user = CurrentUser(id=data["docente_id"], tenant_id=tenant_id, email="teacher@example.com")
    
    tps = await service.obtener_tps_sin_corregir(materia_id, cohorte_id, curr_user)
    assert len(tps) == 1
    assert tps[0]["actividad"] == "TP_Qual"


@pytest.mark.asyncio
async def test_analisis_service_reporte_rapido_y_notas_finales(db_session, setup_data):
    data = setup_data
    tenant_id = data["tenant_id"]
    materia_id = data["materia_id"]
    cohorte_id = data["cohorte_id"]
    
    c1 = Calificacion(
        tenant_id=tenant_id,
        entrada_padron_id=data["entrada1"].id,
        materia_id=materia_id,
        docente_id=data["docente_id"],
        actividad="TP1",
        nota_numerica=90.0,
        aprobado=True,
        finalizado=True
    )
    db_session.add(c1)
    await db_session.commit()
    
    service = AnalisisService(db_session, tenant_id)
    curr_user = CurrentUser(id=data["docente_id"], tenant_id=tenant_id, email="teacher@example.com")
    
    # 1. Reporte Rápido
    reporte = await service.obtener_reporte_rapido(materia_id, cohorte_id, curr_user)
    assert reporte["total_alumnos"] == 2
    assert reporte["total_calificaciones"] == 1
    assert reporte["tasa_aprobacion"] == 100.0
    
    # 2. Notas Finales
    notas = await service.obtener_notas_finales(materia_id, cohorte_id, curr_user)
    assert len(notas) == 2
    # Find student 1
    s1_entry = next(n for n in notas if n["padron_id"] == data["entrada1"].id)
    assert "TP1" in s1_entry["calificaciones"]
    assert s1_entry["calificaciones"]["TP1"]["nota"] == 90.0
    assert s1_entry["calificaciones"]["TP1"]["aprobado"] is True


@pytest.mark.asyncio
async def test_analisis_service_monitor_general(db_session, setup_data):
    data = setup_data
    tenant_id = data["tenant_id"]
    materia_id = data["materia_id"]
    cohorte_id = data["cohorte_id"]
    
    c1 = Calificacion(
        tenant_id=tenant_id,
        entrada_padron_id=data["entrada1"].id,
        materia_id=materia_id,
        docente_id=data["docente_id"],
        actividad="TP1",
        nota_numerica=85.0,
        aprobado=True,
        finalizado=True,
        importado_at=datetime.now(timezone.utc).replace(tzinfo=None)
    )
    db_session.add(c1)
    await db_session.commit()
    
    service = AnalisisService(db_session, tenant_id)
    curr_user = CurrentUser(id=data["docente_id"], tenant_id=tenant_id, email="teacher@example.com")
    
    # Monitor general
    monitor = await service.obtener_monitor_general(
        current_user=curr_user,
        materia_id=materia_id,
        cohorte_id=cohorte_id,
        comision="Comision A"
    )
    assert len(monitor) == 1
    assert monitor[0]["padron_id"] == data["entrada1"].id
    assert monitor[0]["estado"] == "Aprobado"
    assert monitor[0]["nota"] == 85.0


@pytest.mark.asyncio
async def test_analisis_service_permission_boundaries(db_session, setup_data):
    data = setup_data
    tenant_id = data["tenant_id"]
    materia_id = data["materia_id"]
    cohorte_id = data["cohorte_id"]
    
    service = AnalisisService(db_session, tenant_id)
    
    # 1. Admin (with atrasados:ver) can query with any docente_id
    admin_curr_user = CurrentUser(id=data["admin_id"], tenant_id=tenant_id, email="admin@example.com")
    doc_filter = await service._check_access_and_get_docente_filter(admin_curr_user, materia_id, docente_id=uuid.uuid4())
    # Should not raise any error, and return the passed docente_id
    assert doc_filter is not None
    
    # 2. Teacher (with only atrasados:ver_propio) cannot query other docente_id
    teacher_curr_user = CurrentUser(id=data["docente_id"], tenant_id=tenant_id, email="teacher@example.com")
    with pytest.raises(ValueError, match="No tiene permiso para ver información de otros docentes"):
        await service._check_access_and_get_docente_filter(teacher_curr_user, materia_id, docente_id=uuid.uuid4())
        
    # 3. User with no permissions raises error
    no_perm_user = CurrentUser(id=uuid.uuid4(), tenant_id=tenant_id, email="noperm@example.com")
    with pytest.raises(ValueError, match="Permisos insuficientes"):
        await service._check_access_and_get_docente_filter(no_perm_user, materia_id)

