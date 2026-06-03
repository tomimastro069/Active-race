# Design: C-07 Usuarios y Asignaciones

## Technical Approach

We will augment the `Usuario` model to include encrypted PII fields and a deterministic `email_hash`. We will add the `estado_vigencia` property to `Asignacion`. We will then build the corresponding schemas, repositories, services, and FastAPI routers under `backend/app/api/v1/routers/`.

## Architecture Decisions

### Decision: Email Uniqueness with Encryption

**Choice**: Use `email_hash` column for exact lookups and unique constraints.
**Alternatives considered**: 
- Deterministic AES encryption for `email` (less secure as it leaks equality).
- Custom TypeDecorator that encrypts the email but sacrifices uniqueness constraint (requires manual checks in Python, vulnerable to race conditions).
**Rationale**: By hashing the email with HMAC-SHA256 (using a secret salt) into `email_hash`, we can safely add a unique constraint `UniqueConstraint('tenant_id', 'email_hash')` without compromising the encrypted `email` ciphertext (which uses Fernet and a random IV).

### Decision: PII Encryption Implementation

**Choice**: SQLAlchemy **TypeDecorator** (`EncryptedString`) for `dni`, `cuil`, `cbu`, `alias_cbu`, and `email`.
**Alternatives considered**: Encrypting and decrypting explicitly in the `UsuarioRepository`.
**Rationale**: A `TypeDecorator` makes encryption completely transparent to the application layer. Since these fields (except `email`, which is handled via `email_hash`) don't need exact matching in queries, a `TypeDecorator` wrapping Fernet is the cleanest approach.

### Decision: Asignacion `estado_vigencia`

**Choice**: Define `estado_vigencia` as a Python `@property` in the `Asignacion` model.
**Alternatives considered**: Hybrid property or a database generated column.
**Rationale**: `estado_vigencia` is just a temporal calculation (`desde <= now() <= hasta`). It does not need to be stored or queried in the database directly. If we need to filter active assignments, we can use `desde` and `hasta` in SQL queries explicitly.

## Data Flow

    [Client] ──(POST /api/admin/usuarios)──→ [Usuarios Router]
                                                  │
    [AuditLog] ←──(audit decorators)─── [Usuario Service]
                                                  │
                                          [Usuario Repo]
                                                  │ (TypeDecorator encrypts transparently)
                                            [PostgreSQL]

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `backend/app/models/usuario.py` | Modify | Add `email_hash`, `dni`, `cuil`, `cbu`, `alias_cbu` (encrypted), `nombre`, `apellidos`, `banco`, `regional`, `legajo`, `legajo_profesional`, `facturador`. |
| `backend/app/models/asignacion.py` | Modify | Add `@property` `estado_vigencia`. |
| `backend/app/core/types.py` | Create | `EncryptedString` SQLAlchemy TypeDecorator using `app.core.security`. |
| `backend/app/schemas/usuario.py` | Create | Pydantic models for user CRUD. |
| `backend/app/schemas/asignacion.py` | Create | Pydantic models for assignment CRUD. |
| `backend/app/repositories/usuario.py` | Modify | Add methods for querying by `email_hash`. |
| `backend/app/repositories/asignacion.py` | Modify | Implement CRUD logic for assignments. |
| `backend/app/services/usuario.py` | Create | Handle `email_hash` generation and PII masking. |
| `backend/app/services/asignacion.py` | Create | Business logic for assignments. |
| `backend/app/api/v1/routers/usuarios.py` | Create | REST endpoints for users under `/api/admin/usuarios`. |
| `backend/app/api/v1/routers/asignaciones.py` | Create | REST endpoints for assignments under `/api/asignaciones`. |
| `backend/alembic/versions/xxx_c07.py` | Create | Migration script (add columns + data migration). |

## Interfaces / Contracts

```python
class UsuarioCreate(BaseModel):
    email: EmailStr
    nombre: str
    apellidos: str
    password: str
    dni: Optional[str] = None
    cuil: Optional[str] = None
    # ... other fields

class UsuarioResponse(BaseModel):
    id: UUID4
    email: EmailStr
    nombre: str
    apellidos: str
    # PII fields are omitted unless explicitly requested or masked (e.g. cuil: "***-XXXX")
```

## Testing Strategy

| Layer | What to Test | Approach |
|-------|-------------|----------|
| Unit | `EncryptedString` | Verify data is encrypted in DB and decrypted on read. |
| Unit | `estado_vigencia` | Test boundary dates for Vigente/Vencida. |
| Integration | `UsuarioRepository` | Verify unique constraint on `email_hash` per tenant. |
| E2E | `/api/admin/usuarios` | Verify endpoints create user and return masked PII. |
| E2E | `/api/asignaciones` | Verify endpoints require `equipos:asignar` guard. |

## Migration / Rollout

Alembic migration is required. It MUST include a data migration to process existing users (from C-01/C-03):
1. Add new columns (`email_hash`, PII fields).
2. For each existing user, encrypt their `email` with `Fernet`, generate `email_hash` with HMAC-SHA256, and update the row.
3. Apply NOT NULL and Unique constraints to `email_hash`.

## Open Questions

- [ ] Is `legajo` meant to be unique per tenant? (Assuming no, since it's an optional business attribute).
- [ ] Do we mask emails by default in `UsuarioResponse`, or only DNI/CUIL? (Assuming email is full but DNI/CUIL are masked).
