import pytest
import uuid
from datetime import datetime
from app.models.tenant import Tenant
from app.models.usuario import Usuario
from app.models.padron import VersionPadron, EntradaPadron
from app.models.materia import Materia
from app.models.cohorte import Cohorte
from app.models.carrera import Carrera
from app.repositories.calificacion import CalificacionRepository

@pytest.mark.asyncio
async def test_calificacion_repository_operations(db_session):
    tenant_id = uuid.uuid4()
    docente_a_id = uuid.uuid4()
    docente_b_id = uuid.uuid4()
    student_id = uuid.uuid4()

    # Setup database records
    tenant = Tenant(id=tenant_id, name="Test Repositories Tenant")
    docente_a = Usuario(
        id=docente_a_id,
        tenant_id=tenant_id,
        email="docente_a@example.com",
        hashed_password="pwd"
    )
    docente_b = Usuario(
        id=docente_b_id,
        tenant_id=tenant_id,
        email="docente_b@example.com",
        hashed_password="pwd"
    )
    student = Usuario(
        id=student_id,
        tenant_id=tenant_id,
        email="student_rep@example.com",
        hashed_password="pwd"
    )
    carrera = Carrera(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        codigo="ISI",
        nombre="Sistemas",
        estado="Activa"
    )
    db_session.add_all([tenant, docente_a, docente_b, student, carrera])
    await db_session.commit()

    cohorte = Cohorte(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        carrera_id=carrera.id,
        nombre="Cohorte 2026",
        anio=2026,
        vig_desde=datetime.utcnow().date(),
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

    version_padron = VersionPadron(
        tenant_id=tenant_id,
        materia_id=materia.id,
        cohorte_id=cohorte.id,
        activa=True
    )
    db_session.add(version_padron)
    await db_session.commit()

    entrada = EntradaPadron(
        tenant_id=tenant_id,
        version_id=version_padron.id,
        usuario_id=student_id,
        email="student_rep@example.com",
        nombre="Juan",
        apellidos="Perez"
    )
    db_session.add(entrada)
    await db_session.commit()

    repo = CalificacionRepository(db_session, tenant_id)

    # 1. Bulk upsert grades for Docente A
    grades_data = [
        {
            "entrada_padron_id": entrada.id,
            "actividad": "TP1",
            "nota_numerica": 8.5,
            "nota_textual": None,
            "aprobado": True,
            "finalizado": True,
            "es_numerica": True,
            "origen": "Importado"
        },
        {
            "entrada_padron_id": entrada.id,
            "actividad": "TP2",
            "nota_numerica": None,
            "nota_textual": "Satisfactorio",
            "aprobado": True,
            "finalizado": True,
            "es_numerica": False,
            "origen": "Importado"
        }
    ]
    upserted_count = await repo.bulk_upsert_calificaciones(materia.id, docente_a_id, grades_data)
    assert upserted_count == 2

    # 2. Get and verify
    tp1 = await repo.get_calificacion(entrada.id, materia.id, docente_a_id, "TP1")
    assert tp1 is not None
    assert tp1.nota_numerica == 8.5
    assert tp1.aprobado is True

    # 3. Upsert again (Update TP1 grade)
    grades_data_update = [
        {
            "entrada_padron_id": entrada.id,
            "actividad": "TP1",
            "nota_numerica": 4.0,  # Updated note
            "nota_textual": None,
            "aprobado": False,  # Changed approval
            "finalizado": True,
            "es_numerica": True,
            "origen": "Importado"
        }
    ]
    await repo.bulk_upsert_calificaciones(materia.id, docente_a_id, grades_data_update)
    
    tp1_updated = await repo.get_calificacion(entrada.id, materia.id, docente_a_id, "TP1")
    assert tp1_updated.nota_numerica == 4.0
    assert tp1_updated.aprobado is False

    # 4. Docente B imports grade for same student/activity/subject
    grades_docente_b = [
        {
            "entrada_padron_id": entrada.id,
            "actividad": "TP1",
            "nota_numerica": 10.0,
            "nota_textual": None,
            "aprobado": True,
            "finalizado": True,
            "es_numerica": True,
            "origen": "Importado"
        }
    ]
    await repo.bulk_upsert_calificaciones(materia.id, docente_b_id, grades_docente_b)

    # 5. Clear (vaciado) for Docente A
    cleared_count = await repo.vaciar_calificaciones(materia.id, docente_a_id)
    assert cleared_count == 2  # tp1 and tp2 cleared

    # Verify Docente A has 0 active grades
    grades_a = await repo.get_calificaciones_by_materia(materia.id, docente_a_id)
    assert len(grades_a) == 0

    # Verify Docente B still has active grade (isolation RN-04)
    grades_b = await repo.get_calificaciones_by_materia(materia.id, docente_b_id)
    assert len(grades_b) == 1
    assert grades_b[0].nota_numerica == 10.0


@pytest.mark.asyncio
async def test_new_calificacion_repository_helpers(db_session):
    tenant_id = uuid.uuid4()
    docente_id = uuid.uuid4()
    student_id = uuid.uuid4()

    tenant = Tenant(id=tenant_id, name="Test Helpers Tenant")
    docente = Usuario(id=docente_id, tenant_id=tenant_id, email="helpers_doc@example.com", hashed_password="pwd")
    student = Usuario(id=student_id, tenant_id=tenant_id, email="helpers_stu@example.com", hashed_password="pwd")
    carrera = Carrera(id=uuid.uuid4(), tenant_id=tenant_id, codigo="ISI", nombre="Sistemas", estado="Activa")
    
    db_session.add_all([tenant, docente, student, carrera])
    await db_session.commit()

    cohorte = Cohorte(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        carrera_id=carrera.id,
        nombre="Cohorte 2026",
        anio=2026,
        vig_desde=datetime.utcnow().date(),
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

    version_padron = VersionPadron(
        tenant_id=tenant_id,
        materia_id=materia.id,
        cohorte_id=cohorte.id,
        activa=True
    )
    db_session.add(version_padron)
    await db_session.commit()

    entrada = EntradaPadron(
        tenant_id=tenant_id,
        version_id=version_padron.id,
        usuario_id=student_id,
        email="helpers_stu@example.com",
        nombre="Juan",
        apellidos="Perez"
    )
    db_session.add(entrada)
    await db_session.commit()

    repo = CalificacionRepository(db_session, tenant_id)

    # Insert qualitative ungraded qualification (finalizado=True, nota_numerica=None, nota_textual=None, es_numerica=False)
    grades_data = [
        {
            "entrada_padron_id": entrada.id,
            "actividad": "TP_Ungraded",
            "nota_numerica": None,
            "nota_textual": None,
            "aprobado": False,
            "finalizado": True,
            "es_numerica": False,
            "origen": "Importado"
        },
        {
            "entrada_padron_id": entrada.id,
            "actividad": "TP_Graded_Num",
            "nota_numerica": 8.0,
            "nota_textual": None,
            "aprobado": True,
            "finalizado": True,
            "es_numerica": True,
            "origen": "Importado"
        }
    ]
    await repo.bulk_upsert_calificaciones(materia.id, docente_id, grades_data)

    # 1. Test get_distinct_activities
    activities = await repo.get_distinct_activities(materia.id, docente_id)
    assert set(activities) == {"TP_Ungraded", "TP_Graded_Num"}

    # 2. Test get_ungraded_textual_calificaciones
    ungraded = await repo.get_ungraded_textual_calificaciones(materia.id, docente_id)
    assert len(ungraded) == 1
    assert ungraded[0].actividad == "TP_Ungraded"

