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
├── docker-compose.yml
├── .dockerignore
├── api_keys.json               # API-Keys (nicht im Image, wird gemountet)
├── src/
│   └── title_image_service/
│       ├── __init__.py
│       ├── main.py             # FastAPI-App, Endpunkte
│       ├── auth.py             # API-Key-Validierung
│       ├── generator.py        # Bildgenerierung (aus generate.py übernommen)
│       └── models.py           # Pydantic-Modelle für Request/Response
└── tests/
    ├── test_auth.py
    └── test_generate.py
```

---

## Paket-Setup (pyproject.toml)

Standard-PEP-517-Paket mit `hatchling` oder `setuptools`.
Abhängigkeiten: `fastapi`, `uvicorn[standard]`, `pillow`.
Entry-Point: `title-image-service` startet `uvicorn`.

```toml
[project]
name = "title-image-service"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "fastapi>=0.110",
    "uvicorn[standard]>=0.29",
    "pillow>=10.0",
]

[project.scripts]
title-image-service = "title_image_service.main:run"
```

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
- Redirect auf `/docs` (Swagger UI)

---

## Dockerfile

```dockerfile
FROM python:3.12-slim

# Systemabhängigkeiten: fontconfig für fc-match, curl für Font-Download
RUN apt-get update && apt-get install -y --no-install-recommends \
    fontconfig \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Paket installieren
COPY pyproject.toml .
COPY src/ src/
RUN pip install --no-cache-dir .

# ── Fonts vorinstallieren ────────────────────────────────────────────────────
# Fonts werden zur Build-Zeit von Google Fonts heruntergeladen und in den
# Font-Cache gelegt. Damit entfällt der Download beim ersten Request.
# Betroffene Fonts: Rubik Glitch, Libertinus Mono, JetBrains Mono, Fira Code

RUN mkdir -p /fonts-cache

# Google Fonts liefert bei älterem User-Agent TTF – direkt verwendbar.
# Das Skript lädt je Font die CSS-Antwort, extrahiert die TTF-URL und speichert
# die Datei unter /fonts-cache/<font_name>.ttf
RUN python3 - << 'PYEOF'
import urllib.request, re, sys
from pathlib import Path

CACHE = Path("/fonts-cache")
UA = "Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1)"

FONTS = {
    "rubik_glitch":     "Rubik+Glitch",
    "libertinus_mono":  "Libertinus+Mono",
    "jetbrains_mono":   "JetBrains+Mono",
    "fira_code":        "Fira+Code",
}

for cache_name, gf_name in FONTS.items():
    url = f"https://fonts.googleapis.com/css2?family={gf_name}&display=swap"
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    css = urllib.request.urlopen(req, timeout=30).read().decode()
    urls = re.findall(r"url\((https://[^)]+\.(?:ttf|otf))\)", css)
    if not urls:
        print(f"WARN: Kein TTF/OTF für {gf_name} gefunden", file=sys.stderr)
        continue
    font_data = urllib.request.urlopen(urls[0], timeout=30).read()
    ext = ".otf" if urls[0].endswith(".otf") else ".ttf"
    out = CACHE / (cache_name + ext)
    out.write_bytes(font_data)
    print(f"OK  {out.name}  ({len(font_data):,} Bytes)")
PYEOF

ENV FONT_CACHE_DIR=/fonts-cache

# api_keys.json wird zur Laufzeit gemountet, nicht ins Image gebacken
ENV API_KEYS_FILE=/config/api_keys.json

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

CMD ["title-image-service"]
```

Wichtig: `api_keys.json` **nicht** in das Image kopieren – sie wird als
Volume gemountet (enthält Secrets).

---

## docker-compose.yml

```yaml
services:
  title-image:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - ./api_keys.json:/config/api_keys.json:ro
      - font-cache:/fonts-cache
    environment:
      - API_KEYS_FILE=/config/api_keys.json
      - FONT_CACHE_DIR=/fonts-cache
    restart: unless-stopped

volumes:
  font-cache:
```

Der Font-Cache als benanntes Volume ist optional — die vier vorinstallierten
Fonts (Rubik Glitch, Libertinus Mono, JetBrains Mono, Fira Code) sind bereits
im Image. Das Volume ist sinnvoll, wenn zur Laufzeit weitere Fonts von Google
Fonts nachgeladen werden sollen und diese Neustarts überleben sollen.

---

## Uvicorn-Start (main.py → run())

```python
def run():
    import uvicorn
    uvicorn.run(
        "title_image_service.main:app",
        host="0.0.0.0",
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
