from sqlmodel import SQLModel # noqa: F401
from sqlmodel import create_engine
from app.core.config import settings

engine = create_engine(settings.DATABASE_URL, echo=False)
