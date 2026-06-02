## ADDED Requirements

### Requirement: Database-driven Rol and Permiso catalogs
The system SHALL provide a database-driven catalog for roles and permissions. This catalog SHALL be customizable per tenant, but also support global default system-wide definitions (where `tenant_id` is null).

#### Scenario: Global default role retrieval
- **GIVEN** a tenant and several global default roles (where `tenant_id` is null)
- **WHEN** the system retrieves the available roles for that tenant
- **THEN** it returns the default system-wide roles alongside any tenant-specific custom roles.

#### Scenario: Tenant-specific role overriding
- **GIVEN** a global default role named 'PROFESOR'
- **AND** a custom role in Tenant A also named 'PROFESOR'
- **WHEN** Tenant A queries for the role 'PROFESOR'
- **THEN** the system returns Tenant A's custom role definition instead of the global default one.
