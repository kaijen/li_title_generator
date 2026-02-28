# Client-Beispiele

## curl

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

# Automatischer Dateiname aus Content-Disposition-Header
curl -X POST http://localhost:8000/generate \
  -H "X-API-Key: sk-abc123" \
  -H "Content-Type: application/json" \
  -d '{"titel": "NIS2 Compliance", "breite": 1920}' \
  -OJ
```

## PowerShell

Das Skript `scripts/New-TitleImage.ps1` stellt die Funktion `New-TitleImage` bereit.

### Einbinden

```powershell
# Einmalig für die aktuelle Session (dot-sourcing)
. .\scripts\New-TitleImage.ps1

# Dauerhaft ins PowerShell-Profil eintragen
Add-Content $PROFILE ". $(Resolve-Path .\scripts\New-TitleImage.ps1)"
```

### Konfiguration

URL und API-Key werden automatisch aus einer `.env`-Datei im aktuellen Verzeichnis gelesen.

**Beispiel `.env`:**

```dotenv
TITLE_IMAGE_SERVICE_URL=https://title-image.example.com
TITLE_IMAGE_API_KEY=sk-abc123
```

Priorität der Konfiguration (höchste zuerst):

| Einstellung | Parameter | Umgebungsvariable | `.env`-Eintrag | Default |
|-------------|-----------|-------------------|----------------|---------|
| URL | `-Url` | `TITLE_IMAGE_SERVICE_URL` | `TITLE_IMAGE_SERVICE_URL` | `http://localhost:8000` |
| API-Key | `-ApiKey` | `TITLE_IMAGE_API_KEY` | `TITLE_IMAGE_API_KEY` | – |
| PFX-Datei | `-CertPfx` | `TITLE_IMAGE_CERT_PFX` | `TITLE_IMAGE_CERT_PFX` | – |
| PFX-Passwort | `-CertPfxPass` | `TITLE_IMAGE_CERT_PFX_PASS` | `TITLE_IMAGE_CERT_PFX_PASS` | – |
| Thumbprint | `-CertThumbprint` | `TITLE_IMAGE_CERT_THUMBPRINT` | `TITLE_IMAGE_CERT_THUMBPRINT` | – |

### Beispiele

```powershell
# URL und API-Key aus .env
New-TitleImage -Titel "NIS2 Compliance" -Breite 1920

# Alle Parameter explizit
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

# Montagspost (Font = "Barriecito", Text = "Ein Montagspost")
New-TitleImage -Titel "Montag, der Motivator" -m

# Anti-Pattern (Font = "Rubik Glitch", Text = "Ein Anti-Pattern")
New-TitleImage -Titel "God Object" -a

# Mit Client-Zertifikat (PFX)
New-TitleImage -t "NIS2 Compliance" -b 1920 `
    -CertPfx "C:\certs\client.pfx" -CertPfxPass "geheim"

# Mit Client-Zertifikat aus Windows-Zertifikatspeicher
New-TitleImage -t "NIS2 Compliance" -b 1920 `
    -CertThumbprint "A1B2C3D4E5F6A1B2C3D4E5F6A1B2C3D4E5F6A1B2"
```

## Python

```python
import httpx

response = httpx.post(
    "http://localhost:8000/generate",
    headers={"X-API-Key": "sk-abc123"},
    json={
        "titel": "NIS2 Compliance",
        "text": "Umsetzung in der Praxis",
        "hintergrund": "#1a1a2e",
        "vordergrund": "white",
        "breite": 1920,
        "titelzeilen": 2,
    },
)
response.raise_for_status()

with open("nis2-slide.png", "wb") as f:
    f.write(response.content)
```
