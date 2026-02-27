# title-image-service

FastAPI-Webservice zum Erzeugen von 16:9-Titelbildern (PNG) aus JSON-Parametern –
z. B. für LinkedIn-Posts oder Präsentationsfolien.

**Dokumentation:** https://kaijen.github.io/li_title_generator/

---

## Schnellstart

```bash
cd deploy
cp .env.sample .env
cp api_keys.json.sample api_keys.json
# IMAGE_TAG und eigene Keys in api_keys.json eintragen

docker compose up -d

curl -X POST http://localhost:8000/generate \
  -H "X-API-Key: sk-abc123" \
  -H "Content-Type: application/json" \
  -d '{"titel": "Hallo Welt", "breite": 1920}' \
  --output titel.png
```

Swagger-UI: `http://localhost:8000/docs`

---

## Tests

```bash
pip install -e ".[dev]"
pytest
```

## Task-Runner

Das Projekt nutzt [`just`](https://github.com/casey/just):

```bash
just dev          # Dev-Image bauen und starten (Port 8001, kein Auth)
just build        # Docker-Image lokal bauen
just push         # Image mit SBOM zu ghcr.io pushen
just docs         # Docs lokal vorschauen
```

Alle Befehle: `just --list`
