# usuario-pii-management Specification

## Purpose

Manage user identities and their sensitive Personal Identifiable Information (PII) securely, ensuring DB-level isolation per tenant and encryption at rest. It also provides the CRUD REST APIs for administrators.

## Requirements

### Requirement: Store Encrypted PII

The system MUST encrypt sensitive user fields (`dni`, `cuil`, `cbu`, `alias_cbu`) at rest using AES-256.

#### Scenario: User creation with PII
- GIVEN valid user data including a DNI
- WHEN the user is created
- THEN the DNI is encrypted before saving to the database
- AND is decrypted transparently when retrieved.

### Requirement: Tenant-Scoped Email Uniqueness

The system MUST enforce that user emails are unique within a tenant using a database constraint on a deterministic hash of the email (`email_hash`), while storing the actual email encrypted.

#### Scenario: Duplicate email in same tenant
- GIVEN a user with email "test@example.com" exists in Tenant A
- WHEN an admin tries to create another user with "test@example.com" in Tenant A
- THEN the system MUST reject the creation with a 409 Conflict based on the `email_hash` constraint.

### Requirement: Admin User Management API

The system MUST provide an `/api/admin/usuarios` endpoint to create, read, update, and delete users, guarded by the `usuarios:gestionar` permission. Sensitive PII MUST NOT be returned unless explicitly requested by authorized clients.

#### Scenario: Fetch user list
- GIVEN an admin with `usuarios:gestionar` permission
- WHEN they request the user list
- THEN the system returns the users with masked or omitted PII fields by default.
