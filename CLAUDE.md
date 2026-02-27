# CLAUDE.md

Dieses Dokument ist in zwei Teile gegliedert:

- **Teil 1** – Allgemeine Muster und Boilerplate für FastAPI-Docker-Projekte
  dieser Bauart; wiederverwendbar für ähnliche Services.
- **Teil 2** – Projektspezifische Rahmenbedingungen für diesen Service.

---

# Teil 1: Allgemeine Muster

## FastAPI-Microservice-Skeleton

Minimale Struktur für einen authentifizierten FastAPI-Service als Python-Paket:

```
my-service/
├── pyproject.toml
├── Dockerfile
├── compose.dev.yml
├── justfile
├── .dockerignore
├── scripts/           # Build-Zeit-Skripte (z.B. Assets vorinstallieren)
├── src/
│   └── my_service/
│       ├── __init__.py
│       ├── main.py    # FastAPI-App + run()-Entry-Point
│       ├── auth.py    # API-Key-Validierung
│       └── models.py  # Pydantic-Request/Response-Modelle
├── tests/
│   └── test_*.py
└── deploy/
    ├── .gitignore     # ignoriert .env, api_keys.json, compose.override.yml
    ├── compose.yml    # versioniert – kein manuelles Kopieren nötig
    ├── .env.sample
    └── api_keys.json.sample
```

---

## Python-Paket mit hatchling + hatch-vcs

### pyproject.toml-Minimalvorlage

```toml
[build-system]
requires = ["hatchling", "hatch-vcs"]
build-backend = "hatchling.build"

[project]
name = "my-service"
dynamic = ["version"]
requires-python = ">=3.11"
dependencies = [
    "fastapi>=0.110",
    "uvicorn[standard]>=0.29",
]

[project.scripts]
my-service = "my_service.main:run"

[tool.hatch.version]
source = "vcs"

[tool.hatch.version.raw-options]
version_scheme = "post-release"
local_scheme = "node-and-date"
dist_name = "my-service"        # Pflicht: steuert SETUPTOOLS_SCM_PRETEND_VERSION_FOR_*

[tool.hatch.build.targets.wheel]
packages = ["src/my_service"]

[project.optional-dependencies]
dev = ["pytest>=8.0", "httpx>=0.27", "build>=1.0"]

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["src"]
```

**Versionsschema:** Auf einem Tag `v1.2.0` → `1.2.0`. Drei Commits später →
`1.2.0.post3+g4a2b1c.d20260225`. Erstes Tag: `git tag v0.1.0`.

**Wichtig:** `dist_name` muss dem `[project].name` exakt entsprechen.
`hatch-vcs` konstruiert daraus den Namen der Umgebungsvariable
`SETUPTOOLS_SCM_PRETEND_VERSION_FOR_MY_SERVICE` (Unterstriche, Großbuchstaben).
Ohne `dist_name` greift die Variable im Docker-Build nicht.

---

## Dockerfile-Muster

Muster für einen Service mit versioniertem Python-Paket, das im Docker-Build-
Kontext kein `.git` hat:

```dockerfile
FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    <systemabhängigkeiten> && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY pyproject.toml .
COPY src/ src/

# Version an hatch-vcs übergeben – .git fehlt im Build-Kontext
ARG VERSION=0.0.0.dev0
RUN SETUPTOOLS_SCM_PRETEND_VERSION_FOR_MY_SERVICE=${VERSION} \
    SETUPTOOLS_SCM_PRETEND_VERSION=${VERSION} \
    pip install --no-cache-dir .

# Secrets nie ins Image kopieren – zur Laufzeit als Volume mounten
ENV API_KEYS_FILE=/config/api_keys.json

LABEL org.opencontainers.image.version="${VERSION}"

# Unprivilegierter Benutzer
RUN useradd --no-create-home --shell /bin/false appuser \
    && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"
CMD ["my-service"]
```

Beide `SETUPTOOLS_SCM_PRETEND_VERSION*`-Variablen setzen: Die `_FOR_*`-Variante
für `dist_name`-basiertes Lookup, die globale als Fallback.

---

## Docker-Compose-Muster

### Dev/Prod-Trennung

`compose.dev.yml` baut das Image aus dem Quellcode, mappt auf einen anderen Port
und schaltet Auth ab:

```yaml
name: my-service-dev   # verhindert Namenskollision mit Prod

services:
  my-service:
    container_name: my-service-dev
    build:
      context: .
      args:
        VERSION: "${VERSION:-undefined}"
    ports:
      - "8001:8000"        # anderer Port als Prod
    environment:
      - HOST=0.0.0.0       # Pflicht: Uvicorn bindet sonst auf 127.0.0.1 (im Container)
      - ALLOW_UNAUTHENTICATED=true
    restart: "no"
```

`deploy/compose.yml` (versioniert) nutzt das fertige Image aus der Registry:

```yaml
name: ${COMPOSE_PROJECT_NAME:-my-service-prod}

services:
  my-service-prod:
    image: ${IMAGE_NAME:-ghcr.io/org/my-service}:${IMAGE_TAG:-latest}
    container_name: ${CONTAINER_NAME:-my-service}
    ports:
      - "${PORT:-8000}:8000"
    restart: unless-stopped
```

### Overlay-Pattern

Instanzspezifische Erweiterungen kommen als lokales Overlay (`compose.override.yml`,
nicht versioniert):

```yaml
# deploy/compose.override.yml
services:
  my-service-prod:
    deploy:
      resources:
        limits:
          memory: 512m
```

```bash
# COMPOSE_FILE=compose.yml:compose.override.yml in .env setzen
docker compose up -d
```

### deploy/.gitignore

Nur instanzspezifische Dateien ignorieren, versionierbare Templates einchecken:

```
.env
api_keys.json
compose.override.yml
```

`compose.yml` selbst ist versioniert – kein manuelles Kopieren aus `.sample` nötig.

---

## just Task-Runner

Cross-Platform-Kompatibilität: `set windows-shell` für PowerShell, plattform-
spezifische Rezepte via `[unix]`/`[windows]`.

```just
set windows-shell := ["powershell.exe", "-NoLogo", "-Command"]

version    := if os_family() == "windows" { `hatch version` } else { `hatch version 2>/dev/null || git describe --tags --always` }
# Docker-Tags erlauben kein '+' (PEP-440 Local) – lokalen Teil abschneiden
docker_tag := if os_family() == "windows" { `(hatch version) -replace '\+.*',''` } else { `hatch version 2>/dev/null | sed 's/+.*//'` }

install:
    pip install -e ".[dev]"

wheel:
    python -m build

[unix]
dev:
    VERSION={{version}} docker compose -f compose.dev.yml up --build

[windows]
dev:
    $env:VERSION = "{{version}}"; docker compose -f compose.dev.yml up --build

build:
    docker build --build-arg VERSION={{version}} -t org/my-service:{{docker_tag}} -t org/my-service:latest .

push:
    docker buildx build --sbom=true --provenance=mode=max --build-arg VERSION={{version}} -t org/my-service:{{docker_tag}} -t org/my-service:latest --push .

sbom:
    syft org/my-service:{{docker_tag}} -o cyclonedx-json=my-service-{{docker_tag}}.sbom.json
```

---

## API-Key-Authentifizierung

Keys in einer lokalen JSON-Datei; Pfad via Umgebungsvariable `API_KEYS_FILE`.
Die Datei wird **bei jedem Request** neu gelesen – kein Neustart bei Key-Änderungen.

```json
{ "keys": ["sk-abc123", "sk-xyz789"] }
```

Client: `X-API-Key: sk-abc123` als HTTP-Header. Ungültig/fehlend → 401.

Offener Zugriff ohne Keys:

| Situation | Verhalten |
|-----------|-----------|
| `HOST=127.0.0.1` (Loopback) | Automatisch erlaubt – keine Variable nötig |
| `HOST=0.0.0.0` | Jeder Request → 401 |
| `HOST=0.0.0.0` + `ALLOW_UNAUTHENTICATED=true` | Offen – nur für Entwicklung |

FastAPI-Implementierung als `Depends(verify_api_key)` in geschützten Endpunkten.

---

## SBOM via Docker BuildKit

`docker buildx build --sbom=true --provenance=mode=max --push` bettet eine SBOM
als OCI-Attestation direkt ins Image ein. Kein separates Tool nötig; die SBOM
lebt neben dem Image in der Registry.

Einschränkung: `--sbom=true` funktioniert nur mit `--push`. Lokale Builds
(`--load`) unterstützen keine Attestationen.

SBOM abrufen:
```bash
docker buildx imagetools inspect ghcr.io/org/my-service:latest \
  --format '{{ json .SBOM }}'
```

Für Audits/Release-Anhänge: `syft` erzeugt eine Standalone-Datei (CycloneDX JSON):
```bash
syft ghcr.io/org/my-service:<tag> -o cyclonedx-json=my-service-<tag>.sbom.json
```

---

---

# Teil 2: Projektspezifisch

## Projektziel

FastAPI-Webservice, der einen Bildgenerator (`generate.py`) als HTTP-API
bereitstellt. Clients senden JSON, erhalten ein 16:9-PNG zurück – z.B. für
LinkedIn-Posts oder Präsentationsfolien.

---

## Projektstruktur (aktuell)

```
li_title_generator/
├── CLAUDE.md
├── pyproject.toml
├── Dockerfile
├── compose.dev.yml             # Lokale Entwicklung (build: ., Port 8001)
├── justfile
├── .dockerignore
├── scripts/
│   ├── install_fonts.py        # Font-Download (läuft im Dockerfile)
│   └── New-TitleImage.ps1      # PowerShell-Client
├── src/
│   └── title_image_service/
│       ├── __init__.py
│       ├── main.py
│       ├── auth.py
│       ├── generator.py
│       └── models.py
├── tests/
│   ├── test_auth.py
│   └── test_generate.py
└── deploy/
    ├── .gitignore              # ignoriert .env, api_keys.json, compose.override.yml
    ├── compose.yml             # versioniert – direkt nutzbar, kein cp nötig
    ├── compose.traefik.yml     # Traefik-Overlay (versioniert)
    ├── traefik-mtls-options.yml.sample
    ├── .env.sample
    └── api_keys.json.sample
```

---

## Paket-Setup (pyproject.toml)

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
dist_name = "title-image-service"

[tool.hatch.build.targets.wheel]
packages = ["src/title_image_service"]

[project.optional-dependencies]
dev = ["pytest>=8.0", "httpx>=0.27", "build>=1.0"]

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["src"]
```

---

## HTTP-Endpunkte (main.py)

### `POST /generate`
- **Auth**: `X-API-Key` erforderlich
- **Body**: `ImageRequest` als JSON
- **Response**: PNG (`Content-Type: image/png`)
- **Header**: `Content-Disposition: attachment; filename="<dateiname>"`
- Fehler bei ungültigen Parametern → HTTP 422

### `GET /health`
- **Auth**: keine
- **Response**: `{"status": "ok"}`

### `GET /`
- **Auth**: keine
- **Response**: `{"service": "title-image-service", "docs": "/docs"}`

---

## Datenmodell (models.py)

```python
class ImageRequest(BaseModel):
    titel:       str = ""
    text:        str = ""
    vordergrund: str = "white"
    hintergrund: str = "black"
    breite:      int = 1024
    font:        str = "Rubik Glitch"
    titelzeilen: int = 1
    dateiname:   str = ""   # Leer → linkedin_title_<YYYY-MM-DD-HH-mm>.png
```

`dateiname`: `field_validator` erlaubt nur alphanumerische Zeichen, Punkte,
Bindestriche, Unterstriche, max. 128 Zeichen.

---

## Bildgenerator (generator.py)

`generate.py` wird nicht kopiert, sondern als `generator.py` ins Paket überführt:

- Funktionen `resolve_font`, `normalize_color`, `wrap_text`, `generate_image`
  bleiben inhaltlich unverändert
- `generate_image(output_path=None)`: ohne Pfad → `bytes` (PNG im RAM),
  mit Pfad → Datei auf Disk (CLI-Kompatibilität)
- Font-Cache: Umgebungsvariable `FONT_CACHE_DIR`,
  Default `~/.cache/title-image-fonts`
- Deutsch-Farbnamen (`schwarz`, `weiß`/`weiss`, `rot`, …) werden in
  Pillow-kompatible Namen übersetzt

Pillow-Operationen laufen im RAM (`io.BytesIO`), kein temporäres File.
`generate_image()` ist CPU-gebunden → `asyncio.to_thread()` im FastAPI-Handler
verwenden, um den Event-Loop nicht zu blockieren.

---

## Build-Workflow

```
| Befehl        | Beschreibung                                                              |
|---------------|---------------------------------------------------------------------------|
| just version  | Aktuelle Version ausgeben                                                 |
| just install  | Dev-Abhängigkeiten installieren (pip install -e ".[dev]")                 |
| just wheel    | Python-Wheel und Source-Distribution bauen (dist/)                        |
| just dev      | Lokales Dev-Image bauen und auf Port 8001 starten                         |
| just build    | Docker-Image lokal bauen und taggen                                       |
| just push     | Image bauen, SBOM-Attestation einbetten und zu ghcr.io pushen             |
| just sbom     | SBOM aus gepushtem Image erzeugen (CycloneDX JSON)                        |
| just export   | Docker-Image als title-image-<VERSION>.tar.gz exportieren                 |
```

Image-Namen: `ghcr.io/kaijen/title-image:<VERSION>` und `latest`.
Docker-Tag: PEP-440-Local-Identifier (`+`) wird abgeschnitten, da Docker-Tags
kein `+` erlauben.

---

## Betrieb (deploy/)

`deploy/compose.yml` ist versioniert – kein manuelles Kopieren aus `.sample`.

### Einmalig einrichten

```bash
cd deploy
cp .env.sample .env
cp api_keys.json.sample api_keys.json
# IMAGE_TAG, TRAEFIK_HOST etc. in .env anpassen
# API-Keys in api_keys.json eintragen
```

### Starten

```bash
cd deploy
docker compose up -d
```

### Mit Traefik-Overlay

`COMPOSE_FILE=compose.yml:compose.traefik.yml` in `.env` setzen.
Variablen: `TRAEFIK_HOST`, `TRAEFIK_NETWORK`, `TRAEFIK_ENTRYPOINT`,
`TRAEFIK_CERTRESOLVER`.

### Instanzspezifische Anpassungen

Über `compose.override.yml` (nicht versioniert, in `deploy/.gitignore`):

```bash
# COMPOSE_FILE=compose.yml:compose.override.yml in .env
docker compose up -d
```

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
- Font nicht auflösbar → HTTP 500
- `api_keys.json` nicht gefunden → Server startet trotzdem, jeder Request → 401
- Jede Exception in `/generate` → geloggt (inkl. Stacktrace), dann HTTP 500
- Logging via Python `logging`, Level via `LOG_LEVEL` (Default: `INFO`)

---

## Beispiel-Request

```bash
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
```
