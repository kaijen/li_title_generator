# Nutzung – Übersicht

## Erstes Bild erzeugen

```bash
curl -X POST http://localhost:8000/generate \
  -H "X-API-Key: sk-abc123" \
  -H "Content-Type: application/json" \
  -d '{
    "titel": "NIS2 Compliance",
    "text": "Umsetzung in der Praxis",
    "hintergrund": "#1a1a2e",
    "vordergrund": "white",
    "breite": 1920,
    "titelzeilen": 2,
    "dateiname": "nis2-slide.png"
  }' \
  --output nis2-slide.png
```

## Weiterführende Themen

- [Parameter](parameters.md) – alle Request-Felder im Detail
- [Farben](colors.md) – Hex, CSS-Namen, deutsche Aliase
- [Fonts](fonts.md) – verfügbare Schriften, Cache, eigene Fonts
- [Client-Beispiele](clients.md) – curl, PowerShell, Python
