## Why

La gestión académica requiere que cada usuario pueda editar su información personal y mantener una comunicación interna segura y trazable. Actualmente, los usuarios no pueden actualizar sus datos fiscales/bancarios ni disponer de una mensajería interna efectiva directamente en la plataforma. Sin esto, la trazabilidad, la autogestión de datos sensibles y la interacción entre roles docentes/administrativos quedan fragmentadas y dependen de canales externos no auditados.

## What Changes

- Permitir la edición del propio perfil: nombre, datos fiscales, bancarios, regional, modalidad de cobro (CUIL solo lectura)
- Crear una bandeja de entrada (inbox) propia para cada usuario donde reciba hilos de mensajes y pueda responder dentro del hilo
- Implementar mensajería interna dirigida entre usuarios registrados del sistema (paralela a las comunicaciones a alumnos)
- Exponer endpoints RESTful `/api/perfil`, `/api/inbox/*` para estas capacidades
- Permitir el cierre de sesión explícito
- Agregar pruebas para la edición de campos, no modificación de CUIL, uso y aislamiento correcto de la mensajería

## Capabilities

### New Capabilities
- `user-profile-edit`: Edición de perfil propio (nombre, datos fiscales/bancarios, regional, modalidad de cobro; CUIL solo lectura)
- `internal-messaging`: Bandeja de mensajes interna, hilo de discusión entre usuarios del sistema

### Modified Capabilities


## Impact

- Se crean nuevos endpoints `/api/perfil`, `/api/inbox/*`
- Afecta modelo de Usuario: distingue campos editables de los de solo lectura (CUIL siempre solo lectura por seguridad)
- Nuevos modelos/módulos para mensajería interna entre usuarios
- Pruebas de endpoints: edición, sesión, mensajería
- Aislamiento multi-tenant: inbox y perfil sólo accesibles/autorizados para el usuario autenticado
