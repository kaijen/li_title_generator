function New-TitleImage {
    <#
    .SYNOPSIS
        Erzeugt ein 16:9-Titelbild (PNG) über den title-image-service.

    .DESCRIPTION
        Sendet einen POST-Request an /generate und speichert das zurückgegebene
        PNG lokal. URL und API-Key werden aus Parametern, Umgebungsvariablen oder
        einer .env-Datei im aktuellen Verzeichnis gelesen (Priorität: Parameter >
        Umgebungsvariable > .env > Default).

        Für mTLS-gesicherte Endpunkte kann ein Client-Zertifikat als PFX-Datei
        oder über den Windows-Zertifikatspeicher (Thumbprint) übergeben werden.

    .PARAMETER Url
        URL des title-image-service, z. B. "https://title-image.example.com".
        Default: TITLE_IMAGE_SERVICE_URL (Umgebungsvariable/.env) oder http://localhost:8000.

    .PARAMETER ApiKey
        API-Key (X-API-Key-Header). Optional, wenn der Service ohne Keys betrieben wird.
        Default: TITLE_IMAGE_API_KEY (Umgebungsvariable/.env).

    .PARAMETER CertPfx
        Pfad zu einer PFX/P12-Datei für mTLS-Client-Authentifizierung.
        Hat Vorrang vor -CertThumbprint.

    .PARAMETER CertPfxPass
        Passwort zur PFX-Datei. Leer lassen, wenn die Datei ungeschützt ist.

    .PARAMETER CertThumbprint
        Thumbprint eines Zertifikats aus dem Windows-Zertifikatspeicher
        (CurrentUser\My oder LocalMachine\My).

    .PARAMETER Titel
        Titeltext des Bilds. Alias: -t

    .PARAMETER Text
        Untertitel oder Fließtext. Leer lässt das Textfeld frei.

    .PARAMETER Vordergrund
        Schriftfarbe: englischer Name ("white"), Hex ("#1a1a2e") oder
        deutscher Name ("weiß", "schwarz", "rot", …). Default: "white"

    .PARAMETER Hintergrund
        Hintergrundfarbe (gleiche Formate wie -Vordergrund). Default: "black"

    .PARAMETER Breite
        Bildbreite in Pixeln; die Höhe wird als 9/16 der Breite berechnet.
        Alias: -b  Default: 1920

    .PARAMETER Font
        Google-Fonts-Name oder installierter Systemfont. Alias: -f
        Default: "Rubik Glitch"

    .PARAMETER Titelzeilen
        Anzahl der Zeilen, auf die der Titel aufgeteilt wird. Alias: -z  Default: 1

    .PARAMETER Dateiname
        Lokaler Dateiname der gespeicherten PNG-Datei.
        Leer oder weggelassen → linkedin_title_<YYYY-MM-DD-HH-mm>.png

    .PARAMETER Montagspost
        Setzt Text auf "Ein Montagspost" und Font auf "Barriecito". Alias: -m

    .PARAMETER AntiPattern
        Setzt Text auf "Ein Anti-Pattern" und Font auf "Rubik Glitch". Alias: -a

    .EXAMPLE
        New-TitleImage -Titel "NIS2 Compliance" -Breite 1920

        URL und API-Key aus .env; automatischer Dateiname.

    .EXAMPLE
        New-TitleImage -t "NIS2 Compliance" -b 1920 -z 2 -f "Fira Code"

        Kurzform mit Aliases.

    .EXAMPLE
        New-TitleImage -Titel "Montag, der Motivator" -m

        Montagspost: Text und Font werden automatisch gesetzt.

    .EXAMPLE
        New-TitleImage -Titel "God Object" -a

        Anti-Pattern-Post.

    .EXAMPLE
        New-TitleImage -t "NIS2 Compliance" -b 1920 `
            -CertPfx "C:\certs\client.pfx" -CertPfxPass "geheim"

        mTLS mit PFX-Datei.

    .EXAMPLE
        New-TitleImage -t "NIS2 Compliance" -b 1920 `
            -CertThumbprint "A1B2C3D4E5F6A1B2C3D4E5F6A1B2C3D4E5F6A1B2"

        mTLS mit Zertifikat aus dem Windows-Zertifikatspeicher.

    .NOTES
        Konfigurationspriorität (höchste zuerst):
          Parameter > Umgebungsvariable > .env-Datei (KEY=VALUE) > Default

        .env-Variablen: TITLE_IMAGE_SERVICE_URL, TITLE_IMAGE_API_KEY,
        TITLE_IMAGE_CERT_PFX, TITLE_IMAGE_CERT_PFX_PASS, TITLE_IMAGE_CERT_THUMBPRINT

        -CertPfx und -CertThumbprint schließen sich gegenseitig aus;
        wird beides angegeben, hat -CertPfx Vorrang.
    #>
    [CmdletBinding()]
    param(
        [string] $Url             = "",
        [string] $ApiKey          = "",

        # Client-Zertifikat (optional) – entweder PFX-Datei oder Thumbprint
        [string] $CertPfx         = "",   # Pfad zur PFX/P12-Datei
        [string] $CertPfxPass     = "",   # Passwort der PFX-Datei (optional)
        [string] $CertThumbprint  = "",   # Thumbprint aus Windows-Zertifikatspeicher

        [Alias("t")]
        [string] $Titel       = "",
        [string] $Text        = "",
        [string] $Vordergrund = "white",
        [string] $Hintergrund = "black",
        [Alias("b")]
        [int]    $Breite      = 1920,
        [Alias("f")]
        [string] $Font        = "Rubik Glitch",
        [Alias("z")]
        [int]    $Titelzeilen = 1,
        [string] $Dateiname   = "",

        [Alias("m")]
        [switch] $Montagspost,

        [Alias("a")]
        [switch] $AntiPattern
    )

    # .env im aktuellen Verzeichnis einlesen (KEY=VALUE, # Kommentare werden übersprungen)
    $dotenv = @{}
    $dotenvPath = Join-Path $PWD ".env"
    if (Test-Path $dotenvPath) {
        Get-Content $dotenvPath |
            Where-Object { $_ -match '^\s*[^#\s]' -and $_ -match '=' } |
            ForEach-Object {
                $key, $val = $_ -split '=', 2
                $dotenv[$key.Trim()] = $val.Trim().Trim('"').Trim("'")
            }
    }

    # URL: Parameter → Umgebungsvariable → .env → Default
    if (-not $Url) {
        if ($env:TITLE_IMAGE_SERVICE_URL)           { $Url = $env:TITLE_IMAGE_SERVICE_URL }
        elseif ($dotenv['TITLE_IMAGE_SERVICE_URL']) { $Url = $dotenv['TITLE_IMAGE_SERVICE_URL'] }
        else                                        { $Url = "http://localhost:8000" }
    }

    # API-Key: Parameter → Umgebungsvariable → .env → leer (Key ist optional)
    if (-not $ApiKey) {
        if ($env:TITLE_IMAGE_API_KEY)           { $ApiKey = $env:TITLE_IMAGE_API_KEY }
        elseif ($dotenv['TITLE_IMAGE_API_KEY']) { $ApiKey = $dotenv['TITLE_IMAGE_API_KEY'] }
    }

    # Client-Zertifikat: Parameter → Umgebungsvariable → .env → keines
    if (-not $CertPfx) {
        if ($env:TITLE_IMAGE_CERT_PFX)           { $CertPfx = $env:TITLE_IMAGE_CERT_PFX }
        elseif ($dotenv['TITLE_IMAGE_CERT_PFX']) { $CertPfx = $dotenv['TITLE_IMAGE_CERT_PFX'] }
    }
    if (-not $CertPfxPass) {
        if ($env:TITLE_IMAGE_CERT_PFX_PASS)           { $CertPfxPass = $env:TITLE_IMAGE_CERT_PFX_PASS }
        elseif ($dotenv['TITLE_IMAGE_CERT_PFX_PASS']) { $CertPfxPass = $dotenv['TITLE_IMAGE_CERT_PFX_PASS'] }
    }
    if (-not $CertThumbprint) {
        if ($env:TITLE_IMAGE_CERT_THUMBPRINT)           { $CertThumbprint = $env:TITLE_IMAGE_CERT_THUMBPRINT }
        elseif ($dotenv['TITLE_IMAGE_CERT_THUMBPRINT']) { $CertThumbprint = $dotenv['TITLE_IMAGE_CERT_THUMBPRINT'] }
    }

    # Zertifikat laden – PFX-Datei hat Vorrang vor Thumbprint
    $cert = $null
    if ($CertPfx) {
        if (-not (Test-Path -LiteralPath $CertPfx)) {
            Write-Error "PFX-Datei nicht gefunden: '$CertPfx'"
            return
        }
        try {
            $cert = if ($CertPfxPass) {
                New-Object System.Security.Cryptography.X509Certificates.X509Certificate2($CertPfx, $CertPfxPass)
            } else {
                New-Object System.Security.Cryptography.X509Certificates.X509Certificate2($CertPfx)
            }
        } catch {
            Write-Error "PFX-Datei konnte nicht geladen werden: $($_.Exception.Message)"
            return
        }
    } elseif ($CertThumbprint) {
        $cert = Get-ChildItem -Path Cert:\CurrentUser\My, Cert:\LocalMachine\My -ErrorAction SilentlyContinue |
                    Where-Object { $_.Thumbprint -eq $CertThumbprint } |
                    Select-Object -First 1
        if (-not $cert) {
            Write-Error "Kein Zertifikat mit Thumbprint '$CertThumbprint' im Zertifikatspeicher gefunden."
            return
        }
    }

    if ($Montagspost) {
        $Text = "Ein Montagspost"
        $Font = "Barriecito"
    }
    elseif ($AntiPattern) {
        $Text = "Ein Anti-Pattern"
        $Font = "Rubik Glitch"
    }

    if (-not $Titel -and -not $Text) {
        Write-Warning "Weder -Titel noch -Text angegeben. Das Bild enthält keinen Text."
    }

    $body = @{
        titel       = $Titel
        text        = $Text
        vordergrund = $Vordergrund
        hintergrund = $Hintergrund
        breite      = $Breite
        font        = $Font
        titelzeilen = $Titelzeilen
        dateiname   = $Dateiname
    } | ConvertTo-Json

    $headers = @{ "Content-Type" = "application/json" }
    if ($ApiKey) { $headers["X-API-Key"] = $ApiKey }

    $outFile = if ($Dateiname) {
        $Dateiname
    } else {
        "linkedin_title_$(Get-Date -Format 'yyyy-MM-dd-HH-mm').png"
    }

    $iwrParams = @{
        Uri     = "$Url/generate"
        Method  = "POST"
        Headers = $headers
        Body    = $body
        OutFile = $outFile
    }
    if ($cert) { $iwrParams["Certificate"] = $cert }

    try {
        Invoke-WebRequest @iwrParams -ErrorAction Stop
        Write-Host "Gespeichert: $outFile"
    } catch {
        # HTTP-Statuscode auslesen – kompatibel mit PS 5.1 und PS 7+
        $statusCode = $null
        if ($_.Exception.PSObject.Properties['StatusCode']) {
            $statusCode = [int]$_.Exception.StatusCode
        } elseif ($_.Exception.Response) {
            $statusCode = [int]$_.Exception.Response.StatusCode
        }

        # Detailmeldung aus dem Response-Body (vorhanden in PS 7+ via ErrorDetails)
        $detail = if ($_.ErrorDetails.Message) { " – $($_.ErrorDetails.Message)" } else { "" }

        if ($null -ne $statusCode) {
            switch ($statusCode) {
                401 { Write-Error "Authentifizierung fehlgeschlagen (HTTP 401). API-Key prüfen.$detail" }
                422 { Write-Error "Ungültige Parameter (HTTP 422).$detail" }
                500 { Write-Error "Interner Serverfehler (HTTP 500). Logs des Service prüfen.$detail" }
                default { Write-Error "HTTP-Fehler $statusCode.$detail" }
            }
        } else {
            Write-Error "Service nicht erreichbar unter '$Url': $($_.Exception.Message)"
        }
    }
}
