# tests/conftest.py
import pytest
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db import Base, get_db
from app.main import app
from starlette.testclient import TestClient

SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL")
API_TOKEN = os.getenv("PRODUCT_API_TOKEN")


@pytest.fixture(scope="function")
def db_engine():
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db_session(db_engine):
    TestingSessionLocal = sessionmaker(
        autocommit=False, autoflush=False, bind=db_engine
    )
    session = TestingSessionLocal()
    yield session
    session.close()


@pytest.fixture(scope="function")
def auth_headers():
    """Provide authentication headers for tests"""
    api_token = os.getenv("PRODUCT_API_TOKEN", API_TOKEN)
    return {"Authorization": f"Bearer {api_token}"}


@pytest.fixture(scope="function")
def client(db_session):
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def sample_product_data():
    """Provide sample product data for tests"""
    return {
        "name": "Test Produit",
        "price": 12.34,
        "description": "Description test",
        "color": "Rouge",
        "stock": 5,
    }


@pytest.fixture(scope="function")
def created_product(client, auth_headers, sample_product_data):
    """Create a product for tests that need an existing product"""
    response = client.post("/products", json=sample_product_data, headers=auth_headers)
    assert response.status_code == 200
    return response.json()
