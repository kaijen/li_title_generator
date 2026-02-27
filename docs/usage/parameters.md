# Parameter

Alle Felder des Request-Body sind optional und haben sinnvolle Standardwerte.

## Übersicht

| Feld | Typ | Default | Beschreibung |
|------|-----|---------|--------------|
| `titel` | string | `""` | Titelzeile(n); wird bei `titelzeilen > 1` auf mehrere Zeilen aufgeteilt |
| `text` | string | `""` | Untertitel oder Fließtext unterhalb des Titels |
| `vordergrund` | string | `"white"` | Schriftfarbe – englischer Name, Hex oder deutsches Alias |
| `hintergrund` | string | `"black"` | Hintergrundfarbe – englischer Name, Hex oder deutsches Alias |
| `breite` | int | `1024` | Bildbreite in Pixeln; die Höhe wird automatisch als 9/16 × Breite berechnet |
| `font` | string | `"Rubik Glitch"` | Google-Fonts-Name oder Systemfont-Name |
| `titelzeilen` | int | `1` | Anzahl Zeilen, auf die der Titel aufgeteilt wird |
| `dateiname` | string | `""` | Dateiname im `Content-Disposition`-Header; leer → automatisch generiert |

## Details

### `titel` und `titelzeilen`

`titelzeilen` steuert, wie viele Zeilen der Titel einnehmen darf. Der Text wird
automatisch umgebrochen. Bei `titelzeilen: 2` wird der Titel z. B. auf zwei
möglichst gleich lange Zeilen aufgeteilt.

```json
{
  "titel": "Sehr langer Titel der auf zwei Zeilen passt",
  "titelzeilen": 2
}
```

### `dateiname`

Erlaubte Zeichen: alphanumerisch, `.`, `-`, `_`; maximal 128 Zeichen.

Wird kein Dateiname angegeben, generiert der Service automatisch einen Namen
nach dem Schema `linkedin_title_YYYY-MM-DD-HH-mm.png`.

### `breite`

Empfohlene Werte:

| Verwendungszweck | Breite |
|------------------|--------|
| LinkedIn-Post | `1920` |
| Präsentationsfolie (Full HD) | `1920` |
| Vorschau / Test | `1024` |

### Farben

Siehe [Farben](colors.md) für alle unterstützten Formate und deutschen Aliase.

### Fonts

Siehe [Fonts](fonts.md) für den Font-Cache und eigene Schriften.

## Beispiele

### Minimaler Request

```json
{ "titel": "Hallo Welt" }
```

### LinkedIn-Post mit allen Feldern

```json
{
  "titel": "NIS2 Compliance",
  "text": "Umsetzung in der Praxis",
  "hintergrund": "#1a1a2e",
  "vordergrund": "white",
  "breite": 1920,
  "titelzeilen": 2,
  "dateiname": "nis2-slide.png"
}
```
