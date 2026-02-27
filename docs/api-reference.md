# API-Referenz

Basis-URL: `http://localhost:8000` (Standard-Port; konfigurierbar via `PORT`)

Interaktive Swagger-UI: `/docs`

---

## POST /generate

Erzeugt ein 16:9-PNG-Bild und gibt es als Datei zurück.

**Authentifizierung:** `X-API-Key`-Header erforderlich

### Request

**Header:**

| Header | Pflicht | Wert |
|--------|---------|------|
| `X-API-Key` | Ja | API-Key aus `api_keys.json` |
| `Content-Type` | Ja | `application/json` |

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
