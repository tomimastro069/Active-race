# Design: Frontend Shell y Autenticación (C-21)

## Technical Approach

El scaffolding inicial se realizará utilizando **Vite** con el template de **React + TypeScript**. Se establecerá la estructura de directorios orientada a *features* descrita en la arquitectura.
El núcleo técnico de este cambio es la configuración de un cliente HTTP robusto (**Axios**) centralizado en `shared/services/api.ts`. Este cliente implementará interceptores para inyectar el token de acceso y manejar respuestas `401 Unauthorized` de forma transparente, pausando peticiones concurrentes, renovando el token vía `/auth/refresh` y reintentando las llamadas originales.
El enrutamiento se manejará con **React Router DOM**, protegiendo las rutas privadas con un componente `AuthGuard` que verificará el estado de la sesión provisto por un `AuthContext`.

## Architecture Decisions

| Decision | Choice | Alternatives considered | Rationale |
|---|---|---|---|
| **Gestión de Estado de Auth** | **React Context (`AuthContext`)** | Redux, Zustand | El estado de autenticación (usuario, roles, tenant) es global pero de baja frecuencia de actualización. Context es nativo, suficiente y evita dependencias extra. TanStack Query se usará para el resto del estado (server state). |
| **Almacenamiento de Tokens** | **Access Token en Memoria, Refresh Token en LocalStorage** | Ambos en LocalStorage, Ambos en Cookies HttpOnly | Guardar el Access Token en memoria mitiga riesgos de XSS. El Refresh Token en LocalStorage permite persistir la sesión entre recargas (alineado con la propuesta actual, documentando la futura migración a Cookies HttpOnly). |
| **Lógica de Refresh (401)** | **Interceptor de Axios con Cola de Peticiones** | Redirigir al Login ante el primer 401 | Requisito de la arquitectura: el refresh debe ser transparente. Encolar peticiones evita múltiples llamadas a `/auth/refresh` simultáneas y pérdida de requests concurrentes. |

## Data Flow

### Flujo de Refresh de Token Transparente
```ascii
    [Componente/TanStack Query]
             │
             ▼
      Axios (Request) ──(Inyecta Access Token)──┐
             │                                  │
     (Si 401 Unauthorized)                      ▼
             │                               [Backend]
             ▼
    Axios Interceptor (Response)
             │
    ¿Refrescando Token? ──(Sí)──> [Encolar Petición (Promise)]
             │
           (No)
             │
             ▼
    Marcar isRefreshing = true
    Llamar POST /auth/refresh con Refresh Token (desde LocalStorage)
             │
        (Éxito) ────> Actualizar Tokens (Memoria/LocalStorage)
             │        Resolver Cola de Peticiones
             │        Reintentar Petición Original
             │
        (Fallo) ────> Limpiar Tokens (Logout)
                      Rechazar Cola de Peticiones
                      Redirigir a /login
```

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `frontend/package.json` | Create | Dependencias: react, react-dom, react-router-dom, axios, @tanstack/react-query, react-hook-form, zod, tailwindcss, etc. |
| `frontend/vite.config.ts` | Create | Configuración de Vite con alias `@` apuntando a `src/`. |
| `frontend/src/shared/services/api.ts` | Create | Instancia de Axios con interceptores de request (auth header) y response (refresh token logic y queue). |
| `frontend/src/shared/contexts/AuthContext.tsx` | Create | Proveedor de estado global para la sesión del usuario (`AuthContext`, `AuthProvider`, `useAuth`). |
| `frontend/src/shared/components/AuthGuard.tsx` | Create | Componente envoltura (HOC o Route Wrapper) que redirige a `/login` si no hay sesión activa. |
| `frontend/src/features/auth/services/auth.service.ts` | Create | Funciones que consumen la API: `login`, `refresh`, `logout`, etc. |
| `frontend/src/features/auth/pages/LoginPage.tsx` | Create | Formulario de login (React Hook Form + Zod). |
| `frontend/src/App.tsx` | Create | Configuración principal: React Router y QueryClientProvider. |

## Interfaces / Contracts

```typescript
// frontend/src/shared/types/auth.types.ts

export interface AuthUser {
  id: string;
  tenant_id: string;
  email: string;
  roles: string[];
  impersonated_by_id?: string | null;
}

export interface AuthTokens {
  access_token: string;
  token_type: string;
  refresh_token: string | null;
  requires_2fa: boolean;
}

export interface AuthState {
  user: AuthUser | null;
  isAuthenticated: boolean;
  isLoading: boolean;
}
```

La estructura del JWT devuelto por el backend dicta la interfaz `AuthUser`.

## Testing Strategy

| Layer | What to Test | Approach |
|-------|-------------|----------|
| Unit | `api.ts` (Interceptores Axios) | Mockear `axios` y simular respuestas 401. Verificar que múltiples peticiones fallidas se encolan y se reintentan correctamente tras una respuesta exitosa del mock de `/auth/refresh`. Verificar que un fallo en refresh limpia el estado. |
| Integration | `AuthContext` + `LoginPage` | Renderizar `AuthProvider` con `LoginPage`. Simular llenado de formulario y sumisión. Verificar que el estado de `AuthContext` se actualiza con el usuario tras una respuesta exitosa (mockeada) de la API. |
| E2E | Flujo de Login y Rutas Protegidas | N/A en esta fase (se configurará Playwright posteriormente según `.atl/testing-capabilities.md`). |

## Migration / Rollout

No migration required. Este es un nuevo directorio (`frontend/`) y no afecta datos existentes.

## Open Questions

None.
