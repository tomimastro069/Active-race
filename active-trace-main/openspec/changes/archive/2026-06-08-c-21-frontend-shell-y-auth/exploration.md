# Exploration: frontend-shell-y-auth (C-21)

### Current State
El frontend de la aplicación `activia-trace` no está inicializado. Existe una arquitectura backend completa en Python (FastAPI), incluyendo endpoints para autenticación (/login, /refresh, /verify-2fa, /forgot, /reset, /logout, /impersonate) listos para ser consumidos. El frontend debe ser una Single Page Application (SPA) construida sobre React 18, TypeScript y Vite, e implementar las bases transversales del sistema (clientes HTTP con refresh de tokens transparente, layouts responsivos, manejo de roles/permisos, y pantallas de autenticación).

### Affected Areas
No hay archivos de frontend existentes en el repositorio. Crearemos la estructura completa en la raíz de `active-trace-main/frontend/` (o directamente como `frontend/` dentro del repositorio).
- `frontend/` (Nueva carpeta) — Contendrá todo el scaffolding de React 18 + TS + Vite + Tailwind.
- `frontend/src/shared/services/api.ts` (Nuevo archivo) — Cliente Axios centralizado con lógica de interceptores para el refresh automático de tokens.
- `frontend/src/features/auth/` (Nueva carpeta) — Módulo de autenticación (Login, 2FA, password recovery).
- `openspec/changes/c-21-frontend-shell-y-auth/exploration.md` (Este archivo) — Documento de exploración del cambio.

### Approaches

#### 1. Estructura Feature-Based Clásica con Axios Interceptors y React Router Guards
Consiste en seguir estrictamente la estructura por features recomendada en la especificación de arquitectura. La lógica del cliente HTTP utiliza interceptores de Axios (`onRequest`, `onResponseError`) para interceptar las respuestas `401 Unauthorized` de la API, solicitar un nuevo token mediante `/auth/refresh` de manera transparente (encolando las peticiones concurrentes fallidas), y reintentar las peticiones originales con el nuevo JWT.
- **Pros:** 
  - Estricta separación de responsabilidades y modularidad.
  - Implementación estándar de refresh transparente que evita fallas en peticiones concurrentes cuando expira el token.
  - Mayor mantenibilidad a largo plazo para equipos distribuidos.
- **Cons:**
  - Requiere manejo cuidadoso de colas de reintento en Axios para no duplicar llamadas a `/auth/refresh` bajo carga concurrente.
- **Effort:** Medium

#### 2. Auth State centralizado en LocalStorage sin colas de refresh (Fallback simple)
Intercepción simple donde un error `401` redirige inmediatamente al login o intenta una única llamada a `/auth/refresh` y, en caso de fallar, fuerza el logout sin mantener una cola de peticiones concurrentes pendientes.
- **Pros:** 
  - Muy fácil y rápido de implementar en el corto plazo.
- **Cons:**
  - Pésima experiencia de usuario: si múltiples consultas corren al mismo tiempo (ej. dashboard con varios componentes de TanStack Query) y el token expira, cada una podría disparar peticiones de refresh desordenadas o fallar abruptamente, causando cierres de sesión no planeados.
- **Effort:** Low

### Recommendation
Se recomienda el **Enfoque 1 (Estructura Feature-Based con Axios Interceptors y Cola de Reintentos)**. Cumple con las pautas estrictas descritas en `docs/ARQUITECTURA.md` y ofrece una experiencia libre de interrupciones para el usuario mediante un cliente Axios robusto con refresh transparente y encolamiento de llamadas en espera de renovación.

### Risks
- **Desincronización de Sesiones:** El token de acceso dura 15 minutos; si el refresh token expira o es inválido, el backend revocará toda la sesión (previniendo reuso). El frontend debe manejar esto limpiando el estado de sesión y redirigiendo al login.
- **Seguridad en Almacenamiento:** Almacenar el Access Token y el Refresh Token de forma segura. El Access Token se guardará en memoria/estado del frontend, y el Refresh Token en LocalStorage o en cookies según lo decida la configuración final (por ahora LocalStorage para simplificar el scaffolding, documentando la posibilidad de Cookies Secure/HttpOnly en el futuro).

### Ready for Proposal
Yes. El cimiento del frontend está listo para ser propuesto bajo el change `c-21-frontend-shell-y-auth`. El orquestador debe avanzar al paso de propuesta (`sdd-propose`) para detallar las especificaciones y el diseño técnico del scaffolding de la SPA.
