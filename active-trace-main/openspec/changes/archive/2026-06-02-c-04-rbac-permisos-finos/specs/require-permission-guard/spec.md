## ADDED Requirements

### Requirement: require_permission dependency guard
The system SHALL provide a FastAPI dependency/guard to intercept HTTP requests and assert that the current user possesses the required permission or its `_propio` variant.

#### Scenario: Authorized request
- **GIVEN** an endpoint protected by `require_permission("avisos:publicar")`
- **AND** a user with the permission `avisos:publicar`
- **WHEN** the user calls the endpoint
- **THEN** the request proceeds successfully.

#### Scenario: Unauthorized request
- **GIVEN** an endpoint protected by `require_permission("usuarios:gestionar")`
- **AND** a user without the permission
- **WHEN** the user calls the endpoint
- **THEN** the system aborts the request with 403 Forbidden.
