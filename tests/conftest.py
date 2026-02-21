import json

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def keys_file(tmp_path):
    f = tmp_path / "api_keys.json"
    f.write_text(json.dumps({"keys": ["sk-valid"]}))
    return f


@pytest.fixture()
def client(keys_file, monkeypatch):
    monkeypatch.setenv("API_KEYS_FILE", str(keys_file))
    import title_image_service.auth as auth_mod
    monkeypatch.setattr(auth_mod, "_KEYS_FILE", keys_file)
    from title_image_service.main import app
    return TestClient(app)
