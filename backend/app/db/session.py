from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import get_settings


class Base(DeclarativeBase):
    pass


_engine = None
_session_local = None


def _build_engine():
    settings = get_settings()
    connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
    return create_engine(settings.database_url, connect_args=connect_args)


def get_engine():
    global _engine, _session_local
    if _engine is None:
        _engine = _build_engine()
        _session_local = sessionmaker(bind=_engine, autoflush=False, autocommit=False)
    return _engine


def get_session_local():
    if _session_local is None:
        get_engine()
    return _session_local


def reset_engine() -> None:
    global _engine, _session_local
    if _engine is not None:
        _engine.dispose()
    _engine = None
    _session_local = None


def get_db() -> Generator[Session, None, None]:
    db = get_session_local()()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    from app.db import models  # noqa: F401

    Base.metadata.create_all(bind=get_engine())
