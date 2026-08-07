from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from auth import (
    create_access_token,
    hash_password,
    oauth2_scheme,
    verify_access_token,
    verify_hash_password,
)
from database import get_db
from model import Post, User
from schema import (
    CreateUser,
    PostResponse,
    Token,
    UpdateUser,
    UserPrivateResponse,
    UserResponse,
)

router = APIRouter()


# CREATE USER
@router.post(
    "",
    response_model=UserPrivateResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_user(
    create_user_input: CreateUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):

    # Validate if username exist
    username_exist_stmnt = select(User).where(
        func.lower(User.username) == create_user_input.username.lower(),
    )
    username_exist = (await db.execute(username_exist_stmnt)).scalars().first()

    if username_exist:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exist.",
        )

    # Validate if email is exist
    email_exist_stmnt = select(User).where(
        func.lower(User.email) == create_user_input.email.lower(),
    )
    email_exist = (await db.execute(email_exist_stmnt)).scalars().first()

    if email_exist:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already exist.",
        )

    new_user = User(
        username=create_user_input.username,
        email=create_user_input.email.lower(),
        hash_password=hash_password(create_user_input.password),
    )

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    return new_user


@router.post("/token", response_model=Token)
async def sign_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    query_user = await db.execute(
        select(User).where(func.lower(User.email) == form_data.username.lower()),
    )
    user = query_user.scalars().first()

    if not user or not verify_hash_password(form_data.password, user.hash_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = {
        "sub": str(user.id),
    }

    access_token = create_access_token(data=payload, expire_delta=timedelta(minutes=20))

    return Token(
        access_token=access_token,
        token_type="bearer",  # noqa: S106
    )


@router.get("/me", response_model=UserPrivateResponse)
async def get_authed_user(
    access_token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Verify if access token is valid."""
    decoded_user_id = verify_access_token(access_token)
    if decoded_user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expire access token 1",
            headers={"WWW-Authenticate": "Bearer"},
        )

    """Verify id decoded user id is valid integer."""
    try:
        user_id = int(decoded_user_id)
    except (TypeError, ValueError):
        raise HTTPException(  # noqa: B904
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expire access token 2",
            headers={"WWW-Authenticate": "Bearer"},
        )

    query_user = await db.execute(select(User).where(User.id == user_id))
    user = query_user.scalars().first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expire access token 3",
        )
    return user


# UPDATE USER
@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_data: UpdateUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    # Check if user exist
    stmnt = select(User).where(User.id == user_id)
    user = (await db.execute(stmnt)).scalars().first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )

    # Check if username is in payload and the username already been taken by other user.
    if user_data.username is not None:
        username_stmnt = select(User).where(
            User.username == user_data.username,
        )
        username = (await db.execute(username_stmnt)).scalars().first()

        if username:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken.",
            )

        # set updated username
        user.username = user_data.username

    # Check if email is in payload and the email already been taken by other user.
    if user_data.email is not None:
        email_stmnt = select(User).where(User.email == user_data.email)
        email = (await db.execute(email_stmnt)).scalars().first()

        if email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already taken.",
            )

        # set updated email
        user.email = user_data.email

    # Check if img_path is in payload
    if user_data.img_file is not None:
        user.img_file = user_data.img_file

    await db.commit()
    await db.refresh(user)

    return user


# DELETE USER
@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: int, db: Annotated[AsyncSession, Depends(get_db)]):
    stmnt = select(User).where(User.id == user_id)
    user = (await db.execute(stmnt)).scalars().first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User not found.",
        )

    await db.delete(user)
    await db.commit()


# GET ALL USERS
@router.get("", response_model=list[UserResponse])
async def get_users(db: Annotated[AsyncSession, Depends(get_db)]):
    stmnt = select(User)
    users = (await db.execute(stmnt)).scalars()
    return users


# GET ALL USER POSTS
@router.get("/{user_id}/posts", response_model=list[PostResponse])
async def get_user_posts(user_id: int, db: Annotated[AsyncSession, Depends(get_db)]):
    user_stmnt = select(User).where(User.id == user_id)
    user = (await db.execute(user_stmnt)).scalars().first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"User id {user_id} not found",
        )

    posts_stmnt = (
        select(Post).options(selectinload(Post.author)).where(Post.user_id == user.id)
    )

    posts = (await db.execute(posts_stmnt)).scalars().all()
    return posts
