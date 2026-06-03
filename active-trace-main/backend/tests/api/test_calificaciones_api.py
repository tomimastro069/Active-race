import pytest
import uuid
from httpx import ASGITransport, AsyncClient
from datetime import datetime
from app.main import app
from app.core.dependencies import get_db, get_current_user
from app.schemas.auth import CurrentUser
from app.models.tenant import Tenant
from app.models.usuario import Usuario
from app.models.rol import Rol
from app.models.asignacion import Asignacion
from app.models.padron import VersionPadron, EntradaPadron
from app.models.carrera import Carrera
from app.models.materia import Materia
from app.models.cohorte import Cohorte
from app.core.security import generate_email_hash

@pytest.mark.asyncio
async def test_calificaciones_api_flow(db_session, monkeypatch):
    tenant_id = uuid.uuid4()
    actor_id = uuid.uuid4()
    student_id = uuid.uuid4()
    materia_id = uuid.uuid4()
    cohorte_id = uuid.uuid4()

    # Seed Tenant, Actor, Student, Rol, Carrera, Materia, Cohorte
    tenant = Tenant(id=tenant_id, name="API Calificaciones Tenant")
    actor = Usuario(
        id=actor_id,
        tenant_id=tenant_id,
        email="docente_api@example.com",
        email_hash=generate_email_hash("docente_api@example.com"),
        hashed_password="pwd"
    )
    student = Usuario(
        id=student_id,
        tenant_id=tenant_id,
        email="student_api@example.com",
        email_hash=generate_email_hash("student_api@example.com"),
        hashed_password="pwd",
        nombre="Juan",
        apellidos="Perez"
    )
    rol = Rol(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        nombre="PROFESOR"
    )
    carrera = Carrera(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        codigo="ISI",
        nombre="Sistemas",
        estado="Activa"
    )
    materia = Materia(
        id=materia_id,
        tenant_id=tenant_id,
        codigo="AED",
        nombre="Algoritmos",
        estado="Activa"
    )
    cohorte = Cohorte(
        id=cohorte_id,
        tenant_id=tenant_id,
        carrera_id=carrera.id,
        nombre="Cohorte 2026",
        anio=2026,
        vig_desde=datetime.utcnow().date(),
        estado="Activa"
    )
    db_session.add_all([tenant, actor, student, rol, carrera, materia, cohorte])
    await db_session.commit()

    # Seed Assignment for teacher
    asignacion = Asignacion(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        usuario_id=actor_id,
        rol_id=rol.id,
        materia_id=materia_id,
        desde=datetime.utcnow()
    )
    db_session.add(asignacion)
    await db_session.commit()

    # Seed active padron
    version_padron = VersionPadron(
        tenant_id=tenant_id,
        materia_id=materia_id,
        cohorte_id=cohorte_id,
        activa=True
    )
    db_session.add(version_padron)
    await db_session.commit()

    entrada = EntradaPadron(
        tenant_id=tenant_id,
        version_id=version_padron.id,
        usuario_id=student_id,
        email="student_api@example.com",
        nombre="Juan",
        apellidos="Perez"
    )
    db_session.add(entrada)
    await db_session.commit()

    # Mock permissions
    async def mock_get_effective_permissions(*args, **kwargs):
        return ["calificaciones:importar"]
    
    monkeypatch.setattr(
        "app.repositories.asignacion.AsignacionRepository.get_effective_permissions",
        mock_get_effective_permissions
    )

    # Set dependency overrides
    mock_docente = CurrentUser(
        id=actor_id,
        tenant_id=tenant_id,
        email="docente_api@example.com",
        roles=["PROFESOR"]
    )
    app.dependency_overrides[get_db] = lambda: db_session
    app.dependency_overrides[get_current_user] = lambda: mock_docente

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # 1. Preview CSV (POST /api/v1/calificaciones/preview-csv)
        csv_content = b"email,Examen 1 (Real),TP1\nstudent_api@example.com,75,Aprobado\n"
        files = {"file": ("grades.csv", csv_content, "text/csv")}
        res_preview = await ac.post("/api/v1/calificaciones/preview-csv", files=files)
        assert res_preview.status_code == 200
        data_prev = res_preview.json()
        assert len(data_prev["headers"]) == 2
        assert "Examen 1 (Real)" in data_prev["headers"]
        assert len(data_prev["rows"]) == 1
        assert data_prev["rows"][0]["email"] == "student_api@example.com"

        # 2. Import CSV (POST /api/v1/calificaciones/import-csv)
        files_import = {"file": ("grades.csv", csv_content, "text/csv")}
        data_import = {
            "materia_id": str(materia_id),
            "cohorte_id": str(cohorte_id)
        }
        res_import = await ac.post("/api/v1/calificaciones/import-csv", data=data_import, files=files_import)
        assert res_import.status_code == 201
        data_imp = res_import.json()
        assert data_imp["imported_count"] == 2
        assert len(data_imp["unmatched_emails"]) == 0

        # 3. Configure threshold (POST /api/v1/calificaciones/umbral)
        payload_umbral = {
            "materia_id": str(materia_id),
            "umbral_pct": 80,
            "valores_aprobatorios": ["Satisfactorio", "Aprobado"]
        }
        res_umbral = await ac.post("/api/v1/calificaciones/umbral", json=payload_umbral)
        assert res_umbral.status_code == 200
        data_umb = res_umbral.json()
        assert data_umb["umbral_pct"] == 80
        assert data_umb["valores_aprobatorios"] == ["Satisfactorio", "Aprobado"]

        # 4. Get threshold (GET /api/v1/calificaciones/umbral)
        res_get_umb = await ac.get("/api/v1/calificaciones/umbral", params={"materia_id": str(materia_id)})
        assert res_get_umb.status_code == 200
        assert res_get_umb.json()["umbral_pct"] == 80

        # 5. Clear grades (POST /api/v1/calificaciones/vaciar)
        payload_vaciar = {
            "materia_id": str(materia_id)
        }
        res_vaciar = await ac.post("/api/v1/calificaciones/vaciar", json=payload_vaciar)
        assert res_vaciar.status_code == 200
        assert res_vaciar.json()["status"] == "success"

    app.dependency_overrides.clear()
