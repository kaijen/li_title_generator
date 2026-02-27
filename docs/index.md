# Title Image Service

FastAPI-Webservice zum Erzeugen von **16:9-Titelbildern (PNG)** aus JSON-Parametern –
z. B. für LinkedIn-Posts oder Präsentationsfolien.

## Was kann der Service?

- Generiert 16:9-PNG-Bilder aus einfachem JSON-Request
- Flexibler Font-Support via Google Fonts (automatischer Download und Cache)
- Farbangaben als englischer Name, Hex-Code oder deutschsprachige Aliase
- API-Key-Authentifizierung mit Hot-Reload (kein Neustart bei Key-Änderungen)
- Docker-ready mit Compose-Overlays für Traefik und mTLS

## Einstieg

Neu hier? → **[Schnellstart](getting-started.md)**

## Dokumentation im Überblick

| Abschnitt | Inhalt |
|-----------|--------|
| [Schnellstart](getting-started.md) | Erstes Bild in wenigen Schritten |
| [Installation](installation/index.md) | Docker Compose, Traefik, lokale Entwicklung |
| [Nutzung](usage/index.md) | Parameter, Farben, Fonts, Client-Beispiele |
| [API-Referenz](api-reference.md) | Endpunkte, Request/Response-Schemas, HTTP-Codes |
| [Konfiguration](configuration.md) | Alle Umgebungsvariablen |
