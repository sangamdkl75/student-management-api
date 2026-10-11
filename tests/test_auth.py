from datetime import datetime, timedelta, timezone

import jwt
import pytest

import models
from routers import auth as auth_router


@pytest.mark.parametrize("secret_key", [None, "", "too-short"])
def test_secret_key_rejects_missing_or_short_values(secret_key):
    with pytest.raises(RuntimeError):
        auth_router.get_secret_key(secret_key)


def test_secret_key_accepts_at_least_32_bytes():
    secret_key = "x" * 32

    assert auth_router.get_secret_key(secret_key) == secret_key


@pytest.mark.parametrize("value", ["0", "-1", "not-an-integer"])
def test_access_token_lifetime_rejects_invalid_values(value):
    with pytest.raises(RuntimeError):
        auth_router.get_access_token_expiry_minutes(value)


def test_access_token_lifetime_defaults_to_30_minutes():
    assert auth_router.get_access_token_expiry_minutes(None) == 30


def test_login_token_is_valid_and_expires(client):
    test_client, _ = client
    registration = test_client.post(
        "/auth/register",
        json={"username": "token-lifetime-user", "password": "test-only-password"},
    )
    assert registration.status_code == 200
    login = test_client.post(
        "/auth/login",
        data={"username": "token-lifetime-user", "password": "test-only-password"},
    )

    assert login.status_code == 200
    token = login.json()["access_token"]
    claims = jwt.decode(
        token,
        auth_router.SECRET_KEY,
        algorithms=["HS256"],
    )
    remaining_seconds = claims["exp"] - int(datetime.now(timezone.utc).timestamp())
    assert 0 < remaining_seconds <= auth_router.ACCESS_TOKEN_EXPIRE_MINUTES * 60

    response = test_client.get(
        "/students/",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200


def test_expired_access_token_is_rejected(client):
    test_client, _ = client
    registration = test_client.post(
        "/auth/register",
        json={"username": "expired-token-user", "password": "test-only-password"},
    )
    assert registration.status_code == 200
    expired_token = jwt.encode(
        {
            "sub": "expired-token-user",
            "exp": datetime.now(timezone.utc) - timedelta(seconds=1),
        },
        auth_router.SECRET_KEY,
        algorithm="HS256",
    )

    response = test_client.get(
        "/students/",
        headers={"Authorization": f"Bearer {expired_token}"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid token"


def test_register_creates_user_with_hashed_password(client):
    test_client, testing_session_local = client
    response = test_client.post(
        "/auth/register",
        json={"username": "new-user", "password": "a-test-password"}
    )

    assert response.status_code == 200
    assert response.json() == {
        "message": "User registers successfully",
        "username": "new-user"
    }

    with testing_session_local() as db:
        user = db.query(models.User).filter(
            models.User.username == "new-user"
        ).one()

    assert user.password_hash != "a-test-password"
    assert auth_router.password_hash.verify(
        "a-test-password",
        user.password_hash
    )
    assert user.role == "user"


@pytest.mark.parametrize(
    "payload",
    [
        {"username": "", "password": "a-test-password"},
        {"username": "new-user", "password": ""},
        {"username": "new-user"},
    ]
)
def test_register_rejects_invalid_input(client, payload):
    test_client, _ = client

    response = test_client.post("/auth/register", json=payload)

    assert response.status_code == 422


def test_register_rejects_duplicate_username(client):
    test_client, _ = client
    payload = {"username": "existing-user", "password": "a-test-password"}

    first_response = test_client.post("/auth/register", json=payload)
    duplicate_response = test_client.post("/auth/register", json=payload)

    assert first_response.status_code == 200
    assert duplicate_response.status_code == 400
    assert duplicate_response.json()["detail"] == "Username already exists"
