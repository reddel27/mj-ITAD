from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import main
from main import app
from models import Base


SQLALCHEMY_DATABASE_URL = "sqlite:///./test_mj_itad.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class FakeGoogleMapsClient:
    def places_nearby(self, location, radius, keyword):
        return {
            "results": [
                {
                    "place_id": "test-place-1",
                    "name": "Test Dispensary",
                    "vicinity": "123 Test St",
                    "geometry": {"location": {"lat": 37.0, "lng": -122.0}},
                }
            ]
        }


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


def setup_function():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    app.dependency_overrides[main.get_db] = override_get_db


def teardown_function():
    app.dependency_overrides.clear()


def test_root_healthcheck():
    client = TestClient(app)
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "MJ-ITAD API is running"}


def test_get_dispensaries_success(monkeypatch):
    monkeypatch.setattr(main, "get_gmaps_client", lambda: FakeGoogleMapsClient())

    client = TestClient(app)
    response = client.get("/dispensaries", params={"lat": 37.0, "lng": -122.0, "radius": 5000})

    assert response.status_code == 200
    payload = response.json()
    assert "dispensaries" in payload
    assert len(payload["dispensaries"]) == 1
    assert payload["dispensaries"][0]["name"] == "Test Dispensary"


def test_get_products_returns_empty_for_missing_dispensary():
    client = TestClient(app)
    response = client.get("/products/999")

    assert response.status_code == 200
    assert response.json() == {"products": []}
