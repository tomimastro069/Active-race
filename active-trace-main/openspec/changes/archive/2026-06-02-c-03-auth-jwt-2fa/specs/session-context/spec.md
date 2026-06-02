## ADDED Requirements

### Requirement: Identity and Tenant Resolution (Golden Rule)
The system SHALL resolve the authenticated user's identity, tenant context, and roles exclusively from a verified JWT access token. No request parameters, headers, or payload fields SHALL override this context.

#### Scenario: Valid Access Token Resolution
- **WHEN** a request provides a valid JWT access token
- **THEN** the system extracts `user_id`, `tenant_id`, and `roles` from the payload, populating a `CurrentUser` context

#### Scenario: Missing or Invalid Token
- **WHEN** a request to a protected endpoint lacks a valid JWT
- **THEN** the system rejects the request with 401 Unauthorized

### Requirement: FastAPI Security Dependency
The system SHALL provide a FastAPI dependency `get_current_user` that enforces token validation and provides the resolved identity context to protected routes.

#### Scenario: Route Protection
- **WHEN** an endpoint uses the `get_current_user` dependency
- **THEN** it executes only if the token is valid, receiving the `CurrentUser` object
