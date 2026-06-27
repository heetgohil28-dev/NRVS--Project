import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database.connection import Base, get_db
from app.main import app

TEST_DATABASE_URL = "sqlite:///./test_scan.db"

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
def auth_headers(client):
    client.post("/api/auth/register", json={
        "username": "scanuser",
        "email": "scanuser@test.com",
        "password": "Test@1234",
        "role": "analyst"
    })
    response = client.post("/api/auth/login", json={
        "username": "scanuser",
        "password": "Test@1234"
    })
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


class TestScanStart:
    def test_start_scan_no_auth(self, client):
        response = client.post("/api/scan/start", json={
            "targets": ["127.0.0.1"],
            "profile": "quick"
        })
        assert response.status_code in (401, 403)

    def test_start_scan_blocked_custom_args(self, client, auth_headers):
        response = client.post("/api/scan/start", json={
            "targets": ["127.0.0.1"],
            "profile": "quick",
            "custom_args": "-oX /tmp/output.xml"
        }, headers=auth_headers)
        assert response.status_code == 422

    @patch("app.api.scan.run_scan_background")
    def test_start_scan_success(self, mock_bg, client, auth_headers):
        mock_bg.return_value = None
        response = client.post("/api/scan/start", json={
            "targets": ["127.0.0.1"],
            "profile": "quick"
        }, headers=auth_headers)
        assert response.status_code == 202
        data = response.json()
        assert "scan_id" in data
        assert data["status"] == "pending"


class TestScanList:
    def test_list_scans_no_auth(self, client):
        response = client.get("/api/scan/list")
        assert response.status_code in (401, 403)

    def test_list_scans_empty(self, client, auth_headers):
        response = client.get("/api/scan/list", headers=auth_headers)
        assert response.status_code == 200
        assert response.json() == []


class TestScanGet:
    def test_get_nonexistent_scan(self, client, auth_headers):
        response = client.get("/api/scan/9999", headers=auth_headers)
        assert response.status_code == 404

    def test_get_scan_no_auth(self, client):
        response = client.get("/api/scan/1")
        assert response.status_code in (401, 403)


class TestCidrUtils:
    def test_validate_valid_ip(self):
        from app.utils.cidr_utils import is_valid_ip
        assert is_valid_ip("192.168.1.1") is True
        assert is_valid_ip("127.0.0.1") is True

    def test_validate_invalid_ip(self):
        from app.utils.cidr_utils import is_valid_ip
        assert is_valid_ip("999.999.999.999") is False
        assert is_valid_ip("not_an_ip") is False

    def test_validate_cidr(self):
        from app.utils.cidr_utils import is_valid_cidr
        assert is_valid_cidr("192.168.1.0/24") is True
        assert is_valid_cidr("invalid") is False

    def test_expand_cidr(self):
        from app.utils.cidr_utils import expand_cidr
        ips = expand_cidr("192.168.1.0/30")
        assert "192.168.1.1" in ips
        assert "192.168.1.2" in ips

    def test_cidr_too_large(self):
        from app.utils.cidr_utils import expand_cidr
        with pytest.raises(ValueError):
            expand_cidr("10.0.0.0/8")

    def test_nmap_args_blocked_flag(self):
        from app.utils.nmap_args_validator import validate_custom_args
        with pytest.raises(ValueError):
            validate_custom_args("-oX /tmp/out.xml")

    def test_nmap_args_injection(self):
        from app.utils.nmap_args_validator import validate_custom_args
        with pytest.raises(ValueError):
            validate_custom_args("-T4; rm -rf /")

    def test_nmap_args_valid(self):
        from app.utils.nmap_args_validator import validate_custom_args
        result = validate_custom_args("-T4 --open")
        assert result == "-T4 --open"
