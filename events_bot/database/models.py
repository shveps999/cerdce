from sqlalchemy import (
    String,
    Text,
    DateTime,
    Boolean,
    ForeignKey,
    Table,
    func,
    Column,
    Integer,
    Enum as SQLAlchemyEnum,
    BigInteger,
)
from sqlalchemy.orm import DeclarativeBase, mapped_column, relationship
from sqlalchemy.orm import Mapped
from typing import List, Optional, Dict
import enum


# Enum для действий модерации
class ModerationAction(enum.Enum):
    APPROVE = 1
    REJECT = 2
    REQUEST_CHANGES = 3


# Базовый класс для моделей в стиле SQLAlchemy 2.0
class Base(DeclarativeBase):
    pass


# Базовый класс с полями времени
class TimestampMixin:
    """Миксин для добавления полей времени создания и обновления"""

    created_at: Mapped[DateTime] = mapped_column(
        DateTime, default=func.now(), nullable=False
    )
    updated_at: Mapped[DateTime] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now(), nullable=False
    )


# Таблица связи многие-ко-многим для пользователей и категорий
user_categories = Table(
    "user_categories",
    Base.metadata,
    Column("user_id", ForeignKey("users.id"), primary_key=True),
    Column("category_id", ForeignKey("categories.id"), primary_key=True),
)

# Таблица связи многие-ко-многим для постов и категорий
post_categories = Table(
    "post_categories",
    Base.metadata,
    Column("post_id", ForeignKey("posts.id"), primary_key=True),
    Column("category_id", ForeignKey("categories.id"), primary_key=True),
)


class CategoryNames:
    """Класс для работы с текстовыми названиями категорий"""
    
    # Словарь соответствия ID категорий и их текстовых названий (без эмодзи)
    TEXT_NAMES: Dict[int, str] = {
        1: "Вечеринки",
        2: "Спорт",
        3: "Культура",
        4: "Наука",
        5: "Бизнес",
        6: "Медицина",
        7: "Образование",
        8: "Путешествия",
        9: "Кулинария",
        10: "Театр",
        11: "Настолки",
        12: "Музыка",
        13: "Кино",
        15: "Игры"
    }

    @classmethod
    def get_text_name(cls, category_id: int) -> str:
        """Возвращает текстовое название категории по ID"""
        return cls.TEXT_NAMES.get(category_id, "Неизвестная категория")

    @classmethod
    def get_all_categories(cls) -> Dict[int, str]:
        """Возвращает словарь всех категорий {id: название}"""
        return cls.TEXT_NAMES.copy()


class User(Base, TimestampMixin):
    """Модель пользователя Telegram"""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(
        BigInteger(), primary_key=True
    )  # ID пользователя в Telegram
    username: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    first_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    last_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    city: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Связи
    categories: Mapped[List["Category"]] = relationship(
        secondary=user_categories, back_populates="users"
    )
    posts: Mapped[List["Post"]] = relationship(back_populates="author")


class Category(Base, TimestampMixin):
    """Модель категории"""

    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Связи
    users: Mapped[List[User]] = relationship(
        secondary=user_categories, back_populates="categories"
    )
    posts: Mapped[List["Post"]] = relationship(
        secondary=post_categories, back_populates="categories"
    )

    @property
    def text_name(self) -> str:
        """Возвращает текстовое название категории (без эмодзи) для уведомлений"""
        return CategoryNames.get_text_name(self.id)


class Post(Base, TimestampMixin):
    """Модель поста"""

    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    city: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    image_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_approved: Mapped[bool] = mapped_column(Boolean, default=False)
    is_published: Mapped[bool] = mapped_column(Boolean, default=False)
    published_at: Mapped[Optional[DateTime]] = mapped_column(DateTime, nullable=True)

    # Связи
    author: Mapped[User] = relationship(back_populates="posts")
    categories: Mapped[List[Category]] = relationship(
        secondary=post_categories, back_populates="posts"
    )
    moderation_records: Mapped[List["ModerationRecord"]] = relationship(
        back_populates="post"
    )

    def get_category_text_names(self) -> List[str]:
        """Возвращает список текстовых названий категорий поста"""
        return [category.text_name for category in self.categories]


class ModerationRecord(Base, TimestampMixin):
    """Модель записи модерации"""

    __tablename__ = "moderation_records"

    id: Mapped[int] = mapped_column(primary_key=True)
    post_id: Mapped[int] = mapped_column(ForeignKey("posts.id"), nullable=False)
    moderator_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    action: Mapped[ModerationAction] = mapped_column(
        SQLAlchemyEnum(ModerationAction), nullable=False
    )
    comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Связи
    post: Mapped[Post] = relationship(back_populates="moderation_records")
    moderator: Mapped[User] = relationship()


class Like(Base, TimestampMixin):
    """Модель лайка пользователя на пост"""

    __tablename__ = "likes"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    post_id: Mapped[int] = mapped_column(ForeignKey("posts.id"), nullable=False)

    # Связи
    user: Mapped[User] = relationship()
    post: Mapped[Post] = relationship()

    # Уникальный индекс для предотвращения дублирования лайков
    __table_args__ = (
        # Один пользователь может поставить только один лайк на один пост
    )
