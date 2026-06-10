# Tasks: fix-04-frontend-flujo-2fa

## 1. Frontend

- [x] 1.1 `auth.service.ts`: no persistir tokens cuando `requires_2fa`; quitar `token_2fa` de
      `LoginCredentials`; agregar `verify2fa(temporaryToken, totpCode)` contra
      `POST /auth/verify-2fa`.
- [x] 1.2 `LoginPage.tsx`: conservar el token temporal del paso 1 y completar el 2FA con
      `authService.verify2fa(...)`.

## 2. Verificación

- [x] 2.1 `tsc --noEmit` limpio.
- [x] 2.2 Vitest en verde.
