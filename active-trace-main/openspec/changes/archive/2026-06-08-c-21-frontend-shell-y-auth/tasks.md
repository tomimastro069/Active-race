# Tasks: Frontend Shell y Autenticación (C-21)

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | 600-800 líneas (incluye Vite boilerplate + package-lock) |
| 400-line budget risk | High |
| Chained PRs recommended | Yes |
| Suggested split | PR 1 → PR 2 |
| Delivery strategy | ask-on-risk |
| Chain strategy | stacked-to-main |

Decision needed before apply: No
Chained PRs recommended: Yes
Chain strategy: stacked-to-main
400-line budget risk: High

### Suggested Work Units

| Unit | Goal | Likely PR | Notes |
|------|------|-----------|-------|
| 1 | Scaffolding Vite y HTTP Client (api.ts) | PR 1 | Base `main`; incluye config inicial e interceptores Axios. |
| 2 | AuthContext, Guards y UI de Login | PR 2 | Base branch: PR 1; incluye componentes de Auth, validación 2FA, React Router. |

## Phase 1: Foundation / Infrastructure
- [x] 1.1 Crear scaffolding de Vite (React + TS) en carpeta `frontend/` mediante `npm create vite@latest`.
- [x] 1.2 Instalar dependencias en `frontend/` (react-router-dom, axios, @tanstack/react-query, tailwindcss).
- [x] 1.3 Configurar `vite.config.ts` para soportar alias `@` apuntando a `src/`.
- [x] 1.4 Crear interfaces en `frontend/src/shared/types/auth.types.ts` (`AuthUser`, `AuthTokens`, `AuthState`).

## Phase 2: HTTP Client & Interceptors (Core)
- [x] 2.1 Crear `frontend/src/shared/services/api.ts` e inicializar instancia base de Axios.
- [x] 2.2 Implementar request interceptor en `api.ts` para inyectar Access Token desde memoria.
- [x] 2.3 Implementar response interceptor en `api.ts` para capturar errores 401.
- [x] 2.4 Agregar lógica de cola (queue) en el interceptor 401 para pausar peticiones concurrentes.
- [x] 2.5 Implementar llamada a `POST /auth/refresh` y resolución/rechazo de la cola de peticiones.

## Phase 3: Auth State & Routing (Integration)
- [x] 3.1 Crear funciones base en `frontend/src/features/auth/services/auth.service.ts` (`login`, `refresh`, `logout`).
- [x] 3.2 Crear `frontend/src/shared/contexts/AuthContext.tsx` con su Provider y hook `useAuth`.
- [x] 3.3 Crear componente `AuthGuard.tsx` en `shared/components/` para redirigir a `/login` a usuarios sin sesión.
- [x] 3.4 Crear formulario `frontend/src/features/auth/pages/LoginPage.tsx` (Login, 2FA y recovery mockup).
- [x] 3.5 Configurar React Router y QueryClient en `frontend/src/App.tsx`, integrando `AuthGuard` y `LoginPage`.

## Phase 4: Testing & Verification
- [x] 4.1 Escribir test unitario para la cola de interceptores Axios en `api.test.ts`.
- [x] 4.2 Verificar redirección manual de `AuthGuard` con mock en AuthContext.
- [x] 4.3 Comprobar funcionamiento del build mediante `npm run build`.
