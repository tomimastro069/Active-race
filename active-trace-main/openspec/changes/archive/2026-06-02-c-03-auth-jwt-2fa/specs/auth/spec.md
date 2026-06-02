## ADDED Requirements

### Requirement: Email and Password Login
The system SHALL allow users to authenticate using their email and password. Passwords MUST be verified against an Argon2id hash. Upon success, the system SHALL issue an access token and a refresh token.

#### Scenario: Successful Login
- **WHEN** user provides valid email and password
- **THEN** system returns an access token (JWT, 15m expiration) and a refresh token (stored in DB)

#### Scenario: Invalid Credentials
- **WHEN** user provides invalid email or password
- **THEN** system returns 401 Unauthorized

### Requirement: Refresh Token Rotation
The system SHALL support session extension via refresh tokens. When a valid refresh token is presented, the system SHALL issue a new access token and a NEW refresh token, revoking the old refresh token.

#### Scenario: Successful Token Refresh
- **WHEN** user provides a valid refresh token
- **THEN** system issues new access and refresh tokens, and invalidates the old refresh token

#### Scenario: Refresh Token Reuse Detection
- **WHEN** user provides a refresh token that has already been used
- **THEN** system revokes ALL refresh tokens for that user session and returns 401 Unauthorized

### Requirement: Optional 2FA Support
The system SHALL support a two-factor authentication flow if the user or tenant requires it.

#### Scenario: 2FA Required on Login
- **WHEN** user provides valid credentials but 2FA is enabled
- **THEN** system returns a temporary `2fa_required` token instead of access/refresh tokens

#### Scenario: Successful 2FA Verification
- **WHEN** user submits a valid TOTP code along with the `2fa_required` token
- **THEN** system returns full access and refresh tokens

### Requirement: Password Recovery
The system SHALL allow users to recover their passwords securely.

#### Scenario: Password Recovery Request
- **WHEN** user requests password recovery for a valid email
- **THEN** system generates a single-use token and sends a recovery email

#### Scenario: Successful Password Reset
- **WHEN** user submits a new password with a valid recovery token
- **THEN** system updates the password hash, invalidates the token, and revokes all active sessions for the user
