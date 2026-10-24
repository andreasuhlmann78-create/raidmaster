"""
RaidMaster-Bot – Datenlogik ohne Discord-Abhängigkeit.

Enthält:
- Leser für die WoW-Datei SavedVariables/RaidMaster.lua
- DKP-Auswertung (Tabelle, Loot-Protokoll)
- Raid- und Anmeldungsverwaltung (JSON-Speicher)
- Datums-Auswertung und Export-Text für das Addon
"""

from __future__ import annotations

import json
import os
import re
import tempfile
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

# ---------------------------------------------------------------------------
# Klassen und Rollen
# ---------------------------------------------------------------------------

CLASSES = {
    "WARRIOR": "Krieger",
    "PALADIN": "Paladin",
    "HUNTER": "Jäger",
    "ROGUE": "Schurke",
    "PRIEST": "Priester",
    "SHAMAN": "Schamane",
    "MAGE": "Magier",
    "WARLOCK": "Hexenmeister",
    "DRUID": "Druide",
}

ROLES = {
    "tank": "Tank",
    "heal": "Heiler",
    "melee": "Nahkampf",
    "ranged": "Fernkampf",
}

ROLE_ICONS = {"tank": "🛡️", "heal": "💚", "melee": "⚔️", "ranged": "🏹"}

# Talentbäume (Reihenfolge wie im Spiel): Name, Hauptrolle, mögliche Rollen – gleich wie Spec.lua
SPEC_TREES = {
    "WARRIOR": [("Waffen", "melee", ("melee", "tank")), ("Furor", "melee", ("melee", "tank")), ("Schutz", "tank", ("tank",))],
    "PALADIN": [("Heilig", "heal", ("heal",)), ("Schutz", "tank", ("tank",)), ("Vergeltung", "melee", ("melee",))],
    "HUNTER": [("Tierherrschaft", "ranged", ("ranged",)), ("Treffsicherheit", "ranged", ("ranged",)), ("Überleben", "ranged", ("ranged",))],
    "ROGUE": [("Meucheln", "melee", ("melee",)), ("Kampf", "melee", ("melee",)), ("Täuschung", "melee", ("melee",))],
    "PRIEST": [("Disziplin", "heal", ("heal",)), ("Heilig", "heal", ("heal",)), ("Schatten", "ranged", ("ranged",))],
    "SHAMAN": [("Elementar", "ranged", ("ranged",)), ("Verstärkung", "melee", ("melee",)), ("Wiederherstellung", "heal", ("heal",))],
    "MAGE": [("Arkan", "ranged", ("ranged",)), ("Feuer", "ranged", ("ranged",)), ("Frost", "ranged", ("ranged",))],
    "WARLOCK": [("Gebrechen", "ranged", ("ranged",)), ("Dämonologie", "ranged", ("ranged",)), ("Zerstörung", "ranged", ("ranged",))],
    "DRUID": [("Gleichgewicht", "ranged", ("ranged",)), ("Wilder Kampf", "melee", ("melee", "tank")), ("Wiederherstellung", "heal", ("heal",))],
}
SPEC_SOURCES = {"self": "eigene Angabe im Addon", "addon": "Addon", "inspect": "betrachtet"}

# DKP-Töpfe (gleich wie im Addon)
POOLS = {
    "mc": "Molten Core",
    "ony": "Onyxias Hort",
    "barrow": "Barrow Deeps",
    "hyjal": "Hyjalgipfel",
}
POOL_ORDER = ["mc", "ony", "barrow", "hyjal"]
POOL_SLUGS = {"mc": "dkp-molten-core", "ony": "dkp-onyxia", "barrow": "dkp-barrow-deeps", "hyjal": "dkp-hyjal"}

MODES = {"dkp": "DKP-Raid", "pug": "PUG-Raid (Loot wird ausgewürfelt)"}

STATUS = {
    "an": "Angemeldet",
    "ersatz": "Ersatzbank",
    "vielleicht": "Vielleicht",
    "ab": "Abgemeldet",
}


# ---------------------------------------------------------------------------
# Lua-Leser (SavedVariables)
# ---------------------------------------------------------------------------

class LuaParseError(Exception):
    pass


class _LuaReader:
    def __init__(self, text: str):
        self.s = text
        self.i = 0
        self.n = len(text)

    def skip(self):
        s, n = self.s, self.n
        while self.i < n:
            c = s[self.i]
            if c in " \t\r\n,;":
                self.i += 1
            elif s.startswith("--", self.i):
                if s.startswith("--[[", self.i):
                    end = s.find("]]", self.i + 4)
                    self.i = n if end < 0 else end + 2
                else:
                    end = s.find("\n", self.i)
                    self.i = n if end < 0 else end + 1
            else:
                break

    def peek(self) -> str:
        self.skip()
        return self.s[self.i] if self.i < self.n else ""

    def expect(self, ch: str):
        self.skip()
        if self.i >= self.n or self.s[self.i] != ch:
            raise LuaParseError(f"'{ch}' erwartet an Position {self.i}")
        self.i += 1

    def string(self) -> str:
        quote = self.s[self.i]
        self.i += 1
        out = []
        s = self.s
        while self.i < self.n:
            c = s[self.i]
            if c == quote:
                self.i += 1
                return "".join(out)
            if c == "\\":
                self.i += 1
                e = s[self.i]
                if e == "n":
                    out.append("\n")
                elif e == "t":
                    out.append("\t")
                elif e == "r":
                    out.append("\r")
                elif e.isdigit():
                    m = re.match(r"\d{1,3}", s[self.i:])
                    out.append(chr(int(m.group(0))))
                    self.i += len(m.group(0)) - 1
                elif e == "\n":
                    out.append("\n")
                else:
                    out.append(e)
                self.i += 1
            else:
                out.append(c)
                self.i += 1
        raise LuaParseError("Unbeendeter Text")

    def long_string(self) -> str:
        m = re.match(r"\[(=*)\[", self.s[self.i:])
        if not m:
            raise LuaParseError("Ungültiger langer Text")
        close = "]" + m.group(1) + "]"
        start = self.i + len(m.group(0))
        end = self.s.find(close, start)
        if end < 0:
            raise LuaParseError("Unbeendeter langer Text")
        self.i = end + len(close)
        return self.s[start:end]

    def value(self):
        c = self.peek()
        if c == "{":
            return self.table()
        if c in "\"'":
            return self.string()
        if c == "[" and re.match(r"\[=*\[", self.s[self.i:]):
            return self.long_string()
        m = re.match(r"-?(0x[0-9a-fA-F]+|\d+\.?\d*(?:[eE][-+]?\d+)?|\.\d+)", self.s[self.i:])
        if m:
            self.i += len(m.group(0))
            txt = m.group(0)
            if "x" in txt.lower():
                return int(txt, 16)
            num = float(txt)
            return int(num) if num.is_integer() and "." not in txt and "e" not in txt.lower() else num
        m = re.match(r"[A-Za-z_][A-Za-z0-9_]*", self.s[self.i:])
        if m:
            word = m.group(0)
            self.i += len(word)
            if word == "true":
                return True
            if word == "false":
                return False
            if word == "nil":
                return None
            raise LuaParseError(f"Unerwartetes Wort '{word}'")
        raise LuaParseError(f"Unerwartetes Zeichen '{c}' an Position {self.i}")

    def table(self):
        self.expect("{")
        result: dict = {}
        auto = 1
        while True:
            c = self.peek()
            if c == "}":
                self.i += 1
                break
            if c == "":
                raise LuaParseError("Unbeendete Tabelle")
            if c == "[" and not re.match(r"\[=*\[", self.s[self.i:]):
                self.i += 1
                key = self.value()
                self.expect("]")
                self.expect("=")
                result[key] = self.value()
            else:
                m = re.match(r"([A-Za-z_][A-Za-z0-9_]*)\s*=(?!=)", self.s[self.i:])
                if m:
                    self.i += len(m.group(0))
                    result[m.group(1)] = self.value()
                else:
                    result[auto] = self.value()
                    auto += 1
        return result


def parse_saved_variables(text: str) -> dict:
    """Liest eine SavedVariables-Datei: NAME = { ... } (mehrere möglich)."""
    r = _LuaReader(text)
    out = {}
    while True:
        r.skip()
        if r.i >= r.n:
            break
        m = re.match(r"([A-Za-z_][A-Za-z0-9_]*)\s*=", r.s[r.i:])
        if not m:
            raise LuaParseError(f"Zuweisung erwartet an Position {r.i}")
        r.i += len(m.group(0))
        out[m.group(1)] = r.value()
    return out


def lua_list(t) -> list:
    """Lua-Array (dict mit 1..n) als Python-Liste."""
    if isinstance(t, list):
        return t
    if not isinstance(t, dict):
        return []
    keys = sorted(k for k in t if isinstance(k, int))
    return [t[k] for k in keys]


# ---------------------------------------------------------------------------
# Skillungen (aus RaidMasterDB.specs)
# ---------------------------------------------------------------------------

def make_spec(cls: str, points: list, at: int = 0, src: str = "") -> dict | None:
    """Skillung aus Klasse und Punkten {a,b,c}. None, wenn ungültig."""
    trees = SPEC_TREES.get(cls)
    if not trees:
        return None
    try:
        pts = [int(p or 0) for p in (list(points) + [0, 0, 0])[:3]]
    except (TypeError, ValueError):
        return None
    if sum(pts) <= 0 or sum(pts) > 100:
        return None
    tree = max(range(3), key=lambda i: (pts[i], -i))
    label, role, roles = trees[tree]
    return {"cls": cls, "tree": tree + 1, "label": label, "points": "/".join(str(p) for p in pts),
            "role": role, "roles": list(roles), "at": int(at or 0), "src": src}


def specs_from_db(db: dict | None) -> dict[str, dict]:
    """{name_klein: spec} aus der gelesenen RaidMaster-Datei."""
    out: dict[str, dict] = {}
    for name, e in ((db or {}).get("specs") or {}).items():
        if not isinstance(e, dict) or not isinstance(name, str):
            continue
        spec = make_spec(e.get("c") or "", lua_list(e.get("p")), e.get("t") or 0, e.get("s") or "")
        if spec:
            spec["name"] = name
            out[name.lower()] = spec
    return out


def spec_short(spec: dict | None) -> str:
    """'Feuer 0/31/20'"""
    if not spec:
        return ""
    return f"{spec['label']} {spec['points']}"


# ---------------------------------------------------------------------------
# DKP-Auswertung
# ---------------------------------------------------------------------------

def load_raidmaster_db(path: str) -> dict | None:
    """Liefert die komplette RaidMasterDB (data, assign, ...) oder None."""
    if not path or not os.path.isfile(path):
        return None
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        text = f.read()
    return parse_saved_variables(text).get("RaidMasterDB") or {}


def load_raidmaster_file(path: str) -> dict | None:
    """Liefert RaidMasterDB.data oder None."""
    db = load_raidmaster_db(path)
    return db.get("data") if db is not None else None


def assignment_from_db(db: dict) -> dict | None:
    """Einteilung aus dem Addon: {v, by, title, ctx: {key: {n, lines, p}}}."""
    a = (db or {}).get("assign")
    if not isinstance(a, dict) or not a.get("v"):
        return None
    return a


ASSIGN_ORDER = ["general", "lucifron", "magmadar", "gehennas", "garr", "shazzrah", "sulfuron", "golemagg", "majordomo", "ragnaros"]
ICON_EMOJI = {"1": "⭐", "2": "🟠", "3": "🟣", "4": "🟢", "5": "🌙", "6": "🟦", "7": "❌", "8": "💀"}


def discord_icons(text: str) -> str:
    """WoW-Symbole {rt8} in Emojis für Discord umwandeln."""
    return re.sub(r"\{rt(\d)\}", lambda m: ICON_EMOJI.get(m.group(1), ""), text or "")


def assignment_overview(a: dict) -> list[str]:
    """Übersicht aller Einteilungen als Discord-Nachrichten (je max. ~1900 Zeichen)."""
    blocks = []
    ctx = a.get("ctx") or {}
    for key in ASSIGN_ORDER + sorted(k for k in ctx if k not in ASSIGN_ORDER):
        c = ctx.get(key)
        if not isinstance(c, dict):
            continue
        lines = [discord_icons(l) for l in lua_list(c.get("lines"))]
        if lines:
            blocks.append(f"**{c.get('n') or key}**\n" + "\n".join(f"• {l}" for l in lines))
    head = f"📋 **Einteilung – {a.get('title') or 'Raid'}** (erstellt von {a.get('by') or '?'})"
    return chunk_blocks([head] + blocks)


def personal_assignment(a: dict, name: str) -> str | None:
    ctx = a.get("ctx") or {}
    parts = []
    for key in ASSIGN_ORDER + sorted(k for k in ctx if k not in ASSIGN_ORDER):
        c = ctx.get(key)
        if isinstance(c, dict):
            p = (c.get("p") or {}).get(name)
            if p:
                parts.append(f"**{c.get('n') or key}:** {discord_icons(p)}")
    if not parts:
        return None
    return f"📋 Deine Aufgaben für **{a.get('title') or 'den Raid'}**:\n" + "\n".join(parts)


def chunk_blocks(blocks: list[str], limit: int = 1900) -> list[str]:
    out, cur = [], ""
    for b in blocks:
        if cur and len(cur) + len(b) + 2 > limit:
            out.append(cur)
            cur = ""
        cur = (cur + "\n\n" + b) if cur else b
    if cur:
        out.append(cur[:2000])
    return out


def player_pool_value(p: dict, pool: str) -> int:
    d = p.get("d")
    if isinstance(d, dict) and pool in d:
        return int(round(d.get(pool) or 0))
    # ältere Daten ohne Töpfe gehören zu Molten Core
    if pool == "mc" and "dkp" in p:
        return int(round(p.get("dkp") or 0))
    return 0


def pool_list(data: dict) -> list[str]:
    """Alle DKP-Töpfe: feste Reihenfolge, danach automatisch angelegte Raids."""
    keys = list(POOL_ORDER)
    extra = set()
    for k in ((data or {}).get("pools") or {}):
        if k not in keys:
            extra.add(str(k))
    for p in ((data or {}).get("players") or {}).values():
        if isinstance(p, dict) and isinstance(p.get("d"), dict):
            for k in p["d"]:
                if k not in keys:
                    extra.add(str(k))
    return keys + sorted(extra)


def pool_name(key: str, data: dict | None = None) -> str:
    if key in POOLS:
        return POOLS[key]
    custom = ((data or {}).get("pools") or {}).get(key)
    if isinstance(custom, dict) and custom.get("n"):
        return str(custom["n"])
    return key


def standings(data: dict, pool: str = "mc") -> list[dict]:
    players = (data or {}).get("players") or {}
    rows = []
    for name, p in players.items():
        if not isinstance(p, dict):
            continue
        rows.append({"name": str(name), "dkp": player_pool_value(p, pool), "class": p.get("c") or ""})
    rows.sort(key=lambda r: (-r["dkp"], r["name"].lower()))
    return rows


def player_summary(data: dict, name: str) -> list[tuple[str, int, int, int]]:
    """Für /dkp: (Raidname, DKP, Platz, Spielerzahl) je Topf mit Stand ungleich 0."""
    out = []
    for key in pool_list(data):
        rows = [r for r in standings(data, key)]
        found = find_player(rows, name)
        if found and found[1]["dkp"] != 0:
            out.append((pool_name(key, data), found[1]["dkp"], found[0], len(rows)))
    return out


def item_name(link: str | None) -> str:
    if not link:
        return ""
    m = re.search(r"\|h\[(.*?)\]\|h", link)
    return m.group(1) if m else link


def loot_entries(data: dict) -> list[dict]:
    """Item-Buchungen (ohne rückgängig gemachte), älteste zuerst."""
    out = []
    for e in lua_list((data or {}).get("log")):
        if not isinstance(e, dict) or e.get("k") != "item" or e.get("u"):
            continue
        deltas = e.get("d") or {}
        pool = e.get("pool") or "mc"
        for name, d in deltas.items():
            out.append({
                "id": e.get("id"), "t": e.get("t", 0), "name": name,
                "amount": -int(d), "item": item_name(e.get("i")), "by": e.get("by", ""),
                "pool": pool, "pool_name": e.get("pn") or pool_name(pool, data),
            })
    out.sort(key=lambda x: (x["t"], str(x["id"])))
    return out


def format_standings(rows: list[dict], limit_chars: int = 1900) -> list[str]:
    """DKP-Tabelle als Codeblöcke (je Nachricht max. limit_chars)."""
    if not rows:
        return ["```\nNoch keine DKP-Daten.\n```"]
    lines = []
    for i, r in enumerate(rows, 1):
        cls = CLASSES.get(r["class"], "")
        lines.append(f"{i:>3}. {r['name']:<14} {cls:<13} {r['dkp']:>6}")
    header = f"{'#':>3}  {'Name':<14} {'Klasse':<13} {'DKP':>6}\n" + "-" * 40
    chunks, cur = [], [header]
    size = len(header)
    for line in lines:
        if size + len(line) + 10 > limit_chars:
            chunks.append("```\n" + "\n".join(cur) + "\n```")
            cur, size = [], 0
        cur.append(line)
        size += len(line) + 1
    chunks.append("```\n" + "\n".join(cur) + "\n```")
    return chunks


def find_player(rows: list[dict], name: str) -> tuple[int, dict] | None:
    name = (name or "").strip().lower()
    for i, r in enumerate(rows, 1):
        if r["name"].lower() == name:
            return i, r
    return None


# ---------------------------------------------------------------------------
# Teilnahme und Aufstellung
# ---------------------------------------------------------------------------

STAMM_THRESHOLD = 0.7
ATTENDANCE_WINDOW = 10

# Optimale Besetzung je Raidgröße (Rollen) und Mindestanzahl wichtiger Klassen
TEMPLATES = {
    10: {"tank": 2, "heal": 3, "melee": 2, "ranged": 3, "min": {"PRIEST": 1}},
    20: {"tank": 2, "heal": 5, "melee": 6, "ranged": 7, "min": {"PRIEST": 2, "MAGE": 2, "HUNTER": 1, "WARLOCK": 1}},
    40: {"tank": 4, "heal": 12, "melee": 12, "ranged": 12,
         "min": {"PRIEST": 4, "MAGE": 3, "HUNTER": 2, "WARLOCK": 3, "DRUID": 1}},
}
ROLE_ORDER = ["tank", "melee", "ranged", "heal"]


def template_for(size: int) -> dict:
    size = size or 40
    if size <= 10:
        base, key = TEMPLATES[10], 10
    elif size <= 20:
        base, key = TEMPLATES[20], 20
    else:
        base, key = TEMPLATES[40], 40
    if size == key:
        return base
    f = size / key
    t = {r: max(1, round(base[r] * f)) for r in ("tank", "heal", "melee", "ranged")}
    t["min"] = {c: max(1, round(n * f)) for c, n in base["min"].items()}
    return t


def attendance_from_addon(data: dict | None, window: int = ATTENDANCE_WINDOW) -> tuple[dict, int]:
    """Teilnahme aus den DKP-Buchungen (Raidstart/Bosskills) – je Raidtag gezählt."""
    days: dict[str, set] = {}
    for e in lua_list((data or {}).get("log")):
        if not isinstance(e, dict) or e.get("u") or e.get("k") not in ("start", "boss"):
            continue
        day = datetime.fromtimestamp(int(e.get("t") or 0)).strftime("%Y-%m-%d")
        days.setdefault(day, set()).update(str(n) for n in (e.get("d") or {}).keys())
    last = sorted(days)[-window:]
    counts: dict[str, int] = {}
    for d in last:
        for n in days[d]:
            counts[n.lower()] = counts.get(n.lower(), 0) + 1
    return ({n: c / len(last) for n, c in counts.items()} if last else {}), len(last)


def attendance_from_book(book: "RaidBook", window: int = ATTENDANCE_WINDOW, now: float | None = None) -> tuple[dict, int]:
    """Teilnahme aus vergangenen Discord-Anmeldungen (Status 'angemeldet')."""
    now = now or datetime.now().timestamp()
    past = [r for r in book.all() if r["start"] < now and not r.get("cancelled")]
    past.sort(key=lambda r: -r["start"])
    past = past[:window]
    counts: dict[str, int] = {}
    for r in past:
        for s in r["signups"].values():
            if s["status"] == "an":
                counts[s["name"].lower()] = counts.get(s["name"].lower(), 0) + 1
    return ({n: c / len(past) for n, c in counts.items()} if past else {}), len(past)


def attendance(data: dict | None, book: "RaidBook") -> tuple[dict, int, str]:
    att, n = attendance_from_addon(data)
    if n > 0:
        return att, n, "Addon"
    att, n = attendance_from_book(book)
    return att, n, "Discord"


def build_lineup(raid: dict, att: dict) -> dict:
    """Optimale Besetzung zuerst, innerhalb der Rollen Stammspieler vor anderen.
    Liefert {"groups": {name: nr}, "bench": [...], "players": [...], "stamm": set, "size": n}."""
    size = raid.get("max") or 40
    tpl = template_for(size)
    signed = [s for s in raid["signups"].values() if s["status"] == "an"]
    backup = [s for s in raid["signups"].values() if s["status"] == "ersatz"]

    def ratio(s):
        return att.get(s["name"].lower(), 0.0)

    def is_stamm(s):
        return ratio(s) >= STAMM_THRESHOLD

    def prio(s):
        return (0 if is_stamm(s) else 1, -ratio(s), s.get("t", 0))

    pool = sorted(signed, key=prio)
    chosen: list[dict] = []

    def take(pred, n):
        for s in pool:
            if n <= 0 or len(chosen) >= size:
                break
            if s not in chosen and pred(s):
                chosen.append(s)
                n -= 1

    def count(pred):
        return sum(1 for s in chosen if pred(s))

    take(lambda s: s["role"] == "tank", tpl["tank"])
    take(lambda s: s["role"] == "heal", tpl["heal"])
    for cls, n in tpl["min"].items():
        have = count(lambda s, c=cls: s["cls"] == c)
        take(lambda s, c=cls: s["cls"] == c and s["role"] != "tank", n - have)
    take(lambda s: s["role"] == "melee", tpl["melee"] - count(lambda s: s["role"] == "melee"))
    take(lambda s: s["role"] == "ranged", tpl["ranged"] - count(lambda s: s["role"] == "ranged"))
    # freie Plätze: zuerst weitere DPS, erst dann zusätzliche Heiler/Tanks
    take(lambda s: s["role"] in ("melee", "ranged"), size - len(chosen))
    take(lambda s: s["role"] == "heal", size - len(chosen))
    take(lambda s: True, size - len(chosen))
    # freie Plätze mit der Discord-Ersatzbank auffüllen
    for s in sorted(backup, key=prio):
        if len(chosen) >= size:
            break
        chosen.append(s)

    # Gruppen: Gruppe 1 mit MT und Tanks, dann Nahkampf, Fernkampf, Heiler.
    # Innerhalb der Rolle: Stammspieler alphabetisch (fester Platz), danach die anderen.
    def stable(s):
        return (0, s["name"].lower()) if is_stamm(s) else (1, -ratio(s), s["name"].lower())

    tanks = sorted([s for s in chosen if s["role"] == "tank"], key=lambda s: (-ratio(s), s["name"].lower()))
    ordered = list(tanks)
    for role in ("melee", "ranged", "heal"):
        ordered += sorted([s for s in chosen if s["role"] == role], key=stable)
    ordered += [s for s in chosen if s not in ordered]
    groups = {s["name"]: i // 5 + 1 for i, s in enumerate(ordered)}
    bench = [s["name"] for s in sorted(signed + backup, key=prio) if s not in chosen]
    return {
        "groups": groups, "bench": bench, "players": ordered, "size": size,
        "stamm": {s["name"] for s in ordered if is_stamm(s)}, "template": tpl,
    }


def lineup_text(raid: dict, lineup: dict, att_source: str, att_count: int) -> list[str]:
    players = lineup["players"]
    blocks = [f"🛡️ **Aufstellung – {raid['title']}** (<t:{raid['start']}:F>) · {len(players)}/{lineup['size']} Spieler"]
    n_groups = (len(players) + 4) // 5
    for g in range(1, n_groups + 1):
        members = [s for s in players if lineup["groups"][s["name"]] == g]
        parts = []
        for s in members:
            star = "⭐" if s["name"] in lineup["stamm"] else ""
            cls_text = CLASSES.get(s['cls'], s['cls'])
            if s.get("spec"):
                cls_text = f"{cls_text} {s['spec'].rsplit(' ', 1)[0]}"
            parts.append(f"{star}{s['name']} ({cls_text}, {ROLES.get(s['role'], s['role'])})")
        label = "Gruppe 1 (MT)" if g == 1 else f"Gruppe {g}"
        blocks.append(f"**{label}:** " + ", ".join(parts))
    counts = {r: sum(1 for s in players if s["role"] == r) for r in ("tank", "heal", "melee", "ranged")}
    blocks.append("Besetzung: " + " · ".join(f"{ROLES[r]} {counts[r]}" for r in ("tank", "heal", "melee", "ranged")))
    if lineup["bench"]:
        blocks.append("**Ersatzbank:** " + ", ".join(lineup["bench"]))
    blocks.append(f"⭐ = Stammspieler (mind. {int(STAMM_THRESHOLD * 100)} % der letzten {att_count} Raids, Quelle: {att_source})")
    return chunk_blocks(blocks)


# ---------------------------------------------------------------------------
# Datum
# ---------------------------------------------------------------------------

def parse_datetime(date_text: str, time_text: str, tz: str, now: datetime | None = None) -> datetime:
    """Akzeptiert z. B. '29.10.2026', '29.10.26', '29.10.' und '20:00', '20', '20.30'."""
    zone = ZoneInfo(tz)
    now = now or datetime.now(zone)
    d = date_text.strip().rstrip(".")
    parts = [p for p in re.split(r"[.\-/]", d) if p]
    if len(parts) < 2:
        raise ValueError("Datum bitte als TT.MM.JJJJ angeben, z. B. 29.10.2026")
    day, month = int(parts[0]), int(parts[1])
    if len(parts) >= 3:
        year = int(parts[2])
        if year < 100:
            year += 2000
    else:
        year = now.year
    t = time_text.strip().replace(".", ":").replace("h", "")
    if ":" in t:
        hh, mm = t.split(":", 1)
        hour, minute = int(hh), int(mm or 0)
    else:
        hour, minute = int(t), 0
    dt = datetime(year, month, day, hour, minute, tzinfo=zone)
    if len(parts) < 3 and dt < now - timedelta(hours=12):
        dt = dt.replace(year=year + 1)
    return dt


# ---------------------------------------------------------------------------
# Speicher (JSON)
# ---------------------------------------------------------------------------

class Store:
    """Einfache JSON-Datei mit atomarem Speichern."""

    def __init__(self, path: str, default):
        self.path = path
        self.data = default
        if os.path.isfile(path):
            with open(path, "r", encoding="utf-8") as f:
                self.data = json.load(f)

    def save(self):
        folder = os.path.dirname(self.path) or "."
        os.makedirs(folder, exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=folder, suffix=".tmp")
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)
        os.replace(tmp, self.path)


class RaidBook:
    """Raids und Anmeldungen."""

    def __init__(self, folder: str):
        self.raids = Store(os.path.join(folder, "raids.json"), {"next_id": 1, "raids": {}})
        self.profiles = Store(os.path.join(folder, "profiles.json"), {})

    # Profile -------------------------------------------------------------
    def profile(self, user_id: int) -> dict | None:
        return self.profiles.data.get(str(user_id))

    def set_profile(self, user_id: int, name: str, cls: str, role: str) -> dict:
        name = clean_name(name)
        p = {"name": name, "cls": cls, "role": role}
        old = self.profiles.data.get(str(user_id)) or {}
        # Skillung behalten, solange es derselbe Charakter ist
        if old.get("spec") and old.get("name") == name and old.get("cls") == cls:
            p["spec"] = old["spec"]
        self.profiles.data[str(user_id)] = p
        self.profiles.save()
        # offene Anmeldungen mitziehen
        for raid in self.raids.data["raids"].values():
            s = raid["signups"].get(str(user_id))
            if s and not raid.get("closed"):
                s.update(name=name, cls=cls, role=role, spec=spec_short(p.get("spec")))
        self.raids.save()
        return p

    def apply_specs(self, specs: dict[str, dict]) -> list[dict]:
        """Skillungen aus dem Spiel in die Profile übernehmen.

        Die Rolle wird nur angepasst, wenn sich die Skillung geändert hat und die bisherige Rolle
        zu ihr nicht passt (z. B. Schattenpriester als Heiler). Liefert die Änderungen."""
        changes = []
        for uid, p in self.profiles.data.items():
            spec = specs.get((p.get("name") or "").lower())
            if not spec:
                continue
            old = p.get("spec") or {}
            if old.get("points") == spec["points"] and old.get("tree") == spec["tree"] and p.get("cls") == spec["cls"]:
                if spec["at"] > old.get("at", 0):
                    old["at"] = spec["at"]
                    old["src"] = spec["src"]
                continue
            old_role = p.get("role")
            p["spec"] = {k: spec[k] for k in ("tree", "label", "points", "role", "roles", "at", "src")}
            p["cls"] = spec["cls"]
            if old_role not in spec["roles"]:
                p["role"] = spec["role"]
            changes.append({"user_id": int(uid), "name": p["name"], "old": old.get("label"), "spec": spec,
                            "old_role": old_role, "role": p["role"]})
            for raid in self.raids.data["raids"].values():
                s = raid["signups"].get(uid)
                if s and not raid.get("closed"):
                    s.update(cls=p["cls"], role=p["role"], spec=spec_short(p["spec"]))
        if changes:
            self.profiles.save()
            self.raids.save()
        return changes

    # Raids ---------------------------------------------------------------
    def create(self, title: str, start: datetime, description: str, max_players: int, creator: int, channel_id: int,
               mode: str = "dkp") -> dict:
        rid = str(self.raids.data["next_id"])
        self.raids.data["next_id"] += 1
        raid = {
            "id": rid, "title": title, "start": int(start.timestamp()), "description": description or "",
            "max": int(max_players or 0), "creator": creator, "channel_id": channel_id, "message_id": None,
            "signups": {}, "closed": False, "cancelled": False, "reminded": False,
            "mode": mode if mode in MODES else "dkp",
        }
        self.raids.data["raids"][rid] = raid
        self.raids.save()
        return raid

    def get(self, rid: str) -> dict | None:
        return self.raids.data["raids"].get(str(rid))

    def all(self) -> list[dict]:
        return list(self.raids.data["raids"].values())

    def open_raids(self) -> list[dict]:
        return sorted((r for r in self.all() if not r.get("closed")), key=lambda r: r["start"])

    def save(self):
        self.raids.save()

    def count_status(self, raid: dict, status: str) -> int:
        return sum(1 for s in raid["signups"].values() if s["status"] == status)

    def signup(self, raid: dict, user_id: int, status: str, profile: dict, now_ts: int) -> str:
        """Setzt den Status. Liefert den tatsächlich gesetzten Status (bei vollem Raid -> Ersatzbank)."""
        key = str(user_id)
        current = raid["signups"].get(key)
        if status == "an" and raid.get("max"):
            already = current and current["status"] == "an"
            if not already and self.count_status(raid, "an") >= raid["max"]:
                status = "ersatz"
        entry = current or {"t": now_ts}
        entry.update(name=profile["name"], cls=profile["cls"], role=profile["role"], status=status,
                     spec=spec_short(profile.get("spec")))
        if not current or current.get("status") != status:
            entry["t"] = now_ts
        raid["signups"][key] = entry
        self.save()
        return status


def clean_name(name: str) -> str:
    name = re.sub(r"\s+", "", name or "")
    if not name:
        return ""
    return name[:1].upper() + name[1:].lower()


# ---------------------------------------------------------------------------
# Darstellung
# ---------------------------------------------------------------------------

def raid_fields(raid: dict) -> list[tuple[str, str, bool]]:
    """Felder fürs Discord-Embed: (Titel, Inhalt, inline)."""
    fields = []
    signed = sorted((s for s in raid["signups"].values() if s["status"] == "an"), key=lambda s: s["t"])
    for role, label in ROLES.items():
        members = [s for s in signed if s["role"] == role]
        text = "\n".join(f"{s['name']} · {CLASSES.get(s['cls'], s['cls'])}"
                         + (f" {s['spec'].rsplit(' ', 1)[0]}" if s.get("spec") else "") for s in members) or "–"
        fields.append((f"{ROLE_ICONS[role]} {label} ({len(members)})", text[:1024], True))
    # 2 Spalten: Tank | Heiler / Nahkampf | Fernkampf (Platzhalter füllt die 3. Spalte)
    fields.insert(2, ("\u200b", "\u200b", True))
    fields.append(("\u200b", "\u200b", True))
    for status in ("ersatz", "vielleicht"):
        members = sorted((s for s in raid["signups"].values() if s["status"] == status), key=lambda s: s["t"])
        if members:
            text = ", ".join(f"{s['name']} ({CLASSES.get(s['cls'], s['cls'])})" for s in members)
            fields.append((f"{STATUS[status]} ({len(members)})", text[:1024], False))
    out = sum(1 for s in raid["signups"].values() if s["status"] == "ab")
    if out:
        names = ", ".join(sorted(s["name"] for s in raid["signups"].values() if s["status"] == "ab"))
        fields.append((f"Abgemeldet ({out})", names[:1024], False))
    return fields


def class_summary(raid: dict) -> str:
    counts: dict[str, int] = {}
    for s in raid["signups"].values():
        if s["status"] == "an":
            counts[s["cls"]] = counts.get(s["cls"], 0) + 1
    if not counts:
        return ""
    return " · ".join(f"{CLASSES.get(c, c)} {n}" for c, n in sorted(counts.items(), key=lambda x: -x[1]))


def export_text(raid: dict, tz: str, lineup: dict | None = None, link: str = "") -> str:
    """Text zum Einfügen in RaidMaster (Seite 'Anmeldungen')."""
    start = datetime.fromtimestamp(raid["start"], ZoneInfo(tz))
    lines = [
        "RAIDMASTER-ANMELDUNG v1",
        f"Raid: {raid['title']}",
        f"Datum: {start.strftime('%d.%m.%Y %H:%M')}",
    ]
    lines.append(f"Start: {raid['start']}")
    if raid.get("pool"):
        lines.append(f"Topf: {raid['pool']}")
    if raid.get("mode") == "pug":
        lines.append("Modus: pug")
    if raid.get("max"):
        lines.append(f"Max: {int(raid['max'])}")
    if link:
        lines.append(f"Link: {link}")
    order = {"an": 0, "ersatz": 1, "vielleicht": 2, "ab": 3}
    for s in sorted(raid["signups"].values(), key=lambda s: (order.get(s["status"], 9), s["t"])):
        lines.append(f"{s['name']};{s['cls']};{s['role']};{s['status']}")
    if lineup:
        for name, g in lineup["groups"].items():
            lines.append(f"GRP;{name};{g}")
        for name in lineup["bench"]:
            lines.append(f"BANK;{name}")
    return "\n".join(lines)

