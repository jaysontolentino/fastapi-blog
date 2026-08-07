from datetime import UTC, datetime, timedelta

import jwt
from fastapi.security import OAuth2PasswordBearer
from pwdlib import PasswordHash

from config import settings

password_hash = PasswordHash.recommended()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/users/token")


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_hash_password(password: str, hashed_password: str) -> bool:
    return password_hash.verify(password, hashed_password)


def create_access_token(data: dict, expire_delta: timedelta | None = None) -> str:
    payload = data.copy()

    if expire_delta:
        expire = datetime.now(UTC) + expire_delta
    else:
        expire = datetime.now(UTC) + timedelta(minutes=settings.jwt_expire_minutes)

    payload.update({"exp": expire})

    jwt_encoded = jwt.encode(
        payload=payload,
        key=settings.jwt_secret_key.get_secret_value(),
        algorithm=settings.jwt_algorithm,
    )

    return jwt_encoded


def verify_access_token(token: str) -> str | None:
    try:
        decoded = jwt.decode(
            jwt=token,
            key=settings.jwt_secret_key.get_secret_value(),
            algorithms=[settings.jwt_algorithm],
            options={"require": ["sub", "exp"]},
        )
    except jwt.InvalidTokenError:
        return None
    else:
        return decoded.get("sub")  # this is the user_id
