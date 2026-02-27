# Installation – Übersicht

Der Service lässt sich auf drei Wegen betreiben:

| Weg | Geeignet für |
|-----|--------------|
| [Docker Compose](docker-compose.md) | Produktion, empfohlener Standardweg |
| [Traefik-Overlay](traefik.md) | Produktion hinter Traefik-Reverse-Proxy |
| [Lokale Entwicklung](local-dev.md) | Entwicklung, Tests, Anpassungen am Code |

## Voraussetzungen

- Docker ≥ 24.x und Docker Compose ≥ 2.x
- Für lokale Entwicklung: Python ≥ 3.11 und [`just`](https://github.com/casey/just)
