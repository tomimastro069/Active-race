## Context

The system has a foundational architecture (C-01) and strong multi-tenant data isolation (C-02). We now need to implement the core authentication and session management layer (C-03). According to the Knowledge Base (FL-01 and Actores y Roles), the system relies on a Golden Rule: identity, roles, and tenant context are derived *exclusively* from an authenticated session. No parameter from the request can alter this.

## Goals / Non-Goals

**Goals:**
- Provide a secure login endpoint using email and password.
- Issue short-lived JWT access tokens and rotatable refresh tokens.
- Establish a mechanism to enforce the "Golden Rule" via a FastAPI dependency (`get_current_user`).
- Support an optional TOTP-based 2FA flow.
- Implement a secure password recovery flow via email.
- Ensure all passwords are hashed using Argon2id.

**Non-Goals:**
- Fine-grained RBAC permissions (this is C-04; C-03 only cares about establishing the authenticated identity and roles).
- Session impersonation logic (this is part of C-05 Audit Log & Impersonation).
- External identity providers (OAuth/SSO) for now.

## Decisions

### 1. Password Hashing: Argon2id
- **Decision:** Use `passlib[argon2]` for hashing passwords.
- **Rationale:** Argon2id is the current recommended standard for password hashing, offering strong resistance against both GPU cracking and side-channel attacks.
- **Alternatives Considered:** bcrypt (acceptable but older, Argon2id is superior).

### 2. Session Strategy: Stateless JWT + Stateful Refresh Tokens
- **Decision:** Use stateless short-lived JWTs (15 minutes) for access tokens, and stateful refresh tokens stored in the database.
- **Rationale:** Stateless access tokens keep API validation fast without database hits per request. Storing refresh tokens in the database allows for immediate revocation, device tracking, and refresh token rotation (re-use of a refresh token invalidates the entire token family, enhancing security).
- **Alternatives Considered:** Pure stateless refresh tokens (prevents immediate revocation); Stateful sessions (e.g., Redis-backed session IDs, which adds infrastructure overhead we want to avoid early on).

### 3. Golden Rule Enforcement: FastAPI Dependency
- **Decision:** Create a core FastAPI dependency `get_current_user` that decodes the JWT and returns a `CurrentUser` DTO containing `user_id`, `tenant_id`, and `roles`.
- **Rationale:** By using FastAPI's dependency injection system, we guarantee that any endpoint requiring `get_current_user` receives a trusted context derived strictly from the token. The token signature prevents tampering.

### 4. Optional 2FA Flow
- **Decision:** If a tenant/user requires 2FA, the initial login will return a temporary `2fa_required` token instead of a full access token. A subsequent endpoint `/api/v1/auth/verify-2fa` will exchange this temporary token and the TOTP code for the actual access and refresh tokens.
- **Rationale:** This keeps the standard login flow simple while supporting 2FA via a clear two-step state machine without keeping server-side session state for incomplete logins.

## Risks / Trade-offs

- **Risk:** Stolen Refresh Tokens.
  - **Mitigation:** Implement strict refresh token rotation. If a refresh token is used twice, the system must revoke all tokens for that user session immediately.
- **Risk:** Brute-force login attacks.
  - **Mitigation:** Implement rate-limiting on the `/login` and `/recover-password` endpoints.
- **Risk:** Access Token Expiration UX.
  - **Mitigation:** Ensure the frontend handles 401 Unauthorized responses by automatically calling the refresh endpoint and retrying the request.
