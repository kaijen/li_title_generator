# just installieren: winget install Casey.Just  |  brew install just

set windows-shell := ["powershell.exe", "-NoLogo", "-Command"]

version    := if os_family() == "windows" { `hatch version` } else { `hatch version 2>/dev/null || git describe --tags --always` }
# Docker-Tags erlauben kein '+' (PEP-440-Local-Identifier) – lokalen Teil abschneiden
docker_tag := if os_family() == "windows" { `(hatch version) -replace '\+.*',''` } else { `hatch version 2>/dev/null | sed 's/+.*//' || git describe --tags --abbrev=0` }

# Aktuelle Version ausgeben
version:
    @echo {{version}}

# Entwicklungsabhängigkeiten im aktiven venv installieren
install:
    pip install -e ".[dev]"

# Python-Wheel und Source-Distribution bauen (erzeugt dist/)
wheel:
    python -m build

# Lokale Entwicklung – baut Image mit aktueller Version und startet den Service
[unix]
dev:
    VERSION={{version}} docker compose -f compose.dev.yml up --build

[windows]
dev:
    $env:VERSION = "{{version}}"; docker compose -f compose.dev.yml up --build

# Docker-Image bauen und taggen
build:
    docker build --build-arg VERSION={{version}} -t ghcr.io/kaijen/title-image:{{docker_tag}} -t ghcr.io/kaijen/title-image:latest .

# Docker-Image bauen, SBOM-Attestation einbetten und zu ghcr.io pushen (setzt voraus: docker login ghcr.io)
push:
    docker buildx build --sbom=true --provenance=mode=max --build-arg VERSION={{version}} -t ghcr.io/kaijen/title-image:{{docker_tag}} -t ghcr.io/kaijen/title-image:latest --push .

# SBOM aus gepushtem Image erzeugen (CycloneDX JSON; setzt voraus: syft – winget install anchore.syft)
sbom:
    syft ghcr.io/kaijen/title-image:{{docker_tag}} -o cyclonedx-json=title-image-{{docker_tag}}.sbom.json
    @echo "SBOM: title-image-{{docker_tag}}.sbom.json"

# Docs lokal vorschauen (http://127.0.0.1:8000)
docs:
    mkdocs serve

# Statische Docs nach site/ bauen
docs-build:
    mkdocs build

# Docker-Image als Tarball exportieren (erzeugt title-image-<VERSION>.tar.gz)
[unix]
export:
    docker save ghcr.io/kaijen/title-image:{{docker_tag}} | gzip > title-image-{{docker_tag}}.tar.gz
    @echo "Exportiert: title-image-{{docker_tag}}.tar.gz"
    @echo "Import beim Empfänger: docker load -i title-image-{{docker_tag}}.tar.gz"

[windows]
export:
    docker save ghcr.io/kaijen/title-image:{{docker_tag}} -o title-image-{{docker_tag}}.tar; `
    & { if (Get-Command gzip -ErrorAction SilentlyContinue) { gzip -f title-image-{{docker_tag}}.tar } else { Compress-Archive -Force -Path title-image-{{docker_tag}}.tar -DestinationPath title-image-{{docker_tag}}.tar.gz; Remove-Item title-image-{{docker_tag}}.tar } }
    @echo "Exportiert: title-image-{{docker_tag}}.tar.gz"
    @echo "Import beim Empfänger: docker load -i title-image-{{docker_tag}}.tar.gz"
