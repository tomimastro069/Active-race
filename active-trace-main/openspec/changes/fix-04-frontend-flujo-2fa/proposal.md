# Fix 04 — El flujo 2FA del frontend es incompatible con el backend

## Why

Cuando el login devuelve `requires_2fa: true`, el frontend reenvía `POST /auth/login` con
`{email, token_2fa}` (sin password). El backend implementa otro protocolo (C-03): el login con
2FA devuelve un **token temporal** en `access_token`, y el segundo paso es
`POST /auth/verify-2fa` con `{temporary_token, totp_code}`. Resultado: ningún usuario con 2FA
habilitado puede completar el login desde la UI.

Defecto asociado: `authService.login` persiste `access_token` vía `setAccessToken` incluso cuando
`requires_2fa` es `true`, es decir, trataba el token temporal (que no es una sesión) como access
token real.

## What Changes

- `auth.service.ts`:
  - `login` solo persiste tokens cuando `requires_2fa` es `false`; elimina `token_2fa` de
    `LoginCredentials` (no existe en el contrato del backend).
  - Nuevo `verify2fa(temporaryToken, totpCode)` → `POST /auth/verify-2fa` con
    `{temporary_token, totp_code}`; persiste access/refresh al completar.
- `LoginPage.tsx`: guarda el token temporal devuelto por el login y lo usa en el paso 2FA
  llamando a `authService.verify2fa(...)`. El resto del flujo (me() → loginUser → navigate)
  no cambia.

## Impact

- `frontend/src/features/auth/services/auth.service.ts`
- `frontend/src/features/auth/pages/LoginPage.tsx`
- Sin cambios de backend. `tsc --noEmit` y Vitest en verde.
