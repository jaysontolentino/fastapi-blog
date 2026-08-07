from datetime import UTC, datetime, timedelta
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pwdlib import PasswordHash
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from database import get_db
from model import User

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


async def get_authed_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    decoded_user_id = verify_access_token(token)

    if not decoded_user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expire token.",
            headers={"WWW-authenticate": "Bearer"},
        )

    try:
        user_id = int(decoded_user_id)
    except (TypeError, ValueError):
        raise HTTPException(  # noqa: B904
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expire token.",
            headers={"WWW-authenticate": "Bearer"},
        )

    query_user = await db.execute(select(User).where(User.id == user_id))
    user = query_user.scalars().first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expire token.",
            headers={"WWW-authenticate": "Bearer"},
        )

    return user


AuthedUser = Annotated[User, Depends(get_authed_user)]
