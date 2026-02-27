# API-Referenz

Basis-URL: `http://localhost:8000` (Standard-Port; konfigurierbar via `PORT`)

Interaktive Swagger-UI: `/docs`

---

## POST /generate

Erzeugt ein 16:9-PNG-Bild und gibt es als Datei zurück.

**Authentifizierung:** abhängig von der Serverkonfiguration (siehe [Konfiguration](configuration.md))

| Situation | Auth erforderlich |
|-----------|------------------|
| `HOST=127.0.0.1` (Loopback, Standard) | Nein – Loopback-Requests automatisch erlaubt |
| `HOST=0.0.0.0` | Ja – `X-API-Key`-Header erforderlich |
| `HOST=0.0.0.0` + `ALLOW_UNAUTHENTICATED=true` | Nein – nur für Entwicklung |

### Request

**Header:**

| Header | Pflicht | Wert |
|--------|---------|------|
| `X-API-Key` | Nein / Ja* | API-Key aus `api_keys.json` |
| `Content-Type` | Ja | `application/json` |

*Pflicht wenn `HOST=0.0.0.0` und `ALLOW_UNAUTHENTICATED` nicht gesetzt.

**Body:** JSON-Objekt – alle Felder optional. Siehe [Parameter](usage/parameters.md).

### Response

| Status | Beschreibung |
|--------|--------------|
| `200 OK` | PNG-Bilddaten (`Content-Type: image/png`) |
| `401 Unauthorized` | Fehlender oder ungültiger API-Key |
| `422 Unprocessable Entity` | Ungültige Parameter (z. B. unbekannte Farbe, ungültiger Dateiname) |
| `500 Internal Server Error` | Interner Fehler (z. B. Font nicht abrufbar) |

Der `Content-Disposition`-Header enthält den Dateinamen:

```
Content-Disposition: attachment; filename="nis2-slide.png"
```

---

## GET /health

Healthcheck-Endpunkt. Keine Authentifizierung erforderlich.

### Response

```json
{ "status": "ok" }
```

---

## GET /

Service-Info. Keine Authentifizierung erforderlich.

### Response

```json
{ "service": "title-image-service", "docs": "/docs" }
```
