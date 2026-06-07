## 1. Endpoints - Perfil

- [x] 1.1 Crear endpoint `/api/perfil` GET: devuelve perfil propio
- [x] 1.2 Crear endpoint `/api/perfil` PATCH/PUT: edita campos permitidos (valida CUIL solo lectura)
- [x] 1.3 Auditar cambios de perfil
- [x] 1.4 Tests: edición exitosa, rechazo CUIL, cifrado de sensitve, audit log

## 2. Endpoints - Mensajería interna

- [x] 2.1 Modelar entidades Thread y Message en dominio y DB
- [x] 2.2 Crear endpoint `/api/inbox/threads` GET: listar hilos propios
- [x] 2.3 Crear endpoint `/api/inbox/thread/{id}` GET: ver mensajes si es miembro
- [x] 2.4 Crear endpoint `/api/inbox/threads` POST: crear nuevo hilo con usuarios del mismo tenant
- [x] 2.5 Crear endpoint `/api/inbox/thread/{id}/reply` POST: responder si es miembro
- [x] 2.6 Validar y testear aislamiento por tenant y miembro
- [x] 2.7 Auditar todos los mensajes enviados o recibidos
- [x] 2.8 Test de acceso no autorizado, creación, respuestas y aislamiento multi-tenant

## 3. Seguridad y Multiflow

- [x] 3.1 Identidad SIEMPRE desde sesión autenticada (no param)
- [x] 3.2 Tests de cobertura mínima 80% y edge cases: edición de propio perfil, mensajería multi-tenant
- [x] 3.3 Documentar endpoints con contratos OpenAPI
