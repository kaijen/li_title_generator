# title-image-service

FastAPI-Webservice zum Erzeugen von 16:9-Titelbildern (PNG) aus JSON-Parametern – z. B. für LinkedIn-Posts oder Präsentationsfolien.

## Inhalt

- [Schnellstart mit Docker](#schnellstart-mit-docker)
- [Lokale Installation](#lokale-installation)
- [API](#api)
- [PowerShell-Funktion](#powershell-funktion)
- [Authentifizierung](#authentifizierung)
- [Umgebungsvariablen](#umgebungsvariablen)
- [Betrieb hinter Traefik](#betrieb-hinter-traefik)
- [Tests](#tests)

---

## Schnellstart mit Docker

```bash
# API-Keys anlegen
cp api_keys.json.sample api_keys.json
# api_keys.json anpassen (eigene Keys eintragen)

# Container bauen und starten
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

Die folgende Funktion kann in ein PowerShell-Profil (`$PROFILE`) eingefügt oder per `. .\New-TitleImage.ps1` geladen werden.

Die URL wird automatisch aus der Umgebungsvariable `TITLE_IMAGE_SERVICE_URL` gelesen, sofern sie gesetzt ist. Andernfalls gilt `http://localhost:8000`.

```powershell
function New-TitleImage {
    [CmdletBinding()]
    param(
        [string] $Url         = "",
        [string] $ApiKey      = "",

        [Alias("t")]
        [string] $Titel       = "",
        [string] $Text        = "",
        [string] $Vordergrund = "white",
        [string] $Hintergrund = "black",
        [Alias("b")]
        [int]    $Breite      = 1920,
        [Alias("f")]
        [string] $Font        = "Rubik Glitch",
        [Alias("z")]
        [int]    $Titelzeilen = 1,
        [string] $Dateiname   = "",

        [Alias("m")]
        [switch] $Montagspost,

        [Alias("a")]
        [switch] $AntiPattern
    )

    # .env im aktuellen Verzeichnis einlesen (KEY=VALUE, # Kommentare werden übersprungen)
    $dotenv = @{}
    $dotenvPath = Join-Path $PWD ".env"
    if (Test-Path $dotenvPath) {
        Get-Content $dotenvPath |
            Where-Object { $_ -match '^\s*[^#\s]' -and $_ -match '=' } |
            ForEach-Object {
                $key, $val = $_ -split '=', 2
                $dotenv[$key.Trim()] = $val.Trim().Trim('"').Trim("'")
            }
    }

    # URL: Parameter → Umgebungsvariable → .env → Default
    if (-not $Url) {
        if ($env:TITLE_IMAGE_SERVICE_URL)           { $Url = $env:TITLE_IMAGE_SERVICE_URL }
        elseif ($dotenv['TITLE_IMAGE_SERVICE_URL']) { $Url = $dotenv['TITLE_IMAGE_SERVICE_URL'] }
        else                                        { $Url = "http://localhost:8000" }
    }

    # API-Key: Parameter → Umgebungsvariable → .env → leer (Key ist optional)
    if (-not $ApiKey) {
        if ($env:TITLE_IMAGE_API_KEY)           { $ApiKey = $env:TITLE_IMAGE_API_KEY }
        elseif ($dotenv['TITLE_IMAGE_API_KEY']) { $ApiKey = $dotenv['TITLE_IMAGE_API_KEY'] }
    }

    if ($Montagspost) {
        $Text = "Ein Montagspost"
        $Font = "Barriecito"
    }
    elseif ($AntiPattern) {
        $Text = "Ein Anti-Pattern"
        $Font = "Rubik Glitch"
    }

    $body = @{
        titel       = $Titel
        text        = $Text
        vordergrund = $Vordergrund
        hintergrund = $Hintergrund
        breite      = $Breite
        font        = $Font
        titelzeilen = $Titelzeilen
        dateiname   = $Dateiname
    } | ConvertTo-Json

    $headers = @{ "Content-Type" = "application/json" }
    if ($ApiKey) { $headers["X-API-Key"] = $ApiKey }

    $outFile = if ($Dateiname) {
        $Dateiname
    } else {
        "linkedin_title_$(Get-Date -Format 'yyyy-MM-dd-HH-mm').png"
    }

    Invoke-WebRequest `
        -Uri     "$Url/generate" `
        -Method  POST `
        -Headers $headers `
        -Body    $body `
        -OutFile $outFile

    Write-Host "Gespeichert: $outFile"
}
```

Priorität der Konfiguration (höchste zuerst):

| Einstellung | Parameter | Umgebungsvariable | `.env`-Eintrag | Default |
|-------------|-----------|-------------------|----------------|---------|
| URL | `-Url` | `TITLE_IMAGE_SERVICE_URL` | `TITLE_IMAGE_SERVICE_URL` | `http://localhost:8000` |
| API-Key | `-ApiKey` | `TITLE_IMAGE_API_KEY` | `TITLE_IMAGE_API_KEY` | – (optional) |

**Beispiel `.env`:**

```dotenv
TITLE_IMAGE_SERVICE_URL=https://title-image.example.com
TITLE_IMAGE_API_KEY=sk-abc123
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
| `HOST=0.0.0.0` (Standard) | Jeder Request wird mit HTTP 401 abgelehnt |
| `HOST=0.0.0.0` + `ALLOW_UNAUTHENTICATED=true` | Offener Zugriff explizit erlaubt |

```bash
# Lokale Entwicklung ohne Keys – einfach auf localhost binden
HOST=127.0.0.1 title-image-service

# Produktiv: Keys pflegen
cp api_keys.json.sample api_keys.json
# Eigene Keys eintragen
```

---

## Umgebungsvariablen

| Variable | Default | Beschreibung |
|----------|---------|--------------|
| `API_KEYS_FILE` | `./api_keys.json` | Pfad zur API-Keys-Datei |
| `HOST` | `0.0.0.0` | Bind-Adresse; `127.0.0.1` erlaubt offenen Zugriff ohne Keys automatisch |
| `PORT` | `8000` | HTTP-Port des Servers |
| `ALLOW_UNAUTHENTICATED` | `false` | Auf `true` setzen, um offenen Zugriff auf `0.0.0.0` ohne Keys zu erlauben (nur für Entwicklung) |
| `FONT_CACHE_DIR` | `~/.cache/title-image-fonts` | Verzeichnis für heruntergeladene Fonts |
| `LOG_LEVEL` | `INFO` | Log-Level (`DEBUG`, `INFO`, `WARNING`, …) |

---

## Betrieb hinter Traefik

Für den Betrieb hinter einem bestehenden Traefik-Container steht ein separates Compose-Overlay bereit.

```bash
# Konfiguration anlegen
cp .env.sample .env
# .env anpassen: TRAEFIK_HOST, TRAEFIK_NETWORK, …

# Mit Traefik-Overlay starten (deaktiviert Port-Binding, aktiviert Labels)
docker compose -f docker-compose.yml -f docker-compose.traefik.yml up -d
```

Das Overlay (`docker-compose.traefik.yml`):
- deaktiviert das direkte Port-Binding aus `docker-compose.yml`
- verbindet den Container mit dem externen Traefik-Netzwerk
- setzt Traefik-Labels für Routing und TLS

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

**2. Labels in `docker-compose.traefik.yml` aktivieren**

Den auskommentierten mTLS-Block in `docker-compose.traefik.yml` einkommentieren.
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
