# encuentros-gestion Specification

## Purpose

Gestión de clases sincrónicas (encuentros) mediante la creación de slots recurrentes o únicos, generación de instancias, y registro de enlaces de videollamadas y grabaciones.

## Requirements

### Requirement: Crear Encuentro Recurrente

El sistema MUST permitir la creación de un SlotEncuentro recurrente que genere automáticamente N instancias semanales.

#### Scenario: Generación exitosa de instancias recurrentes

- GIVEN un profesor autenticado con permisos de `encuentros:gestionar`
- WHEN crea un encuentro para los lunes a las 18:00 por 4 semanas
- THEN el sistema MUST crear 1 SlotEncuentro
- AND el sistema MUST generar 4 InstanciaEncuentro correspondientes a los próximos 4 lunes a las 18:00
- AND todas las instancias MUST tener el estado `Programado`

#### Scenario: Fallo por falta de permisos

- GIVEN un alumno autenticado
- WHEN intenta crear un encuentro recurrente
- THEN el sistema MUST rechazar la petición con un error `403 Forbidden`

### Requirement: Editar Instancia de Encuentro

El sistema MUST permitir actualizar el estado y los enlaces (videoconferencia y grabación) de una instancia individual.

#### Scenario: Registro de grabación post-encuentro

- GIVEN una instancia en estado `Programado`
- WHEN el profesor actualiza el estado a `Realizado` y proporciona una `video_url`
- THEN el sistema MUST guardar los cambios
- AND la instancia MUST reflejar el nuevo estado y URL

### Requirement: Generar contenido HTML de encuentros

El sistema SHOULD generar un bloque HTML con los encuentros programados para embeber en el LMS.

#### Scenario: Exportación a HTML

- GIVEN una materia con encuentros programados
- WHEN se solicita la vista de exportación
- THEN el sistema MUST devolver un bloque HTML formateado con las fechas, horarios y enlaces de los encuentros
