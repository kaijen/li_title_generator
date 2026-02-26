# just installieren: winget install Casey.Just  |  brew install just

set windows-shell := ["powershell.exe", "-NoLogo", "-Command"]

version := if os_family() == "windows" { `hatch version` } else { `hatch version 2>/dev/null || git describe --tags --always` }

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
    docker build --build-arg VERSION={{version}} -t ghcr.io/kaijen/title-image:{{version}} -t ghcr.io/kaijen/title-image:latest .

# Docker-Image zu ghcr.io pushen (setzt voraus: docker login ghcr.io)
push: build
    docker push ghcr.io/kaijen/title-image:{{version}}
    docker push ghcr.io/kaijen/title-image:latest

# Docker-Image als Tarball exportieren (erzeugt title-image-<VERSION>.tar.gz)
[unix]
export:
    docker save ghcr.io/kaijen/title-image:{{version}} | gzip > title-image-{{version}}.tar.gz
    @echo "Exportiert: title-image-{{version}}.tar.gz"
    @echo "Import beim Empfänger: docker load -i title-image-{{version}}.tar.gz"

[windows]
export:
    docker save ghcr.io/kaijen/title-image:{{version}} -o title-image-{{version}}.tar; `
    & { if (Get-Command gzip -ErrorAction SilentlyContinue) { gzip -f title-image-{{version}}.tar } else { Compress-Archive -Force -Path title-image-{{version}}.tar -DestinationPath title-image-{{version}}.tar.gz; Remove-Item title-image-{{version}}.tar } }
    @echo "Exportiert: title-image-{{version}}.tar.gz"
    @echo "Import beim Empfänger: docker load -i title-image-{{version}}.tar.gz"
