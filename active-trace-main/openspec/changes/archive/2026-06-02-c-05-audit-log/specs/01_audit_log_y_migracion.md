# Especificación 01: AuditLog y Migraciones (C-05)

## 1. Responsabilidad
Esta especificación define la entidad `AuditLog` (E-AUD), su esquema relacional inmutable mediante Alembic, y el bloqueo estricto (append-only) a nivel de la capa de repositorios.

## 2. Definición del Modelo
Crear `backend/app/models/audit_log.py`:
- No heredar soft-deletes.
- Campos obligatorios: `id` (UUID), `tenant_id` (UUID, not null), `fecha_hora` (DateTime, default `now()`), `actor_id` (UUID, not null), `accion` (String, not null).
- Campos opcionales: `impersonado_id` (UUID, nullable), `materia_id` (UUID, nullable), `detalle` (JSON, nullable), `filas_afectadas` (Integer, nullable), `ip` (String, nullable), `user_agent` (String, nullable).

## 3. Repositorio Restringido
Crear `AuditLogRepository` heredando de `BaseRepository` pero sobreescribiendo métodos de borrado y modificación:
```python
def update(self, *args, **kwargs):
    raise NotImplementedError("Los registros de auditoría son append-only.")

def delete(self, *args, **kwargs):
    raise NotImplementedError("No se pueden eliminar registros de auditoría.")

def soft_delete(self, *args, **kwargs):
    raise NotImplementedError("No se pueden aplicar soft-deletes a la auditoría.")
```

## 4. Migración
Generar la migración Alembic `004_audit_log` con las sentencias correspondientes y las claves foráneas hacia `tenant` y `usuario` (tanto para `actor_id` como `impersonado_id`).
