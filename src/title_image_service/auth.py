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


_LOCALHOST_HOSTS = {"127.0.0.1", "::1", "localhost"}


def _is_localhost_only() -> bool:
    return os.environ.get("HOST", "0.0.0.0").lower() in _LOCALHOST_HOSTS


async def verify_api_key(x_api_key: str | None = Header(None, alias="X-API-Key")) -> str | None:
    """FastAPI-Dependency: prüft den X-API-Key Header.

    Wenn keine Keys konfiguriert sind (leere oder fehlende Datei), wird
    offener Zugriff automatisch erlaubt, wenn der Service nur auf localhost
    lauscht (HOST=127.0.0.1 / ::1 / localhost). Andernfalls muss
    ALLOW_UNAUTHENTICATED=true explizit gesetzt werden.
    """
    valid_keys = _load_keys()
    if not valid_keys:
        if _is_localhost_only():
            logger.warning(
                "Keine API-Keys konfiguriert. Service läuft nur auf localhost – "
                "offener Zugriff wird automatisch erlaubt."
            )
            return None
        allow_unauth = os.environ.get("ALLOW_UNAUTHENTICATED", "").lower() == "true"
        if allow_unauth:
            logger.warning(
                "Keine API-Keys konfiguriert. ALLOW_UNAUTHENTICATED=true ist gesetzt – "
                "der Endpunkt ist ohne Authentifizierung erreichbar."
            )
            return None
        raise HTTPException(
            status_code=401,
            detail="Keine API-Keys konfiguriert. Service auf localhost starten oder ALLOW_UNAUTHENTICATED=true setzen.",
        )
    if x_api_key not in valid_keys:
        raise HTTPException(status_code=401, detail="Ungültiger oder fehlender API-Key")
    return x_api_key
