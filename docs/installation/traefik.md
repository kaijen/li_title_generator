# Traefik-Integration

Für den Betrieb hinter einem bestehenden Traefik-Container steht ein Compose-Overlay bereit.

## Einrichten

In `deploy/.env` setzen:

```dotenv
COMPOSE_FILE=compose.yml:compose.traefik.yml
TRAEFIK_HOST=title-image.example.com
TRAEFIK_NETWORK=traefik
TRAEFIK_ENTRYPOINT=websecure
TRAEFIK_CERTRESOLVER=letsencrypt
```

Dann starten:

```bash
cd deploy
docker compose up -d
```

Das Overlay deaktiviert das direkte Port-Binding aus `compose.yml` und verbindet
den Container mit dem externen Traefik-Netzwerk.

## Konfigurierbare Variablen

| Variable | Beispiel | Beschreibung |
|----------|----------|--------------|
| `TRAEFIK_HOST` | `title-image.example.com` | Öffentlicher Hostname |
| `TRAEFIK_NETWORK` | `traefik` | Externes Docker-Netzwerk |
| `TRAEFIK_ENTRYPOINT` | `websecure` | Traefik-Entrypoint |
| `TRAEFIK_CERTRESOLVER` | `letsencrypt` | Certificate-Resolver |

## Client-Zertifikat-Authentifizierung (mTLS)

Traefik kann zusätzlich ein TLS-Client-Zertifikat erzwingen.

### 1. Traefik-seitige TLS-Option anlegen

`deploy/traefik-mtls-options.yml.sample` in den dynamic-config-Pfad von Traefik
kopieren (z. B. `/etc/traefik/dynamic/mtls.yml`) und die CA-Datei eintragen:

```yaml
tls:
  options:
    mtls:
      minVersion: VersionTLS12
      clientAuth:
        caFiles:
          - /etc/traefik/certs/client-ca.pem
        clientAuthType: RequireAndVerifyClientCert
```

### 2. mTLS-Labels in compose.traefik.yml aktivieren

Den auskommentierten mTLS-Block in `deploy/compose.traefik.yml` einkommentieren.

### Weitergeleitete Headers

| Header | Inhalt |
|--------|--------|
| `X-Forwarded-Tls-Client-Cert-Info` | URL-kodierte Zertifikats-Attribute (Subject, Issuer, SANs, Gültigkeit) |
| `X-Forwarded-Tls-Client-Cert` | Vollständiges PEM-Zertifikat URL-kodiert (nur wenn `pem=true`) |

### Request mit Client-Zertifikat (curl)

```bash
# Selbstsigniertes Client-Zertifikat erzeugen (einmalig)
openssl req -x509 -newkey rsa:4096 -keyout client.key -out client.crt \
  -days 365 -nodes \
  -subj "/CN=my-client/O=Meine Organisation"

# Request mit Client-Zertifikat
curl -X POST https://title-image.example.com/generate \
  --cert client.crt \
  --key client.key \
  -H "Content-Type: application/json" \
  -d '{"titel": "NIS2 Compliance", "breite": 1920}' \
  --output nis2-slide.png
```

!!! note "mTLS + API-Key kombinieren"
    Bei aktiviertem mTLS kann `api_keys.json` weggelassen werden, wenn
    `ALLOW_UNAUTHENTICATED=true` gesetzt ist – dann reicht das Client-Zertifikat
    als einzige Authentifizierung. Beide Methoden lassen sich auch kombinieren.
