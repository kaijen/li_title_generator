#!/usr/bin/env python3
"""Lädt Google Fonts in den Font-Cache herunter.

Wird beim Docker-Build ausgeführt. Kann auch lokal genutzt werden:
  FONT_CACHE_DIR=~/.cache/title-image-fonts python scripts/install_fonts.py
"""
import os
import re
import sys
import urllib.request
from pathlib import Path

CACHE = Path(os.getenv("FONT_CACHE_DIR", "/fonts-cache"))
CACHE.mkdir(parents=True, exist_ok=True)

UA = "Mozilla/5.0 (compatible; title-image-service/1.0)"

FONTS = {
    "rubik_glitch":    "Rubik+Glitch",
    "libertinus_mono": "Libertinus+Mono",
    "jetbrains_mono":  "JetBrains+Mono",
    "fira_code":       "Fira+Code",
}

for cache_name, gf_name in FONTS.items():
    url = f"https://fonts.googleapis.com/css2?family={gf_name}&display=swap"
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    css = urllib.request.urlopen(req, timeout=30).read().decode()
    urls = re.findall(r"url\((https://[^)]+\.(?:ttf|otf))\)", css)
    if not urls:
        print(f"WARN: Kein TTF/OTF für {gf_name} gefunden", file=sys.stderr)
        continue
    font_data = urllib.request.urlopen(urls[0], timeout=30).read()
    ext = ".otf" if urls[0].endswith(".otf") else ".ttf"
    out = CACHE / (cache_name + ext)
    out.write_bytes(font_data)
    print(f"OK  {out.name}  ({len(font_data):,} Bytes)")
