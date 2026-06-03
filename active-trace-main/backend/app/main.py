from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.core.logging import setup_logging
from app.core.observability import setup_observability
from app.api.v1.routers.health import router as health_router
from app.api.v1.routers.auth import router as auth_router
from app.api.v1.routers.carreras import router as carreras_router
from app.api.v1.routers.materias import router as materias_router
from app.api.v1.routers.cohortes import router as cohortes_router
from app.api.v1.routers.usuarios import router as usuarios_router
from app.api.v1.routers.asignaciones import router as asignaciones_router
from app.core.database import engine

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

# Register routers
app.include_router(health_router, prefix="/api/v1")
app.include_router(auth_router, prefix="/api/v1")
app.include_router(carreras_router, prefix="/api/v1")
app.include_router(materias_router, prefix="/api/v1")
app.include_router(cohortes_router, prefix="/api/v1")
app.include_router(usuarios_router, prefix="/api/v1")
app.include_router(asignaciones_router, prefix="/api/v1")

