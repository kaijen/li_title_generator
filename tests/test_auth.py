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


# ── GET / Redirect ────────────────────────────────────────────────────────────

def test_root_redirects_to_docs(client):
    resp = client.get("/", follow_redirects=False)
    assert resp.status_code in (301, 302, 307, 308)
    assert resp.headers["location"] == "/docs"


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


# ── api_keys.json fehlt → offener Zugriff (kein Crash) ───────────────────────

def test_missing_keys_file_allows_access(tmp_path, monkeypatch):
    absent = tmp_path / "nonexistent.json"
    monkeypatch.setenv("API_KEYS_FILE", str(absent))
    import title_image_service.auth as auth_mod
    monkeypatch.setattr(auth_mod, "_KEYS_FILE", absent)

    from title_image_service.main import app
    test_client = TestClient(app)
    resp = test_client.post(
        "/generate",
        json={"titel": "Test", "breite": 320},
    )
    assert resp.status_code == 200


# ── Leere Keys-Liste → offener Zugriff ───────────────────────────────────────

def test_empty_keys_list_allows_access(tmp_path, monkeypatch):
    f = tmp_path / "api_keys.json"
    f.write_text(json.dumps({"keys": []}))
    monkeypatch.setenv("API_KEYS_FILE", str(f))
    import title_image_service.auth as auth_mod
    monkeypatch.setattr(auth_mod, "_KEYS_FILE", f)

    from title_image_service.main import app
    test_client = TestClient(app)
    resp = test_client.post(
        "/generate",
        json={"titel": "Test", "breite": 320},
    )
    assert resp.status_code == 200
