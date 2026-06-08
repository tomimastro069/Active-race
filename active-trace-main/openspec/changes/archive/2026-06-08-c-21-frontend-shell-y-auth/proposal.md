# Proposal: Frontend Shell y Autenticación (C-21)

## Intent
Inicializar el frontend SPA del proyecto e implementar la infraestructura transversal para autenticación y llamadas HTTP seguras con refresh transparente de tokens.

## Scope

### In Scope
- Scaffolding de React 18 + TS + Vite + Tailwind CSS + TanStack Query + Axios en `/frontend`.
- Cliente HTTP Axios centralizado con interceptores y cola para refresh transparente de JWT.
- Pantallas de autenticación: Login, verificación 2FA (TOTP) y recuperación de contraseña.
- Layout principal responsivo y adaptable según los roles/permisos del usuario logueado.
- Guards de rutas basados en roles y permisos finos del backend (`C-04`).

### Out of Scope
- Portal interactivo del alumno y pantallas de visualización de calificaciones (Fase 2).
- Módulos específicos de visualización de docentes, liquidaciones u otros módulos de negocio.

## Capabilities

### New Capabilities
- `frontend-shell-y-auth`: Scaffolding general del frontend, autenticación y cliente API seguro.

### Modified Capabilities
None

## Approach
Configurar un proyecto Vite con React/TS en la carpeta `frontend/`. Implementar un cliente Axios centralizado en `shared/services/api.ts` que guarde el access token en memoria y el refresh token en localStorage, interceptando errores 401 para reintentar llamadas en cola de forma transparente tras invocar `/auth/refresh`. Las rutas se protegerán con un guard global que valide la sesión y los permisos.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `frontend/` | New | Directorio raíz para la aplicación SPA React. |
| `frontend/src/shared/services/api.ts` | New | Implementación del cliente Axios centralizado con refresh. |
| `frontend/src/features/auth/` | New | Formularios y lógica de login, 2FA y forgot/reset. |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Loop infinito en Axios Interceptor | Med | Implementar bandera de control para evitar reintentar la llamada de refresh a sí misma. |
| Exposición del Refresh Token | Low | Usar localStorage de forma temporal y planificar migración a Cookie segura HttpOnly. |

## Rollback Plan
El cambio es 100% aditivo (nueva carpeta `frontend/`). Si ocurre algún problema grave, se puede revertir eliminando el directorio `/frontend` y la carpeta del change en `openspec/`.

## Dependencies
- `C-03 auth-jwt-2fa` (completado)
- `C-04 rbac-permisos-finos` (completado)

## Success Criteria
- [ ] La SPA inicia correctamente en dev (`npm run dev`).
- [ ] Login, 2FA, password reset y logout funcionan consumiendo la API del backend.
- [ ] El refresh de tokens se ejecuta automáticamente ante respuestas 401 sin que el usuario lo note.
