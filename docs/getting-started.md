# Schnellstart

Erstes Titelbild in vier Schritten.

## Voraussetzungen

- Docker und Docker Compose ≥ 2.x

## 1. Konfiguration einrichten

```bash
cd deploy
cp .env.sample .env
cp api_keys.json.sample api_keys.json
```

In `api_keys.json` eigene API-Keys eintragen und in `.env` das gewünschte `IMAGE_TAG` setzen.

## 2. Service starten

```bash
docker compose up -d
```

Der Service ist danach unter `http://localhost:8000` erreichbar.

## 3. Erstes Bild erzeugen

```bash
curl -X POST http://localhost:8000/generate \
  -H "X-API-Key: sk-abc123" \
  -H "Content-Type: application/json" \
  -d '{"titel": "Hallo Welt", "breite": 1920}' \
  --output titel.png
```

Das erzeugt eine Datei `titel.png` im aktuellen Verzeichnis.

## 4. Interaktive API-Doku

Die Swagger-UI öffnet sich unter:

```
http://localhost:8000/docs
```

## Nächste Schritte

- [Alle Parameter kennenlernen](usage/parameters.md)
- [Farben und Fonts anpassen](usage/colors.md)
- [Traefik-Integration einrichten](installation/traefik.md)
