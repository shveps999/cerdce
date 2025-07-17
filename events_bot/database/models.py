from sqlalchemy import (
    String, Text, DateTime, Boolean, ForeignKey,
    Table, Column, Integer, Enum, BigInteger
)
from sqlalchemy.orm import DeclarativeBase, mapped_column, relationship, Mapped
from typing import List, Optional
import enum
from datetime import datetime

class ModerationAction(enum.Enum):
    APPROVE = 1
    REJECT = 2
    REQUEST_CHANGES = 3

class Base(DeclarativeBase):
    pass

class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now, onupdate=datetime.now, nullable=False
    )

user_categories = Table(
    "user_categories",
    Base.metadata,
    Column("user_id", ForeignKey("users.id"), primary_key=True),
    Column("category_id", ForeignKey("categories.id"), primary_key=True),
)

post_categories = Table(
    "post_categories",
    Base.metadata,
    Column("post_id", ForeignKey("posts.id"), primary_key=True),
    Column("category_id", ForeignKey("categories.id"), primary_key=True),
)

class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger(), primary_key=True)
    username: Mapped[Optional[str]] = mapped_column(String(100))
    first_name: Mapped[Optional[str]] = mapped_column(String(100))
    last_name: Mapped[Optional[str]] = mapped_column(String(100))
    city: Mapped[Optional[str]] = mapped_column(String(100))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Relationships
    categories: Mapped[List["Category"]] = relationship(
        secondary=user_categories, back_populates="users"
    )
    posts: Mapped[List["Post"]] = relationship(back_populates="author")
    likes: Mapped[List["Like"]] = relationship(back_populates="user")

class Category(Base, TimestampMixin):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    description: Mapped[Optional[str]] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    users: Mapped[List[User]] = relationship(
        secondary=user_categories, back_populates="categories"
    )
    posts: Mapped[List["Post"]] = relationship(
        secondary=post_categories, back_populates="categories"
    )

class Post(Base, TimestampMixin):
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    content: Mapped[str] = mapped_column(Text)
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    city: Mapped[Optional[str]] = mapped_column(String(100))
    image_id: Mapped[Optional[str]] = mapped_column(String(255))
    is_approved: Mapped[bool] = mapped_column(Boolean, default=False)
    is_published: Mapped[bool] = mapped_column(Boolean, default=False)
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    author: Mapped["User"] = relationship(back_populates="posts")
    categories: Mapped[List[Category]] = relationship(
        secondary=post_categories, back_populates="posts"
    )
    moderation_records: Mapped[List["ModerationRecord"]] = relationship(
        back_populates="post"
    )
    likes: Mapped[List["Like"]] = relationship(back_populates="post")

class ModerationRecord(Base, TimestampMixin):
    __tablename__ = "moderation_records"

    id: Mapped[int] = mapped_column(primary_key=True)
    post_id: Mapped[int] = mapped_column(ForeignKey("posts.id"))
    moderator_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    action: Mapped[ModerationAction] = mapped_column(Enum(ModerationAction))
    comment: Mapped[Optional[str]] = mapped_column(Text)

    post: Mapped["Post"] = relationship(back_populates="moderation_records")
    moderator: Mapped["User"] = relationship()

class Like(Base, TimestampMixin):
    __tablename__ = "likes"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    post_id: Mapped[int] = mapped_column(ForeignKey("posts.id"))

    user: Mapped["User"] = relationship(back_populates="likes")
    post: Mapped["Post"] = relationship(back_populates="likes")

    __table_args__ = (
        # Уникальный индекс для предотвращения дублирования лайков
    )
