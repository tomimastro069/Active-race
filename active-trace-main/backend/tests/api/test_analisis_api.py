import pytest
import uuid
from httpx import ASGITransport, AsyncClient
from datetime import datetime, timezone, timedelta
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
from app.models.calificacion import Calificacion
from app.models.umbral import UmbralMateria

@pytest.mark.asyncio
async def test_analisis_api_endpoints(db_session, monkeypatch):
    tenant_id = uuid.uuid4()
    actor_id = uuid.uuid4()
    student_id = uuid.uuid4()
    materia_id = uuid.uuid4()
    cohorte_id = uuid.uuid4()

    # Seed entities
    tenant = Tenant(id=tenant_id, name="API Analisis Tenant")
    actor = Usuario(id=actor_id, tenant_id=tenant_id, email="teacher_api@example.com", hashed_password="pwd")
    student = Usuario(id=student_id, tenant_id=tenant_id, email="student_api@example.com", hashed_password="pwd", nombre="Juan", apellidos="Perez")
    rol = Rol(id=uuid.uuid4(), tenant_id=tenant_id, nombre="PROFESOR")
    carrera = Carrera(id=uuid.uuid4(), tenant_id=tenant_id, codigo="ISI", nombre="Sistemas", estado="Activa")
    materia = Materia(id=materia_id, tenant_id=tenant_id, codigo="AED", nombre="Algoritmos", estado="Activa")
    cohorte = Cohorte(id=cohorte_id, tenant_id=tenant_id, carrera_id=carrera.id, nombre="Cohorte 2026", anio=2026, vig_desde=datetime.now(timezone.utc).date(), estado="Activa")
    
    db_session.add_all([tenant, actor, student, rol, carrera, materia, cohorte])
    await db_session.commit()

    asignacion = Asignacion(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        usuario_id=actor_id,
        rol_id=rol.id,
        materia_id=materia_id,
        desde=(datetime.now(timezone.utc) - timedelta(days=1)).replace(tzinfo=None)
    )
    db_session.add(asignacion)
    await db_session.commit()

    version_padron = VersionPadron(tenant_id=tenant_id, materia_id=materia_id, cohorte_id=cohorte_id, activa=True)
    db_session.add(version_padron)
    await db_session.commit()

    entrada = EntradaPadron(tenant_id=tenant_id, version_id=version_padron.id, usuario_id=student_id, email="student_api@example.com", nombre="Juan", apellidos="Perez", comision="Comision A")
    db_session.add(entrada)
    await db_session.commit()

    # Seed some grades: student has numeric grade 50 on TP1 (below default threshold 60)
    c1 = Calificacion(
        tenant_id=tenant_id,
        entrada_padron_id=entrada.id,
        materia_id=materia_id,
        docente_id=actor_id,
        actividad="TP1",
        nota_numerica=50.0,
        aprobado=False,
        finalizado=True,
        es_numerica=True
    )
    db_session.add(c1)
    await db_session.commit()

    # Mock permissions
    async def mock_get_effective_permissions(*args, **kwargs):
        return ["atrasados:ver", "atrasados:ver_propio"]
    
    monkeypatch.setattr(
        "app.repositories.asignacion.AsignacionRepository.get_effective_permissions",
        mock_get_effective_permissions
    )

    # Set dependency overrides
    mock_docente = CurrentUser(
        id=actor_id,
        tenant_id=tenant_id,
        email="teacher_api@example.com",
        roles=["PROFESOR"]
    )
    app.dependency_overrides[get_db] = lambda: db_session
    app.dependency_overrides[get_current_user] = lambda: mock_docente

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # 1. GET /api/v1/analisis/atrasados
        res = await ac.get("/api/v1/analisis/atrasados", params={"materia_id": str(materia_id), "cohorte_id": str(cohorte_id)})
        assert res.status_code == 200
        data = res.json()
        assert len(data) == 1
        assert data[0]["actividad"] == "TP1"
        assert data[0]["motivo"] == "Nota menor al umbral"

        # 2. GET /api/v1/analisis/ranking
        res_rank = await ac.get("/api/v1/analisis/ranking", params={"materia_id": str(materia_id), "cohorte_id": str(cohorte_id)})
        assert res_rank.status_code == 200
        # Student 1 has 0 approved activities, so ranking is empty
        assert len(res_rank.json()) == 0

        # 3. GET /api/v1/analisis/reporte-rapido
        res_rep = await ac.get("/api/v1/analisis/reporte-rapido", params={"materia_id": str(materia_id), "cohorte_id": str(cohorte_id)})
        assert res_rep.status_code == 200
        assert res_rep.json()["total_alumnos"] == 1

        # 4. GET /api/v1/analisis/notas-finales
        res_nf = await ac.get("/api/v1/analisis/notas-finales", params={"materia_id": str(materia_id), "cohorte_id": str(cohorte_id)})
        assert res_nf.status_code == 200
        assert len(res_nf.json()) == 1

        # 5. GET /api/v1/analisis/tps-sin-corregir
        res_tps = await ac.get("/api/v1/analisis/tps-sin-corregir", params={"materia_id": str(materia_id), "cohorte_id": str(cohorte_id)})
        assert res_tps.status_code == 200
        assert len(res_tps.json()) == 0

        # 6. GET /api/v1/analisis/tps-sin-corregir/export
        res_exp = await ac.get("/api/v1/analisis/tps-sin-corregir/export", params={"materia_id": str(materia_id), "cohorte_id": str(cohorte_id)})
        assert res_exp.status_code == 200
        assert "text/csv" in res_exp.headers["content-type"]

        # 7. GET /api/v1/analisis/monitor
        res_mon = await ac.get("/api/v1/analisis/monitor", params={"materia_id": str(materia_id), "cohorte_id": str(cohorte_id)})
        assert res_mon.status_code == 200
        assert len(res_mon.json()) == 1

    app.dependency_overrides.clear()
