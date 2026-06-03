"""
AES-256 encryption utilities for sensitive data.

Sensitive attributes (DNI, CUIL, CBU, email) are encrypted at rest using
Fernet (symmetric encryption with AES-128 in CBC mode).

The encryption key is loaded from ENCRYPTION_KEY environment variable (32 bytes exactly).
Decryption errors are logged securely without exposing plaintext.
"""

from cryptography.fernet import Fernet, InvalidToken
from app.core.config import Settings
import logging

logger = logging.getLogger(__name__)


def get_cipher_suite() -> Fernet:
    """
    Get the Fernet cipher suite initialized with the encryption key from settings.
    
    The key is loaded from ENCRYPTION_KEY environment variable, which MUST be:
    - Exactly 32 characters (URL-safe Base64 encoded)
    - Kept secret (never committed to version control)
    
    Returns:
        Fernet: Initialized cipher suite
    
    Raises:
        ValueError: If ENCRYPTION_KEY is not properly configured
    """
    try:
        settings = Settings()
        key = settings.ENCRYPTION_KEY.encode() if isinstance(settings.ENCRYPTION_KEY, str) else settings.ENCRYPTION_KEY
        # Fernet key must be URL-safe Base64-encoded (32 bytes → 44 chars)
        # We'll generate a proper Fernet key from the 32-byte encryption key
        from base64 import urlsafe_b64encode
        from cryptography.fernet import Fernet as FernetCipher
        
        # If ENCRYPTION_KEY is 32 bytes, derive a Fernet key from it
        if len(key) == 32:
            proper_key = urlsafe_b64encode(key)  # This creates a 44-char base64
            return FernetCipher(proper_key)
        else:
            # Assume it's already a proper Fernet key
            return FernetCipher(key)
    except Exception as e:
        logger.error(f"Failed to initialize cipher suite: {e}")
        raise ValueError(f"ENCRYPTION_KEY configuration error: {e}")


def encrypt_attr(plaintext: str) -> str:
    """
    Encrypt a sensitive attribute.
    
    Args:
        plaintext: The plain text value to encrypt (e.g., DNI, email)
    
    Returns:
        str: Base64-encoded encrypted cipher text
    
    Raises:
        Exception: If encryption fails (logged securely)
    """
    if not plaintext:
        # Handle empty string gracefully
        return ""
    
    try:
        cipher_suite = get_cipher_suite()
        plaintext_bytes = plaintext.encode('utf-8')
        encrypted_bytes = cipher_suite.encrypt(plaintext_bytes)
        # Return as string (already base64-encoded by Fernet)
        return encrypted_bytes.decode('utf-8')
    except Exception as e:
        logger.error(f"Encryption failed: {type(e).__name__}")
        raise


def decrypt_attr(cipher: str) -> str:
    """
    Decrypt a sensitive attribute.
    
    Args:
        cipher: The base64-encoded cipher text
    
    Returns:
        str: The decrypted plaintext
    
    Raises:
        InvalidToken: If the cipher is invalid or corrupted
        Exception: If decryption fails
    """
    if not cipher:
        return ""
    
    try:
        cipher_suite = get_cipher_suite()
        cipher_bytes = cipher.encode('utf-8')
        plaintext_bytes = cipher_suite.decrypt(cipher_bytes)
        return plaintext_bytes.decode('utf-8')
    except InvalidToken as e:
        logger.error(f"Decryption failed: Invalid token (possible key mismatch or corrupted data)")
        raise
    except Exception as e:
        logger.error(f"Decryption failed: {type(e).__name__}")
        raise


def validate_encryption_key(key: str) -> bool:
    """
    Validate that the encryption key is properly formatted.
    
    Args:
        key: The ENCRYPTION_KEY value
    
    Returns:
        bool: True if valid
    
    Raises:
        ValueError: If key is invalid
    """
    if not isinstance(key, str):
        raise ValueError("ENCRYPTION_KEY must be a string")
    
    # We accept 32-byte keys or proper Fernet keys (44 chars base64)
    if len(key) not in [32, 44]:
        raise ValueError(
            f"ENCRYPTION_KEY must be 32 bytes or 44 chars (Fernet). Got {len(key)}"
        )
    
    return True


def generate_email_hash(email: str) -> str:
    """
    Generate a deterministic HMAC-SHA256 hash of the normalized email
    using the ENCRYPTION_KEY as the salt.
    """
    if not email:
        return ""
    import hmac
    import hashlib
    settings = Settings()
    normalized_email = email.lower().strip()
    # ENCRYPTION_KEY is used as the key for HMAC
    key = settings.ENCRYPTION_KEY.encode('utf-8') if isinstance(settings.ENCRYPTION_KEY, str) else settings.ENCRYPTION_KEY
    return hmac.new(key, normalized_email.encode('utf-8'), hashlib.sha256).hexdigest()



# --- Auth utilities: Password Hashing & JWT ---
from passlib.context import CryptContext
import jwt
from datetime import datetime, timedelta

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, hash: str) -> bool:
    return pwd_context.verify(password, hash)


def create_access_token(data: dict, expires_minutes: int = 15, impersonated_sub: str = None) -> str:
    settings = Settings()
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=expires_minutes)
    to_encode.update({"exp": expire})
    if impersonated_sub:
        to_encode.update({"impersonated_sub": impersonated_sub})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_access_token(token: str) -> dict:
    settings = Settings()
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
