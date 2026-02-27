# Lokale Entwicklung

## Mit just (empfohlen)

`just dev` baut das Image direkt aus dem Quellcode und startet es auf Port 8001
mit deaktivierter Authentifizierung.

**Voraussetzung:** [`just`](https://github.com/casey/just) installieren:

```bash
winget install Casey.Just   # Windows
brew install just            # macOS / Linux
```

```bash
just dev
```

Der Service läuft dann auf `http://localhost:8001`.

## Ohne Docker (pip)

Voraussetzung: Python ≥ 3.11

```bash
# Paket inkl. Entwicklungsabhängigkeiten installieren
pip install -e ".[dev]"

# Service starten (bindet auf localhost – kein API-Key erforderlich)
title-image-service
```

Der Service lauscht auf `http://localhost:8000`.

## Tests ausführen

```bash
pytest          # alle Tests
pytest -v       # mit ausführlicher Ausgabe
```

## Verfügbare just-Befehle

| Befehl | Beschreibung |
|--------|--------------|
| `just version` | Aktuelle Version ausgeben |
| `just install` | Dev-Abhängigkeiten installieren |
| `just dev` | Dev-Image bauen und starten (Port 8001, kein Auth) |
| `just wheel` | Python-Wheel und Source-Distribution bauen |
| `just build` | Docker-Image lokal bauen und taggen |
| `just push` | Image mit SBOM-Attestation zu ghcr.io pushen |
| `just export` | Docker-Image als `.tar.gz` exportieren |
| `just sbom` | SBOM aus gepushtem Image erzeugen |
| `just docs` | Docs lokal unter http://127.0.0.1:8000 vorschauen |
| `just docs-build` | Statische Docs nach `site/` bauen |
