from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_home():
    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {
        "message": "Student Management API"
    }


def test_get_students():
    response = client.get("/students")

    assert response.status_code == 401


def test_login():
    response = client.post(
        "/auth/login",
        data={
            "username": "Ram",
            "password": "123456"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_get_students_with_token():
    login_response = client.post(
        "/auth/login",
        data={
            "username": "Ram",
            "password": "123456"
        }
    )

    token = login_response.json()["access_token"]

    response = client.get(
        "/students/",
        headers={
            "Authorization": f"Bearer {token}"
        }
    )

    assert response.status_code == 200
