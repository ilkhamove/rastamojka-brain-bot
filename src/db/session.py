from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

from src.config import settings


class Base(DeclarativeBase):
    """Базовый класс для всех моделей SQLAlchemy."""
    pass


engine = create_engine(
    settings.DATABASE_URL,
    echo=False,
    future=True,
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)


def get_db():
    """Генератор сессии базы данных (на будущее)."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
