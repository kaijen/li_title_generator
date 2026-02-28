# Build-Umgebung auf Vollständigkeit prüfen
# Aufgerufen via: just checkenv
#
# Prueft: Python >= 3.11, git, hatch, docker, docker buildx (Pflicht)
#         syft (optional)

$ErrorActionPreference = "Continue"
$errors = 0

function Get-ToolVersion([string]$Cmd) {
    try { return ((& $Cmd --version 2>&1) | Select-Object -First 1) }
    catch { return "" }
}

function Write-Ok([string]$Label, [string]$Ver) {
    Write-Host ("  [OK]     {0,-24} {1}" -f $Label, $Ver) -ForegroundColor Green
}

function Write-Fail {
    param([string]$Label, [string[]]$Hints)
    Write-Host ("  [FEHLT]  {0,-24}" -f $Label) -ForegroundColor Red
    foreach ($h in $Hints) { Write-Host ("           -> {0}" -f $h) }
    $script:errors++
}

function Write-Info([string]$Label, [string]$Hint) {
    Write-Host ("  [-]      {0,-24}" -f $Label) -ForegroundColor Yellow
    if ($Hint) { Write-Host ("           -> {0}" -f $Hint) }
}

Write-Host ""
Write-Host "-- Build-Umgebung pruefen --------------------------------------------------------"
Write-Host ""
Write-Host "  Pflichtkomponenten:"

# Python >= 3.11
$pyCmd = $null
if (Get-Command python  -ErrorAction SilentlyContinue) { $pyCmd = "python"  }
elseif (Get-Command python3 -ErrorAction SilentlyContinue) { $pyCmd = "python3" }

if ($pyCmd) {
    $verRaw = ((& $pyCmd --version 2>&1) -join "")
    if ($verRaw -match "Python (\d+)\.(\d+)") {
        $maj = [int]$Matches[1]; $min = [int]$Matches[2]
        if ($maj -ge 3 -and $min -ge 11) {
            Write-Ok "Python >= 3.11" "($verRaw)"
        } else {
            Write-Host ("  [FEHLT]  {0,-24} gefunden: {1}" -f "Python >= 3.11", $verRaw) -ForegroundColor Red
            Write-Host "           -> winget install Python.Python.3.12"
            Write-Host "           -> https://www.python.org/downloads/"
            $errors++
        }
    } else {
        Write-Fail "Python >= 3.11" @("winget install Python.Python.3.12", "https://www.python.org/downloads/")
    }
} else {
    Write-Fail "Python" @("winget install Python.Python.3.12", "https://www.python.org/downloads/")
}

# git
if (Get-Command git -ErrorAction SilentlyContinue) {
    Write-Ok "git" ("(" + (Get-ToolVersion "git") + ")")
} else {
    Write-Fail "git" @("winget install Git.Git", "https://git-scm.com")
}

# hatch
if (Get-Command hatch -ErrorAction SilentlyContinue) {
    Write-Ok "hatch" ("(" + (Get-ToolVersion "hatch") + ")")
} else {
    Write-Fail "hatch" @("pip install hatch", "winget install pypa.hatch")
}

# docker + docker buildx
if (Get-Command docker -ErrorAction SilentlyContinue) {
    Write-Ok "docker" ("(" + (Get-ToolVersion "docker") + ")")

    $bxOut = (& docker buildx version 2>&1) | Select-Object -First 1
    if ($LASTEXITCODE -eq 0) {
        Write-Ok "docker buildx" "($bxOut)"
    } else {
        Write-Fail "docker buildx" @(
            "In Docker Desktop bereits enthalten",
            "https://docs.docker.com/desktop/install/windows-install/"
        )
    }
} else {
    Write-Fail "docker" @(
        "winget install Docker.DockerDesktop",
        "https://docs.docker.com/desktop/install/windows-install/"
    )
    Write-Host ("  [--]     {0,-24} (nicht pruefbar – docker fehlt)" -f "docker buildx") -ForegroundColor DarkGray
}

Write-Host ""
Write-Host "  Optionale Komponenten:"

# syft
if (Get-Command syft -ErrorAction SilentlyContinue) {
    Write-Ok "syft (SBOM)" ("(" + (Get-ToolVersion "syft") + ")")
} else {
    Write-Info "syft (SBOM)" "winget install anchore.syft"
}

Write-Host ""
Write-Host "---------------------------------------------------------------------------------"
if ($errors -eq 0) {
    Write-Host "  Alle Pflichtkomponenten vorhanden. OK" -ForegroundColor Green
} else {
    Write-Host ("  {0} Pflichtkomponente(n) fehlen - Hinweise beachten." -f $errors) -ForegroundColor Red
    exit 1
}
Write-Host ""
