# just installieren: winget install Casey.Just  |  brew install just

set windows-shell := ["powershell.exe", "-NoLogo", "-Command"]

version    := if os_family() == "windows" { `hatch version` } else { `hatch version 2>/dev/null || git describe --tags --always` }
# Docker-Tags erlauben kein '+' (PEP-440-Local-Identifier) – lokalen Teil abschneiden
docker_tag := if os_family() == "windows" { `(hatch version) -replace '\+.*',''` } else { `hatch version 2>/dev/null | sed 's/+.*//' || git describe --tags --abbrev=0` }

# Aktuelle Version ausgeben
version:
    @echo {{version}}

# Build-Umgebung auf Vollständigkeit prüfen (Python ≥ 3.11, git, hatch, docker, docker buildx)
[unix]
checkenv:
    #!/usr/bin/env bash
    set +e
    errors=0
    ok()   { printf "  \033[32m✓\033[0m  %-24s %s\n"  "$1" "$2"; }
    fail() { printf "  \033[31m✗\033[0m  %-24s %s\n"  "$1" "$2"; errors=$((errors+1)); }
    info() { printf "  \033[33m–\033[0m  %-24s %s\n"  "$1" "$2"; }

    echo ""
    echo "── Build-Umgebung prüfen ─────────────────────────────────────────────"
    echo ""
    echo "  Pflichtkomponenten:"

    py=$(command -v python3 2>/dev/null || command -v python 2>/dev/null)
    if [ -n "$py" ]; then
        ver=$("$py" --version 2>&1)
        maj=$("$py" -c "import sys; print(sys.version_info.major)")
        min=$("$py" -c "import sys; print(sys.version_info.minor)")
        if [ "$maj" -ge 3 ] && [ "$min" -ge 11 ]; then
            ok "Python ≥ 3.11" "($ver)"
        else
            fail "Python ≥ 3.11 erforderlich" "gefunden: $ver"
            info "" "→ apt/dnf install python3.11  |  https://www.python.org/downloads/"
        fi
    else
        fail "Python" "nicht gefunden"
        info "" "→ apt install python3  |  dnf install python3  |  https://www.python.org"
    fi

    if command -v git &>/dev/null; then
        ok "git" "($(git --version))"
    else
        fail "git" "nicht gefunden"
        info "" "→ apt install git  |  dnf install git  |  https://git-scm.com"
    fi

    if command -v hatch &>/dev/null; then
        ok "hatch" "($(hatch --version 2>&1 | head -1))"
    else
        fail "hatch" "nicht gefunden"
        info "" "→ pip install hatch  |  pipx install hatch"
    fi

    if command -v docker &>/dev/null; then
        ok "docker" "($(docker --version))"
        if docker buildx version &>/dev/null 2>&1; then
            ok "docker buildx" "($(docker buildx version 2>&1 | head -1))"
        else
            fail "docker buildx" "nicht gefunden"
            info "" "→ Ab Docker 23 enthalten  |  https://github.com/docker/buildx#installing"
        fi
    else
        fail "docker" "nicht gefunden"
        info "" "→ https://docs.docker.com/engine/install/"
        fail "docker buildx" "nicht prüfbar (docker fehlt)"
    fi

    echo ""
    echo "  Optionale Komponenten:"

    if command -v syft &>/dev/null; then
        ok "syft (SBOM)" "($(syft --version 2>&1 | head -1))"
    else
        info "syft (SBOM)" "nicht installiert"
        info "" "→ curl -sSfL https://raw.githubusercontent.com/anchore/syft/main/install.sh | sh -s -- -b /usr/local/bin"
    fi

    echo ""
    echo "─────────────────────────────────────────────────────────────────────"
    if [ "$errors" -eq 0 ]; then
        printf "\033[32m  Alle Pflichtkomponenten vorhanden. ✓\033[0m\n"
    else
        printf "\033[31m  %d Pflichtkomponente(n) fehlen – Hinweise beachten. ✗\033[0m\n" "$errors"
        exit 1
    fi
    echo ""

[windows]
checkenv:
    powershell -NonInteractive -ExecutionPolicy Bypass -File scripts\checkenv.ps1

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
