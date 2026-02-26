# title-image-service

FastAPI-Webservice, der `generate.py` als HTTP-API bereitstellt.
Clients senden JSON, erhalten ein 16:9-PNG zurück.

## Projektziel

Den bestehenden Bildgenerator (`generate.py`) als installierbares Python-Paket
und Docker-Container betreiben. Authentifizierung über API-Keys in einer lokalen
JSON-Datei, kein Benutzer- oder Rollenkonzept.

---

## Projektstruktur

```
title-image-service/
├── CLAUDE.md
├── pyproject.toml              # Paket-Metadaten und Abhängigkeiten
├── Dockerfile
├── compose.dev.yml             # Lokale Entwicklung (build: .)
├── .dockerignore
├── scripts/
│   └── install_fonts.py        # Font-Download (wird im Dockerfile ausgeführt)
├── src/
│   └── title_image_service/
│       ├── __init__.py
│       ├── main.py             # FastAPI-App, Endpunkte
│       ├── auth.py             # API-Key-Validierung
│       ├── generator.py        # Bildgenerierung (aus generate.py übernommen)
│       └── models.py           # Pydantic-Modelle für Request/Response
├── tests/
│   ├── test_auth.py
│   └── test_generate.py
└── deploy/                     # Betriebskonfiguration (nicht vollständig versioniert)
    ├── .gitignore              # ignoriert compose.yml, .env, api_keys.json
    ├── compose.yml.sample      # Template → cp compose.yml.sample compose.yml
    ├── compose.traefik.yml     # Traefik-Overlay (versioniert, nur .env-Variablen)
    ├── .env.sample             # Template → cp .env.sample .env
    └── api_keys.json.sample    # Template → cp api_keys.json.sample api_keys.json
```

---

## Paket-Setup (pyproject.toml)

Standard-PEP-517-Paket mit `hatchling` und `hatch-vcs`.
Abhängigkeiten: `fastapi`, `uvicorn[standard]`, `pillow`.
Entry-Point: `title-image-service` startet `uvicorn`.

```toml
[build-system]
requires = ["hatchling", "hatch-vcs"]
build-backend = "hatchling.build"

[project]
name = "title-image-service"
dynamic = ["version"]
requires-python = ">=3.11"
dependencies = [
    "fastapi>=0.110",
    "uvicorn[standard]>=0.29",
    "pillow>=10.0",
]

[project.scripts]
title-image-service = "title_image_service.main:run"

[tool.hatch.version]
source = "vcs"

[tool.hatch.version.raw-options]
version_scheme = "post-release"
local_scheme = "node-and-date"

[tool.hatch.build.targets.wheel]
packages = ["src/title_image_service"]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "httpx>=0.27",
    "build>=1.0",
]

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["src"]
```

Die Version wird automatisch aus Git-Tags gelesen. Auf einem Tag `v1.2.0`
ergibt sich `1.2.0`, drei Commits danach `1.2.0.post3+g4a2b1c.d20260225`.
Erstes Tag setzen mit: `git tag v0.1.0`

Installation lokal: `pip install -e .`

---

## API-Key-Authentifizierung (auth.py)

- Keys werden aus `api_keys.json` gelesen (Pfad via Umgebungsvariable
  `API_KEYS_FILE`, Default: `./api_keys.json`)
- Format der Datei:
  ```json
  {
    "keys": [
      "sk-abc123",
      "sk-xyz789"
    ]
  }
  ```
- Die Datei wird bei **jedem Request** neu gelesen – so lassen sich Keys
  hinzufügen oder entfernen ohne Neustart.
- Der Client übergibt den Key als HTTP-Header: `X-API-Key: sk-abc123`
- Ungültiger oder fehlender Key → HTTP 401

**Verhalten wenn keine Keys konfiguriert sind (leere/fehlende Datei):**

| Situation | Verhalten |
|-----------|-----------|
| `HOST=127.0.0.1` (localhost, Default) | Offener Zugriff automatisch erlaubt – keine Variable nötig |
| `HOST=0.0.0.0` | Jeder Request → HTTP 401 |
| `HOST=0.0.0.0` + `ALLOW_UNAUTHENTICATED=true` | Offener Zugriff explizit erlaubt |

Implementierung als FastAPI-Dependency (`Depends(verify_api_key)`), die
in alle geschützten Endpunkte injiziert wird.

---

## Datenmodelle (models.py)

Request-Modell spiegelt die JSON-Eingabe von `generate.py` exakt wider:

```python
class ImageRequest(BaseModel):
    titel:       str  = ""
    text:        str  = ""
    vordergrund: str  = "white"
    hintergrund: str  = "black"
    breite:      int  = 1024
    font:        str  = "Rubik Glitch"
    titelzeilen: int  = 1
    dateiname:   str  = ""  # Leer → linkedin_title_<YYYY-MM-DD-HH-mm>.png
```

Alle Felder optional mit denselben Defaults wie im CLI-Script.

`dateiname` wird per `field_validator` geprüft: nur alphanumerische Zeichen,
Punkte, Bindestriche und Unterstriche, maximal 128 Zeichen. Leerstring (Default)
überspringt die Prüfung.

`dateiname` steuert den `Content-Disposition`-Header der HTTP-Antwort:
- Angegeben: der übergebene Name wird verwendet (z. B. `"nis2-slide.png"`)
- Leer oder weggelassen: automatisch `linkedin_title_<YYYY-MM-DD-HH-mm>.png`

---

## Bildgenerator (generator.py)

`generate.py` wird **nicht kopiert**, sondern sein Kern in `generator.py`
überführt:

- Alle Funktionen (`resolve_font`, `normalize_color`, `wrap_text`,
  `generate_image`, …) bleiben inhaltlich unverändert
- `generate_image()` erhält einen zusätzlichen Parameter `output_path=None`:
  - Wenn `None`: gibt die Bilddaten als `bytes` (PNG) zurück statt zu speichern
  - Wenn Pfad angegeben: verhält sich wie bisher (für CLI-Kompatibilität)
- Font-Cache-Verzeichnis via Umgebungsvariable `FONT_CACHE_DIR`,
  Default: `~/.cache/title-image-fonts`

---

## HTTP-Endpunkte (main.py)

### `POST /generate`
- **Auth**: `X-API-Key` required
- **Body**: `ImageRequest` als JSON
- **Response**: PNG-Bilddaten (`Content-Type: image/png`)
- **Header**: `Content-Disposition: attachment; filename="<dateiname>"`
  – Dateiname aus `dateiname`-Feld oder automatisch `linkedin_title_<YYYY-MM-DD-HH-mm>.png`
- Fehler bei ungültigen Farben oder Parametern → HTTP 422

### `GET /health`
- **Auth**: keine
- **Response**: `{"status": "ok"}`
- Für Docker-Healthcheck und Load-Balancer

### `GET /`
- **Auth**: keine
- **Response**: `{"service": "title-image-service", "docs": "/docs"}`
- Kein Redirect – gibt Service-Info als JSON zurück

---

## Dockerfile

Das Dockerfile akzeptiert ein `VERSION`-Build-Argument, das die Python-Paketversion
und das OCI-Image-Label setzt. Ohne Angabe greift der Default `0.0.0.dev0`.

Da im Docker-Build-Kontext kein `.git` vorhanden ist, wird die Version über
`SETUPTOOLS_SCM_PRETEND_VERSION_FOR_TITLE_IMAGE_SERVICE` an `hatch-vcs` übergeben.

```dockerfile
FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    fontconfig curl && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY pyproject.toml .
COPY src/ src/
ARG VERSION=0.0.0.dev0
RUN SETUPTOOLS_SCM_PRETEND_VERSION_FOR_TITLE_IMAGE_SERVICE=${VERSION} \
    pip install --no-cache-dir .

COPY scripts/install_fonts.py /tmp/install_fonts.py
RUN mkdir -p /fonts-cache \
    && FONT_CACHE_DIR=/fonts-cache python3 /tmp/install_fonts.py \
    && rm /tmp/install_fonts.py

ENV FONT_CACHE_DIR=/fonts-cache
ENV API_KEYS_FILE=/config/api_keys.json

LABEL org.opencontainers.image.version="${VERSION}"

RUN useradd --no-create-home --shell /bin/false appuser \
    && chown -R appuser:appuser /app /fonts-cache
USER appuser

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"
CMD ["title-image-service"]
```

Wichtig: `api_keys.json` **nicht** in das Image kopieren – sie wird als
Volume gemountet (enthält Secrets).

---

## Build-Workflow

Das Projekt nutzt [`just`](https://github.com/casey/just) als Task-Runner.
Installation: `winget install Casey.Just` (Windows) · `brew install just` (macOS/Linux).

Die Version liest `just` über `hatch version` (Windows) oder
`hatch version || git describe --tags --always` (Unix).

| Befehl | Beschreibung |
|--------|--------------|
| `just version` | Aktuelle Version ausgeben |
| `just install` | Dev-Abhängigkeiten im aktiven venv installieren (`pip install -e ".[dev]"`) |
| `just wheel` | Python-Wheel und Source-Distribution bauen (`dist/`) |
| `just dev` | Lokale Entwicklung – baut Image mit aktueller Version und startet via `compose.dev.yml` |
| `just build` | Docker-Image bauen und taggen (`ghcr.io/kaijen/title-image:<VERSION>` + `latest`) |
| `just export` | Docker-Image als `title-image-<VERSION>.tar.gz` exportieren |

**Manuell (ohne just):**

```bash
VERSION=$(git describe --tags --always)

docker build \
  --build-arg VERSION=${VERSION} \
  -t ghcr.io/kaijen/title-image:${VERSION} \
  -t ghcr.io/kaijen/title-image:latest \
  .
```

---

## Betrieb (deploy/)

`deploy/` enthält versionierte Templates und nicht versionierte Betriebsdateien.
`deploy/.gitignore` ignoriert `compose.yml`, `.env` und `api_keys.json`.

### Einmalig einrichten

```bash
cd deploy
cp compose.yml.sample compose.yml
cp .env.sample .env
cp api_keys.json.sample api_keys.json
# IMAGE_TAG, TRAEFIK_HOST etc. in .env anpassen
# API-Keys in api_keys.json eintragen
```

### Starten

```bash
cd deploy
docker compose up -d

# Mit Traefik-Overlay: COMPOSE_FILE=compose.yml:compose.traefik.yml in .env setzen
docker compose up -d
```

`compose.traefik.yml` ist versioniert, weil es ausschließlich Variablen aus `.env`
nutzt und keine instanzspezifischen Hardcodes enthält. Weitere Anpassungen
kommen als zusätzliches Overlay (nicht versioniert).

---

## Lokale Entwicklung

```bash
docker compose -f compose.dev.yml up --build
```

`compose.dev.yml` baut das Image direkt aus dem Quellcode (`build: .`),
setzt `ALLOW_UNAUTHENTICATED=true` und mountet `deploy/api_keys.json.sample`
als Platzhalter.

---

## Uvicorn-Start (main.py → run())

```python
def run():
    import uvicorn
    uvicorn.run(
        "title_image_service.main:app",
        host=os.getenv("HOST", "127.0.0.1"),
        port=int(os.getenv("PORT", 8000)),
        reload=False,
    )
```

---

## Fehlerbehandlung

- Ungültige Farbe (Pillow-Exception) → HTTP 422 mit sprechender Meldung
- Font nicht auflösbar (alle Fallbacks fehlgeschlagen) → HTTP 500
- `api_keys.json` nicht gefunden beim Start → Server startet trotzdem,
  jeder Request → 401 (kein stiller Fehler)
- Jede Exception in `/generate` wird geloggt (inkl. Stacktrace) bevor
  HTTP 500 zurückgegeben wird

---

## Beispiel-Request

```bash
# Mit explizitem Dateinamen
curl -X POST http://localhost:8000/generate \
  -H "X-API-Key: sk-abc123" \
  -H "Content-Type: application/json" \
  -d '{
    "titel": "NIS2 Compliance",
    "text": "Umsetzung in der Praxis",
    "hintergrund": "#1a1a2e",
    "vordergrund": "white",
    "breite": 1920,
    "titelzeilen": 2,
    "dateiname": "nis2-slide.png"
  }' \
  --output nis2-slide.png

# Ohne Dateinamen → linkedin_title_<YYYY-MM-DD-HH-mm>.png im Content-Disposition-Header
curl -X POST http://localhost:8000/generate \
  -H "X-API-Key: sk-abc123" \
  -H "Content-Type: application/json" \
  -d '{"titel": "NIS2 Compliance", "breite": 1920}' \
  -OJ
```

---

## Hinweise für die Implementierung

- `generate_image()` läuft synchron und ist CPU-gebunden. Bei vielen
  gleichzeitigen Requests `asyncio.to_thread()` verwenden, damit der
  Event-Loop nicht blockiert.
- Die Pillow-Operationen erzeugen das Bild im RAM (`io.BytesIO`), kein
  temporäres File auf Disk nötig.
- Logging mit Python `logging` (nicht `print`), Level via Umgebungsvariable
  `LOG_LEVEL` (Default: `INFO`).
