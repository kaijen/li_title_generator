# Installation mit Docker Compose

Empfohlener Weg für den Produktivbetrieb.

## Einmalig einrichten

```bash
cd deploy
cp .env.sample .env
cp api_keys.json.sample api_keys.json
```

Anpassen:

- `.env` – `IMAGE_TAG` auf die gewünschte Version setzen
- `api_keys.json` – eigene API-Keys eintragen (Format: `{"keys": ["sk-abc123"]}`)

## Starten

```bash
cd deploy
docker compose up -d
```

## Stoppen / Aktualisieren

```bash
# Stoppen
docker compose down

# Image aktualisieren und neu starten
docker compose pull
docker compose up -d
```

## Instanzspezifische Anpassungen

Erweiterungen (Resource-Limits, Log-Treiber, …) kommen als lokales Overlay
`deploy/compose.override.yml` (nicht versioniert):

```yaml
# deploy/compose.override.yml
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
# COMPOSE_FILE=compose.yml:compose.override.yml in deploy/.env setzen
docker compose up -d
```

## Konfigurierbare Variablen

Alle Variablen in `deploy/.env.sample` sind dokumentiert. Die wichtigsten:

| Variable | Beispiel | Beschreibung |
|----------|----------|--------------|
| `IMAGE_TAG` | `1.2.0` | Image-Version aus ghcr.io |
| `PORT` | `8000` | Externer HTTP-Port |
| `CONTAINER_NAME` | `title-image` | Docker-Container-Name |

Vollständige Liste → [Konfiguration](../configuration.md)
