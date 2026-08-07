from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.exception_handlers import (
    http_exception_handler,
    request_validation_exception_handler,
)
from fastapi.exceptions import RequestValidationError
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from starlette.exceptions import HTTPException as StarletteHTTPException

import model
from database import BaseModel, engine, get_db
from routes import posts, users


@asynccontextmanager
async def lifespan(_app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(BaseModel.metadata.create_all)

    yield

    await engine.dispose()


app = FastAPI(lifespan=lifespan)

template = Jinja2Templates(directory="templates")

app.mount("/public", StaticFiles(directory="public"), name="static")
app.mount("/media", StaticFiles(directory="media"), name="media")


# ================== API ENDPOINTS ======================== #
app.include_router(users.router, prefix="/api/users", tags=["users"])
app.include_router(posts.router, prefix="/api/posts", tags=["posts"])


@app.get("/login", include_in_schema=False)
def login(req: Request):
    return template.TemplateResponse(request=req, name="auth/login.html")


@app.get("/register", include_in_schema=False)
def register(req: Request):
    return template.TemplateResponse(request=req, name="auth/register.html")


@app.get("/my-account", include_in_schema=False, name="my_account")
def my_account(req: Request):
    return template.TemplateResponse(request=req, name="users/my-account.html")


@app.get("/", include_in_schema=False, name="home")
@app.get("/posts", include_in_schema=False, name="posts")
async def index(req: Request, db: Annotated[AsyncSession, Depends(get_db)]):
    stmnt = (
        select(model.Post)
        .options(selectinload(model.Post.author))
        .order_by(model.Post.date_posted.desc())
    )
    posts = (await db.execute(stmnt)).scalars().all()
    return template.TemplateResponse(
        request=req,
        name="posts/index.html",
        context={"title": "Home", "posts": posts, "flash": None, "errors": None},
    )


@app.get("/posts/{post_id}", include_in_schema=False)
async def show_post(
    req: Request,
    post_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    stmnt = (
        select(model.Post)
        .options(selectinload(model.Post.author))
        .where(model.Post.id == post_id)
    )
    post = (await db.execute(stmnt)).scalars().first()

    if post:
        return template.TemplateResponse(
            request=req,
            name="posts/show.html",
            context={"post": post, "flash": None, "errors": None},
        )

    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="post not found")


@app.get("/users/{user_id}/posts", include_in_schema=False, name="user_posts")
async def show_user_posts(
    req: Request,
    user_id: int,
    db: Annotated[
        AsyncSession,
        Depends(get_db),
    ],
):

    user_stmnt = select(model.User).where(model.User.id == user_id)
    user = (await db.execute(user_stmnt)).scalars().first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User not exist",
        )

    posts_stmnt = (
        select(model.Post)
        .options(selectinload(model.Post.author))
        .where(model.Post.user_id == user.id)
    )
    user_posts = (await db.execute(posts_stmnt)).scalars().all()

    return template.TemplateResponse(
        request=req,
        name="posts/user-posts.html",
        context={
            "posts": user_posts,
            "user": user,
            "flash": None,
            "errors": None,
        },
    )


# Global error handler
errors = {
    400: {"title": "Bad request", "sub": "The request couldn't be understood."},
    401: {"title": "Not authenticated", "sub": "You need to sign in to access this."},
    403: {"title": "Access forbidden", "sub": "You don't have permission to do that."},
    404: {"title": "Post not found", "sub": "This post doesn't exist or was moved."},
    408: {"title": "Request timeout", "sub": "The server took too long to respond."},
    409: {"title": "Conflict", "sub": "The request conflicts with existing data."},
    410: {"title": "Gone", "sub": "This resource has been permanently removed."},
    422: {
        "title": "Unprocessable content",
        "sub": "The submitted data couldn't be processed.",
    },
    429: {
        "title": "Too many requests",
        "sub": "Slow down — you've hit the rate limit.",
    },
    500: {"title": "Internal server error", "sub": "Something went wrong on our end."},
    502: {
        "title": "Bad gateway",
        "sub": "An upstream service returned an invalid response.",
    },
    503: {
        "title": "Service unavailable",
        "sub": "The server is temporarily down for maintenance.",
    },
}


@app.exception_handler(StarletteHTTPException)
async def global_error_handler(req: Request, exception: StarletteHTTPException):
    message = exception.detail or "Something went wrong."

    if req.url.path.startswith("/api"):
        return await http_exception_handler(req, exception)

    return template.TemplateResponse(
        request=req,
        name="errors/error.html",
        context={
            "title": exception.status_code,
            "message": message,
            "status_code": exception.status_code,
            "info": errors[exception.status_code],
        },
        status_code=exception.status_code,
    )


@app.exception_handler(RequestValidationError)
async def global_validation_error_handler(
    req: Request,
    exception: RequestValidationError,
):
    if req.url.path.startswith("/api"):
        return await request_validation_exception_handler(req, exception)

    return template.TemplateResponse(
        request=req,
        name="errors/error.html",
        context={
            "title": status.HTTP_422_UNPROCESSABLE_CONTENT,
            "status_code": status.HTTP_422_UNPROCESSABLE_CONTENT,
            "info": errors[status.HTTP_422_UNPROCESSABLE_CONTENT],
        },
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
    )
