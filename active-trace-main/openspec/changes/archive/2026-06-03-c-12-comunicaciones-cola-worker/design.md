# Design: C-12 — comunicaciones-cola-worker

> Grounded in the REAL codebase patterns (verified against actual files). Design corrections take precedence over spec assumptions.

---

## 0. Codebase Reality Checks (corrections vs. spec)

**The apply agent MUST follow these — verified by reading actual files:**

1. **FK targets**: `materia_id` → `materias.id` (table is **plural**). `enviado_por` → `usuario.id`. `tenant_id` mixin column: no explicit FK constraint (follow existing convention).
2. **`ServiceError` does NOT exist**: `app/core/exceptions.py` is an empty placeholder. C-12 must CREATE it.
3. **`require_permission` IS the user-yielding dependency**: pattern is `current_user: CurrentUser = Depends(require_permission("modulo:accion"))`. NO separate `get_current_user` + `require_permission` split.
4. **Service constructor**: `__init__(self, db: AsyncSession, tenant_id: UUID)`. Methods do NOT take `session` as parameter — use `self.db`.
5. **Repository constructor**: `__init__(self, session, tenant_id)` → `super().__init__(Model, session, tenant_id)`. Methods use `self.session`.
6. **Router registration**: in `app/main.py` via `include_router`. `routers/__init__.py` is empty and unused.
7. **UUID import**: use `from sqlalchemy.dialects.postgresql import UUID as SQLAlchemyUUID` (consistent with `calificacion.py`).
8. **`generate_email_hash`**: returns 64-char HMAC-SHA256 hex digest → matches `String(64)`.
9. **`aiosmtplib`**: ABSENT from `pyproject.toml` — must add `"aiosmtplib>=3.0.0"`.
10. **Migration head**: `fbbfb2cc45f9` confirmed (down_revision `0c396488b5e9`).
11. **Tests**: use `Base.metadata.create_all`. `Comunicacion` must be imported in `app/models/__init__.py`.

---

## 1. Layer Architecture

```
HTTP endpoints:
  Client → Router → Service → Repository → Model/DB

Worker (system-level, parallel):
  run_worker() → recover_stuck(session) → poll_once(session) → dispatch_one(row, session)
                                                              → ComunicacionRepository (cross-tenant)
                                                              → AuditService
```

Unidirectional: Router has NO business logic. Service has NO direct DB access. Repository has NO domain logic.

---

## 2. SQLAlchemy Model

```python
# backend/app/models/comunicacion.py
import enum
from sqlalchemy import Column, String, Text, Integer, Boolean, DateTime, ForeignKey, Index, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID as SQLAlchemyUUID
from app.models.base import Base, TimestampedTenant
from app.core.types import EncryptedString

class EstadoComunicacion(str, enum.Enum):
    PENDIENTE = "Pendiente"
    ENVIANDO  = "Enviando"
    ENVIADO   = "Enviado"
    ERROR     = "Error"
    CANCELADO = "Cancelado"

class Comunicacion(Base, TimestampedTenant):
    __tablename__ = "comunicacion"

    enviado_por = Column(SQLAlchemyUUID(as_uuid=True), ForeignKey("usuario.id", ondelete="CASCADE"), nullable=False)
    materia_id  = Column(SQLAlchemyUUID(as_uuid=True), ForeignKey("materias.id", ondelete="CASCADE"), nullable=False)  # plural!
    destinatario      = Column(EncryptedString, nullable=False)   # NEVER log or expose
    destinatario_hash = Column(String(64), nullable=False, index=True)
    asunto      = Column(String(500), nullable=False)
    cuerpo      = Column(Text, nullable=False)
    estado      = Column(SAEnum(EstadoComunicacion, name="estadocomunicacion"), nullable=False, default=EstadoComunicacion.PENDIENTE)
    lote_id     = Column(SQLAlchemyUUID(as_uuid=True), nullable=True)
    aprobado    = Column(Boolean, nullable=False, default=False)
    enviado_at  = Column(DateTime, nullable=True)
    intentos    = Column(Integer, nullable=False, default=0)
    max_intentos = Column(Integer, nullable=False, default=3)

    __table_args__ = (
        Index("idx_comunicacion_tenant_estado", "tenant_id", "estado"),
        Index("idx_comunicacion_lote_id", "lote_id"),
        Index("idx_comunicacion_tenant_enviado_por", "tenant_id", "enviado_por"),
        Index("idx_comunicacion_destinatario_hash", "destinatario_hash"),
    )

    def __repr__(self):
        # NEVER include destinatario in repr
        return f"<Comunicacion(id={self.id!r}, estado={self.estado!r}, hash={self.destinatario_hash!r})>"
```

---

## 3. ComunicacionRepository

```python
# backend/app/repositories/comunicacion.py
class ComunicacionRepository(BaseRepository[Comunicacion]):
    def __init__(self, session, tenant_id):
        super().__init__(Comunicacion, session, tenant_id)

    async def list_by_lote(self, lote_id: UUID) -> list[Comunicacion]:
        """Tenant-scoped."""
        q = select(self.model).where(self.model.lote_id == lote_id)
        return list((await self.session.execute(self._apply_tenant_scope(q))).scalars().all())

    async def list_by_estado_sistema(self, estado: EstadoComunicacion) -> list[Comunicacion]:
        """SYSTEM-LEVEL — cross-tenant. Used by worker crash recovery only. No tenant scope."""
        q = select(self.model).where(and_(self.model.estado == estado, self.model.deleted_at.is_(None)))
        return list((await self.session.execute(q)).scalars().all())

    async def list_dispatchable(self) -> list[Comunicacion]:
        """SYSTEM-LEVEL — cross-tenant. PENDIENTE AND aprobado=True AND not deleted. Worker only."""
        q = select(self.model).where(and_(
            self.model.estado == EstadoComunicacion.PENDIENTE,
            self.model.aprobado.is_(True),
            self.model.deleted_at.is_(None),
        ))
        return list((await self.session.execute(q)).scalars().all())

    async def list_filtered(self, estado=None, lote_id=None, enviado_por=None, skip=0, limit=100):
        """Tenant-scoped, paginated."""
        q = select(self.model)
        if estado: q = q.where(self.model.estado == estado)
        if lote_id: q = q.where(self.model.lote_id == lote_id)
        if enviado_por: q = q.where(self.model.enviado_por == enviado_por)
        q = self._apply_tenant_scope(q).offset(skip).limit(limit)
        return list((await self.session.execute(q)).scalars().all())

    async def lote_resumen(self, lote_id: UUID) -> dict[str, int]:
        """Aggregate by estado for a lote (tenant-scoped)."""
        q = select(self.model.estado, func.count()).where(self.model.lote_id == lote_id).group_by(self.model.estado)
        q = self._apply_tenant_scope(q)
        return {e.value: c for e, c in (await self.session.execute(q)).all()}

    async def bulk_approve_lote(self, lote_id: UUID) -> int:
        rows = await self.list_by_lote(lote_id)
        n = sum(1 for r in rows if r.estado == EstadoComunicacion.PENDIENTE and not r.aprobado
                and setattr(r, 'aprobado', True) is None)
        await self.session.flush()
        return n

    async def bulk_cancel_lote(self, lote_id: UUID) -> int:
        rows = await self.list_by_lote(lote_id)
        n = 0
        for r in rows:
            if r.estado == EstadoComunicacion.PENDIENTE:
                r.estado = EstadoComunicacion.CANCELADO
                n += 1
        await self.session.flush()
        return n
```

---

## 4. ComunicacionService

```python
# backend/app/services/comunicacion_service.py
VALID_TRANSITIONS: dict[EstadoComunicacion, set[EstadoComunicacion]] = {
    EstadoComunicacion.PENDIENTE: {EstadoComunicacion.ENVIANDO, EstadoComunicacion.CANCELADO},
    EstadoComunicacion.ENVIANDO:  {EstadoComunicacion.ENVIADO, EstadoComunicacion.ERROR, EstadoComunicacion.PENDIENTE},
    EstadoComunicacion.ENVIADO:   set(),
    EstadoComunicacion.ERROR:     {EstadoComunicacion.PENDIENTE},
    EstadoComunicacion.CANCELADO: set(),
}

class ComunicacionService:
    def __init__(self, db: AsyncSession, tenant_id: UUID):
        self.db = db
        self.tenant_id = tenant_id
        self.repo = ComunicacionRepository(db, tenant_id)

    @staticmethod
    def _render(template_str: str, variables: dict) -> str:
        return Template(template_str).safe_substitute(variables)

    @staticmethod
    def _assert_transition(current: EstadoComunicacion, target: EstadoComunicacion) -> None:
        if target not in VALID_TRANSITIONS[current]:
            raise ServiceError(f"Invalid state transition: {current.value} -> {target.value}")

    def preview(self, request: ComunicacionPreviewRequest) -> ComunicacionPreviewResponse:
        return ComunicacionPreviewResponse(
            asunto_renderizado=self._render(request.asunto_template, request.variables),
            cuerpo_renderizado=self._render(request.cuerpo_template, request.variables),
        )

    async def encolar(self, request, current_user) -> list[Comunicacion]:
        tenant = await BaseRepository(Tenant, self.db, self.tenant_id).get_by_id(self.tenant_id)
        es_batch = len(request.destinatarios) > 1
        lote_id = uuid4() if es_batch else None
        aprobado_default = not (tenant.aprobacion_comunicaciones_masivas and lote_id is not None)
        settings = Settings()
        creados = []
        for d in request.destinatarios:
            tvars = {"nombre": d.nombre, "materia": str(request.materia_id), "actividades_faltantes": d.actividades_faltantes}
            row = Comunicacion(
                tenant_id=self.tenant_id, enviado_por=current_user.id,  # JWT-derived
                materia_id=request.materia_id,
                destinatario=d.email, destinatario_hash=generate_email_hash(d.email),
                asunto=self._render(request.asunto_template, tvars),
                cuerpo=self._render(request.cuerpo_template, tvars),
                estado=EstadoComunicacion.PENDIENTE, lote_id=lote_id,
                aprobado=aprobado_default, intentos=0, max_intentos=settings.MAX_INTENTOS,
            )
            await self.repo.create(row)
            creados.append(row)
        await self.db.commit()
        return creados

    async def aprobar_lote(self, lote_id, tenant_id) -> int:
        n = await self.repo.bulk_approve_lote(lote_id)
        await self.db.commit()
        return n

    async def aprobar_individual(self, comunicacion_id, tenant_id) -> Comunicacion:
        row = await self.repo.get_by_id(comunicacion_id)
        if row is None: raise ServiceError("Comunicacion not found")
        if row.estado == EstadoComunicacion.PENDIENTE:
            row.aprobado = True
            await self.db.commit()
        return row  # idempotent on ENVIADO

    async def cancelar_lote(self, lote_id, tenant_id) -> int:
        n = await self.repo.bulk_cancel_lote(lote_id)
        await self.db.commit()
        return n

    async def cancelar_individual(self, comunicacion_id, tenant_id) -> Comunicacion:
        row = await self.repo.get_by_id(comunicacion_id)
        if row is None: raise ServiceError("Comunicacion not found")
        self._assert_transition(row.estado, EstadoComunicacion.CANCELADO)
        row.estado = EstadoComunicacion.CANCELADO
        await self.db.commit()
        return row
```

---

## 5. Worker

```python
# backend/app/workers/main.py  (REPLACE placeholder)
async def recover_stuck(session) -> int:
    repo = ComunicacionRepository(session, tenant_id=None)
    stuck = await repo.list_by_estado_sistema(EstadoComunicacion.ENVIANDO)
    for row in stuck:
        row.estado = EstadoComunicacion.PENDIENTE
    await session.commit()
    return len(stuck)

async def dispatch_one(row: Comunicacion, session, settings: Settings) -> None:
    row.estado = EstadoComunicacion.ENVIANDO
    await session.commit()
    try:
        await send_email(settings, row.destinatario, row.asunto, row.cuerpo)
    except Exception as exc:
        row.intentos += 1
        row.estado = EstadoComunicacion.PENDIENTE if row.intentos < row.max_intentos else EstadoComunicacion.ERROR
        await session.commit()
        # NEVER log row.destinatario — log id + hash + estado only
        logger.warning("dispatch failed id=%s hash=%s intentos=%s estado=%s err=%s",
                       row.id, row.destinatario_hash, row.intentos, row.estado.value, type(exc).__name__)
        return
    row.estado = EstadoComunicacion.ENVIADO
    row.enviado_at = datetime.utcnow()
    await session.commit()
    await AuditService(session, row.tenant_id).log_action(
        actor_id=row.enviado_por, accion="COMUNICACION_ENVIAR",
        materia_id=row.materia_id, filas_afectadas=1,
    )
    await session.commit()

async def poll_once(session, settings: Settings) -> None:
    repo = ComunicacionRepository(session, tenant_id=None)
    rows = await repo.list_dispatchable()
    for row in rows:
        await dispatch_one(row, session, settings)

async def run_worker() -> None:
    settings = Settings()
    async with SessionLocal() as session:
        n = await recover_stuck(session)
        logger.info("crash recovery: requeued %d ENVIANDO rows", n)
    while True:
        async with SessionLocal() as session:
            await poll_once(session, settings)
        await asyncio.sleep(settings.WORKER_POLL_INTERVAL_SECONDS)
```

---

## 6. Router

```python
# backend/app/api/v1/routers/comunicaciones.py
# PATTERN: require_permission() returns CurrentUser — single Depends, not two
router = APIRouter(prefix="/comunicaciones", tags=["comunicaciones"])

@router.post("/preview", response_model=ComunicacionPreviewResponse)
async def preview_comunicacion(
    request: ComunicacionPreviewRequest,
    current_user: CurrentUser = Depends(require_permission("comunicacion:enviar")),
    db: AsyncSession = Depends(get_db),
): ...

# + 7 more handlers: POST /, GET /, GET /lotes/{id},
#   POST /lotes/{id}/aprobar, POST /{id}/aprobar,
#   POST /lotes/{id}/cancelar, POST /{id}/cancelar
```

**Register in `app/main.py`** (NOT in `routers/__init__.py`):
```python
from app.api.v1.routers.comunicaciones import router as comunicaciones_router
app.include_router(comunicaciones_router, prefix="/api/v1")
```

---

## 7. Non-trivial Design Decisions

| Decision | Rationale |
|----------|-----------|
| `aprobado` as Boolean, not extra state | Approval is orthogonal to lifecycle — keeps state machine to 5 clean states |
| `list_dispatchable()` cross-tenant | Worker is system-level; no JWT/no single tenant; dispatches for all tenants |
| `string.Template.safe_substitute` | Braces safe, non-blocking on missing vars, no injection surface, stdlib |
| Single-process worker | ADR-003 provisional; `FOR UPDATE SKIP LOCKED` is the documented hardening path for multi-process |
| `enviado_por` from JWT | Audit integrity — forging sender corrupts `COMUNICACION_ENVIAR` trail on ALTO-governance channel |

---

## 8. New Dependencies

- **`aiosmtplib>=3.0.0`** — add to `backend/pyproject.toml` `[project].dependencies`. ABSENT today.
- All other deps are stdlib (`string.Template`, `enum`, `uuid`, `hmac`/`hashlib`).

---

## 9. Apply Order

1. `backend/pyproject.toml` — add aiosmtplib
2. `backend/app/core/config.py` — SMTP + worker settings
3. `backend/app/core/exceptions.py` — create ServiceError
4. `backend/app/models/comunicacion.py` — model + EstadoComunicacion
5. `backend/app/models/tenant.py` — add `aprobacion_comunicaciones_masivas`
6. `backend/app/models/__init__.py` — register Comunicacion
7. `backend/app/repositories/comunicacion.py` — ComunicacionRepository
8. `backend/app/schemas/comunicacion.py` — DTOs
9. `backend/app/services/comunicacion_service.py` — service
10. `backend/app/workers/main.py` — replace placeholder
11. `backend/app/api/v1/routers/comunicaciones.py` — router
12. `backend/app/main.py` — include_router
13. `backend/alembic/versions/XXXX_c12_comunicacion.py` — migration
14. `backend/tests/test_comunicacion_service.py` — TDD
15. `backend/tests/test_comunicacion_worker.py` — TDD
