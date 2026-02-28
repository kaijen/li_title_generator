# Farben

Farben können in drei Formaten angegeben werden:

## Formate

| Format | Beispiele |
|--------|-----------|
| Englischer CSS-Name | `"white"`, `"black"`, `"red"`, `"navy"` |
| Hex-Code | `"#1a1a2e"`, `"#fff"` |
| Deutsches Alias | `"schwarz"`, `"weiß"`, `"rot"` |

## Deutsche Farbaliase

| Deutsch | Pillow-Name |
|---------|-------------|
| `schwarz` | `black` |
| `weiß`, `weiss` | `white` |
| `rot` | `red` |
| `grün`, `gruen` | `green` |
| `blau` | `blue` |
| `gelb` | `yellow` |
| `orange` | `orange` |
| `lila` | `purple` |
| `violett` | `violet` |
| `pink` | `pink` |
| `grau` | `gray` |
| `braun` | `brown` |
| `türkis`, `tuerkis` | `cyan` |
| `silber` | `silver` |
| `gold` | `gold` |

## Fehlerverhalten

Eine ungültige Farbe (Name nicht erkennbar, ungültiger Hex-Code) führt zu
`HTTP 422 Unprocessable Entity` mit einer beschreibenden Fehlermeldung.

## Beispiele

```json
{ "hintergrund": "#1a1a2e", "vordergrund": "white" }
{ "hintergrund": "schwarz", "vordergrund": "weiß" }
{ "hintergrund": "navy",    "vordergrund": "gold" }
```
