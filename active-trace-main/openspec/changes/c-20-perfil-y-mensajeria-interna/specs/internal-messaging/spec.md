## ADDED Requirements

### Requirement: Mensajería interna estrictamente privada entre usuarios
El sistema SHALL proveer a cada usuario autenticado un inbox privado con soporte de hilos donde puede leer y responder solo los mensajes de los hilos en los que participa; el inbox no es público ni visible fuera de los miembros del hilo.

#### Scenario: Visualización de mensajes
- **WHEN** el usuario accede a su inbox
- **THEN** sólo ve los hilos en los que es miembro.

#### Scenario: Envío de mensaje dentro de un hilo
- **WHEN** el usuario responde a un hilo del inbox
- **THEN** el mensaje es visible sólo para miembros de ese hilo y se registra en la auditoría

#### Scenario: Intento de acceso no autorizado
- **WHEN** un usuario solicita acceder a un hilo o mensaje donde no es miembro
- **THEN** se retorna HTTP 403 Forbidden

#### Scenario: Creación de nuevos hilos
- **WHEN** un usuario inicia un nuevo hilo con otro usuario válido
- **THEN** se crea el hilo de conversación y ambos miembros lo ven en su inbox

#### Scenario: Aislamiento multi-tenant
- **WHEN** un usuario de un tenant intenta comunicarse fuera de su tenant
- **THEN** el sistema rechaza la operación (HTTP 403) y no cruza mensajes
