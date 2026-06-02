## 1. Environment and Dependencies

- [x] 1.1 Add `passlib[argon2]`, `PyJWT`, and related dependencies to the project requirements.
- [x] 1.2 Update `.env.example` and Pydantic `Settings` to include `SECRET_KEY`, `ALGORITHM` (HS256), `ACCESS_TOKEN_EXPIRE_MINUTES`, and `REFRESH_TOKEN_EXPIRE_DAYS`.

## 2. Core Security Utilities

- [ ] 2.1 Implement password hashing utilities using Argon2id in `backend/app/core/security.py`.
- [ ] 2.2 Implement JWT token creation and decoding functions (access and refresh tokens).

## 3. Database Models and Repositories

- [ ] 3.1 Create `User` model inheriting from `TimestampedTenant` with email, hashed password, and roles.
- [ ] 3.2 Create `RefreshToken` model to store active refresh tokens linked to users.
- [ ] 3.3 Create Alembic migration for `User` and `RefreshToken` models and apply it.
- [ ] 3.4 Create `UserRepository` to handle user lookup by email (scoped by tenant).
- [ ] 3.5 Create `RefreshTokenRepository` to manage token storage and rotation.

## 4. FastAPI Dependency (Golden Rule)

- [ ] 4.1 Create `CurrentUser` DTO schema.
- [ ] 4.2 Implement `get_current_user` FastAPI dependency in `backend/app/core/dependencies.py` to decode JWT, validate it, and return `CurrentUser`.

## 5. API Endpoints

- [ ] 5.1 Implement `POST /api/v1/auth/login` to validate credentials and return tokens (or `2fa_required`).
- [ ] 5.2 Implement `POST /api/v1/auth/refresh` to validate the refresh token, rotate it, and return new tokens.
- [ ] 5.3 Implement `POST /api/v1/auth/verify-2fa` to exchange `2fa_required` token and TOTP for final tokens.
- [ ] 5.4 Implement password recovery endpoints (`/recover-password` and `/reset-password`).
- [ ] 5.5 Integrate a simple rate limiter for authentication endpoints to prevent brute-force.

## 6. Testing

- [ ] 6.1 Write unit tests for password hashing and JWT utilities.
- [ ] 6.2 Write integration tests for login OK/KO and refresh rotation (reuse invalidates family).
- [ ] 6.3 Write integration tests for the 2FA flow.
- [ ] 6.4 Write integration tests for password recovery.
- [ ] 6.5 Write tests to ensure `get_current_user` rejects invalid tokens and correctly parses valid ones.
