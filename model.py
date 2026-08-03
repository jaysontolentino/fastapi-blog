from __future__ import annotations

import re
import unicodedata
from datetime import UTC, datetime

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import BaseModel


class User(BaseModel):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, index=True, primary_key=True)
    username: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    img_file: Mapped[str | None] = mapped_column(String(255), nullable=True)

    posts: Mapped[list[Post]] = relationship(
        back_populates="author",
        cascade="all, delete-orphan",
    )

    @property
    def img_path(self):
        if self.img_file:
            return f"/media/user_profile/{self.img_file}"
        return "/public/user_profile/default.jpg"


class Post(BaseModel):
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(120), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    tags: Mapped[list[str]] = mapped_column(JSON, default=list)
    user_id: Mapped[int] = mapped_column(ForeignKey(column="users.id"), nullable=False)
    date_posted: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.now(tz=UTC),
    )

    author: Mapped[User] = relationship(back_populates="posts")

    @property
    def slug(self):
        # Convert accents/unicode to ASCII equivalents
        text = (
            unicodedata.normalize("NFKD", self.title)
            .encode("ascii", "ignore")
            .decode("utf-8")
        )
        # Lowercase the text
        text = text.lower()
        # Replace spaces and special characters with hyphens
        text = re.sub(r"[^a-z0-9\s-]", "", text)
        text = re.sub(r"[\s-]+", "-", text)
        # Strip leading/trailing hyphens
        return text.strip("-")
