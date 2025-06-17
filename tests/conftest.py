import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.main import create_app
import backend.main  # for patching get_engine & SessionLocal
from backend.models import Base
import backend.db  # so we can patch SessionLocal + engine
from pathlib import Path


@pytest.fixture(scope="session", autouse=True)
def db_engine():
    """Configure test database engine and patch global engine/session makers."""
    test_engine = create_engine(
        "sqlite:///:memory:",
        future=True,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    # Patch core engine and sessionmaker
    backend.db.engine = test_engine
    backend.db.SessionLocal.configure(bind=test_engine)

    # Clear and override global get_engine / get_sessionmaker
    backend.db.get_engine.cache_clear()
    backend.db.get_sessionmaker.cache_clear()
    backend.db.get_engine = lambda db_uri=None: test_engine
    backend.db.get_sessionmaker = lambda db_uri=None: backend.db.SessionLocal

    # Patch backend.main references too
    backend.main.get_engine = backend.db.get_engine
    backend.main.SessionLocal = backend.db.SessionLocal

    # Init test DB schema
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="session")
def app():
    app = create_app()
    app.config.update({"TESTING": True})
    return app


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def db_session():
    db = backend.db.SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def gedcom_path():
    # Adjust if test file lives elsewhere
    return Path(__file__).parent / "data/test_family_events.ged"


@pytest.fixture
def dummy_location_service():
    class Dummy:
        def resolve_location(self, **kwargs):
            class Out:
                normalized_name = "dummy_loc"
                raw_name = "Dummy, Loc"
                latitude = 1.0
                longitude = 2.0
                confidence_score = 1.0
                status = "ok"
                source = "test"
            return Out()
    return Dummy()


@pytest.fixture
def latest_tree_version_id(db_session):
    """Return the most recently created TreeVersion ID from the test DB."""
    row = db_session.execute(
        text("SELECT id FROM tree_versions ORDER BY created_at DESC LIMIT 1")
    ).fetchone()
    assert row is not None, "No tree_versions found in test DB"
    return row[0]
