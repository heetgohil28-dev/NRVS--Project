import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database.connection import Base, get_db
from app.main import app

TEST_DATABASE_URL = "sqlite:///./test_auth.db"

engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def clean_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def registered_user(client):
    client.post("/api/auth/register", json={
        "username": "testuser",
        "email": "testuser@test.com",
        "password": "Test@1234",
        "role": "analyst"
    })
    return {"username": "testuser", "password": "Test@1234"}


@pytest.fixture
def auth_headers(client):
    client.post("/api/auth/register", json={
        "username": "authuser",
        "email": "authuser@test.com",
        "password": "Test@1234",
        "role": "analyst"
    })
    response = client.post("/api/auth/login", json={
        "username": "authuser",
        "password": "Test@1234"
    })
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


class TestRegister:
    def test_register_success(self, client):
        response = client.post("/api/auth/register", json={
            "username": "newuser",
            "email": "newuser@test.com",
            "password": "Test@1234",
            "role": "analyst"
        })
        assert response.status_code == 201
        data = response.json()
        assert data["username"] == "newuser"
        assert "hashed_password" not in data

    def test_register_duplicate_username(self, client, registered_user):
        response = client.post("/api/auth/register", json={
            "username": "testuser",
            "email": "other@test.com",
            "password": "Test@1234",
            "role": "analyst"
        })
        assert response.status_code == 409

    def test_register_duplicate_email(self, client, registered_user):
        response = client.post("/api/auth/register", json={
            "username": "otheruser",
            "email": "testuser@test.com",
            "password": "Test@1234",
            "role": "analyst"
        })
        assert response.status_code == 409

    def test_register_weak_password(self, client):
        response = client.post("/api/auth/register", json={
            "username": "weakuser",
            "email": "weak@test.com",
            "password": "password",
            "role": "analyst"
        })
        assert response.status_code == 422

    def test_register_invalid_role(self, client):
        response = client.post("/api/auth/register", json={
            "username": "roleuser",
            "email": "role@test.com",
            "password": "Test@1234",
            "role": "superadmin"
        })
        assert response.status_code == 422

    def test_register_invalid_username(self, client):
        response = client.post("/api/auth/register", json={
            "username": "u",
            "email": "u@test.com",
            "password": "Test@1234",
            "role": "analyst"
        })
        assert response.status_code == 422


class TestLogin:
    def test_login_success(self, client, registered_user):
        response = client.post("/api/auth/login", json=registered_user)
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    def test_login_wrong_password(self, client, registered_user):
        response = client.post("/api/auth/login", json={
            "username": "testuser",
            "password": "Wrong@1234"
        })
        assert response.status_code == 401

    def test_login_wrong_username(self, client):
        response = client.post("/api/auth/login", json={
            "username": "nonexistent",
            "password": "Test@1234"
        })
        assert response.status_code == 401


class TestMe:
    def test_get_me(self, client, auth_headers):
        response = client.get("/api/auth/me", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "authuser"
        assert "hashed_password" not in data

    def test_get_me_no_token(self, client):
        response = client.get("/api/auth/me")
        assert response.status_code in (401, 403)

    def test_get_me_invalid_token(self, client):
        response = client.get("/api/auth/me", headers={"Authorization": "Bearer invalidtoken"})
        assert response.status_code == 401


class TestRefreshToken:
    def test_refresh_token(self, client, registered_user):
        login = client.post("/api/auth/login", json=registered_user)
        refresh_token = login.json()["refresh_token"]
        response = client.post("/api/auth/refresh", json={"refresh_token": refresh_token})
        assert response.status_code == 200
        assert "access_token" in response.json()

    def test_refresh_with_access_token(self, client, registered_user):
        login = client.post("/api/auth/login", json=registered_user)
        access_token = login.json()["access_token"]
        response = client.post("/api/auth/refresh", json={"refresh_token": access_token})
        assert response.status_code == 401


class TestPasswordChange:
    def test_change_password(self, client, registered_user, auth_headers):
        response = client.post("/api/auth/change-password", json={
            "current_password": "Test@1234",
            "new_password": "NewPass@5678"
        }, headers=auth_headers)
        assert response.status_code == 200

    def test_change_password_wrong_current(self, client):
        client.post("/api/auth/register", json={
            "username": "pwuser",
            "email": "pwuser@test.com",
            "password": "Test@1234",
            "role": "analyst"
        })
        login = client.post("/api/auth/login", json={
            "username": "pwuser", "password": "Test@1234"
        })
        headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
        response = client.post("/api/auth/change-password", json={
            "current_password": "Wrong@1234",
            "new_password": "NewPass@5678"
        }, headers=headers)
        assert response.status_code == 401
