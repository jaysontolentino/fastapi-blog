from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from database import get_db
from model import Post, User
from schema import CreatePost, PostResponse, UpdatePost

router = APIRouter()


# GET ALL POSTS
@router.get("", response_model=list[PostResponse])
async def get_posts(db: Annotated[AsyncSession, Depends(get_db)]):
    stmnt = select(Post).options(selectinload(Post.author))
    posts = (await db.execute(stmnt)).scalars().all()
    return posts


# GET POST BY ID
@router.get("/{post_id}", response_model=PostResponse)
async def get_post(post_id: int, db: Annotated[AsyncSession, Depends(get_db)]):
    post_stmnt = (
        select(Post).options(selectinload(Post.author)).where(Post.id == post_id)
    )
    post = (await db.execute(post_stmnt)).scalars().first()

    if post:
        return post

    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")


# CREATE POST
@router.post(
    "",
    response_model=PostResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_post(
    create_post_input: CreatePost,
    db: Annotated[AsyncSession, Depends(get_db)],
):

    # Validate if user not exist, this is temporary validation
    user_stmnt = select(User).where(User.id == create_post_input.user_id)
    user = (await db.execute(user_stmnt)).scalars().first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User exist",
        )

    new_post = Post(
        title=create_post_input.title,
        body=create_post_input.body,
        tags=create_post_input.tags,
        user_id=create_post_input.user_id,
    )

    db.add(new_post)
    await db.commit()
    await db.refresh(new_post, attribute_names=["author"])

    return new_post


# FULL POST UPDATE
@router.put("/{post_id}", response_model=PostResponse)
async def full_update_post(
    post_id: int,
    post_data: CreatePost,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    stmnt = select(Post).where(Post.id == post_id)
    post = (await db.execute(stmnt)).scalars().first()

    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found.",
        )

    if post.user_id != post_data.user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User not found.",
        )

    post.title = post_data.title
    post.body = post_data.body
    post.tags = post_data.tags

    await db.commit()
    await db.refresh(post, attribute_names=["author"])

    return post


# PARTIAL POST UPDATE
@router.patch("/{post_id}", response_model=PostResponse)
async def partial_update_post(
    post_id: int,
    post_data: UpdatePost,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    stmnt = select(Post).where(Post.id == post_id)
    post = (await db.execute(stmnt)).scalars().first()

    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found.",
        )

    update_post = post_data.model_dump(exclude_unset=True)

    for key, value in update_post.items():
        setattr(post, key, value)

    await db.commit()
    await db.refresh(post, attribute_names=["author"])

    return post


# DELETE POST
@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_post(post_id: int, db: Annotated[AsyncSession, Depends(get_db)]):
    stmnt = select(Post).where(Post.id == post_id)
    post = (await db.execute(stmnt)).scalars().first()

    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found.",
        )

    await db.delete(post)
    await db.commit()
