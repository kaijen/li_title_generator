import json
import re

import pytest
from fastapi.testclient import TestClient


# ── Bestehende Tests (Fixtures kommen aus conftest.py) ───────────────────────

def test_health_no_auth(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_generate_missing_key(client):
    # Keys sind konfiguriert → fehlender Header → 401
    resp = client.post("/generate", json={"titel": "Test"})
    assert resp.status_code == 401


def test_generate_invalid_key(client):
    resp = client.post(
        "/generate",
        json={"titel": "Test"},
        headers={"X-API-Key": "sk-wrong"},
    )
    assert resp.status_code == 401


def test_generate_valid_key(client):
    resp = client.post(
        "/generate",
        json={"titel": "Test", "breite": 320},
        headers={"X-API-Key": "sk-valid"},
    )
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "image/png"
    assert resp.content[:4] == b"\x89PNG"


# ── GET / Service-Info ───────────────────────────────────────────────────────

def test_root_returns_service_info(client):
    resp = client.get("/")
    assert resp.status_code == 200
    body = resp.json()
    assert body["service"] == "title-image-service"
    assert body["docs"] == "/docs"


# ── Content-Disposition-Header ────────────────────────────────────────────────

def test_content_disposition_auto_filename(client):
    resp = client.post(
        "/generate",
        json={"titel": "Test", "breite": 320},
        headers={"X-API-Key": "sk-valid"},
    )
    assert resp.status_code == 200
    cd = resp.headers["content-disposition"]
    assert re.search(
        r'filename="linkedin_title_\d{4}-\d{2}-\d{2}-\d{2}-\d{2}\.png"', cd
    ), f"Unerwarteter Content-Disposition-Header: {cd}"


def test_content_disposition_explicit_filename(client):
    resp = client.post(
        "/generate",
        json={"titel": "NIS2", "breite": 320, "dateiname": "nis2-slide.png"},
        headers={"X-API-Key": "sk-valid"},
    )
    assert resp.status_code == 200
    cd = resp.headers["content-disposition"]
    assert 'filename="nis2-slide.png"' in cd


# ── Ungültige Farbe → 422 ─────────────────────────────────────────────────────

def test_generate_invalid_color_returns_422(client):
    resp = client.post(
        "/generate",
        json={"titel": "Test", "breite": 320, "hintergrund": "notacolor!!!"},
        headers={"X-API-Key": "sk-valid"},
    )
    assert resp.status_code == 422


# ── api_keys.json fehlt → 401 (kein stiller Open-Access) ────────────────────

def test_missing_keys_file_denies_access(tmp_path, monkeypatch):
    absent = tmp_path / "nonexistent.json"
    monkeypatch.delenv("ALLOW_UNAUTHENTICATED", raising=False)
    import title_image_service.auth as auth_mod
    monkeypatch.setattr(auth_mod, "_KEYS_FILE", absent)

    from title_image_service.main import app
    test_client = TestClient(app)
    resp = test_client.post(
        "/generate",
        json={"titel": "Test", "breite": 320},
    )
    assert resp.status_code == 401


def test_missing_keys_file_with_allow_unauthenticated(tmp_path, monkeypatch):
    absent = tmp_path / "nonexistent.json"
    monkeypatch.setenv("ALLOW_UNAUTHENTICATED", "true")
    import title_image_service.auth as auth_mod
    monkeypatch.setattr(auth_mod, "_KEYS_FILE", absent)

    from title_image_service.main import app
    test_client = TestClient(app)
    resp = test_client.post(
        "/generate",
        json={"titel": "Test", "breite": 320},
    )
    assert resp.status_code == 200


# ── Leere Keys-Liste → 401 ───────────────────────────────────────────────────

def test_empty_keys_list_denies_access(tmp_path, monkeypatch):
    f = tmp_path / "api_keys.json"
    f.write_text(json.dumps({"keys": []}))
    monkeypatch.delenv("ALLOW_UNAUTHENTICATED", raising=False)
    import title_image_service.auth as auth_mod
    monkeypatch.setattr(auth_mod, "_KEYS_FILE", f)

    from title_image_service.main import app
    test_client = TestClient(app)
    resp = test_client.post(
        "/generate",
        json={"titel": "Test", "breite": 320},
    )
    assert resp.status_code == 401


def test_empty_keys_list_with_allow_unauthenticated(tmp_path, monkeypatch):
    f = tmp_path / "api_keys.json"
    f.write_text(json.dumps({"keys": []}))
    monkeypatch.setenv("ALLOW_UNAUTHENTICATED", "true")
    import title_image_service.auth as auth_mod
    monkeypatch.setattr(auth_mod, "_KEYS_FILE", f)

    from title_image_service.main import app
    test_client = TestClient(app)
    resp = test_client.post(
        "/generate",
        json={"titel": "Test", "breite": 320},
    )
    assert resp.status_code == 200


# ── Content-Type-Validierung ─────────────────────────────────────────────────

def test_wrong_content_type_returns_422(client):
    # FastAPI lehnt Requests ohne application/json mit 422 ab
    resp = client.post(
        "/generate",
        content=b"titel=Test",
        headers={"X-API-Key": "sk-valid", "Content-Type": "application/x-www-form-urlencoded"},
    )
    assert resp.status_code == 422
