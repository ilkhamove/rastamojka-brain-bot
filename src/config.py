import os
from pathlib import Path

from dotenv import load_dotenv

# Абсолютный путь к корню проекта
BASE_DIR = Path(__file__).resolve().parent.parent

# Явно грузим .env из корня проекта, а не из текущей папки
env_path = BASE_DIR / ".env"
load_dotenv(env_path)


class Settings:
    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///rastamojka_brain.db")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")


settings = Settings()
