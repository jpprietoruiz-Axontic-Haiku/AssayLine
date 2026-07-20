import fakeredis
import pytest
from fastapi.testclient import TestClient
from rq import Queue
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.api.reports import get_queue_dependency
from app.core.db import get_db
from app.main import app
from app.models import Base
from app.services import storage


@pytest.fixture()
def db_session_factory(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'test.db'}")
    Base.metadata.create_all(engine)
    yield sessionmaker(bind=engine, autoflush=False, autocommit=False)
    engine.dispose()


@pytest.fixture()
def sync_queue():
    connection = fakeredis.FakeStrictRedis()
    return Queue("ingestion", connection=connection, is_async=False)


DEFAULT_EXTRACTION_RESULT = {
    "fields": [{"name": "ph", "value": 7.2, "unit": None, "confidence": 0.9}]
}


@pytest.fixture()
def client(monkeypatch, tmp_path, db_session_factory, sync_queue):
    monkeypatch.setattr(storage, "_base_dir", lambda: tmp_path / "reports")
    monkeypatch.setattr("app.services.pipeline.get_session_factory", lambda: db_session_factory)
    monkeypatch.setattr(
        "app.services.pipeline.run_extraction_agent", lambda *a, **k: DEFAULT_EXTRACTION_RESULT
    )

    def override_get_db():
        db = db_session_factory()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_queue_dependency] = lambda: sync_queue

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
