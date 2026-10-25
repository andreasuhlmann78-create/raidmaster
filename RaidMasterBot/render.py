"""Tabellen als Bild – Namen in den echten WoW-Klassenfarben (wie im Spiel).

Discord kann Text nicht frei einfärben, deshalb zeichnet der Bot DKP-Stand und Raid-Abrechnung als PNG.
Fehlt Pillow, liefern die Funktionen None und der Bot postet wie bisher als Text.
"""
from __future__ import annotations

import io
import os

try:
    from PIL import Image, ImageDraw, ImageFont
except Exception:  # noqa: BLE001 – Pillow fehlt: Textfallback
    Image = ImageDraw = ImageFont = None

# Klassenfarben wie im Spiel (RAID_CLASS_COLORS)
CLASS_COLORS = {
    "WARRIOR": (198, 155, 109),
    "PALADIN": (244, 140, 186),
    "HUNTER": (170, 211, 114),
    "ROGUE": (255, 244, 104),
    "PRIEST": (255, 255, 255),
    "SHAMAN": (0, 112, 221),
    "MAGE": (63, 199, 235),
    "WARLOCK": (135, 136, 238),
    "DRUID": (255, 124, 10),
    "DEATHKNIGHT": (196, 30, 58),
    "MONK": (0, 255, 152),
    "DEMONHUNTER": (163, 48, 201),
    "EVOKER": (51, 147, 127),
}
CLASS_NAMES = {
    "WARRIOR": "Krieger", "PALADIN": "Paladin", "HUNTER": "Jäger", "ROGUE": "Schurke", "PRIEST": "Priester",
    "SHAMAN": "Schamane", "MAGE": "Magier", "WARLOCK": "Hexenmeister", "DRUID": "Druide",
    "DEATHKNIGHT": "Todesritter", "MONK": "Mönch", "DEMONHUNTER": "Dämonenjäger", "EVOKER": "Rufer",
}
CLASS_ICON = "https://wow.zamimg.com/images/wow/icons/large/classicon_{}.jpg"

BG = (18, 19, 24)
BG_ALT = (26, 27, 34)
HEAD = (255, 140, 26)      # RaidMaster-Orange
MUTED = (150, 150, 160)
TEXT = (230, 230, 235)
GOOD = (64, 255, 64)
BAD = (255, 85, 68)
LINE = (60, 62, 72)

FONT_PATHS = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    "C:/Windows/Fonts/segoeui.ttf",
    "C:/Windows/Fonts/arial.ttf",
]
BOLD_PATHS = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    "C:/Windows/Fonts/segoeuib.ttf",
    "C:/Windows/Fonts/arialbd.ttf",
]


def available() -> bool:
    return Image is not None


def class_color(cls: str | None) -> tuple[int, int, int]:
    return CLASS_COLORS.get(str(cls or "").upper(), TEXT)


def class_icon_url(cls: str | None) -> str | None:
    c = str(cls or "").lower()
    return CLASS_ICON.format(c) if c and c.upper() in CLASS_COLORS else None


def _font(size: int, bold: bool = False):
    for path in (BOLD_PATHS if bold else FONT_PATHS):
        if os.path.isfile(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:  # noqa: BLE001
                pass
    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        return ImageFont.load_default()


def _text_w(draw, text: str, font) -> int:
    try:
        return int(draw.textlength(text, font=font))
    except Exception:  # noqa: BLE001
        return len(text) * 8


def render_table(title: str, subtitle: str, columns: list[tuple[str, str, int]], rows: list[dict]) -> bytes | None:
    """columns: (Überschrift, Ausrichtung 'l'/'r', Mindestbreite); rows: {'cells': [...], 'cls': Klasse,
    'colored': Spaltenindizes in Klassenfarbe, 'colors': {Spalte: (r,g,b)}}. Liefert PNG-Bytes."""
    if not available():
        return None
    f_title, f_sub, f_head, f_cell = _font(22, True), _font(14), _font(14, True), _font(15)
    tmp = ImageDraw.Draw(Image.new("RGB", (10, 10)))
    pad, row_h, gap = 18, 26, 22
    widths = []
    for i, (name, _, minw) in enumerate(columns):
        w = max(minw, _text_w(tmp, name, f_head))
        for r in rows:
            w = max(w, _text_w(tmp, str(r["cells"][i]), f_cell))
        widths.append(w)
    width = max(pad * 2 + sum(widths) + gap * (len(columns) - 1),
                _text_w(tmp, title, f_title) + pad * 2, _text_w(tmp, subtitle, f_sub) + pad * 2, 420)
    top = pad + 30 + (22 if subtitle else 0) + 10
    height = top + row_h + len(rows) * row_h + pad
    img = Image.new("RGB", (width, height), BG)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, width - 1, height - 1], outline=LINE)
    d.text((pad, pad), title, font=f_title, fill=HEAD)
    if subtitle:
        d.text((pad, pad + 32), subtitle, font=f_sub, fill=MUTED)
    # Kopfzeile
    x = pad
    for i, (name, align, _) in enumerate(columns):
        tx = x if align == "l" else x + widths[i] - _text_w(d, name, f_head)
        d.text((tx, top + 4), name, font=f_head, fill=MUTED)
        x += widths[i] + gap
    d.line([pad, top + row_h - 2, width - pad, top + row_h - 2], fill=HEAD, width=1)
    # Zeilen
    y = top + row_h
    for n, r in enumerate(rows):
        if n % 2 == 1:
            d.rectangle([pad - 6, y, width - pad + 6, y + row_h - 1], fill=BG_ALT)
        x = pad
        for i, (_, align, _) in enumerate(columns):
            text = str(r["cells"][i])
            color = (r.get("colors") or {}).get(i)
            if color is None:
                color = class_color(r.get("cls")) if i in (r.get("colored") or ()) else TEXT
            tx = x if align == "l" else x + widths[i] - _text_w(d, text, f_cell)
            d.text((tx, y + 4), text, font=f_cell, fill=color)
            x += widths[i] + gap
        y += row_h
    buf = io.BytesIO()
    img.save(buf, "PNG", optimize=True)
    return buf.getvalue()


def render_standings(title: str, subtitle: str, rows: list[dict]) -> bytes | None:
    """DKP-Stand: Platz, Name und Klasse in Klassenfarbe, DKP, Verdient (und Raids)."""
    rows = [r for r in rows if r["dkp"] != 0 or r.get("earned")] or rows
    with_raids = any("raids" in r for r in rows)
    cols = [("#", "r", 24), ("Name", "l", 120), ("Klasse", "l", 90), ("DKP", "r", 50), ("Verdient", "r", 60)]
    if with_raids:
        cols.append(("Raids", "r", 40))
    out = []
    for i, r in enumerate(rows, 1):
        cells = [i, r["name"], CLASS_NAMES.get(str(r.get("class") or "").upper(), ""), r["dkp"], int(r.get("earned") or 0)]
        if with_raids:
            cells.append(int(r.get("raids") or 0))
        out.append({"cells": cells, "cls": r.get("class"), "colored": (1, 2),
                    "colors": {3: BAD} if r["dkp"] < 0 else {}})
    return render_table(title, subtitle, cols, out)


def render_summary(title: str, subtitle: str, srows: list[dict]) -> bytes | None:
    """Raid-Abrechnung: Name/Klasse in Klassenfarbe, +DKP (grün), Items (rot), Stand."""
    cols = [("Name", "l", 120), ("Klasse", "l", 90), ("+DKP", "r", 50), ("Items", "r", 50), ("Stand", "r", 56)]
    out = []
    for r in srows:
        bench = not r.get("present", True)
        cells = [r["name"] + (" (Ersatzbank)" if bench else ""), CLASS_NAMES.get(str(r.get("class") or "").upper(), ""),
                 f"+{r['earned']}" if r["earned"] else "0", f"-{r['spent']}" if r["spent"] else "0", r["balance"]]
        out.append({"cells": cells, "cls": r.get("class"), "colored": (0, 1),
                    "colors": {2: GOOD if r["earned"] else MUTED, 3: BAD if r["spent"] else MUTED}})
    return render_table(title, subtitle, cols, out)
