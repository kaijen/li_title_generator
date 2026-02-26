# title-image-service

FastAPI-Webservice zum Erzeugen von 16:9-Titelbildern (PNG) aus JSON-Parametern – z. B. für LinkedIn-Posts oder Präsentationsfolien.

## Inhalt

- [title-image-service](#title-image-service)
  - [Inhalt](#inhalt)
  - [Schnellstart mit Docker](#schnellstart-mit-docker)
  - [Lokale Installation](#lokale-installation)
  - [API](#api)
    - [`POST /generate`](#post-generate)
    - [`GET /health`](#get-health)
    - [`GET /`](#get-)
  - [PowerShell-Funktion](#powershell-funktion)
  - [Authentifizierung](#authentifizierung)
  - [Umgebungsvariablen](#umgebungsvariablen)
  - [Betrieb hinter Traefik](#betrieb-hinter-traefik)
    - [Client-Zertifikat-Authentifizierung (mTLS)](#client-zertifikat-authentifizierung-mtls)
  - [Tests](#tests)
  - [Task-Runner (just)](#task-runner-just)
  - [Paket bauen](#paket-bauen)
  - [SBOM](#sbom)

---

## Schnellstart mit Docker

```bash
# Konfiguration einmalig einrichten
cd deploy
cp .env.sample .env
cp api_keys.json.sample api_keys.json
# IMAGE_TAG und eigene Keys in api_keys.json eintragen

# Container starten
docker compose up -d

# Testbild erzeugen
curl -X POST http://localhost:8000/generate \
  -H "X-API-Key: sk-abc123" \
  -H "Content-Type: application/json" \
  -d '{"titel": "Hallo Welt", "breite": 1920}' \
  --output titel.png
```

Der Service ist danach unter `http://localhost:8000` erreichbar.
Die Swagger-UI (interaktive API-Doku) öffnet sich unter `http://localhost:8000/docs`.

---

## Lokale Installation

Voraussetzungen: Python ≥ 3.11

```bash
# Paket inkl. Entwicklungsabhängigkeiten installieren
pip install -e ".[dev]"

# Service starten
title-image-service
```

Der Service lauscht standardmäßig auf Port `8000`. Der Port lässt sich über die Umgebungsvariable `PORT` ändern.

**Alternativ mit Docker** (`compose.dev.yml`, baut Image direkt aus dem Quellcode):

```bash
# just installieren (einmalig)
winget install Casey.Just   # Windows
# brew install just         # macOS

just dev   # Version aus hatch version, ALLOW_UNAUTHENTICATED=true
```

---

## API

### `POST /generate`

Erzeugt ein 16:9-PNG-Bild und gibt es direkt als Datei zurück.

**Header:**

| Header | Pflicht | Beschreibung |
|--------|---------|--------------|
| `X-API-Key` | Ja | API-Key aus `api_keys.json` |
| `Content-Type` | Ja | `application/json` |

**Request-Body (alle Felder optional):**

| Feld | Typ | Default | Beschreibung |
|------|-----|---------|--------------|
| `titel` | string | `""` | Titelzeile(n) |
| `text` | string | `""` | Untertitel / Fließtext |
| `vordergrund` | string | `"white"` | Schriftfarbe (englisch, Hex oder Deutsch) |
| `hintergrund` | string | `"black"` | Hintergrundfarbe (englisch, Hex oder Deutsch) |
| `breite` | int | `1024` | Bildbreite in Pixeln; Höhe wird als 16:9 berechnet |
| `font` | string | `"Rubik Glitch"` | Google-Fonts-Name oder Systemfont |
| `titelzeilen` | int | `1` | Anzahl der Zeilen, auf die der Titel aufgeteilt wird |
| `dateiname` | string | `""` | Dateiname im `Content-Disposition`-Header; leer → automatisch |

**Farben** können als englischer Name (`"red"`), Hex-Code (`"#1a1a2e"`) oder deutscher Name angegeben werden:

> `schwarz`, `weiß` / `weiss`, `rot`, `grün` / `gruen`, `blau`, `gelb`, `orange`, `lila`, `violett`, `pink`, `grau`, `braun`, `türkis` / `tuerkis`, `silber`, `gold`

**Response:**

- `200 OK` – PNG-Bilddaten (`Content-Type: image/png`)
- `401 Unauthorized` – ungültiger oder fehlender API-Key
- `422 Unprocessable Entity` – ungültige Parameter (z. B. unbekannte Farbe)

**Beispiele:**

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

# Automatischer Dateiname (linkedin_title_YYYY-MM-DD-HH-MM.png)
curl -X POST http://localhost:8000/generate \
  -H "X-API-Key: sk-abc123" \
  -H "Content-Type: application/json" \
  -d '{"titel": "NIS2 Compliance", "breite": 1920}' \
  -OJ
```

### `GET /health`

Healthcheck-Endpunkt, keine Authentifizierung erforderlich.

```bash
curl http://localhost:8000/health
# {"status": "ok"}
```

### `GET /`

Gibt Service-Informationen zurück (kein Redirect, kein Auth erforderlich).

```bash
curl http://localhost:8000/
# {"service": "title-image-service", "docs": "/docs"}
```

---

## PowerShell-Funktion

Die Funktion `New-TitleImage` liegt als eigenständiges Skript unter
[`scripts/New-TitleImage.ps1`](scripts/New-TitleImage.ps1).

**Einbinden (einmalig):**

```powershell
# Option A – für die aktuelle Session laden (dot-sourcing)
. .\scripts\New-TitleImage.ps1

# Option B – dauerhaft ins PowerShell-Profil eintragen
Add-Content $PROFILE ". $(Resolve-Path .\scripts\New-TitleImage.ps1)"
```

URL und API-Key werden automatisch aus einer `.env`-Datei im aktuellen
Verzeichnis gelesen. Alternativ können Umgebungsvariablen oder Parameter gesetzt werden.

Priorität der Konfiguration (höchste zuerst):

| Einstellung | Parameter | Umgebungsvariable | `.env`-Eintrag | Default |
|-------------|-----------|-------------------|----------------|---------|
| URL | `-Url` | `TITLE_IMAGE_SERVICE_URL` | `TITLE_IMAGE_SERVICE_URL` | `http://localhost:8000` |
| API-Key | `-ApiKey` | `TITLE_IMAGE_API_KEY` | `TITLE_IMAGE_API_KEY` | – (optional) |
| PFX-Datei | `-CertPfx` | `TITLE_IMAGE_CERT_PFX` | `TITLE_IMAGE_CERT_PFX` | – (optional) |
| PFX-Passwort | `-CertPfxPass` | `TITLE_IMAGE_CERT_PFX_PASS` | `TITLE_IMAGE_CERT_PFX_PASS` | – (optional) |
| Thumbprint | `-CertThumbprint` | `TITLE_IMAGE_CERT_THUMBPRINT` | `TITLE_IMAGE_CERT_THUMBPRINT` | – (optional) |

> **Hinweis:** `-CertPfx` und `-CertThumbprint` schließen sich gegenseitig aus – wird beides angegeben, hat die PFX-Datei Vorrang.

**Beispiel `.env`:**

```dotenv
TITLE_IMAGE_SERVICE_URL=https://title-image.example.com
TITLE_IMAGE_API_KEY=sk-abc123

# Client-Zertifikat (eine der beiden Varianten):
# Variante A – PFX-Datei
TITLE_IMAGE_CERT_PFX=C:\certs\client.pfx
TITLE_IMAGE_CERT_PFX_PASS=geheim

# Variante B – Thumbprint aus Windows-Zertifikatspeicher
# TITLE_IMAGE_CERT_THUMBPRINT=A1B2C3D4E5F6...
```

**Beispiele:**

```powershell
# API-Key und URL aus .env – kein expliziter Parameter nötig
New-TitleImage -Titel "NIS2 Compliance" -Breite 1920

# Mit allen Parametern (überschreibt .env und Umgebungsvariablen)
New-TitleImage `
    -Url         "http://localhost:8000" `
    -ApiKey      "sk-abc123" `
    -Titel       "NIS2 Compliance" `
    -Text        "Umsetzung in der Praxis" `
    -Hintergrund "#1a1a2e" `
    -Vordergrund "white" `
    -Breite      1920 `
    -Titelzeilen 2 `
    -Dateiname   "nis2-slide.png"

# Kurzform mit Aliases
New-TitleImage -t "NIS2 Compliance" -b 1920 -z 2 -f "Fira Code"

# Montagspost (Text = "Ein Montagspost", Font = "Barriecito")
New-TitleImage -Titel "Montag, der Motivator" -m

# Anti-Pattern (Text = "Ein Anti-Pattern", Font = "Rubik Glitch")
New-TitleImage -Titel "God Object" -a

# Mit Client-Zertifikat aus PFX-Datei
New-TitleImage -t "NIS2 Compliance" -b 1920 `
    -CertPfx "C:\certs\client.pfx" -CertPfxPass "geheim"

# Mit Client-Zertifikat aus Windows-Zertifikatspeicher (Thumbprint)
New-TitleImage -t "NIS2 Compliance" -b 1920 `
    -CertThumbprint "A1B2C3D4E5F6A1B2C3D4E5F6A1B2C3D4E5F6A1B2"
```

---

## Authentifizierung

API-Keys werden in `api_keys.json` verwaltet:

```json
{
  "keys": [
    "sk-abc123",
    "sk-xyz789"
  ]
}
```

Die Datei wird bei **jedem Request neu eingelesen** – Keys lassen sich also ohne Neustart hinzufügen oder entfernen.

**Verhalten ohne konfigurierte Keys:**

| Situation | Verhalten |
|-----------|-----------|
| `HOST=127.0.0.1` (localhost) | Offener Zugriff automatisch erlaubt – keine Umgebungsvariable nötig |
| `HOST=0.0.0.0` | Jeder Request wird mit HTTP 401 abgelehnt |
| `HOST=0.0.0.0` + `ALLOW_UNAUTHENTICATED=true` | Offener Zugriff explizit erlaubt |

```bash
# Lokale Entwicklung ohne Keys – einfach auf localhost binden
HOST=127.0.0.1 title-image-service

# Produktiv: Keys pflegen
cp deploy/api_keys.json.sample deploy/api_keys.json
# Eigene Keys eintragen
```

---

## Umgebungsvariablen

| Variable | Default | Beschreibung |
|----------|---------|--------------|
| `API_KEYS_FILE` | `./api_keys.json` | Pfad zur API-Keys-Datei |
| `HOST` | `127.0.0.1` | Bind-Adresse; `127.0.0.1` erlaubt offenen Zugriff ohne Keys automatisch |
| `PORT` | `8000` | HTTP-Port des Servers |
| `ALLOW_UNAUTHENTICATED` | `false` | Auf `true` setzen, um offenen Zugriff auf `0.0.0.0` ohne Keys zu erlauben (nur für Entwicklung) |
| `FONT_CACHE_DIR` | `~/.cache/title-image-fonts` | Verzeichnis für heruntergeladene Fonts |
| `LOG_LEVEL` | `INFO` | Log-Level (`DEBUG`, `INFO`, `WARNING`, …) |

---

## Betrieb hinter Traefik

Für den Betrieb hinter einem bestehenden Traefik-Container steht ein separates Compose-Overlay bereit.

```bash
cd deploy
# .env anpassen: TRAEFIK_HOST, TRAEFIK_NETWORK, …
# COMPOSE_FILE=compose.yml:compose.traefik.yml in .env setzen

docker compose up -d
```

Das Overlay (`deploy/compose.traefik.yml`):
- deaktiviert das direkte Port-Binding aus `compose.yml`
- verbindet den Container mit dem externen Traefik-Netzwerk
- setzt Traefik-Labels für Routing und TLS

### Anpassungen über Overlays

`compose.yml` wird nicht manuell geändert. Alle instanzspezifischen Erweiterungen
(zusätzliche Netzwerke, Resource-Limits, Log-Treiber, …) kommen als lokales Overlay:

```bash
# deploy/compose.override.yml – nicht versioniert
services:
  title-image-prod:
    deploy:
      resources:
        limits:
          memory: 512m
    logging:
      driver: journald
```

```bash
docker compose -f compose.yml -f compose.override.yml up -d
# Oder COMPOSE_FILE=compose.yml:compose.override.yml in .env setzen
```

Konfigurierbare Variablen in `.env`:

| Variable | Beispiel | Beschreibung |
|----------|----------|--------------|
| `TRAEFIK_HOST` | `title-image.example.com` | Öffentlicher Hostname |
| `TRAEFIK_NETWORK` | `traefik` | Externes Docker-Netzwerk |
| `TRAEFIK_ENTRYPOINT` | `websecure` | Traefik-Entrypoint |
| `TRAEFIK_CERTRESOLVER` | `letsencrypt` | Certificate-Resolver |

Voraussetzung: Docker Compose ≥ 2.x.

### Client-Zertifikat-Authentifizierung (mTLS)

Traefik kann zusätzlich ein TLS-Client-Zertifikat erzwingen und dessen Attribute
als HTTP-Header an den Backend-Container weiterleiten. Dafür sind zwei Schritte nötig:

**1. Traefik-seitige TLS-Option anlegen**

Beispieldatei `traefik-mtls-options.yml.sample` in den dynamic-config-Pfad von
Traefik kopieren (z. B. `/etc/traefik/dynamic/mtls.yml`) und die CA-Datei eintragen:

```yaml
tls:
  options:
    mtls:
      minVersion: VersionTLS12
      clientAuth:
        caFiles:
          - /etc/traefik/certs/client-ca.pem
        clientAuthType: RequireAndVerifyClientCert
```

**2. Labels in `deploy/compose.traefik.yml` aktivieren**

Den auskommentierten mTLS-Block in `deploy/compose.traefik.yml` einkommentieren.
Traefik setzt dann folgende Header, die der Service empfängt:

| Header | Inhalt |
|--------|--------|
| `X-Forwarded-Tls-Client-Cert-Info` | URL-kodierte Zertifikats-Attribute (Subject, Issuer, SANs, Gültigkeit) |
| `X-Forwarded-Tls-Client-Cert` | Vollständiges PEM-Zertifikat URL-kodiert (nur wenn `pem=true`) |

Beispielwert von `X-Forwarded-Tls-Client-Cert-Info`:
```
Subject=%22CN%3Dmy-client%2CO%3DMeine+Organisation%22;Issuer=%22CN%3DMeine+CA%22
```

**curl-Beispiel mit Client-Zertifikat**

```bash
# Selbstsigniertes Client-Zertifikat erzeugen (einmalig)
openssl req -x509 -newkey rsa:4096 -keyout client.key -out client.crt \
  -days 365 -nodes \
  -subj "/CN=my-client/O=Meine Organisation"

# Request mit Client-Zertifikat
curl -X POST https://title-image.example.com/generate \
  --cert client.crt \
  --key client.key \
  --cacert server-ca.pem \
  -H "Content-Type: application/json" \
  -d '{
    "titel": "NIS2 Compliance",
    "text": "Umsetzung in der Praxis",
    "hintergrund": "#1a1a2e",
    "vordergrund": "white",
    "breite": 1920
  }' \
  --output nis2-slide.png

# Wenn das Server-Zertifikat von einer öffentlichen CA stammt,
# kann --cacert entfallen (curl nutzt dann den System-Trust-Store).
```

> **Hinweis:** Bei aktiviertem mTLS kann `api_keys.json` weggelassen werden,
> wenn `ALLOW_UNAUTHENTICATED=true` gesetzt ist – dann reicht das
> Client-Zertifikat als einzige Authentifizierung. Beide Methoden lassen sich
> auch kombinieren (mTLS + API-Key).

---

## Tests

```bash
# Abhängigkeiten installieren (einmalig)
pip install -e ".[dev]"

# Alle Tests ausführen
pytest

# Mit Ausgabe
pytest -v
```

Die Testsuite deckt ab:
- API-Authentifizierung (gültige/ungültige/fehlende Keys, fehlende Datei)
- Automatischer offener Zugriff bei `HOST=127.0.0.1` ohne Keys
- `ALLOW_UNAUTHENTICATED`-Verhalten bei `HOST=0.0.0.0`
- HTTP-Endpunkte (`/health`, `/generate`, `/`)
- `Content-Disposition`-Header (automatischer und expliziter Dateiname)
- Content-Type-Validierung (falsche MIME-Types → 422)
- Bildgenerierung (16:9-Verhältnis, Farben, Schriften, Dateiausgabe)
- Farbauflösung inkl. vollständiger Deutsch-Tabelle

---

## Task-Runner (just)

Das Projekt nutzt [`just`](https://github.com/casey/just) als Task-Runner für alle häufigen Entwicklungs- und Build-Aufgaben.

**Installation (einmalig):**

```bash
winget install Casey.Just   # Windows
brew install just            # macOS / Linux
```

Die Version bestimmt `just` automatisch über `hatch version` (Fallback: `git describe --tags --always`) und übergibt sie als `--build-arg VERSION=` an Docker.

| Befehl | Beschreibung |
|--------|--------------|
| `just version` | Aktuelle Version ausgeben |
| `just install` | Dev-Abhängigkeiten installieren (`pip install -e ".[dev]"`) |
| `just wheel` | Python-Wheel und Source-Distribution bauen (`dist/`) |
| `just dev` | Lokale Entwicklung – baut Image mit aktueller Version, startet via `compose.dev.yml` auf Port 8001 |
| `just build` | Docker-Image bauen und taggen (`ghcr.io/kaijen/title-image:<VERSION>` + `latest`) |
| `just push` | Image bauen, SBOM-Attestation einbetten und zu `ghcr.io` pushen (beide Tags) |
| `just export` | Docker-Image als `title-image-<VERSION>.tar.gz` exportieren |
| `just sbom` | SBOM aus gepushtem Image erzeugen (`title-image-<VERSION>.sbom.json`) |

### Image zu ghcr.io pushen

`just push` baut das Image und lädt es in die GitHub Container Registry hoch. Voraussetzung ist eine einmalige Anmeldung:

```bash
# Mit GitHub CLI (empfohlen)
gh auth token | docker login ghcr.io -u kaijen --password-stdin

# Alternativ mit Personal Access Token (Scope: write:packages)
echo $GITHUB_TOKEN | docker login ghcr.io -u kaijen --password-stdin
```

Danach genügt:

```bash
just push
```

Das lädt `ghcr.io/kaijen/title-image:<VERSION>` und `ghcr.io/kaijen/title-image:latest` hoch.

---

## Paket bauen

Das Paket lässt sich als Wheel (`.whl`) bauen – zur Weitergabe oder für Deployments ohne Docker.

**Voraussetzung:** Das Repo muss einen Git-Tag tragen. Die Version wird von `hatch-vcs` aus `git describe --tags` gelesen. Ohne Tag gibt `hatch-vcs` einen Fehler aus.

```bash
# Erstes Tag setzen, falls noch keins existiert
git tag v0.1.0

# Build-Tool installieren (einmalig)
pip install build

# Wheel und Source-Distribution bauen
python -m build
```

Das erzeugt im Verzeichnis `dist/`:

- `title_image_service-<VERSION>-py3-none-any.whl` – installierbares Wheel
- `title_image_service-<VERSION>.tar.gz` – Source-Distribution

Die Version im Dateinamen entspricht dem aktuellen Git-Tag (z. B. `1.2.0`) bzw. dem Post-Release-Format bei späteren Commits (`1.2.0.post3+g4a2b1c.d20260226`).

**Installation aus dem Wheel:**

```bash
pip install dist/title_image_service-1.2.0-py3-none-any.whl
title-image-service
```

Danach ist `title-image-service` als Kommando verfügbar. Der Service benötigt zur Laufzeit eine `api_keys.json` und die Umgebungsvariablen wie unter [Umgebungsvariablen](#umgebungsvariablen) beschrieben.

**Docker-Image mit eingebetteter Version bauen:**

```bash
just build    # liest Version automatisch, baut und taggt das Image
just export   # exportiert Image als title-image-<VERSION>.tar.gz
```

Siehe [Task-Runner (just)](#task-runner-just) für alle verfügbaren Befehle. Die Version landet im Python-Paket (über `SETUPTOOLS_SCM_PRETEND_VERSION_FOR_TITLE_IMAGE_SERVICE`) und als OCI-Label `org.opencontainers.image.version`.

Das exportierte Archiv lässt sich auf einem anderen Rechner ohne Registry importieren:

```bash
docker load -i title-image-<VERSION>.tar.gz
```

```bash
# Version im fertigen Image prüfen
VERSION=$(hatch version) docker inspect ghcr.io/kaijen/title-image:${VERSION} \
  --format '{{index .Config.Labels "org.opencontainers.image.version"}}'
```

---

## SBOM

`just push` bettet beim Push automatisch eine SBOM (Software Bill of Materials)
als OCI-Attestation ins Image ein – über Docker BuildKit (`--sbom=true`). Sie
enthält alle Python-Pakete und OS-Packages aus den Image-Schichten.

**SBOM im Registry abrufen** (nach `just push`):

```bash
docker buildx imagetools inspect ghcr.io/kaijen/title-image:latest \
  --format '{{ json .SBOM }}'
```

**Standalone SBOM-Datei erzeugen** (für Audits oder Release-Anhänge):

Voraussetzung: [`syft`](https://github.com/anchore/syft) installieren.

```bash
winget install anchore.syft   # Windows
brew install syft              # macOS / Linux
```

```bash
just sbom
# → title-image-<VERSION>.sbom.json (CycloneDX JSON)
```

Die Datei deckt beide SBOM-Ebenen ab: Python-Pakete (`fastapi`, `uvicorn`,
`pillow`, transitive Abhängigkeiten) und OS-Packages aus dem Basis-Image
(`python:3.12-slim`).
