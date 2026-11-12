from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError

_hasher = PasswordHasher()

# Verified against when an email is unknown, so a failed login takes the same time either way
# and response timing doesn't reveal which emails are registered.
_DUMMY_HASH = _hasher.hash("not-a-real-password")


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password_hash: str, password: str) -> bool:
    try:
        return _hasher.verify(password_hash, password)
    except (VerificationError, InvalidHashError):
        return False


def verify_dummy_password(password: str) -> None:
    verify_password(_DUMMY_HASH, password)
