## ADDED Requirements

### Requirement: Monitorización avanzada
El sistema DEBERÁ exponer métricas clave y disparar alertas ante incidentes definidos por la operación.

#### Scenario: Métrica crítica cae fuera de umbral
- **WHEN** una métrica, como uso de CPU o latencia, excede el umbral definido
- **THEN** dispara alerta inmediata y deja traza en logs
