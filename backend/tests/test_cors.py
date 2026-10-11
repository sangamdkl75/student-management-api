import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from fastapi.middleware.cors import CORSMiddleware

from main import app, get_allowed_origins


@pytest.mark.parametrize(
    "origin",
    [
        "http://127.0.0.1:5500",
        "http://localhost:5500",
    ]
)
def test_cors_allows_local_frontend_origins(origin):
    response = TestClient(app).options(
        "/",
        headers={
            "Origin": origin,
            "Access-Control-Request-Method": "GET",
        }
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == origin
    assert response.headers["access-control-allow-credentials"] == "true"


def test_cors_rejects_unconfigured_origin():
    response = TestClient(app).options(
        "/",
        headers={
            "Origin": "https://untrusted.example",
            "Access-Control-Request-Method": "GET",
        }
    )

    assert response.status_code == 400
    assert "access-control-allow-origin" not in response.headers


def test_allowed_origins_accepts_explicit_production_origin():
    assert get_allowed_origins("https://frontend.example") == [
        "http://127.0.0.1:5500",
        "http://localhost:5500",
        "https://frontend.example",
    ]


def test_cors_allows_only_configured_production_origin_with_credentials():
    production_origin = "https://configured-frontend.example"
    test_app = FastAPI()
    test_app.add_middleware(
        CORSMiddleware,
        allow_origins=get_allowed_origins(production_origin),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @test_app.get("/")
    def home():
        return {"message": "test"}

    client = TestClient(test_app)

    allowed_response = client.get(
        "/",
        headers={"Origin": production_origin}
    )
    disallowed_response = client.get(
        "/",
        headers={"Origin": "https://untrusted.example"}
    )

    assert (
        allowed_response.headers["access-control-allow-origin"]
        == production_origin
    )
    assert (
        allowed_response.headers["access-control-allow-credentials"]
        == "true"
    )
    assert "access-control-allow-origin" not in disallowed_response.headers


@pytest.mark.parametrize(
    "origin",
    [
        "*",
        "https://*.example.com",
        "https://frontend.example/path",
        "ftp://frontend.example",
    ]
)
def test_allowed_origins_rejects_non_origin_values(origin):
    with pytest.raises(ValueError):
        get_allowed_origins(origin)
