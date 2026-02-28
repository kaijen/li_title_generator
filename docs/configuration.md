# Konfiguration

Der Service wird vollständig über Umgebungsvariablen konfiguriert.
Keine Konfigurationsdatei erforderlich.

## Umgebungsvariablen

| Variable | Default | Beschreibung |
|----------|---------|--------------|
| `HOST` | `127.0.0.1` | Bind-Adresse von Uvicorn. `127.0.0.1` erlaubt automatisch offenen Zugriff ohne API-Keys. |
| `PORT` | `8000` | HTTP-Port des Servers |
| `API_KEYS_FILE` | `./api_keys.json` | Pfad zur API-Keys-Datei; wird bei jedem Request neu eingelesen |
| `ALLOW_UNAUTHENTICATED` | `false` | Auf `true` setzen, um offenen Zugriff auf `0.0.0.0` ohne API-Key zu erlauben (nur für Entwicklung) |
| `FONT_CACHE_DIR` | `~/.cache/title-image-fonts` | Verzeichnis für heruntergeladene Google-Fonts |
| `LOG_LEVEL` | `INFO` | Log-Level für Python-Logging (`DEBUG`, `INFO`, `WARNING`, `ERROR`) |

## Authentifizierungsverhalten

Das Verhalten hängt davon ab, ob Keys konfiguriert sind und wo der Service lauscht.

**Keys konfiguriert** (mindestens ein Eintrag in `api_keys.json`):

`X-API-Key` muss immer einem Eintrag entsprechen – unabhängig von `HOST` und `ALLOW_UNAUTHENTICATED`.

**Keine Keys konfiguriert** (`api_keys.json` fehlt, leer oder nicht lesbar):

| `HOST` | `ALLOW_UNAUTHENTICATED` | Verhalten |
|--------|-------------------------|-----------|
| `127.0.0.1` (Default) | beliebig | Offener Zugriff automatisch erlaubt |
| `0.0.0.0` | `true` | Offener Zugriff – nur für Entwicklung |
| `0.0.0.0` | `false` (Default) | Jeder Request → 401 |

## API-Keys verwalten

Keys werden in `api_keys.json` gepflegt:

```json
{
  "keys": [
    "sk-abc123",
    "sk-xyz789"
  ]
}
```

Die Datei wird **bei jedem Request** neu eingelesen – Keys können ohne
Service-Neustart hinzugefügt oder entfernt werden.

## Im Docker-Container

In `deploy/compose.yml` werden die Variablen über die `environment`-Sektion
oder eine `.env`-Datei gesetzt. Die `api_keys.json` wird als Read-only-Volume
gemountet – nie ins Image kopiert.

Vollständige Beispiel-Konfiguration: `deploy/.env.sample`
