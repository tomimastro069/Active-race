from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.logging import setup_logging, TenantLoggingMiddleware
from app.core.observability import setup_observability
from app.core.tenancy import TenantMiddleware
from app.api.v1.routers.health import router as health_router
from app.api.v1.routers.auth import router as auth_router
from app.api.v1.routers.carreras import router as carreras_router
from app.api.v1.routers.materias import router as materias_router
from app.api.v1.routers.cohortes import router as cohortes_router
from app.api.v1.routers.usuarios import router as usuarios_router
from app.api.v1.routers.asignaciones import router as asignaciones_router
from app.api.v1.routers.equipos import router as equipos_router
from app.api.v1.routers.padron import router as padron_router
from app.api.v1.routers.calificaciones import router as calificaciones_router
from app.api.v1.routers.analisis import router as analisis_router
from app.api.v1.routers.comunicaciones import router as comunicaciones_router
from app.api.v1.routers.encuentros import router as encuentros_router
from app.api.v1.routers.guardias import router as guardias_router
from app.api.v1.routers.evaluaciones import router as evaluaciones_router
from app.api.v1.routers.avisos import router as avisos_router
from app.api.v1.routers.perfil import router as perfil_router
from app.api.v1.routers.inbox import router as inbox_router
from app.api.v1.routers.programas import router as programas_router
from app.core.database import engine

# Monitoring
from monitoring.prometheus_setup import (
    router as prometheus_router,
    PrometheusMiddleware,
)

# Initialize logging at startup
setup_logging()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Setup OpenTelemetry
    setup_observability(app)
    yield
    # Dispose database engine resources
    await engine.dispose()

app = FastAPI(
    title="Activia Trace API",
    version="0.1.0",
    lifespan=lifespan
)

# Middleware (order matters: outermost first)
app.add_middleware(PrometheusMiddleware)
app.add_middleware(TenantLoggingMiddleware)
app.add_middleware(TenantMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(health_router, prefix="/api/v1")
app.include_router(auth_router, prefix="/api/v1")
app.include_router(carreras_router, prefix="/api/v1")
app.include_router(materias_router, prefix="/api/v1")
app.include_router(cohortes_router, prefix="/api/v1")
app.include_router(usuarios_router, prefix="/api/v1")
app.include_router(asignaciones_router, prefix="/api/v1")
app.include_router(equipos_router, prefix="/api/v1")
app.include_router(padron_router, prefix="/api/v1")
app.include_router(calificaciones_router, prefix="/api/v1")
app.include_router(analisis_router, prefix="/api/v1")
app.include_router(comunicaciones_router, prefix="/api/v1")
app.include_router(encuentros_router, prefix="/api/v1")
app.include_router(guardias_router, prefix="/api/v1")
app.include_router(evaluaciones_router, prefix="/api/v1")
app.include_router(avisos_router, prefix="/api/v1/avisos")
from app.api.v1.routers.tareas import router as tareas_router
from app.api.v1.routers.auditoria import router as auditoria_router
app.include_router(tareas_router, prefix="/api/v1/tareas")
app.include_router(perfil_router, prefix="/api/v1")
app.include_router(inbox_router, prefix="/api/v1")
app.include_router(programas_router, prefix="/api/v1")
app.include_router(auditoria_router, prefix="/api/v1/auditoria")
