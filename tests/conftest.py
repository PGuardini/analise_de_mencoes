import sys
from pathlib import Path

import pytest
from sqlmodel import SQLModel, Session, create_engine
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

from app.main import app
from app.models import Brand
from data_manager.database import get_session


@pytest.fixture(name="session")
def session_fixture():
    """Banco SQLite em memória, isolado por teste, já populado com as marcas monitoradas."""
    
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        for brand_name in ["Acme", "Zenith", "Nimbus"]:
            session.add(Brand(name=brand_name))
        session.commit()

        yield session


@pytest.fixture(name="client")
def client_fixture(session):
    """TestClient com a dependência de sessão substituída pelo banco em memória do teste."""

    def get_session_override():
        return session

    app.dependency_overrides[get_session] = get_session_override
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()