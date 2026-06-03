# Proposal: C-07 Usuarios y Asignaciones

## Intent

Implement the full PII fields for the `Usuario` model with AES-256 encryption at rest, complete the `Asignacion` model with date-based validity (`estado_vigencia`), and build the CRUD REST APIs for both entities. This enables the administration of users and the contextual assignment of roles (teams) within the tenant, fulfilling Epic 4 functionality (F4.1, F4.3) and adhering to the multi-tenant and isolation rules.

## Scope

### In Scope
- Add encrypted PII fields (`dni`, `cuil`, `cbu`, `alias_cbu`) and standard fields (`nombre`, `apellidos`, `banco`, `regional`, `legajo`, `legajo_profesional`, `facturador`) to `Usuario`.
- Implement `email_hash` column for deterministic uniqueness check of the encrypted email.
- Define schemas, repositories, and business logic for `Usuario` and `Asignacion`.
- Build `/api/admin/usuarios` and `/api/asignaciones` endpoints with corresponding permission guards.
- Alembic migration and data migration for existing users.

### Out of Scope
- Integration with external HR systems for legajo.
- Frontend implementation (belongs to C-21 and beyond).
- Sending emails for assignments.

## Capabilities

### New Capabilities
- `usuario-pii-management`: Management of User identities, including encrypted PII storage and retrieval.
- `asignacion-contextual`: Context-based role assignments with temporal validity.

### Modified Capabilities
- `user-academic-assignment-e5`: Modifying existing basic structure to full lifecycle.

## Approach

Use **Repository-Level Encryption with Hash Index** for `email` to maintain the DB `UniqueConstraint('tenant_id', 'email_hash')`. Other PII fields (`dni`, `cuil`, `cbu`) will be encrypted at the repository layer. The `Asignacion` model will use a Python hybrid property or standard property to compute `estado_vigencia` (Vigente/Vencida) dynamically, rather than persisting it. Endpoints will map to `usuarios:gestionar` and `equipos:asignar` permissions.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `app/models/usuario.py` | Modified | Add PII columns and `email_hash`. |
| `app/models/asignacion.py` | Modified | Add `estado_vigencia` property. |
| `app/schemas/usuario.py` | New | Pydantic models. |
| `app/schemas/asignacion.py` | New | Pydantic models. |
| `app/repositories/usuario.py` | New | CRUD with transparent AES encryption. |
| `app/repositories/asignacion.py` | New | CRUD for assignments. |
| `app/api/routers/usuarios.py` | New | Admin endpoints. |
| `app/api/routers/asignaciones.py` | New | Assignment endpoints. |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Uniqueness collision of encrypted email | High | Add an `email_hash` column with a deterministic HMAC/SHA-256 for the unique constraint. |
| Existing data migration fails | Medium | Write a robust Alembic data migration that encrypts existing emails and computes their hashes. |
| Unencrypted PII in logs | Low | Explicitly exclude PII fields from `__repr__` and Pydantic logging dumps. |

## Rollback Plan

- Revert code changes to previous commit.
- Downgrade Alembic migration, which drops the new PII columns and `email_hash`. The original `email` values must be decrypted back in the down-migration.

## Dependencies

- Existing AES-256 utilities in `app.core.security`.
- `C-06` (estructura académica) must be deployed for assigning users to subjects/cohorts.

## Success Criteria

- [ ] `Usuario` table stores PII encrypted in the database.
- [ ] Attempting to create two users with the same email in the same tenant fails with 409 Conflict natively at the DB level.
- [ ] Endpoints return user details omitting sensitive PII unless requested by an authorized admin.
- [ ] Asignaciones reflect "Vigente" or "Vencida" correctly based on dates.
