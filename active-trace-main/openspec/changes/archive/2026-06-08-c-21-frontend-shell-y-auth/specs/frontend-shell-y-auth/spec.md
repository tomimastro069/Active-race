# frontend-shell-y-auth Specification

## Purpose
Establecer el scaffolding de la aplicación frontend SPA (React + Vite + TS) y definir la infraestructura transversal de autenticación, cliente HTTP Axios seguro con cola de reintentos para refresco de token transparente, vistas de autenticación, y ruteo seguro (Guards) con control de acceso basado en roles/permisos.

## Requirements

### Requirement: Cliente HTTP Axios Seguro y Refresco Transparente
El sistema MUST centralizar las llamadas HTTP usando Axios e inyectar el Access Token en la cabecera `Authorization: Bearer <token>`. Ante un error HTTP 401 Unauthorized en peticiones concurrentes, el sistema MUST encolar las llamadas, renovar el token mediante `/auth/refresh` y reintentar las peticiones encoladas transparentemente. Si el refresh falla, el sistema MUST limpiar la sesión y redirigir a `/login`.

#### Scenario: Inyección exitosa de token en peticiones
- GIVEN un usuario autenticado con un token de acceso válido
- WHEN realiza una petición HTTP al backend
- THEN el cliente Axios inyecta automáticamente la cabecera `Authorization: Bearer <token>`

#### Scenario: Refresco transparente con peticiones concurrentes encoladas
- GIVEN un token de acceso expirado y un Refresh Token válido en LocalStorage
- WHEN se realizan múltiples llamadas HTTP concurrentes y estas reciben HTTP 401
- THEN se encolan las llamadas, se solicita un nuevo Access Token vía POST `/auth/refresh` una sola vez, se actualiza el token en memoria, y se reintentan las llamadas de forma exitosa

#### Scenario: Fallo de refresco de token y redirección
- GIVEN un Refresh Token inválido o expirado en LocalStorage
- WHEN una petición recibe HTTP 401 y falla el POST `/auth/refresh`
- THEN el sistema limpia el localStorage y la memoria, cancela las peticiones encoladas y redirige al usuario a la página de login

### Requirement: Autenticación, 2FA y Recuperación de Contraseña
El sistema MUST proveer interfaces de usuario seguras y reactivas para: Login (email/password), Verificación de doble factor (2FA/TOTP), y Recuperación de contraseña (solicitud y reset con token).

#### Scenario: Login exitoso con 2FA requerido
- GIVEN un usuario registrado con 2FA activo
- WHEN ingresa credenciales válidas en el formulario de login
- THEN recibe una indicación de que requiere verificación 2FA y es redirigido al formulario de ingreso de código TOTP

#### Scenario: Verificación 2FA exitosa
- GIVEN un usuario en el formulario 2FA tras un login parcial
- WHEN ingresa un código TOTP de 6 dígitos válido
- THEN recibe el Access Token, establece la sesión y es redirigido al dashboard

#### Scenario: Recuperación de contraseña
- GIVEN un usuario no autenticado
- WHEN solicita recuperar contraseña ingresando su email y luego envía el nuevo password usando el token recibido
- THEN el sistema permite establecer la nueva contraseña y redirige a `/login`

### Requirement: Enrutamiento Protegido y Renderizado Basado en Permisos
El sistema MUST utilizar React Router para gestionar las rutas y protegerlas mediante un `AuthGuard`. El layout principal y las rutas privadas MUST validar la sesión del usuario y ocultar u ocultar vistas según los roles y permisos del usuario logueado.

#### Scenario: Acceso restringido para usuario no autenticado
- GIVEN un usuario no autenticado
- WHEN intenta navegar a una ruta privada como `/dashboard`
- THEN el `AuthGuard` lo redirige automáticamente a `/login` preservando la ruta de origen

#### Scenario: Control de acceso por roles y permisos finos
- GIVEN un usuario autenticado sin el permiso requerido para un módulo
- WHEN intenta acceder a la ruta de ese módulo o el sistema renderiza el menú
- THEN el sistema bloquea el acceso (muestra error 403 o redirige) y oculta el enlace del menú correspondiente
