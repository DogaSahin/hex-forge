from sqlalchemy import text

from app.core.database import Base, SessionLocal, engine, get_db


def test_engine_is_sqlite():
    assert engine.url.get_backend_name() == "sqlite"


def test_base_has_metadata():
    assert hasattr(Base, "metadata")


def test_get_db_yields_working_session():
    gen = get_db()
    db = next(gen)
    try:
        assert db.execute(text("SELECT 1")).scalar() == 1
    finally:
        gen.close()


def test_session_local_bound_to_engine():
    session = SessionLocal()
    try:
        assert session.get_bind() is engine
    finally:
        session.close()
