import pytest
import uuid
from datetime import date, datetime
from sqlalchemy import select

from app.models.tenant import Tenant
from app.models.carrera import Carrera
from app.models.cohorte import Cohorte
from app.models.materia import Materia
from app.models.usuario import Usuario
from app.models.asignacion import Asignacion
from app.models.rol import Rol
from app.models.padron import VersionPadron, EntradaPadron
from app.models.calificacion import Calificacion
from app.models.umbral import UmbralMateria
from app.services.calificacion_service import CalificacionService
from app.core.security import generate_email_hash

@pytest.mark.asyncio
async def test_calificacion_service_full_flow(db_session):
    tenant_id = uuid.uuid4()
    docente_id = uuid.uuid4()
    otro_docente_id = uuid.uuid4()
    student_id = uuid.uuid4()

    # 1. Setup Tenant and Users
    tenant = Tenant(id=tenant_id, name="Test Tenant")
    
    # Docente role setup
    rol_docente = Rol(id=uuid.uuid4(), tenant_id=tenant_id, nombre="PROFESOR")
    
    docente = Usuario(
        id=docente_id,
        tenant_id=tenant_id,
        email="docente@example.com",
        hashed_password="password",
        nombre="Docente",
        apellidos="Test"
    )
    otro_docente = Usuario(
        id=otro_docente_id,
        tenant_id=tenant_id,
        email="otro@example.com",
        hashed_password="password",
        nombre="Otro",
        apellidos="Docente"
    )
    student = Usuario(
        id=student_id,
        tenant_id=tenant_id,
        email="student@example.com",
        hashed_password="password",
        nombre="Juan",
        apellidos="Perez"
    )
    
    carrera = Carrera(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        codigo="ISI",
        nombre="Sistemas",
        estado="Activa"
    )
    db_session.add_all([tenant, rol_docente, docente, otro_docente, student, carrera])
    await db_session.flush()

    cohorte = Cohorte(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        carrera_id=carrera.id,
        nombre="Cohorte 2026",
        anio=2026,
        vig_desde=date(2026, 3, 1),
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
    await db_session.flush()

    # Create active assignments for both teachers
    asignacion = Asignacion(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        usuario_id=docente_id,
        rol_id=rol_docente.id,
        materia_id=materia.id,
        desde=datetime.utcnow()
    )
    asignacion_otro = Asignacion(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        usuario_id=otro_docente_id,
        rol_id=rol_docente.id,
        materia_id=materia.id,
        desde=datetime.utcnow()
    )
    db_session.add_all([asignacion, asignacion_otro])
    await db_session.flush()

    # Setup active VersionPadron and EntradaPadron for the student
    version_padron = VersionPadron(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        materia_id=materia.id,
        cohorte_id=cohorte.id,
        activa=True
    )
    db_session.add(version_padron)
    await db_session.flush()

    entrada_student = EntradaPadron(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        version_id=version_padron.id,
        usuario_id=student_id,
        email="student@example.com",
        nombre="Juan",
        apellidos="Perez"
    )
    db_session.add(entrada_student)
    await db_session.flush()

    # Instantiate Service
    service = CalificacionService(db_session, tenant_id)

    # 2. Test Preview CSV
    csv_grades_content = (
        "email,Examen 1 (Real),Trabajo Practico 1\n"
        "student@example.com,75,Aprobado\n"
        "unmatched@example.com,80,Aprobado\n"
    )
    preview = await service.preview_csv(csv_grades_content)
    assert len(preview.headers) == 2
    assert "Examen 1 (Real)" in preview.headers
    assert "Trabajo Practico 1" in preview.headers
    assert preview.estimated_grades_count == 4

    # 3. Test Import CSV (using default threshold: 60% and ["Satisfactorio", "Supera lo esperado"])
    import_res = await service.importar_calificaciones_csv(
        materia_id=materia.id,
        cohorte_id=cohorte.id,
        docente_id=docente_id,
        file_content=csv_grades_content
    )
    await db_session.flush()

    # 75 >= 60 -> Aprobado
    # "Aprobado" not in ["Satisfactorio", "Supera lo esperado"] -> Desaprobado (aprobado=False)
    assert import_res.imported_count == 2
    assert len(import_res.unmatched_emails) == 1
    assert "unmatched@example.com" in import_res.unmatched_emails

    # Verify database state
    grades = await service.calif_repo.get_calificaciones_by_materia(materia.id, docente_id)
    assert len(grades) == 2
    grade_map = {g.actividad: g for g in grades}
    assert grade_map["Examen 1 (Real)"].nota_numerica == 75.0
    assert grade_map["Examen 1 (Real)"].aprobado is True
    assert grade_map["Examen 1 (Real)"].finalizado is True

    assert grade_map["Trabajo Practico 1"].nota_textual == "Aprobado"
    assert grade_map["Trabajo Practico 1"].aprobado is False

    # 4. Configure custom threshold and re-evaluate
    # Set threshold to 80% and allow "Aprobado" as qualitative passing grade
    await service.configurar_umbral(
        docente_id=docente_id,
        materia_id=materia.id,
        umbral_pct=80,
        valores_aprobatorios=["Satisfactorio", "Aprobado"]
    )
    await db_session.flush()

    # Re-import same grades to verify upsert updates approval based on new thresholds
    import_res_updated = await service.importar_calificaciones_csv(
        materia_id=materia.id,
        cohorte_id=cohorte.id,
        docente_id=docente_id,
        file_content=csv_grades_content
    )
    await db_session.flush()

    # 75 < 80 -> Aprobado=False
    # "Aprobado" in ["Satisfactorio", "Aprobado"] -> Aprobado=True
    grades_updated = await service.calif_repo.get_calificaciones_by_materia(materia.id, docente_id)
    assert len(grades_updated) == 2
    grade_map_updated = {g.actividad: g for g in grades_updated}
    assert grade_map_updated["Examen 1 (Real)"].aprobado is False
    assert grade_map_updated["Trabajo Practico 1"].aprobado is True

    # 5. Test Import Completion Report CSV
    # Qualitatives not yet graded are set with finalizado=True, nota_textual=None, aprobado=False
    csv_completion_content = (
        "email,Trabajo Practico 2\n"
        "student@example.com,Completado\n"
    )
    completion_res = await service.importar_finalizaciones_csv(
        materia_id=materia.id,
        cohorte_id=cohorte.id,
        docente_id=docente_id,
        file_content=csv_completion_content
    )
    await db_session.flush()

    assert completion_res.imported_count == 1
    grades_after_completion = await service.calif_repo.get_calificaciones_by_materia(materia.id, docente_id)
    assert len(grades_after_completion) == 3
    grade_map_completion = {g.actividad: g for g in grades_after_completion}
    assert grade_map_completion["Trabajo Practico 2"].finalizado is True
    assert grade_map_completion["Trabajo Practico 2"].es_numerica is False
    assert grade_map_completion["Trabajo Practico 2"].nota_textual is None
    assert grade_map_completion["Trabajo Practico 2"].aprobado is False

    # 6. Test isolated clear (vaciado)
    # Teacher B imports a grade first
    csv_otro_content = (
        "email,Examen 1 (Real)\n"
        "student@example.com,90\n"
    )
    await service.importar_calificaciones_csv(
        materia_id=materia.id,
        cohorte_id=cohorte.id,
        docente_id=otro_docente_id,
        file_content=csv_otro_content
    )
    await db_session.flush()

    # Verify Teacher B has 1 grade
    otro_grades = await service.calif_repo.get_calificaciones_by_materia(materia.id, otro_docente_id)
    assert len(otro_grades) == 1

    # Clear grades of Teacher A
    await service.vaciar_calificaciones(materia.id, docente_id)
    await db_session.flush()

    # Teacher A should have 0 active grades (logical delete)
    active_grades_a = await service.calif_repo.get_calificaciones_by_materia(materia.id, docente_id)
    assert len(active_grades_a) == 0

    # Teacher B's grade must remain untouched (isolation RN-04)
    active_grades_b = await service.calif_repo.get_calificaciones_by_materia(materia.id, otro_docente_id)
    assert len(active_grades_b) == 1
