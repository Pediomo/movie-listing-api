import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import SessionLocal, init_db, Base, engine

client = TestClient(app)

@pytest.fixture(scope="module")
def test_db():
    Base.metadata.create_all(bind=engine)
    init_db()
    yield
    Base.metadata.drop_all(bind=engine)

def test_create_movie(test_db):
    token = "your_test_token_here"  # Replace with a valid token
    response = client.post("/movies/", json={"title": "Test Movie", "description": "A test movie", "release_year": 2024}, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["title"] == "Test Movie"

def test_read_movies(test_db):
    response = client.get("/movies/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
