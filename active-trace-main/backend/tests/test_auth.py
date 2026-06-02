import pytest
from httpx import ASGITransport, AsyncClient
import uuid
import time
from app.main import app
from app.models.usuario import Usuario
from app.models.token_refresco import TokenRefresco
from app.core.security import hash_password
from app.core.dependencies import get_db
from app.services.auth import login_rate_limiter, verify_totp

def calculate_totp_test(secret: str) -> str:
    """Helper to calculate current TOTP code for testing"""
    import base64, struct, hmac, hashlib
    secret = secret.upper().replace(" ", "")
    missing_padding = len(secret) % 8
    if missing_padding:
        secret += '=' * (8 - missing_padding)
    key = base64.b32decode(secret)
    t = int(time.time()) // 30
    msg = struct.pack(">Q", t)
    hmac_hash = hmac.new(key, msg, hashlib.sha1).digest()
    offset = hmac_hash[-1] & 0x0f
    binary = struct.unpack(">I", hmac_hash[offset:offset+4])[0] & 0x7fffffff
    return str(binary % 1000000).zfill(6)

@pytest.fixture(autouse=True)
def clear_rate_limiter():
    """Clear login rate limiter history before each test"""
    login_rate_limiter._history.clear()

@pytest.mark.asyncio
async def test_login_success_and_refresh_rotation(db_session):
    # Setup test user
    tenant_id = uuid.uuid4()
    password = "secure_password_123"
    hashed = hash_password(password)
    user = Usuario(
        tenant_id=tenant_id,
        email="test_login@example.com",
        hashed_password=hashed,
        estado="Activo"
    )
    db_session.add(user)
    await db_session.commit()

    # Override get_db dependency to use our test db_session
    app.dependency_overrides[get_db] = lambda: db_session

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # 1. Login
        login_data = {
            "email": "test_login@example.com",
            "password": password
        }
        res_login = await ac.post("/api/v1/auth/login", json=login_data)
        assert res_login.status_code == 200
        tokens = res_login.json()
        assert "access_token" in tokens
        assert "refresh_token" in tokens
        assert tokens["requires_2fa"] is False

        # 2. Refresh Token
        refresh_token = tokens["refresh_token"]
        refresh_data = {"refresh_token": refresh_token}
        res_refresh = await ac.post("/api/v1/auth/refresh", json=refresh_data)
        assert res_refresh.status_code == 200
        new_tokens = res_refresh.json()
        assert "access_token" in new_tokens
        assert "refresh_token" in new_tokens
        assert new_tokens["refresh_token"] != refresh_token

        # 3. Reuse old refresh token (should be rejected)
        res_reuse = await ac.post("/api/v1/auth/refresh", json=refresh_data)
        assert res_reuse.status_code == 401

    app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_login_invalid_credentials(db_session):
    app.dependency_overrides[get_db] = lambda: db_session
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        login_data = {
            "email": "nonexistent@example.com",
            "password": "wrongpassword"
        }
        res = await ac.post("/api/v1/auth/login", json=login_data)
        assert res.status_code == 401

    app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_login_rate_limiting(db_session):
    app.dependency_overrides[get_db] = lambda: db_session
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        login_data = {
            "email": "rate_limit@example.com",
            "password": "anypassword"
        }
        # First 5 attempts should not trigger rate limit (they return 401 or 200, not 429)
        for _ in range(5):
            res = await ac.post("/api/v1/auth/login", json=login_data)
            assert res.status_code != 429
            
        # 6th attempt should return 429
        res = await ac.post("/api/v1/auth/login", json=login_data)
        assert res.status_code == 429
        assert "Too many login attempts" in res.json()["detail"]

    app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_password_recovery_forgot_and_reset(db_session):
    # Setup test user
    tenant_id = uuid.uuid4()
    user = Usuario(
        tenant_id=tenant_id,
        email="recover@example.com",
        hashed_password=hash_password("old_pass_123"),
        estado="Activo"
    )
    db_session.add(user)
    await db_session.commit()

    app.dependency_overrides[get_db] = lambda: db_session

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # 1. Request recovery token
        res_forgot = await ac.post("/api/v1/auth/forgot", json={"email": "recover@example.com"})
        assert res_forgot.status_code == 200
        forgot_data = res_forgot.json()
        assert "token" in forgot_data
        reset_token = forgot_data["token"]

        # 2. Reset password
        reset_data = {
            "token": reset_token,
            "new_password": "new_awesome_password_456"
        }
        res_reset = await ac.post("/api/v1/auth/reset", json=reset_data)
        assert res_reset.status_code == 200
        assert res_reset.json()["message"] == "Password reset successfully"

        # 3. Verify login works with new password
        login_data = {
            "email": "recover@example.com",
            "password": "new_awesome_password_456"
        }
        res_login = await ac.post("/api/v1/auth/login", json=login_data)
        assert res_login.status_code == 200

    app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_2fa_full_lifecycle(db_session):
    # Setup test user
    tenant_id = uuid.uuid4()
    user = Usuario(
        tenant_id=tenant_id,
        email="twofa@example.com",
        hashed_password=hash_password("mypassword123"),
        estado="Activo"
    )
    db_session.add(user)
    await db_session.commit()

    app.dependency_overrides[get_db] = lambda: db_session

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Log in first to get an access token to enroll 2FA
        res_login_init = await ac.post("/api/v1/auth/login", json={
            "email": "twofa@example.com",
            "password": "mypassword123"
        })
        access_token = res_login_init.json()["access_token"]
        headers = {"Authorization": f"Bearer {access_token}"}

        # 1. Enroll 2FA
        res_enroll = await ac.post("/api/v1/auth/enroll-2fa", headers=headers)
        assert res_enroll.status_code == 200
        enroll_data = res_enroll.json()
        assert "secret" in enroll_data
        assert "provisioning_uri" in enroll_data
        secret = enroll_data["secret"]

        # 2. Try enabling 2FA with incorrect code
        res_enable_fail = await ac.post("/api/v1/auth/enable-2fa", json={"code": "000000"}, headers=headers)
        assert res_enable_fail.status_code == 400

        # 3. Enable 2FA with correct code
        correct_code = calculate_totp_test(secret)
        res_enable_ok = await ac.post("/api/v1/auth/enable-2fa", json={"code": correct_code}, headers=headers)
        assert res_enable_ok.status_code == 200

        # 4. Try logging in again (should now require 2FA)
        res_login_2fa = await ac.post("/api/v1/auth/login", json={
            "email": "twofa@example.com",
            "password": "mypassword123"
        })
        assert res_login_2fa.status_code == 200
        token_2fa_data = res_login_2fa.json()
        assert token_2fa_data["requires_2fa"] is True
        temp_token = token_2fa_data["access_token"]
        assert token_2fa_data["refresh_token"] is None

        # 5. Verify 2FA with wrong code
        res_verify_fail = await ac.post("/api/v1/auth/verify-2fa", json={
            "temporary_token": temp_token,
            "totp_code": "000000"
        })
        assert res_verify_fail.status_code == 401

        # 6. Verify 2FA with correct code
        correct_code_2 = calculate_totp_test(secret)
        res_verify_ok = await ac.post("/api/v1/auth/verify-2fa", json={
            "temporary_token": temp_token,
            "totp_code": correct_code_2
        })
        assert res_verify_ok.status_code == 200
        final_tokens = res_verify_ok.json()
        assert "access_token" in final_tokens
        assert "refresh_token" in final_tokens
        assert final_tokens["requires_2fa"] is False

    app.dependency_overrides.clear()
