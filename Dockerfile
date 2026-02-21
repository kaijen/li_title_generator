FROM python:3.12-slim

# Systemabhängigkeiten: fontconfig für fc-match
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
RUN mkdir -p /fonts-cache

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
