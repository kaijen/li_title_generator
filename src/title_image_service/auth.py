import json
import logging
import os
from pathlib import Path

from fastapi import Header, HTTPException

logger = logging.getLogger(__name__)

_KEYS_FILE = Path(os.environ.get("API_KEYS_FILE", "./api_keys.json"))


def _load_keys() -> set[str]:
    """Liest api_keys.json bei jedem Aufruf neu ein."""
    try:
        with open(_KEYS_FILE, encoding="utf-8") as f:
            data = json.load(f)
        return set(data.get("keys", []))
    except FileNotFoundError:
        logger.warning("API-Keys-Datei nicht gefunden: %s", _KEYS_FILE)
        return set()
    except (json.JSONDecodeError, OSError) as e:
        logger.error("Fehler beim Lesen der API-Keys-Datei: %s", e)
        return set()


async def verify_api_key(x_api_key: str | None = Header(None, alias="X-API-Key")) -> str | None:
    """FastAPI-Dependency: prüft den X-API-Key Header.

    Wenn keine Keys konfiguriert sind (leere oder fehlende Datei),
    ist der Endpunkt ohne Authentifizierung erreichbar.
    """
    valid_keys = _load_keys()
    if not valid_keys:
        return None
    if x_api_key not in valid_keys:
        raise HTTPException(status_code=401, detail="Ungültiger oder fehlender API-Key")
    return x_api_key
