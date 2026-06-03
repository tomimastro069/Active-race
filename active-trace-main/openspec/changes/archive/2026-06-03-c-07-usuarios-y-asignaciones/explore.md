## Exploration: C-07 Usuarios y Asignaciones

### Current State
- The `Usuario` model exists but is currently an auth skeleton (`email`, `hashed_password`, `2FA`, `estado`).
- The `Asignacion` model exists with basic contextual relationships (`usuario_id`, `rol_id`, `materia_id`, etc.) and dates (`desde`, `hasta`), but lacks derived properties and API handlers.
- The `app.core.security` module provides AES-256 encryption (`encrypt_attr`, `decrypt_attr`) with Fernet for sensitive data.
- The system is ready to receive the full PII model, encrypted fields, and the REST endpoints to manage users and assignments.

### Affected Areas
- `backend/app/models/usuario.py` — Needs complete PII fields (`dni`, `cuil`, `cbu`, `alias_cbu`, `banco`, `regional`, `legajo`, `legajo_profesional`, `facturador`, `nombre`, `apellidos`). The PII fields must be encrypted using `app.core.security`.
- `backend/app/models/asignacion.py` — Needs a property for `estado_vigencia` (Vigente / Vencida) based on current datetime and `desde`/`hasta`.
- `backend/app/schemas/usuario.py` — Define Pydantic schemas (Create, Update, Response).
- `backend/app/schemas/asignacion.py` — Define Pydantic schemas for assignments.
- `backend/app/repositories/usuario.py` — Create repository handling encryption/decryption transparently, checking `(tenant_id, email)` uniqueness.
- `backend/app/repositories/asignacion.py` — Create repository to manage assignments and handle overlapping constraints.
- `backend/app/services/usuario.py` & `backend/app/services/asignacion.py` — Business logic layers for user management and role assignment.
- `backend/app/api/routers/usuarios.py` — Implement `/api/admin/usuarios` endpoints guarded by `usuarios:gestionar` (ADMIN).
- `backend/app/api/routers/asignaciones.py` — Implement `/api/asignaciones` endpoints guarded by `equipos:asignar`.
- `backend/alembic/versions/` — Needs Migration 005 for new Usuario columns and data migration for existing users.

### Approaches
1. **Custom SQLAlchemy TypeDecorator** — Use custom SQLAlchemy types to encrypt/decrypt seamlessly on attribute read/write.
   - Pros: Completely transparent to the repository layer.
   - Cons: Can hide complexity. `email` uniqueness constraint breaks if encryption uses a random IV (like standard Fernet).
   - Effort: Medium

2. **Repository-Level Encryption with Hash Index** — Store encrypted values in the columns, and use an `email_hash` column for uniqueness and exact lookups.
   - Pros: Secure. Solves the uniqueness constraint problem natively in the DB.
   - Cons: Requires an extra column `email_hash` in the database.
   - Effort: Medium

### Recommendation
Use **Repository-Level Encryption with Hash Index** for `email` uniqueness. Since `email` needs to be unique per tenant and we must support login by email, a deterministic hash column (`email_hash`) allows fast lookups and DB constraints without compromising the encrypted `email` value. The rest of PII fields (`dni`, `cuil`, `cbu`) don't have unique constraints and can just use `TypeDecorator` or Repository-level encryption.

### Risks
- **Encrypted Unique Constraints**: `email` must be unique per tenant (`UniqueConstraint('tenant_id', 'email')`). If encrypted with Fernet (which includes a timestamp/random IV), identical emails will have different ciphertexts. We must solve this in the design phase (e.g. `email_hash`).
- **Data Migration**: Existing users (like the initial admin from C-01) must have their emails encrypted and hashed during the Alembic migration.

### Ready for Proposal
Yes. The Orchestrator can now run `/opsx-propose C-07-usuarios-y-asignaciones`.
