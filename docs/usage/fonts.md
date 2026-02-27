# Fonts

## Funktionsweise

Der Service lädt Fonts automatisch von Google Fonts herunter und speichert sie
in einem lokalen Cache-Verzeichnis. Bei nachfolgenden Requests wird der Cache
verwendet – kein erneuter Download nötig.

## Font angeben

Im Request-Body den `font`-Parameter auf den exakten Google-Fonts-Namen setzen:

```json
{ "titel": "Hallo Welt", "font": "Fira Code" }
```

Groß-/Kleinschreibung muss dem Google-Fonts-Namen entsprechen.

## Vorinstallierte Fonts

Folgende Fonts werden beim Docker-Build vorinstalliert (via `scripts/install_fonts.py`):

| Font | Verwendung |
|------|-----------|
| Rubik Glitch | Standard-Font (`font`-Default) |
| JetBrains Mono | Monospace / Code-Slides |
| Fira Code | Monospace / Code-Slides |
| Libertinus Mono | Monospace / Serifenbetont |

## Cache-Verzeichnis

| Umgebungsvariable | Default |
|-------------------|---------|
| `FONT_CACHE_DIR` | `~/.cache/title-image-fonts` |

Im Docker-Container ist der Cache im Image vorgebaut. Das Verzeichnis kann über
ein Volume persistiert werden, um Downloads nach Container-Neustarts zu vermeiden.

## Fehlerverhalten

Ist ein Font weder im Cache noch über Google Fonts abrufbar, greift der Service
auf System-Fonts (via `fc-match`) zurück. Sind auch keine System-Fonts vorhanden,
wird der eingebaute PIL-Standardfont verwendet – der Request schlägt **nicht** fehl,
das Bild wird mit dem Fallback-Font gerendert.
