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

def test_add_comment(test_db):
    token = "your_test_token_here"  # Replace with a valid token
    response = client.post("/comments/", json={"movie_id": 1, "text": "Great movie!"}, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["text"] == "Great movie!"
