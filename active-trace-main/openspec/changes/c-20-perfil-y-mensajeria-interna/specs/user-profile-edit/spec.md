## ADDED Requirements

### Requirement: Edición segura del perfil propio
El sistema SHALL permitir a todo usuario autenticado editar su nombre, regional, banco, datos fiscales y bancarios, modalidad de cobro y dirección de correo, pero CUIL será solo lectura. Todos los cambios serán auditables y visibles sólo para el usuario y admins con permiso específico.

#### Scenario: Edición exitosa de perfil
- **WHEN** el usuario accede a la opción de editar su perfil, modifica cualquiera de los campos permitidos (excepto CUIL) y confirma
- **THEN** el sistema actualiza el registro, audita el cambio y refleja sólo los nuevos valores editables

#### Scenario: Intento de edición de CUIL
- **WHEN** el usuario intenta modificar el campo CUIL vía el endpoint de perfil
- **THEN** el sistema rechaza la petición (HTTP 400 o 403) y no realiza cambios

#### Scenario: Edición de datos sensibles
- **WHEN** el usuario edita datos bancarios, fiscales o regional
- **THEN** el sistema almacena cifrado en base de datos y NO expone en logs ni en texto plano devoluciones

#### Scenario: Auditar cambios de perfil
- **WHEN** se modifica cualquier campo editable
- **THEN** el sistema registra el cambio en el log de auditoría con el usuario, timestamp y campo afectado
