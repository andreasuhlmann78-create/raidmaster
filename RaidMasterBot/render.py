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
    """DKP-Stand wie die Seite DKP im Addon: Platz, Name und Klasse in Klassenfarbe, DKP, Verdient –
    dazu "Letzter Raid" (was nach dem letzten Raid dazugekommen ist) und die Zahl der Raids."""
    rows = [r for r in rows if r["dkp"] != 0 or r.get("earned")] or rows
    with_raids = any("raids" in r for r in rows)
    with_last = any("last" in r for r in rows)
    cols = [("#", "r", 24), ("Name", "l", 120), ("Klasse", "l", 90), ("DKP", "r", 50)]
    if with_last:
        cols.append(("Letzter Raid", "r", 80))
    cols.append(("Verdient", "r", 60))
    if with_raids:
        cols.append(("Raids", "r", 40))
    out = []
    for i, r in enumerate(rows, 1):
        cells = [i, r["name"], CLASS_NAMES.get(str(r.get("class") or "").upper(), ""), r["dkp"]]
        colors = {3: BAD} if r["dkp"] < 0 else {}
        if with_last:
            last = r.get("last")
            if last is None:
                cells.append("–")
                colors[len(cells) - 1] = MUTED
            else:
                cells.append(f"+{last}" if last > 0 else str(last))
                colors[len(cells) - 1] = GOOD if last > 0 else (BAD if last < 0 else MUTED)
        cells.append(int(r.get("earned") or 0))
        if with_raids:
            cells.append(int(r.get("raids") or 0))
        out.append({"cells": cells, "cls": r.get("class"), "colored": (1, 2), "colors": colors})
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


def render_roster(title: str, subtitle: str, members: dict[str, str]) -> bytes | None:
    """Teilnehmer nach Klasse gruppiert – Klasse und Namen in Klassenfarbe. members: {Name: Klasse}."""
    by_cls: dict[str, list[str]] = {}
    for name, cls in members.items():
        by_cls.setdefault(str(cls or "").upper(), []).append(name)
    order = [c for c in CLASS_COLORS if c in by_cls] + sorted(c for c in by_cls if c not in CLASS_COLORS)
    rows = []
    for c in order:
        names = sorted(by_cls[c], key=str.lower)
        for i in range(0, len(names), 6):        # höchstens 6 Namen je Zeile
            rows.append({"cells": [CLASS_NAMES.get(c, c.title() or "?") if i == 0 else "", len(names) if i == 0 else "",
                                   ", ".join(names[i:i + 6])], "cls": c, "colored": (0, 2)})
    cols = [("Klasse", "l", 100), ("Anzahl", "r", 50), ("Spieler", "l", 300)]
    return render_table(title, subtitle, cols, rows)


# Ersatz, wenn kein eigenes Emoji angelegt werden kann (ungefähre Farben)
CLASS_FALLBACK_EMOJI = {
    "WARRIOR": "🟤", "PALADIN": "🩷", "HUNTER": "🟢", "ROGUE": "🟡", "PRIEST": "⚪", "SHAMAN": "🔵",
    "MAGE": "🩵", "WARLOCK": "🟣", "DRUID": "🟠", "DEATHKNIGHT": "🔴", "MONK": "🟢", "DEMONHUNTER": "🟣", "EVOKER": "🟢",
}


def class_dot_png(cls: str, size: int = 64) -> bytes | None:
    """Runder Punkt in der genauen Klassenfarbe (für ein Discord-Emoji vor dem Namen)."""
    if not available() or str(cls).upper() not in CLASS_COLORS:
        return None
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    pad = size // 8
    d.ellipse([pad, pad, size - pad, size - pad], fill=CLASS_COLORS[str(cls).upper()] + (255,),
              outline=(20, 20, 24, 255), width=max(2, size // 20))
    buf = io.BytesIO()
    img.save(buf, "PNG")
    return buf.getvalue()


# ---------------------------------------------------------------------------
# DKP-Stände genau wie die Seite "DKP-Stände" im Addon
# ---------------------------------------------------------------------------
ADDON_BG = (11, 12, 15)          # COLORS.bg
ADDON_PANEL = (19, 20, 25)       # COLORS.panel
ADDON_BORDER = (41, 43, 54)
ADDON_ACCENT = (255, 143, 31)
ADDON_MUTED = (148, 153, 168)
ADDON_TEXT = (237, 237, 240)
ADDON_CLASS_TXT = (191, 191, 191)
ADDON_EARNED = (153, 217, 255)
ADDON_BENCH = (255, 204, 77)
ADDON_INRAID = (128, 255, 128)
ADDON_NEG = (255, 89, 89)


def render_addon_dkp(pool_name: str, rows: list[dict], total: int, count: int, footer: str = "",
                     per_panel: int = 25) -> bytes | None:
    """rows: {'name','class','dkp','earned','status'} – gleiche Spalten und Farben wie im Addon.
    Viele Spieler werden in mehrere Spalten nebeneinander verteilt (gut lesbar in Discord)."""
    if not available():
        return None
    f_title, f_head, f_cell, f_small = _font(20, True), _font(13), _font(15), _font(13)
    tmp = ImageDraw.Draw(Image.new("RGB", (10, 10)))
    cols = [("Name", "l"), ("Klasse", "l"), ("DKP", "r"), ("Verdient", "r"), ("Status", "l")]
    cells_of = lambda r: [r["name"], CLASS_NAMES.get(str(r.get("class") or "").upper(), ""), str(r["dkp"]),
                          str(int(r.get("earned") or 0)), r.get("status") or ""]
    widths = [max(_text_w(tmp, c[0], f_head), 30) for c in cols]
    for r in rows:
        for i, t in enumerate(cells_of(r)):
            widths[i] = max(widths[i], _text_w(tmp, t, f_cell))
    widths[4] = max(widths[4], _text_w(tmp, "Ersatzbank", f_cell))
    gap, pad, row_h, inner = 26, 16, 25, 10
    panel_w = inner * 2 + sum(widths) + gap * (len(cols) - 1)
    n_panels = max(1, min(4, -(-len(rows) // per_panel)))
    per = -(-len(rows) // n_panels) if rows else 1
    top = pad + 40
    head_h = 26
    height = top + head_h + per * row_h + inner + pad + (22 if footer else 0)
    width = pad * 2 + n_panels * panel_w + (n_panels - 1) * 14
    title_w = _text_w(tmp, f"DKP-Stände  {pool_name}", f_title) + _text_w(tmp, f"Gesamt {pool_name}: {total} DKP · {count} Spieler", f_cell) + 60
    width = max(width, title_w + pad * 2, 520)
    img = Image.new("RGB", (width, height), ADDON_BG)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, width - 1, height - 1], outline=ADDON_BORDER)
    # Kopf wie im Addon: "DKP-Stände" orange unterstrichen, Raid, Gesamt
    d.text((pad, pad), "DKP-Stände", font=f_title, fill=ADDON_ACCENT)
    tw = _text_w(d, "DKP-Stände", f_title)
    d.line([pad, pad + 28, pad + tw, pad + 28], fill=ADDON_ACCENT, width=1)
    d.text((pad + tw + 18, pad + 3), pool_name, font=f_cell, fill=ADDON_TEXT)
    gtxt_a = f"Gesamt {pool_name}: "
    gtxt_b = f"{total} DKP"
    gtxt_c = f" · {count} Spieler"
    gx = width - pad - _text_w(d, gtxt_a + gtxt_b + gtxt_c, f_cell)
    d.text((gx, pad + 3), gtxt_a, font=f_cell, fill=ADDON_TEXT)
    gx += _text_w(d, gtxt_a, f_cell)
    d.text((gx, pad + 3), gtxt_b, font=f_cell, fill=ADDON_ACCENT)
    gx += _text_w(d, gtxt_b, f_cell)
    d.text((gx, pad + 3), gtxt_c, font=f_cell, fill=ADDON_TEXT)
    for p in range(n_panels):
        part = rows[p * per:(p + 1) * per]
        x0 = pad + p * (panel_w + 14)
        y0 = top
        d.rectangle([x0, y0, x0 + panel_w, y0 + head_h + per * row_h + inner], fill=ADDON_PANEL, outline=ADDON_BORDER)
        # Kopfzeile
        d.rectangle([x0 + 1, y0 + 1, x0 + panel_w - 1, y0 + head_h - 1], fill=(26, 27, 33))
        x = x0 + inner
        for i, (name, align) in enumerate(cols):
            tx = x if align == "l" else x + widths[i] - _text_w(d, name, f_head)
            d.text((tx, y0 + 5), name, font=f_head, fill=ADDON_MUTED)
            x += widths[i] + gap
        d.line([x0 + 1, y0 + head_h, x0 + panel_w - 1, y0 + head_h], fill=(110, 70, 30), width=1)
        y = y0 + head_h + 2
        for n, r in enumerate(part):
            if n % 2 == 1:
                d.rectangle([x0 + 1, y, x0 + panel_w - 1, y + row_h - 1], fill=(23, 24, 30))
            cells = cells_of(r)
            status = cells[4]
            colors = [class_color(r.get("class")), ADDON_CLASS_TXT, ADDON_NEG if r["dkp"] < 0 else ADDON_TEXT, ADDON_EARNED,
                      ADDON_INRAID if status == "Im Raid" else ADDON_BENCH]
            x = x0 + inner
            for i, (_, align) in enumerate(cols):
                t = cells[i]
                tx = x if align == "l" else x + widths[i] - _text_w(d, t, f_cell)
                d.text((tx, y + 4), t, font=f_cell, fill=colors[i])
                x += widths[i] + gap
            y += row_h
    if footer:
        d.text((pad, height - pad - 16), footer, font=f_small, fill=ADDON_MUTED)
    buf = io.BytesIO()
    img.save(buf, "PNG", optimize=True)
    return buf.getvalue()
