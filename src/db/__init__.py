from .session import Base, engine, SessionLocal
from . import models  # чтобы модели подцепились, когда импортируем db
