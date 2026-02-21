"""
Bildgenerator – Kern aus generate.py übernommen.
generate_image() kann Bilddaten als bytes zurückgeben (output_path=None)
oder in eine Datei speichern.
"""

import io
import logging
import os
import re
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
import urllib.request
import urllib.error

logger = logging.getLogger(__name__)

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

FONT_CACHE_DIR = Path(
    os.environ.get("FONT_CACHE_DIR", Path.home() / ".cache" / "title-image-fonts")
)

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
    "/System/Library/Fonts/Menlo.ttc",
    "C:/Windows/Fonts/consola.ttf",
]


# ─── Hilfsfunktionen ──────────────────────────────────────────────────────────

def normalize_color(color: str) -> str:
    normalized = color.strip().lower()
    return GERMAN_COLOR_MAP.get(normalized, color.strip())


def http_get(url: str, timeout: int = 15) -> bytes:
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 (compatible; title-image-skill/1.0)"}
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


# ─── Font-Auflösung ───────────────────────────────────────────────────────────

def try_system_font(font_name: str) -> str | None:
    try:
        family_result = subprocess.run(
            ["fc-match", "--format=%{family}", font_name],
            capture_output=True, text=True, timeout=5
        )
        matched_family = family_result.stdout.strip().lower()
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
    FONT_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    key = font_name.lower().replace(" ", "_")
    for f in FONT_CACHE_DIR.glob(f"{key}*"):
        return str(f)
    return None


def try_google_fonts(font_name: str) -> str | None:
    gf_name = font_name.replace(" ", "+")
    css_url = f"https://fonts.googleapis.com/css2?family={gf_name}&display=swap"

    try:
        logger.info("Google Fonts: %s", css_url)
        req = urllib.request.Request(
            css_url,
            headers={"User-Agent": "Mozilla/5.0 (compatible; title-image-service/1.0)"}
        )
        css = urllib.request.urlopen(req, timeout=10).read().decode("utf-8")

        urls = re.findall(r"url\((https://[^)]+\.(?:ttf|otf))\)", css)
        if not urls:
            logger.warning("Kein TTF/OTF-Link im CSS für '%s' gefunden", font_name)
            return None

        font_url = urls[0]
        logger.info("Lade Font herunter: %s", font_url)
        font_data = http_get(font_url)

        FONT_CACHE_DIR.mkdir(parents=True, exist_ok=True)
        ext = ".otf" if font_url.endswith(".otf") else ".ttf"
        cache_name = font_name.lower().replace(" ", "_") + ext
        cache_path = FONT_CACHE_DIR / cache_name
        cache_path.write_bytes(font_data)
        logger.info("Font gecacht: %s", cache_path)
        return str(cache_path)

    except (urllib.error.URLError, urllib.error.HTTPError, OSError) as e:
        logger.warning("Google Fonts fehlgeschlagen: %s", e)
        return None


def resolve_font(font_name: str) -> tuple[str | None, str]:
    logger.info("Suche Font: '%s'", font_name)

    path = try_system_font(font_name)
    if path:
        logger.info("System-Font gefunden: %s", path)
        return path, font_name

    path = try_cache(font_name)
    if path:
        logger.info("Cache-Font gefunden: %s", path)
        return path, font_name

    logger.info("Versuche Google Fonts…")
    path = try_google_fonts(font_name)
    if path:
        logger.info("Von Google Fonts heruntergeladen: %s", path)
        return path, font_name

    logger.warning("Font '%s' nicht verfügbar. Verwende Systemfallback.", font_name)
    for fallback_path in SYSTEM_FALLBACKS:
        if Path(fallback_path).exists():
            name = Path(fallback_path).stem
            logger.info("Fallback: %s (%s)", name, fallback_path)
            return fallback_path, name

    try:
        result = subprocess.run(
            ["fc-match", "--format=%{file}"],
            capture_output=True, text=True, timeout=5
        )
        path = result.stdout.strip()
        if path and Path(path).exists():
            logger.info("fc-match Fallback: %s", path)
            return path, Path(path).stem
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass

    logger.warning("Kein Font gefunden – verwende PIL-Standardfont.")
    return None, "PIL Default"


# ─── Textumbruch ──────────────────────────────────────────────────────────────

def wrap_text(text: str, font: ImageFont.FreeTypeFont | ImageFont.ImageFont, max_width: int, draw: ImageDraw.ImageDraw) -> list[str]:
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


# ─── Bildgenerierung ──────────────────────────────────────────────────────────

def generate_image(data: dict, output_path: str | None = None) -> bytes | str:
    """
    Erzeugt ein 16:9-Titelbild.

    - output_path=None  → gibt PNG-Bilddaten als bytes zurück
    - output_path=<str> → speichert in Datei, gibt Pfad zurück
    """
    config = {**DEFAULTS, **data}

    titel       = config["titel"]
    text        = config["text"]
    fg_color    = normalize_color(str(config["vordergrund"]))
    bg_color    = normalize_color(str(config["hintergrund"]))
    breite      = int(config["breite"])
    font_name   = config["font"]
    titelzeilen = max(1, int(config["titelzeilen"]))
    hoehe       = int(breite * 9 / 16)

    logger.info("Bildgröße: %dx%dpx (16:9)", breite, hoehe)
    logger.info("Farben: FG=%s  BG=%s", fg_color, bg_color)

    font_path, resolved_name = resolve_font(font_name)

    target_titel_w = int(breite * 0.80)
    padding_h      = int(breite * 0.08)
    max_text_w     = breite - 2 * padding_h

    def load_font(size: int):
        if font_path:
            try:
                return ImageFont.truetype(font_path, size)
            except Exception as e:
                logger.warning("Fehler beim Laden des Fonts (%s), PIL-Standard.", e)
        return ImageFont.load_default()

    img  = Image.new("RGB", (breite, hoehe), color=bg_color)
    draw = ImageDraw.Draw(img)

    def fit_font_to_width(text_str: str, target_w: int, size_min=8, size_max=1000):
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
        logger.debug(
            "Titel-Fontgröße: %dpx → Titelbreite: %dpx (%.1f%%)",
            best_size, actual_w, actual_w / breite * 100,
        )
        return best_font, best_size

    def split_title(title_str: str, n: int) -> list[str]:
        words = title_str.split()
        if n <= 1 or len(words) <= 1:
            return [title_str]
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

    if titel:
        titel_lines_raw = split_title(titel, titelzeilen)
        longest_line = max(titel_lines_raw, key=len)
        titel_font, titel_size = fit_font_to_width(longest_line, target_titel_w)
    else:
        titel_lines_raw = []
        titel_size = max(12, int(breite * 0.07))
        titel_font = load_font(titel_size)

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

    if output_path is None:
        buf = io.BytesIO()
        img.save(buf, "PNG")
        logger.info("Bild erzeugt (%d Bytes)", buf.tell())
        return buf.getvalue()
    else:
        img.save(output_path, "PNG")
        logger.info("Gespeichert: %s", output_path)
        return output_path
