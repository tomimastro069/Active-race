## Why

Activia Trace is a multi-tenant platform where data isolation is critical. While C-02 established data isolation at the database level using `tenant_id`, the system currently lacks a way to securely identify *who* is accessing the system and *which* tenant they belong to. We need to implement an authentication mechanism (C-03) that issues secure sessions so that identity and tenant information is derived exclusively from a verified token, adhering to the project's Golden Rule of Security.

## What Changes

- Implement a login endpoint accepting email and password (hashed with Argon2id).
- Implement a session mechanism issuing short-lived JWT access tokens and rotatable refresh tokens.
- Add an optional 2FA flow (TOTP) configurable per tenant.
- Implement a password recovery flow using single-use short-lived tokens sent via email.
- Create a `get_current_user` FastAPI dependency that securely resolves the user's identity, roles, and `tenant_id` exclusively from the verified JWT.
- Add rate limiting for authentication endpoints to prevent brute-force attacks.

## Capabilities

### New Capabilities
- `auth`: Handles user authentication, session issuance (JWT/refresh tokens), 2FA validation, and password recovery.
- `session-context`: Resolves user identity, tenant context, and roles server-side exclusively from the token.

### Modified Capabilities
- None.

## Impact

- **Security**: Establishes the foundation for all protected routes; enables C-04 (RBAC) by securely providing user identity and roles.
- **API**: Adds new `/api/v1/auth/*` endpoints.
- **Dependencies**: Introduces FastAPI security utilities, JWT libraries (`PyJWT`), password hashing (`passlib[argon2]`), and potentially rate-limiting libraries.
- **Tenancy**: Integrates with the existing `Tenant` isolation layer by ensuring `tenant_id` is always passed securely to repositories.
