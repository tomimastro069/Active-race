import sqlalchemy as sa
from sqlalchemy.types import TypeDecorator
from app.core.security import encrypt_attr, decrypt_attr

class EncryptedString(TypeDecorator):
    """
    SQLAlchemy TypeDecorator that encrypts a string value before storing it in the database,
    and decrypts it when retrieving it.
    """
    impl = sa.String
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        return encrypt_attr(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        return decrypt_attr(value)
