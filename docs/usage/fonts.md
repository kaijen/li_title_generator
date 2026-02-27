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

<!-- TODO: Liste der vorinstallierten Fonts ergänzen -->

## Cache-Verzeichnis

| Umgebungsvariable | Default |
|-------------------|---------|
| `FONT_CACHE_DIR` | `~/.cache/title-image-fonts` |

Im Docker-Container ist der Cache im Image vorgebaut. Das Verzeichnis kann über
ein Volume persistiert werden, um Downloads nach Container-Neustarts zu vermeiden.

## Fehlerverhalten

Ein nicht auflösbarer Font (weder im Cache noch bei Google Fonts abrufbar) führt
zu `HTTP 500 Internal Server Error`.
