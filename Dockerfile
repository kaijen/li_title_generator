FROM python:3.12-slim

# Systemabhängigkeiten: fontconfig für fc-match
RUN apt-get update && apt-get install -y --no-install-recommends \
    fontconfig \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Paket installieren – Version an hatch-vcs übergeben (kein .git im Build-Kontext)
COPY pyproject.toml .
COPY src/ src/
ARG VERSION=0.0.0.dev0
RUN SETUPTOOLS_SCM_PRETEND_VERSION_FOR_TITLE_IMAGE_SERVICE=${VERSION} \
    pip install --no-cache-dir .

# ── Fonts vorinstallieren ────────────────────────────────────────────────────
# Rubik Glitch, Libertinus Mono, JetBrains Mono, Fira Code werden zur Build-Zeit
# von Google Fonts geladen. Damit entfällt der Download beim ersten Request.
COPY scripts/install_fonts.py /tmp/install_fonts.py
RUN mkdir -p /fonts-cache \
    && FONT_CACHE_DIR=/fonts-cache python3 /tmp/install_fonts.py \
    && rm /tmp/install_fonts.py

ENV FONT_CACHE_DIR=/fonts-cache

# api_keys.json wird zur Laufzeit gemountet, nicht ins Image gebacken
ENV API_KEYS_FILE=/config/api_keys.json

LABEL org.opencontainers.image.version="${VERSION}"

# ── Unprivilegierter Benutzer ────────────────────────────────────────────────
RUN useradd --no-create-home --shell /bin/false appuser \
    && chown -R appuser:appuser /app /fonts-cache

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

CMD ["title-image-service"]
