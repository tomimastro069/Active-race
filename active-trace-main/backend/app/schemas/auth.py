from pydantic import BaseModel, EmailStr
from uuid import UUID
from typing import Optional, List

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    refresh_token: Optional[str] = None
    requires_2fa: bool = False

class TokenPayload(BaseModel):
    sub: str  # user_id
    tenant_id: str
    exp: int

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class RefreshRequest(BaseModel):
    refresh_token: str

class Verify2FARequest(BaseModel):
    temporary_token: str
    totp_code: str

class ForgotRequest(BaseModel):
    email: EmailStr

class ResetRequest(BaseModel):
    token: str
    new_password: str

class Enroll2FAResponse(BaseModel):
    secret: str
    provisioning_uri: str

class Enable2FARequest(BaseModel):
    code: str

class CurrentUser(BaseModel):
    id: UUID
    tenant_id: UUID
    email: EmailStr
    # roles se obtienen en C-07/C-04. Lo dejamos vacío por ahora para cumplir la firma.
    roles: List[str] = []
