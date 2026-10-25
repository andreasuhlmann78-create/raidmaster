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
    "DEATHKNIGHT": "Todesritter",
    "MONK": "Mönch",
    "DEMONHUNTER": "Dämonenjäger",
    "EVOKER": "Rufer",
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
    "DEATHKNIGHT": [("Blut", "tank", ("tank", "melee")), ("Frost", "melee", ("melee", "tank")), ("Unheilig", "melee", ("melee", "tank"))],
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

# Alle Raids aller WoW-Versionen (wie im Addon, RaidData.lua): raids.json neben dieser Datei
RAID_ORDER: list[str] = []
try:
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "raids.json"), encoding="utf-8") as _fh:
        for _r in json.load(_fh):
            RAID_ORDER.append(_r["key"])
            POOLS.setdefault(_r["key"], _r["name"])
except (OSError, ValueError, KeyError):
    pass
POOL_SLUGS = {"mc": "dkp-molten-core", "ony": "dkp-onyxia", "barrow": "dkp-barrow-deeps", "hyjal": "dkp-hyjal"}

MODES = {"dkp": "DKP-Raid", "pug": "PUG-Raid (softres.it)"}

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
        if e.get("sid") and e.get("l") and e.get("r") in ROLES:
            # Spezialisierung (Mists of Pandaria / Retail): Name und Rolle kommen direkt aus dem Spiel
            spec = {"cls": e.get("c") or "", "tree": int(e["sid"]), "label": str(e["l"])[:40], "points": "",
                    "role": e["r"], "roles": [e["r"]], "at": int(e.get("t") or 0), "src": e.get("s") or ""}
        else:
            spec = make_spec(e.get("c") or "", lua_list(e.get("p")), e.get("t") or 0, e.get("s") or "")
        if spec:
            spec["name"] = name
            out[name.lower()] = spec
    return out


def spec_label(text: str) -> str:
    """'Wilder Kampf 0/31/20' -> 'Wilder Kampf'"""
    return re.sub(r"\s+\d+/\d+/\d+$", "", text or "")


def spec_short(spec: dict | None) -> str:
    """'Feuer 0/31/20'"""
    if not spec:
        return ""
    return f"{spec['label']} {spec['points']}".strip()


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
    def order(k: str):
        return (RAID_ORDER.index(k) if k in RAID_ORDER else len(RAID_ORDER), k)
    return keys + sorted(extra, key=order)


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
        earned = p.get("e") if isinstance(p.get("e"), dict) else {}
        rows.append({"name": str(name), "dkp": player_pool_value(p, pool), "class": p.get("c") or "",
                     "earned": int(earned.get(pool) or 0)})
    rows.sort(key=lambda r: (-r["dkp"], r["name"].lower()))
    return rows


def pool_total(rows: list[dict]) -> tuple[int, int]:
    """Gesamtpunkte eines Raid-Topfes: Summe aller DKP-Stände, Zahl der Spieler mit Stand."""
    vals = [int(r["dkp"]) for r in rows if r["dkp"] != 0]
    return sum(vals), len(vals)


def total_line(rows: list[dict]) -> str:
    total, count = pool_total(rows)
    return f"Gesamt: **{total} DKP** · {count} Spieler"


def pool_short(key: str) -> str:
    """Kurzname für Tabellenspalten (MC, ONY, BWL ...)."""
    return {"barrow": "BARROW", "hyjal": "HYJAL"}.get(key, key.upper())[:6]


def overall(data: dict) -> tuple[list[str], list[dict]]:
    """Gesamt-DKP je Raider über alle Raids: (Töpfe mit Daten, Zeilen absteigend nach Gesamt).
    Zeile: name, class, per{Topf: DKP}, total, earned (insgesamt verdient über alle Raids)."""
    players = (data or {}).get("players") or {}
    pools = [k for k in pool_list(data)
             if any(isinstance(p, dict) and (player_pool_value(p, k) or ((p.get("e") or {}).get(k) if isinstance(p.get("e"), dict) else 0))
                    for p in players.values())]
    rows = []
    for name, p in players.items():
        if not isinstance(p, dict):
            continue
        per = {k: player_pool_value(p, k) for k in pools}
        e = p.get("e") if isinstance(p.get("e"), dict) else {}
        earned = sum(int(e.get(k) or 0) for k in pools)
        total = sum(per.values())
        if total == 0 and earned == 0:
            continue
        rows.append({"name": str(name), "class": p.get("c") or "", "per": per, "total": total, "earned": earned})
    rows.sort(key=lambda r: (-r["total"], r["name"].lower()))
    return pools, rows


def format_overall(pools: list[str], rows: list[dict], limit_chars: int = 1900) -> list[str]:
    """Tabelle Gesamt-DKP je Raider als Codeblöcke."""
    if not rows:
        return ["```\nNoch keine DKP-Daten.\n```"]
    head = f"{'#':>3}  {'Name':<14} {'Klasse':<10}" + "".join(f" {pool_short(k):>6}" for k in pools) + f" {'Gesamt':>7} {'Verdient':>8}"
    header = head + "\n" + "-" * len(head)
    lines = []
    for i, r in enumerate(rows, 1):
        cls = CLASSES.get(r["class"], "")[:10]
        lines.append(f"{i:>3}. {r['name'][:14]:<14} {cls:<10}" + "".join(f" {r['per'][k]:>6}" for k in pools)
                     + f" {r['total']:>7} {r['earned']:>8}")
    chunks, cur, size = [], [header], len(header)
    for line in lines:
        if size + len(line) + 10 > limit_chars:
            chunks.append("```\n" + "\n".join(cur) + "\n```")
            cur, size = [], 0
        cur.append(line)
        size += len(line) + 1
    chunks.append("```\n" + "\n".join(cur) + "\n```")
    return chunks


def overall_line(rows: list[dict]) -> str:
    return (f"Alle Raids: **{sum(r['total'] for r in rows)} DKP** · {len(rows)} Raider · "
            f"insgesamt verdient {sum(r['earned'] for r in rows)} DKP")


EARN_KINDS = ("start", "end", "boss", "manual", "bench")


def raid_summaries(data: dict) -> list[dict]:
    """Abrechnung je beendetem Raidabend (Raidstart bis Raidende eines Topfes), älteste zuerst.
    Je Spieler: verdient (Start, Bosse, Ende, Gutschriften), für Items ausgegeben, Stand nach dem Raid."""
    log = [e for e in lua_list((data or {}).get("log")) if isinstance(e, dict)]
    log.sort(key=lambda e: (int(e.get("t") or 0), str(e.get("id"))))
    players = (data or {}).get("players") or {}
    out = []
    for i, end in enumerate(log):
        if end.get("k") != "end" or end.get("u"):
            continue
        pool = end.get("pool") or "mc"
        t_end = int(end.get("t") or 0)
        start = None
        for e in reversed(log[:i]):
            if (e.get("pool") or "mc") != pool:
                continue
            if e.get("k") == "end" and not e.get("u"):
                break
            if e.get("k") == "start" and not e.get("u"):
                start = e
                break
        t_start = int(start.get("t") or 0) if start else t_end - 6 * 3600
        rows: dict[str, dict] = {}
        bosses, items = [], []
        for e in log:
            t = int(e.get("t") or 0)
            if (e.get("pool") or "mc") != pool or e.get("u") or t < t_start or t > t_end:
                continue
            k = e.get("k")
            if k == "boss":
                bosses.append(str(e.get("bn") or e.get("x") or "Boss"))
            for name, d in (e.get("d") or {}).items():
                r = rows.setdefault(str(name), {"name": str(name), "earned": 0, "spent": 0, "items": [], "present": False})
                if k != "bench":
                    r["present"] = True
                d = int(d)
                if k in EARN_KINDS and d > 0:
                    r["earned"] += d
                elif k == "item":
                    r["spent"] += -d
                    r["items"].append(item_name(e.get("i")))
                    items.append((str(name), item_name(e.get("i")), -d))
        # Stand nach dem Raid = heutiger Stand minus alles, was danach im Topf gebucht wurde
        after: dict[str, int] = {}
        for e in log:
            if (e.get("pool") or "mc") == pool and not e.get("u") and int(e.get("t") or 0) > t_end:
                for name, d in (e.get("d") or {}).items():
                    after[str(name)] = after.get(str(name), 0) + int(d)
        for r in rows.values():
            p = players.get(r["name"])
            r["balance"] = (player_pool_value(p, pool) if isinstance(p, dict) else 0) - after.get(r["name"], 0)
            r["class"] = (p.get("c") if isinstance(p, dict) else "") or ""
        out.append({"id": str(end.get("id")), "t": t_end, "start": t_start, "pool": pool,
                    "pool_name": end.get("pn") or pool_name(pool, data), "bosses": bosses, "items": items,
                    "rows": sorted(rows.values(), key=lambda r: (-r["balance"], r["name"].lower()))})
    return out


def raid_counts(summaries: list[dict], pool: str) -> dict[str, int]:
    """Wie viele beendete Raidabende jeder Spieler in diesem Topf dabei war."""
    counts: dict[str, int] = {}
    for s in summaries:
        if s["pool"] == pool:
            for r in s["rows"]:
                if r.get("present", True):
                    counts[r["name"]] = counts.get(r["name"], 0) + 1
    return counts


def raid_summary_head(s: dict) -> str:
    """Kopf der Raid-Abrechnung (Datum, Zeit, Bosse, Teilnehmer, Ersatzbank)."""
    from datetime import datetime as _dt
    day = _dt.fromtimestamp(s["t"]).strftime("%d.%m.%Y")
    return (f"📜 **Raid-Abrechnung {s['pool_name']} – {day}** (<t:{s['start']}:t>–<t:{s['t']}:t>)\n"
            f"Bosse ({len(s['bosses'])}): {', '.join(s['bosses']) or '–'} · Teilnehmer: {sum(1 for r in s['rows'] if r.get('present', True))}"
            + (f" · Ersatzbank: {sum(1 for r in s['rows'] if not r.get('present', True))}" if any(not r.get('present', True) for r in s['rows']) else ""))


def raid_summary_items(s: dict) -> list[str]:
    """Items eines Raidabends als Textzeile(n)."""
    if not s["items"]:
        return []
    return split_discord("🎁 " + " · ".join(f"**{n}**: {it} ({a} DKP)" for n, it, a in s["items"]))


def format_raid_summary(s: dict, limit_chars: int = 1900) -> list[str]:
    """Raid-Abrechnung als Nachrichten: Kopf, Tabelle je Spieler, Items."""
    head = raid_summary_head(s)
    lines = [f"{'Name':<14} {'Klasse':<10} {'+DKP':>5} {'Items':>6} {'Stand':>6}", "-" * 45]
    for r in s["rows"]:
        cls = CLASSES.get(r["class"], "")[:10]
        lines.append(f"{r['name'][:14]:<14} {cls:<10} {r['earned']:>5} {(-r['spent'] if r['spent'] else 0):>6} {r['balance']:>6}")
    msgs, cur = [], head + "\n```\n"
    for line in lines:
        if len(cur) + len(line) + 10 > limit_chars:
            msgs.append(cur + "```")
            cur = "```\n"
        cur += line + "\n"
    msgs.append(cur + "```")
    if s["items"]:
        text = "🎁 " + " · ".join(f"**{n}**: {it} ({a} DKP)" for n, it, a in s["items"])
        while text:
            msgs.append(text[:1900])
            text = text[1900:]
    return msgs


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
                "amount": -int(d), "item": item_name(e.get("i")), "link": e.get("i") or "", "by": e.get("by", ""),
                "pool": pool, "pool_name": e.get("pn") or pool_name(pool, data),
            })
    out.sort(key=lambda x: (x["t"], str(x["id"])))
    return out


def format_standings(rows: list[dict], limit_chars: int = 1900) -> list[str]:
    """DKP-Tabelle als Codeblöcke (je Nachricht max. limit_chars)."""
    if not rows:
        return ["```\nNoch keine DKP-Daten.\n```"]
    lines = []
    rows = [r for r in rows if r["dkp"] != 0 or r.get("earned")] or rows
    with_raids = any("raids" in r for r in rows)
    with_last = any("last" in r for r in rows)

    def last_txt(r):
        v = r.get("last")
        return "–" if v is None else (f"+{v}" if v > 0 else str(v))
    for i, r in enumerate(rows, 1):
        cls = CLASSES.get(r["class"], "")
        lines.append(f"{i:>3}. {r['name']:<14} {cls:<13} {r['dkp']:>6}" + (f" {last_txt(r):>6}" if with_last else "")
                     + f" {int(r.get('earned') or 0):>8}" + (f" {int(r.get('raids') or 0):>5}" if with_raids else ""))
    header = (f"{'#':>3}  {'Name':<14} {'Klasse':<13} {'DKP':>6}" + (f" {'Raid':>6}" if with_last else "")
              + f" {'Verdient':>8}" + (f" {'Raids':>5}" if with_raids else "")
              + "\n" + "-" * (49 + (6 if with_raids else 0) + (7 if with_last else 0)))
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


GROUP_LABELS = {"tank": "Tanks", "melee": "Nahkampf", "lock": "Hexer", "caster": "Fernkampf", "hunter": "Jäger", "heal": "Heiler"}


def player_kind(s: dict) -> str:
    """Einordnung für die Gruppen: tank, melee, lock, caster, hunter, heal."""
    cls, role = s.get("cls"), s.get("role")
    if role == "tank":
        return "tank"
    if role == "heal":
        return "heal"
    if cls == "HUNTER":
        return "hunter"
    if cls == "WARLOCK" or (cls == "PRIEST" and role == "ranged"):
        return "lock"          # Schattenpriester gehört zu den Hexern (Vampirumarmung)
    if role == "ranged":
        return "caster"
    return "melee"


def arrange_groups(chosen: list[dict], order_key=None) -> dict:
    """Verteilt die Spieler auf Gruppen zu je 5. Liefert {"groups": [[Spieler]], "labels": ["Tanks", ...]}.
    Main- und Offtank (die ersten beiden Tanks nach order_key) sind immer in Gruppe 1.
    Unterstützer (Schamanen bei der Horde, Paladine bei der Allianz) kommen je einer in jede
    Kampfgruppe – ihre Totems bzw. Auren wirken nur in der eigenen Gruppe."""
    key = order_key or (lambda s: s["name"].lower())
    n = len(chosen)
    if n == 0:
        return {"groups": [], "labels": []}
    n_groups = (n + 4) // 5
    support_cls = "SHAMAN" if any(s["cls"] == "SHAMAN" for s in chosen) else "PALADIN"
    supports = sorted([s for s in chosen if s["cls"] == support_cls and s.get("role") != "tank"],
                      key=lambda s: (0 if s.get("role") != "heal" else 1, key(s)))
    rest = [s for s in chosen if s not in supports]
    by_kind: dict[str, list] = {}
    for s in sorted(rest, key=key):
        by_kind.setdefault(player_kind(s), []).append(s)
    # Feral-Druide (Rudelführer) und Krieger vorn in den Nahkampfgruppen verteilen
    by_kind.setdefault("melee", []).sort(key=lambda s: (0 if s["cls"] == "WARRIOR" else 1 if s["cls"] == "DRUID" else 2, key(s)))

    # Gruppentypen festlegen
    plan: list[str] = []
    if by_kind.get("tank"):
        plan += ["tank"] * ((len(by_kind["tank"]) + 3) // 4)
    plan += ["melee"] * ((len(by_kind.get("melee", [])) + 3) // 4)
    plan += ["lock"] * ((len(by_kind.get("lock", [])) + 3) // 4)
    plan += ["caster"] * ((len(by_kind.get("caster", [])) + 3) // 4)
    if len(by_kind.get("hunter", [])) >= 2:
        plan += ["hunter"] * ((len(by_kind["hunter"]) + 3) // 4)
    else:
        by_kind.setdefault("caster", []).extend(by_kind.pop("hunter", []))
    core_cap = 4
    if len(plan) > n_groups:
        core_cap = 5                       # zu wenig Gruppen: Kampfgruppen voll, Unterstützer zu den Heilern
        plan = [k for k in plan]
        while len(plan) > n_groups:
            # die kleinste Gruppenart zusammenlegen
            for k in ("caster", "hunter", "lock", "melee", "tank"):
                if plan.count(k) > 1 or (k in ("hunter", "lock") and k in plan):
                    plan.remove(k)
                    if k in ("hunter", "lock"):
                        by_kind.setdefault("caster", []).extend(by_kind.pop(k, []))
                        if "caster" not in plan:
                            plan.append("caster")
                    break
            else:
                break
        plan = plan[:n_groups]             # kleine Raids: übrige Spieler füllen freie Plätze
    plan += ["heal"] * (n_groups - len(plan))
    groups: list[list] = [[] for _ in plan]

    def place(s, idxs, cap):
        for i in idxs:
            if len(groups[i]) < cap:
                groups[i].append(s)
                return True
        return False

    leftovers = []
    for kind in ("tank", "melee", "lock", "caster", "hunter"):
        idxs = [i for i, k in enumerate(plan) if k == kind]
        members = by_kind.get(kind, [])
        if kind == "tank":
            # Main- und Offtank (die ersten beiden Tanks) immer zusammen in Gruppe 1, weitere Tanks danach
            for s in members:
                if not place(s, idxs, core_cap):
                    leftovers.append(s)
            continue
        # gleichmäßig verteilen (z. B. 11 Nahkämpfer -> 4/4/3)
        for j, s in enumerate(members):
            if not idxs:
                leftovers.append(s)
                continue
            target = [idxs[j % len(idxs)]] + idxs
            if not place(s, target, core_cap):
                leftovers.append(s)
    # je Kampfgruppe ein Unterstützer (Reihenfolge: Tanks, Nahkampf, Hexer, Fernkampf, Jäger)
    fight = [i for i, k in enumerate(plan) if k != "heal"]
    sup = list(supports)
    for i in fight:
        if not sup:
            break
        if len(groups[i]) < 5:
            groups[i].append(sup.pop(0))
    # Heiler: zuerst Heilergruppen, dann freie Plätze (Gruppen ohne Heiler zuerst)
    healers = by_kind.get("heal", []) + sup + leftovers
    heal_idx = [i for i, k in enumerate(plan) if k == "heal"]
    for s in healers:
        if place(s, heal_idx, 5):
            continue
        free = sorted(range(len(groups)), key=lambda i: (any(player_kind(x) == "heal" or x["cls"] == support_cls for x in groups[i]), len(groups[i])))
        place(s, free, 5)
    labels = [GROUP_LABELS.get(k, "") for k in plan]
    # leere Gruppen am Ende entfernen
    while groups and not groups[-1]:
        groups.pop()
        labels.pop()
    return {"groups": groups, "labels": labels}


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

    # Gruppen wie im Classic-Raid üblich (Gruppen-Buffs wirken nur in der eigenen Gruppe):
    #   Gruppe 1 = Tanks · Nahkampfgruppen (Kampfschrei, Windzorn/Paladin-Aura, Rudelführer) ·
    #   Hexer-Gruppe mit Schattenpriester (Vampirumarmung) · Magier-Gruppen · Jäger-Gruppe (Aura des Volltreffers) ·
    #   je Gruppe ein Unterstützer (Schamane bzw. Paladin) · übrige Heiler auf Heilergruppen und freie Plätze.
    def stable(s):
        return (0, s["name"].lower()) if is_stamm(s) else (1, -ratio(s), s["name"].lower())

    layout = arrange_groups(chosen, stable)
    groups = {}
    ordered = []
    for g, members in enumerate(layout["groups"], 1):
        for s in members:
            groups[s["name"]] = g
            ordered.append(s)
    bench = [s["name"] for s in sorted(signed + backup, key=prio) if s not in chosen]
    return {
        "groups": groups, "bench": bench, "players": ordered, "size": size,
        "stamm": {s["name"] for s in ordered if is_stamm(s)}, "template": tpl,
        "labels": layout["labels"],
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
                cls_text = f"{cls_text} {spec_label(s['spec'])}"
            parts.append(f"{star}{s['name']} ({cls_text}, {ROLES.get(s['role'], s['role'])})")
        kinds = lineup.get("labels") or []
        label = f"Gruppe {g}" + (f" ({kinds[g - 1]})" if g - 1 < len(kinds) and kinds[g - 1] else "")
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
                         + (f" {spec_label(s['spec'])}" if s.get("spec") else "") for s in members) or "–"
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


def export_text(raid: dict, tz: str, lineup: dict | None = None, link: str = "", softres: str = "") -> str:
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
    if raid.get("test"):
        lines.append("Test: 1")           # Testraid mit erfundenen Namen: RaidMaster lädt nie echt ein
    if raid.get("mode") == "pug":
        lines.append("Modus: pug")
    if raid.get("max"):
        lines.append(f"Max: {int(raid['max'])}")
    if link:
        lines.append(f"Link: {link}")
    if softres:
        lines.append(f"SoftRes: {softres}")
    order = {"an": 0, "ersatz": 1, "vielleicht": 2, "ab": 3}
    for s in sorted(raid["signups"].values(), key=lambda s: (order.get(s["status"], 9), s["t"])):
        lines.append(f"{s['name']};{s['cls']};{s['role']};{s['status']}")
    if lineup:
        for name, g in lineup["groups"].items():
            lines.append(f"GRP;{name};{g}")
        for name in lineup["bench"]:
            lines.append(f"BANK;{name}")
    return "\n".join(lines)


DISCORD_LIMIT = 1990


def split_discord(text: str, limit: int = DISCORD_LIMIT) -> list[str]:
    """Text in Discord-taugliche Stücke (max. limit Zeichen) teilen – an Zeilengrenzen,
    offene Codeblöcke (```) werden am Ende eines Stücks geschlossen und im nächsten wieder geöffnet."""
    text = text or ""
    if len(text) <= limit:
        return [text]
    out, cur, in_code = [], "", False
    for line in text.split("\n"):
        # sehr lange Einzelzeilen hart teilen
        pieces = [line[i:i + limit - 10] for i in range(0, len(line), limit - 10)] or [""]
        for piece in pieces:
            extra = len(piece) + 1 + (4 if in_code else 0)
            if cur and len(cur) + extra > limit:
                out.append(cur + ("\n```" if in_code else ""))
                cur = "```" if in_code else ""
            cur = (cur + "\n" + piece) if cur else piece
            if piece.count("```") % 2 == 1:
                in_code = not in_code
    if cur:
        out.append(cur)
    return [c for c in out if c.strip()]


def with_head(head: str, chunks: list[str], limit: int = DISCORD_LIMIT) -> list[str]:
    """Überschrift vor das erste Stück setzen, ohne das Discord-Limit zu sprengen."""
    out = []
    for i, c in enumerate(chunks):
        out.extend(split_discord((head + "\n" + c) if i == 0 and head else c, limit))
    return out


def loot_by_raid(data: dict, pool: str, since: int = 0) -> list[dict]:
    """Loot eines Topfes chronologisch, gruppiert nach Raidabend (Raidstart bis Raidende).
    Items außerhalb eines beendeten Raids landen in einer Gruppe ohne Raid (start=None)."""
    items = [e for e in loot_entries(data) if e["pool"] == pool and e["t"] >= since]
    raids = [s for s in raid_summaries(data) if s["pool"] == pool and s["t"] >= since]
    raids.sort(key=lambda s: s["start"])
    groups = [{"start": s["start"], "end": s["t"], "pool_name": s["pool_name"], "items": []} for s in raids]
    rest = {"start": None, "end": None, "pool_name": pool_name(pool, data), "items": []}
    for e in items:
        for g in groups:
            if g["start"] <= e["t"] <= g["end"]:
                g["items"].append(e)
                break
        else:
            rest["items"].append(e)
    out = [g for g in groups if g["items"]]
    if rest["items"]:
        out.append(rest)
    return out


def format_loot_group(g: dict, prefix: str = "") -> list[str]:
    """Loot eines Raidabends als Nachrichten (chronologisch, mit Uhrzeit)."""
    from datetime import datetime as _dt
    if g["start"]:
        day = _dt.fromtimestamp(g["end"]).strftime("%d.%m.%Y")
        head = f"{prefix}🎁 **Loot {g['pool_name']} – Raid vom {day}** ({len(g['items'])} Items)"
    else:
        head = f"{prefix}🎁 **Loot {g['pool_name']} – außerhalb eines Raids** ({len(g['items'])} Items)"
    lines = [head]
    for e in g["items"]:
        lines.append(f"<t:{int(e['t'])}:t> **{e['name']}** erhält **{e['item']}** für {e['amount']} DKP")
    return split_discord("\n".join(lines))


# ---------------------------------------------------------------------------
# Items wie im Spiel-Tooltip (Daten aus RaidMasterDB.itemTips, gelesen vom Addon)
# ---------------------------------------------------------------------------
QUALITY_COLORS = {0: 0x9D9D9D, 1: 0xFFFFFF, 2: 0x1EFF00, 3: 0x0070DD, 4: 0xA335EE, 5: 0xFF8000, 6: 0xE6CC80}


def item_id(link: str | None) -> int | None:
    m = re.search(r"item:(\d+)", link or "")
    return int(m.group(1)) if m else None


def item_tip(db: dict | None, link: str | None) -> dict | None:
    """Tooltip eines Items aus dem Upload: {'n','q','l':[(farbe, links, rechts)], 'ic'}."""
    iid = item_id(link)
    tips = (db or {}).get("itemTips") or {}
    if not iid or not isinstance(tips, dict):
        return None
    t = tips.get(iid) or tips.get(str(iid))
    if not isinstance(t, dict):
        return None
    lines = []
    for raw in lua_list(t.get("l")):
        parts = str(raw).split("|")
        color = parts[0] if parts else "w"
        lines.append((color, parts[1] if len(parts) > 1 else "", parts[2] if len(parts) > 2 else ""))
    return {"n": t.get("n"), "q": t.get("q"), "l": lines, "ic": t.get("ic")}


def item_color(link: str | None, tip: dict | None = None) -> int:
    """Farbe nach Item-Qualität (aus dem Tooltip oder der Farbe im Item-Link)."""
    if tip and isinstance(tip.get("q"), int) and tip["q"] in QUALITY_COLORS:
        return QUALITY_COLORS[tip["q"]]
    m = re.search(r"\|c[fF]{2}([0-9a-fA-F]{6})", link or "")
    return int(m.group(1), 16) if m else QUALITY_COLORS[4]


ANSI = {"g": "\u001b[0;32m", "r": "\u001b[0;31m", "y": "\u001b[0;33m", "d": "\u001b[0;30m", "w": "\u001b[0;37m"}


def tooltip_block(tip: dict | None, width: int = 34) -> str:
    """Tooltipzeilen als farbiger Codeblock (```ansi) – links/rechts wie im Spiel nebeneinander."""
    if not tip or not tip.get("l"):
        return ""
    out = []
    for color, left, right in tip["l"]:
        text = left
        if right:
            text = (left + " " * max(1, width - len(left) - len(right)) + right) if len(left) + len(right) < width else f"{left}  {right}"
        out.append(ANSI.get(color, ANSI["w"]) + text + "\u001b[0m")
    block = "\n".join(out)
    if len(block) > 3800:
        block = block[:3800]
    return "```ansi\n" + block + "\n```"


def icon_name_from_hint(ic) -> str | None:
    """Symbolname aus dem Addon, wenn es einen Pfad liefert ('Interface\\Icons\\INV_Boots_05')."""
    if isinstance(ic, str) and ic.strip():
        name = re.split(r"[\\/]", ic.strip())[-1]
        name = re.sub(r"\.(blp|tga|png|jpg)$", "", name, flags=re.I)
        return name.lower() or None
    return None


def icon_url(name: str | None) -> str | None:
    return f"https://wow.zamimg.com/images/wow/icons/large/{name}.jpg" if name else None


def wowhead_url(link: str | None, flavor: str = "classic") -> str | None:
    iid = item_id(link)
    return f"https://www.wowhead.com/{flavor}/item={iid}" if iid else None


def last_raid_changes(summaries: list[dict], pool: str) -> tuple[dict | None, dict[str, int]]:
    """Letzter beendeter Raidabend eines Topfes und je Spieler die Änderung (+verdient - Items)."""
    raids = sorted((x for x in summaries if x["pool"] == pool), key=lambda x: x["t"])
    if not raids:
        return None, {}
    last = raids[-1]
    return last, {r["name"]: int(r["earned"]) - int(r["spent"]) for r in last["rows"]}


def add_raid_columns(rows: list[dict], summaries: list[dict], pool: str) -> dict | None:
    """Spalten "Raids" und "Letzter Raid" in die DKP-Tabelle eintragen. Liefert den letzten Raid."""
    counts = raid_counts(summaries, pool)
    last, delta = last_raid_changes(summaries, pool)
    for r in rows:
        r["raids"] = counts.get(r["name"], 0)
        if last is not None:
            r["last"] = delta.get(r["name"])
    return last


def session_active(db: dict | None) -> bool:
    s = (db or {}).get("session") or {}
    return bool(isinstance(s, dict) and s.get("active"))


def tip_from_wowhead_html(html: str, name: str | None = None, quality=None, icon: str | None = None) -> dict | None:
    """Tooltip-HTML von Wowhead in Zeilen wie beim Addon umwandeln: [(farbe, links, rechts)]."""
    import html as _html
    if not html:
        return None
    h = re.sub(r"<!--.*?-->", "", html, flags=re.S)
    # zweispaltige Zeilen (z. B. "Füße | Stoff", "Schaden | Tempo")
    h = re.sub(r"<td[^>]*>(.*?)</td>\s*<th[^>]*>(.*?)</th>", lambda m: m.group(1) + "\t" + m.group(2) + "<br>", h, flags=re.S)
    parts = re.split(r"<br\s*/?>|</tr>|</table>|</div>|<table[^>]*>|<div[^>]*>", h)
    lines = []
    for part in parts:
        cls = re.search(r'class="(q\d*|c\d+)"', part)
        color = "w"
        if cls:
            c = cls.group(1)
            color = {"q2": "g", "q0": "d", "q": "y", "q10": "r"}.get(c, "w")
            if c.startswith("c"):
                color = "w"
        if 'style="color: #ffd100' in part or "q1\"" in part and "Set" in part:
            color = "y"
        text = _html.unescape(re.sub(r"<[^>]+>", "", part)).strip()
        if not text:
            continue
        left, _, right = text.partition("\t")
        lines.append((color, left.strip(), right.strip()))
    if lines and name and lines[0][1] == name:
        lines = lines[1:]
    elif lines and not name:
        name = lines[0][1]
        lines = lines[1:]
    return {"n": name, "q": quality if isinstance(quality, int) else None, "l": lines[:30], "ic": icon}
