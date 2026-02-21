import io

import pytest
from PIL import Image

from title_image_service.generator import generate_image, normalize_color


# ── Bestehende Tests ──────────────────────────────────────────────────────────

def test_normalize_color_german():
    assert normalize_color("schwarz") == "black"
    assert normalize_color("weiß") == "white"
    assert normalize_color("weiss") == "white"
    assert normalize_color("rot") == "red"


def test_normalize_color_passthrough():
    assert normalize_color("#1a1a2e") == "#1a1a2e"
    assert normalize_color("blue") == "blue"


def test_generate_image_returns_bytes():
    data = {"titel": "Test", "breite": 320}
    result = generate_image(data, output_path=None)
    assert isinstance(result, bytes)
    assert result[:4] == b"\x89PNG"


def test_generate_image_16_9_ratio():
    data = {"titel": "16:9", "breite": 320}
    png = generate_image(data, output_path=None)
    img = Image.open(io.BytesIO(png))
    w, h = img.size
    assert w == 320
    assert h == 180  # 320 * 9 / 16


def test_generate_image_saves_to_file(tmp_path):
    out = tmp_path / "out.png"
    result = generate_image({"titel": "File"}, output_path=str(out))
    assert result == str(out)
    assert out.exists()
    assert out.stat().st_size > 0


def test_generate_image_empty_titel():
    data = {"titel": "", "text": "", "breite": 160}
    result = generate_image(data, output_path=None)
    assert isinstance(result, bytes)


def test_generate_image_multiline_titel():
    data = {"titel": "Eins Zwei Drei Vier", "titelzeilen": 2, "breite": 320}
    result = generate_image(data, output_path=None)
    assert isinstance(result, bytes)


# ── Erweiterte Tests: normalize_color ────────────────────────────────────────

def test_normalize_color_strips_whitespace():
    assert normalize_color("  schwarz  ") == "black"
    assert normalize_color("  #ff0000  ") == "#ff0000"


def test_normalize_color_case_insensitive():
    assert normalize_color("SCHWARZ") == "black"
    assert normalize_color("Weiss") == "white"


@pytest.mark.parametrize("german,english", [
    ("weiß",    "white"),
    ("weiss",   "white"),
    ("schwarz", "black"),
    ("rot",     "red"),
    ("grün",    "green"),
    ("gruen",   "green"),
    ("blau",    "blue"),
    ("gelb",    "yellow"),
    ("orange",  "orange"),
    ("lila",    "purple"),
    ("violett", "violet"),
    ("pink",    "pink"),
    ("grau",    "gray"),
    ("braun",   "brown"),
    ("türkis",  "cyan"),
    ("tuerkis", "cyan"),
    ("silber",  "silver"),
    ("gold",    "gold"),
])
def test_normalize_color_full_german_map(german, english):
    assert normalize_color(german) == english


# ── Erweiterte Tests: generate_image ─────────────────────────────────────────

def test_generate_image_with_text():
    data = {"titel": "Haupttitel", "text": "Untertitel hier", "breite": 320}
    result = generate_image(data, output_path=None)
    assert isinstance(result, bytes)
    assert result[:4] == b"\x89PNG"


def test_generate_image_custom_colors():
    data = {
        "titel": "Test",
        "vordergrund": "yellow",
        "hintergrund": "#1a1a2e",
        "breite": 320,
    }
    result = generate_image(data, output_path=None)
    assert isinstance(result, bytes)
    assert result[:4] == b"\x89PNG"


def test_generate_image_german_colors():
    data = {
        "titel": "Farben",
        "vordergrund": "weiß",
        "hintergrund": "schwarz",
        "breite": 320,
    }
    result = generate_image(data, output_path=None)
    assert isinstance(result, bytes)


def test_generate_image_various_widths():
    for width in [160, 320, 640]:
        png = generate_image({"titel": "W", "breite": width}, output_path=None)
        img = Image.open(io.BytesIO(png))
        assert img.size == (width, width * 9 // 16)
