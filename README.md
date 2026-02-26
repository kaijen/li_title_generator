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
  - [Paket bauen](#paket-bauen)

---

## Schnellstart mit Docker

```bash
# Betriebskonfiguration einmalig einrichten
cd deploy
cp compose.yml.sample compose.yml
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
    <#
    .SYNOPSIS
        Erzeugt ein 16:9-Titelbild (PNG) über den title-image-service.

    .DESCRIPTION
        Sendet einen POST-Request an /generate und speichert das zurückgegebene
        PNG lokal. URL und API-Key werden aus Parametern, Umgebungsvariablen oder
        einer .env-Datei im aktuellen Verzeichnis gelesen (Priorität: Parameter >
        Umgebungsvariable > .env > Default).

        Für mTLS-gesicherte Endpunkte kann ein Client-Zertifikat als PFX-Datei
        oder über den Windows-Zertifikatspeicher (Thumbprint) übergeben werden.

    .PARAMETER Url
        URL des title-image-service, z. B. "https://title-image.example.com".
        Default: TITLE_IMAGE_SERVICE_URL (Umgebungsvariable/.env) oder http://localhost:8000.

    .PARAMETER ApiKey
        API-Key (X-API-Key-Header). Optional, wenn der Service ohne Keys betrieben wird.
        Default: TITLE_IMAGE_API_KEY (Umgebungsvariable/.env).

    .PARAMETER CertPfx
        Pfad zu einer PFX/P12-Datei für mTLS-Client-Authentifizierung.
        Hat Vorrang vor -CertThumbprint.

    .PARAMETER CertPfxPass
        Passwort zur PFX-Datei. Leer lassen, wenn die Datei ungeschützt ist.

    .PARAMETER CertThumbprint
        Thumbprint eines Zertifikats aus dem Windows-Zertifikatspeicher
        (CurrentUser\My oder LocalMachine\My).

    .PARAMETER Titel
        Titeltext des Bilds. Alias: -t

    .PARAMETER Text
        Untertitel oder Fließtext. Leer lässt das Textfeld frei.

    .PARAMETER Vordergrund
        Schriftfarbe: englischer Name ("white"), Hex ("#1a1a2e") oder
        deutscher Name ("weiß", "schwarz", "rot", …). Default: "white"

    .PARAMETER Hintergrund
        Hintergrundfarbe (gleiche Formate wie -Vordergrund). Default: "black"

    .PARAMETER Breite
        Bildbreite in Pixeln; die Höhe wird als 9/16 der Breite berechnet.
        Alias: -b  Default: 1920

    .PARAMETER Font
        Google-Fonts-Name oder installierter Systemfont. Alias: -f
        Default: "Rubik Glitch"

    .PARAMETER Titelzeilen
        Anzahl der Zeilen, auf die der Titel aufgeteilt wird. Alias: -z  Default: 1

    .PARAMETER Dateiname
        Lokaler Dateiname der gespeicherten PNG-Datei.
        Leer oder weggelassen → linkedin_title_<YYYY-MM-DD-HH-mm>.png

    .PARAMETER Montagspost
        Setzt Text auf "Ein Montagspost" und Font auf "Barriecito". Alias: -m

    .PARAMETER AntiPattern
        Setzt Text auf "Ein Anti-Pattern" und Font auf "Rubik Glitch". Alias: -a

    .EXAMPLE
        New-TitleImage -Titel "NIS2 Compliance" -Breite 1920

        URL und API-Key aus .env; automatischer Dateiname.

    .EXAMPLE
        New-TitleImage -t "NIS2 Compliance" -b 1920 -z 2 -f "Fira Code"

        Kurzform mit Aliases.

    .EXAMPLE
        New-TitleImage -Titel "Montag, der Motivator" -m

        Montagspost: Text und Font werden automatisch gesetzt.

    .EXAMPLE
        New-TitleImage -Titel "God Object" -a

        Anti-Pattern-Post.

    .EXAMPLE
        New-TitleImage -t "NIS2 Compliance" -b 1920 `
            -CertPfx "C:\certs\client.pfx" -CertPfxPass "geheim"

        mTLS mit PFX-Datei.

    .EXAMPLE
        New-TitleImage -t "NIS2 Compliance" -b 1920 `
            -CertThumbprint "A1B2C3D4E5F6A1B2C3D4E5F6A1B2C3D4E5F6A1B2"

        mTLS mit Zertifikat aus dem Windows-Zertifikatspeicher.

    .NOTES
        Konfigurationspriorität (höchste zuerst):
          Parameter > Umgebungsvariable > .env-Datei (KEY=VALUE) > Default

        .env-Variablen: TITLE_IMAGE_SERVICE_URL, TITLE_IMAGE_API_KEY,
        TITLE_IMAGE_CERT_PFX, TITLE_IMAGE_CERT_PFX_PASS, TITLE_IMAGE_CERT_THUMBPRINT

        -CertPfx und -CertThumbprint schließen sich gegenseitig aus;
        wird beides angegeben, hat -CertPfx Vorrang.
    #>
    [CmdletBinding()]
    param(
        [string] $Url             = "",
        [string] $ApiKey          = "",

        # Client-Zertifikat (optional) – entweder PFX-Datei oder Thumbprint
        [string] $CertPfx         = "",   # Pfad zur PFX/P12-Datei
        [string] $CertPfxPass     = "",   # Passwort der PFX-Datei (optional)
        [string] $CertThumbprint  = "",   # Thumbprint aus Windows-Zertifikatspeicher

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

    # Client-Zertifikat: Parameter → Umgebungsvariable → .env → keines
    if (-not $CertPfx) {
        if ($env:TITLE_IMAGE_CERT_PFX)           { $CertPfx = $env:TITLE_IMAGE_CERT_PFX }
        elseif ($dotenv['TITLE_IMAGE_CERT_PFX']) { $CertPfx = $dotenv['TITLE_IMAGE_CERT_PFX'] }
    }
    if (-not $CertPfxPass) {
        if ($env:TITLE_IMAGE_CERT_PFX_PASS)           { $CertPfxPass = $env:TITLE_IMAGE_CERT_PFX_PASS }
        elseif ($dotenv['TITLE_IMAGE_CERT_PFX_PASS']) { $CertPfxPass = $dotenv['TITLE_IMAGE_CERT_PFX_PASS'] }
    }
    if (-not $CertThumbprint) {
        if ($env:TITLE_IMAGE_CERT_THUMBPRINT)           { $CertThumbprint = $env:TITLE_IMAGE_CERT_THUMBPRINT }
        elseif ($dotenv['TITLE_IMAGE_CERT_THUMBPRINT']) { $CertThumbprint = $dotenv['TITLE_IMAGE_CERT_THUMBPRINT'] }
    }

    # Zertifikat laden – PFX-Datei hat Vorrang vor Thumbprint
    $cert = $null
    if ($CertPfx) {
        $cert = if ($CertPfxPass) {
            New-Object System.Security.Cryptography.X509Certificates.X509Certificate2($CertPfx, $CertPfxPass)
        } else {
            New-Object System.Security.Cryptography.X509Certificates.X509Certificate2($CertPfx)
        }
    } elseif ($CertThumbprint) {
        $cert = Get-ChildItem -Path Cert:\CurrentUser\My, Cert:\LocalMachine\My -ErrorAction SilentlyContinue |
                    Where-Object { $_.Thumbprint -eq $CertThumbprint } |
                    Select-Object -First 1
        if (-not $cert) {
            Write-Error "Kein Zertifikat mit Thumbprint '$CertThumbprint' im Zertifikatspeicher gefunden."
            return
        }
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

    $iwrParams = @{
        Uri     = "$Url/generate"
        Method  = "POST"
        Headers = $headers
        Body    = $body
        OutFile = $outFile
    }
    if ($cert) { $iwrParams["Certificate"] = $cert }

    Invoke-WebRequest @iwrParams

    Write-Host "Gespeichert: $outFile"
}
```

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
VERSION=$(git describe --tags --always)

docker build \
  --build-arg VERSION=${VERSION} \
  -t ghcr.io/kaijen/title-image:${VERSION} \
  -t ghcr.io/kaijen/title-image:latest \
  .
```

Das Build-Argument `VERSION` wird ins Python-Paket (über `SETUPTOOLS_SCM_PRETEND_VERSION_FOR_TITLE_IMAGE_SERVICE`) und als OCI-Label (`org.opencontainers.image.version`) eingebaut.

```bash
# Version im fertigen Image prüfen
docker inspect ghcr.io/kaijen/title-image:${VERSION} \
  --format '{{index .Config.Labels "org.opencontainers.image.version"}}'
```
