#!/usr/bin/env python3
"""
Title Image Generator
Erzeugt ein 16:9-Bild mit zentriertem Titel und Untertext.

Verwendung:
    python3 generate.py '{"titel": "Mein Titel", "text": "Untertext"}'
    python3 generate.py input.json
    python3 generate.py '{"titel": "Test"}' -o output.png
"""

import argparse
import json
import os
import re
import subprocess
import sys
import urllib.request
import urllib.error
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    configured = os.environ.get("TITLE_IMAGE_PYTHON")
    hint = f"$TITLE_IMAGE_PYTHON ({configured})" if configured else "python3"
    print(f"❌ Pillow nicht gefunden (Interpreter: {sys.executable})")
    print(f"   Installieren: {hint} -m pip install Pillow")
    sys.exit(1)

# Interpreter-Info beim Start (nur wenn explizit konfiguriert)
if os.environ.get("TITLE_IMAGE_PYTHON"):
    print(f"🐍 Python: {sys.executable}  [via $TITLE_IMAGE_PYTHON]")


# ─── Konfiguration ────────────────────────────────────────────────────────────

DEFAULTS = {
    "titel": "",
    "text": "",
    "vordergrund": "white",
    "hintergrund": "black",
    "breite": 1024,
    "font": "Rubik Glitch",
    "titelzeilen": 1,
}

# Font-Cache-Verzeichnis (plattformübergreifend)
FONT_CACHE_DIR = Path.home() / ".cache" / "title-image-fonts"

# Deutsche Farbnamen → Pillow-kompatibel
GERMAN_COLOR_MAP = {
    "weiß": "white", "weiss": "white",
    "schwarz": "black",
    "rot": "red",
    "grün": "green", "gruen": "green",
    "blau": "blue",
    "gelb": "yellow",
    "orange": "orange",
    "lila": "purple",
    "violett": "violet",
    "pink": "pink",
    "grau": "gray",
    "braun": "brown",
    "türkis": "cyan", "tuerkis": "cyan",
    "silber": "silver",
    "gold": "gold",
}

SYSTEM_FALLBACKS = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf",
    "/usr/share/fonts/truetype/freefont/FreeMono.ttf",
    "/usr/share/fonts/opentype/noto/NotoSans-Regular.ttf",
    "/System/Library/Fonts/Menlo.ttc",       # macOS
    "C:/Windows/Fonts/consola.ttf",           # Windows
]


# ─── Hilfsfunktionen ──────────────────────────────────────────────────────────

def normalize_color(color: str) -> str:
    normalized = color.strip().lower()
    return GERMAN_COLOR_MAP.get(normalized, color.strip())


def http_get(url: str, timeout: int = 15) -> bytes:
    """Einfacher HTTP-GET mit Browser-User-Agent."""
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 (compatible; title-image-skill/1.0)"}
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


# ─── Font-Auflösung ───────────────────────────────────────────────────────────

def try_system_font(font_name: str) -> str | None:
    """Versucht den Font via fc-match (fontconfig) auf dem System zu finden."""
    try:
        family_result = subprocess.run(
            ["fc-match", "--format=%{family}", font_name],
            capture_output=True, text=True, timeout=5
        )
        matched_family = family_result.stdout.strip().lower()
        # Prüfen ob das Match ungefähr stimmt
        if any(w in matched_family for w in font_name.lower().split()):
            path_result = subprocess.run(
                ["fc-match", "--format=%{file}", font_name],
                capture_output=True, text=True, timeout=5
            )
            path = path_result.stdout.strip()
            if path and Path(path).exists():
                return path
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    return None


def try_cache(font_name: str) -> str | None:
    """Prüft ob der Font bereits im lokalen Cache liegt."""
    FONT_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    key = font_name.lower().replace(" ", "_")
    for f in FONT_CACHE_DIR.glob(f"{key}*"):
        return str(f)
    return None


def try_google_fonts(font_name: str) -> str | None:
    """
    Versucht den Font von Google Fonts herunterzuladen.
    Parst die CSS-Antwort um die TTF/OTF-URL zu extrahieren.
    Gibt den lokalen Cache-Pfad zurück oder None.
    """
    gf_name = font_name.replace(" ", "+")
    css_url = f"https://fonts.googleapis.com/css2?family={gf_name}&display=swap"

    try:
        print(f"  → Google Fonts: {css_url}")
        # Älterer User-Agent → Google liefert TTF statt WOFF2 (direkt verwendbar)
        req = urllib.request.Request(
            css_url,
            headers={"User-Agent": "Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1)"}
        )
        css = urllib.request.urlopen(req, timeout=10).read().decode("utf-8")

        # Font-URL aus CSS extrahieren
        urls = re.findall(r"url\((https://[^)]+\.(?:ttf|otf))\)", css)
        if not urls:
            print(f"  → Kein TTF/OTF-Link im CSS gefunden (Font möglicherweise nicht auf Google Fonts)")
            return None

        font_url = urls[0]
        print(f"  → Lade herunter: {font_url}")
        font_data = http_get(font_url)

        # Im Cache speichern
        FONT_CACHE_DIR.mkdir(parents=True, exist_ok=True)
        ext = ".otf" if font_url.endswith(".otf") else ".ttf"
        cache_name = font_name.lower().replace(" ", "_") + ext
        cache_path = FONT_CACHE_DIR / cache_name
        cache_path.write_bytes(font_data)
        print(f"  → Gecacht: {cache_path}")
        return str(cache_path)

    except (urllib.error.URLError, urllib.error.HTTPError, OSError) as e:
        print(f"  → Google Fonts fehlgeschlagen: {e}")
        return None


def resolve_font(font_name: str) -> tuple[str | None, str]:
    """
    Löst einen Font-Namen zu einem lokalen Dateipfad auf.
    Reihenfolge: System → Cache → Google Fonts → Systemfallback
    """
    print(f"🔍 Suche Font: '{font_name}'")

    # 1. System (fc-match / fontconfig)
    path = try_system_font(font_name)
    if path:
        print(f"✓ System-Font gefunden: {path}")
        return path, font_name

    print(f"  System-Font nicht gefunden.")

    # 2. Lokaler Cache (vorheriger Download)
    path = try_cache(font_name)
    if path:
        print(f"✓ Cache-Font gefunden: {path}")
        return path, font_name

    # 3. Google Fonts
    print(f"  Versuche Google Fonts…")
    path = try_google_fonts(font_name)
    if path:
        print(f"✓ Von Google Fonts heruntergeladen: {path}")
        return path, font_name

    # 4. Systemfallbacks
    print(f"⚠ Font '{font_name}' nicht verfügbar. Verwende Systemfallback.")
    for fallback_path in SYSTEM_FALLBACKS:
        if Path(fallback_path).exists():
            name = Path(fallback_path).stem
            print(f"  Fallback: {name} ({fallback_path})")
            return fallback_path, name

    # 5. fc-match erzwingt immer einen Treffer
    try:
        result = subprocess.run(
            ["fc-match", "--format=%{file}"],
            capture_output=True, text=True, timeout=5
        )
        path = result.stdout.strip()
        if path and Path(path).exists():
            print(f"  fc-match Fallback: {path}")
            return path, Path(path).stem
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass

    print(f"  Kein Font gefunden – verwende PIL-Standardfont.")
    return None, "PIL Default"


# ─── Bildgenerierung ──────────────────────────────────────────────────────────

def wrap_text(text: str, font: ImageFont.FreeTypeFont, max_width: int, draw: ImageDraw.Draw) -> list[str]:
    """Bricht Text in Zeilen um, die nicht breiter als max_width sind."""
    if not text:
        return []
    words = text.split()
    lines, current_line = [], []
    for word in words:
        test_line = " ".join(current_line + [word])
        bbox = draw.textbbox((0, 0), test_line, font=font)
        if bbox[2] - bbox[0] <= max_width:
            current_line.append(word)
        else:
            if current_line:
                lines.append(" ".join(current_line))
                current_line = [word]
            else:
                lines.append(word)
    if current_line:
        lines.append(" ".join(current_line))
    return lines


def generate_image(data: dict, output_path: str = "output.png") -> str:
    """Hauptfunktion zur Bildgenerierung."""
    config = {**DEFAULTS, **data}

    titel       = config["titel"]
    text        = config["text"]
    fg_color    = normalize_color(str(config["vordergrund"]))
    bg_color    = normalize_color(str(config["hintergrund"]))
    breite      = int(config["breite"])
    font_name   = config["font"]
    titelzeilen = max(1, int(config["titelzeilen"]))
    hoehe       = int(breite * 9 / 16)

    print(f"\n{'─'*50}")
    print(f"📐 Bildgröße:   {breite}×{hoehe}px (16:9)")
    print(f"🎨 Farben:      FG={fg_color}  BG={bg_color}")

    font_path, resolved_name = resolve_font(font_name)

    target_titel_w = int(breite * 0.80)  # Titel soll ~80% der Breite einnehmen
    padding_h  = int(breite * 0.08)
    max_text_w = breite - 2 * padding_h

    def load_font(size: int):
        if font_path:
            try:
                return ImageFont.truetype(font_path, size)
            except Exception as e:
                print(f"⚠ Fehler beim Laden des Fonts ({e}), PIL-Standard.")
        return ImageFont.load_default()

    img  = Image.new("RGB", (breite, hoehe), color=bg_color)
    draw = ImageDraw.Draw(img)

    def fit_font_to_width(text_str: str, target_w: int, size_min=8, size_max=1000):
        """Binäre Suche: größte Schriftgröße bei der text_str <= target_w breit ist."""
        lo, hi, best_size = size_min, size_max, size_min
        while lo <= hi:
            mid = (lo + hi) // 2
            f = load_font(mid)
            bbox = draw.textbbox((0, 0), text_str, font=f)
            w = bbox[2] - bbox[0]
            if w <= target_w:
                best_size = mid
                lo = mid + 1
            else:
                hi = mid - 1
        best_font = load_font(best_size)
        bbox = draw.textbbox((0, 0), text_str, font=best_font)
        actual_w = bbox[2] - bbox[0]
        print(f"  Titel-Fontgröße: {best_size}px → Titelbreite: {actual_w}px ({actual_w/breite*100:.1f}% von {breite}px)")
        return best_font, best_size

    # Titel auf titelzeilen Zeilen aufteilen (möglichst gleichmäßig nach Wörtern)
    def split_title(title_str: str, n: int) -> list[str]:
        """Teilt den Titel in n Zeilen auf, gleichmäßig nach Wörtern."""
        words = title_str.split()
        if n <= 1 or len(words) <= 1:
            return [title_str]
        # Zielanzahl Wörter pro Zeile
        per_line = len(words) / n
        lines, i = [], 0
        for line_idx in range(n):
            start = i
            end = round(per_line * (line_idx + 1))
            end = min(end, len(words))
            if line_idx == n - 1:
                end = len(words)
            chunk = words[start:end]
            if chunk:
                lines.append(" ".join(chunk))
            i = end
        return [l for l in lines if l]

    # Titelgröße: längste Zeile soll ~80% der Bildbreite einnehmen
    if titel:
        titel_lines_raw = split_title(titel, titelzeilen)
        longest_line = max(titel_lines_raw, key=len)
        titel_font, titel_size = fit_font_to_width(longest_line, target_titel_w)
        # Kontrollausgabe aller Zeilen
        for i, line in enumerate(titel_lines_raw):
            bbox = draw.textbbox((0, 0), line, font=titel_font)
            w = bbox[2] - bbox[0]
            print(f"  Zeile {i+1}: '{line}' → {w}px ({w/breite*100:.1f}%)")
    else:
        titel_lines_raw = []
        titel_size = max(12, int(breite * 0.07))
        titel_font = load_font(titel_size)

    # Untertext: ~40% der Titelgröße, mindestens 10px; darf umbrechen
    text_size = max(10, int(titel_size * 0.40))
    text_font = load_font(text_size)
    gap       = max(10, int(titel_size * 0.30))

    titel_lines = titel_lines_raw
    text_lines  = wrap_text(text, text_font, max_text_w, draw) if text else []

    def block_height(lines, font, leading=1.3):
        if not lines:
            return 0
        bbox = draw.textbbox((0, 0), "Ag", font=font)
        return int((bbox[3] - bbox[1]) * leading) * len(lines)

    total_h = (block_height(titel_lines, titel_font)
               + (gap if titel_lines and text_lines else 0)
               + block_height(text_lines, text_font))

    y = (hoehe - total_h) // 2

    def draw_lines(lines, font, leading=1.3):
        nonlocal y
        if not lines:
            return
        bbox_ref = draw.textbbox((0, 0), "Ag", font=font)
        line_h = int((bbox_ref[3] - bbox_ref[1]) * leading)
        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=font)
            x = (breite - (bbox[2] - bbox[0])) // 2
            draw.text((x, y), line, font=font, fill=fg_color)
            y += line_h

    draw_lines(titel_lines, titel_font)
    if titel_lines and text_lines:
        y += gap
    draw_lines(text_lines, text_font)

    img.save(output_path, "PNG")
    print(f"\n✅ Gespeichert: {output_path}")
    print(f"{'─'*50}\n")
    return output_path


# ─── CLI ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Erstellt ein 16:9-Titelbild aus JSON-Daten.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Beispiele:
  python3 generate.py '{"titel": "Hallo", "text": "Willkommen"}'
  python3 generate.py input.json -o slide.png
  python3 generate.py '{"titel": "Test", "hintergrund": "#1a1a2e", "breite": 1920}'
        """
    )
    parser.add_argument("input",  help="JSON-String oder Pfad zu einer .json-Datei")
    parser.add_argument("-o", "--output", default="output.png", help="Ausgabepfad (Standard: output.png)")
    args = parser.parse_args()

    input_str = args.input.strip()
    if input_str.startswith("{"):
        try:
            data = json.loads(input_str)
        except json.JSONDecodeError as e:
            print(f"❌ Ungültiges JSON: {e}")
            sys.exit(1)
    else:
        json_path = Path(input_str)
        if not json_path.exists():
            print(f"❌ Datei nicht gefunden: {json_path}")
            sys.exit(1)
        with open(json_path, encoding="utf-8") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError as e:
                print(f"❌ Ungültiges JSON in {json_path}: {e}")
                sys.exit(1)

    generate_image(data, args.output)


if __name__ == "__main__":
    main()
