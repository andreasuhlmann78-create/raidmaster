"""Rekord-Tafeln der Ruhmeshalle (ab Bot 1.5.136, Entscheid des Nutzers 15.11.2026 15:00).

Je Raid und je Dungeon EINE Tafel in #ruhmeshalle (Dungeons oben, Raids immer unten, je mit Überschrift), die der Bot einmal postet und danach nur bearbeitet:
Bosse in der Reihenfolge des Raids mit Bestzeit und Datum, "–" für Bosse ohne Kill, 🆕 für Rekorde vom letzten
Raidabend, darunter die Bestzeit für den ganzen Raid (erster Pull bis letzter Boss an einem Abend).
Die bisherigen einzelnen Zeilen "⏱️ Neuer Rekord: …" entfallen (werden einmal aufgeräumt).

Dungeons (ab 1.5.137, Nutzer 15:15): je Dungeon eine Tafel, nach Level sortiert (bosses.json "dungeons", Quellen in
make_bosses.py). Eine Dungeon-Tafel zeigt nur gelegte Bosse (Name aus dem Spiel, deutsch) und "x von y Bossen".

Zuordnung eines Kills zu Raid/Dungeon (ohne Discord testbar, tests/test_rekord_tafel.py):
1. Encounter-ID steht in bosses.json (Raids aus den Raid-Daten des Addons, Dungeons aus Deadly Boss Mods) -> dieser
   Raid bzw. Dungeon.
2. sonst: Kill hat als Topf einen eigenen Raid von WoW Forever ohne Bossliste (Barrow Deeps, Hyjalgipfel) -> dieser Raid
   (die Bosse kennt das Addon erst ab dem ersten Kampf; Reihenfolge = Reihenfolge des ersten Kills).
3. sonst -> Tafel "Weitere Bosse (ohne Zuordnung)". Grund: Das Addon trägt auch Dungeon-Bosse mit dem Topf des
   laufenden Raidabends ein (RaidMaster/Records.lua PoolFor); der Topf allein sagt also nicht sicher, wo der Boss steht.
"""
from __future__ import annotations

import hashlib
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
OTHER = "_weitere"
OTHER_NAME = "Weitere Bosse (ohne Zuordnung)"
MIN_DURATION = 10           # wie rmd.best_times: kürzere Kämpfe sind Messfehler
EVENING_GAP = 6 * 3600      # mehr als 6 h zwischen zwei Kills = neuer Raidabend
TITLE_PREFIX = "⏱️ Rekorde · "
DUNGEON_PREFIX = "⏱️ Dungeonrekorde · "   # Entscheid des Nutzers 15.11. 16:17


def load_bosses(path: str | None = None, part: str = "raids") -> list[dict]:
    """part = "raids" oder "dungeons" (Dungeons schon nach Level sortiert)."""
    try:
        with open(path or os.path.join(HERE, "bosses.json"), encoding="utf-8") as f:
            return [r for r in json.load(f).get(part) or [] if isinstance(r, dict) and r.get("key")]
    except (OSError, ValueError):
        return []


def load_dungeons(path: str | None = None) -> list[dict]:
    return load_bosses(path, "dungeons")


def encounter_map(raids: list[dict]) -> dict[int, tuple[str, int]]:
    """Encounter-ID -> (Raid-Schlüssel, Position in der Bossliste)."""
    out = {}
    for r in raids:
        for i, b in enumerate(r.get("bosses") or []):
            for e in b.get("e") or []:
                out.setdefault(int(e), (r["key"], i))
    return out


def raid_of(kill: dict, emap: dict, raids: list[dict]) -> str:
    if kill.get("e") in emap:
        return emap[kill["e"]][0]
    p = kill.get("p")
    if p and any(r["key"] == p and not r.get("bosses") for r in raids):
        return p
    return OTHER


def area_of(kill: dict, raids: list[dict], dungeons: list[dict], names: dict[str, str]) -> dict:
    """Wo lag der Boss? {key, name, dungeon}. Für Erstkill-Beiträge (ab 1.5.138): Dungeon-Erstkills ohne Screenshot
    und mit dem Dungeon-Namen statt des Topfs (der Topf ist bei Dungeon-Bossen der des Raidabends)."""
    key = raid_of(kill, encounter_map(list(raids) + list(dungeons or [])), raids)
    dg = next((d for d in dungeons or [] if d["key"] == key), None)
    if dg:
        return {"key": key, "name": dg.get("name", key), "dungeon": True}
    if key == OTHER:
        return {"key": key, "name": "", "dungeon": False}
    return {"key": key, "name": names.get(key, key), "dungeon": False}


def fmt(sec: int | None) -> str:
    """m:ss, ab einer Stunde h:mm:ss."""
    if sec is None:
        return "–"
    sec = int(sec)
    h, m, s = sec // 3600, (sec // 60) % 60, sec % 60
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"


def evenings(kills: list[dict]) -> list[list[dict]]:
    """Kills (nach Zeit sortiert) in Raidabende teilen: Lücke > EVENING_GAP = neuer Abend."""
    out, cur, last = [], [], None
    for k in sorted(kills, key=lambda x: x["t"]):
        if last is not None and k["t"] - last > EVENING_GAP:
            out.append(cur)
            cur = []
        cur.append(k)
        last = k["t"]
    if cur:
        out.append(cur)
    return out


def full_clear(kills: list[dict], boss_ids: list[set]) -> dict | None:
    """Schnellster ganzer Raid: an einem Abend alle Bosse der Liste gelegt. Zeit = letzter Kill minus Beginn des
    ersten Kampfs (Kill-Zeit minus Kampfdauer). Ohne Dauer beim ersten Kill zählt der Abend nicht (Beginn unbekannt)."""
    if not boss_ids:
        return None
    best = None
    for ev in evenings(kills):
        got = {k["e"] for k in ev}
        if not all(ids & got for ids in boss_ids):
            continue
        first = ev[0]
        if not first.get("d"):
            continue
        dur = ev[-1]["t"] - (first["t"] - first["d"])
        if best is None or dur < best["d"]:
            best = {"d": dur, "t": ev[-1]["t"]}
    return best


def boards(kills: list[dict], raids: list[dict], names: dict[str, str],
           dungeons: list[dict] | None = None) -> list[dict]:
    """Alle Tafeln in fester Reihenfolge: Dungeons (nach Level), "Weitere", Raids (Reihenfolge von bosses.json)
    zuletzt. Nur Raids/Dungeons mit mind. einem Kill. Jede Tafel: {key, title, rows: [{n, d, t, new, killed}], full,
    dungeon, total}."""
    dungeons = dungeons or []
    areas = list(raids) + list(dungeons)
    emap = encounter_map(areas)
    by_raid: dict[str, list[dict]] = {}
    for k in kills or []:
        if not k.get("e") or not k.get("t"):
            continue
        by_raid.setdefault(raid_of(k, emap, raids), []).append(k)
    # Reihenfolge (Entscheid des Nutzers 15.11. 16:05): Dungeons (nach Level), ohne Zuordnung, Raids immer zuletzt
    order = [d["key"] for d in dungeons] + [OTHER] + [r["key"] for r in raids]
    out = []
    for key in order:
        ks = by_raid.get(key)
        if not ks:
            continue
        dg = next((d for d in dungeons if d["key"] == key), None)
        if dg:
            out.append(dungeon_board(dg, ks))
            continue
        raid = next((r for r in raids if r["key"] == key), None)
        evs = evenings(ks)
        last_evening = {id(k) for k in evs[-1]} if evs else set()
        best: dict[int, dict] = {}
        for k in ks:
            if k.get("d") and k["d"] >= MIN_DURATION and (k["e"] not in best or k["d"] < best[k["e"]]["d"]):
                best[k["e"]] = k
        rows = []
        if raid and raid.get("bosses"):
            for b in raid["bosses"]:
                ids = [int(e) for e in b.get("e") or []]
                cands = [best[e] for e in ids if e in best]
                k = min(cands, key=lambda x: x["d"]) if cands else None
                killed = any(x["e"] in ids for x in ks)
                rows.append({"n": b["n"], "d": k["d"] if k else None, "t": k["t"] if k else None,
                             "new": bool(k and id(k) in last_evening), "killed": killed})
            full = full_clear(ks, [set(int(e) for e in b.get("e") or []) for b in raid["bosses"]])
        else:
            seen = []
            for k in sorted(ks, key=lambda x: x["t"]):              # Reihenfolge des ersten Kills
                if k["e"] not in seen:
                    seen.append(k["e"])
            for e in seen:
                k = best.get(e)
                name = (k or next(x for x in ks if x["e"] == e)).get("n") or f"Boss {e}"
                rows.append({"n": name, "d": k["d"] if k else None, "t": k["t"] if k else None,
                             "new": bool(k and id(k) in last_evening), "killed": True})
            full = None
        title = TITLE_PREFIX + (OTHER_NAME if key == OTHER else names.get(key, key))
        out.append({"key": key, "title": title, "rows": rows, "full": full, "dungeon": False, "total": None})
    return out


def dungeon_board(dg: dict, ks: list[dict]) -> dict:
    """Dungeon-Tafel: nur gelegte Bosse in der Reihenfolge des Dungeons, Name aus dem Spiel (neuester Kill)."""
    evs = evenings(ks)
    last_evening = {id(k) for k in evs[-1]} if evs else set()
    rows = []
    for b in dg.get("bosses") or []:
        ids = set(int(e) for e in b.get("e") or [])
        mine = [k for k in ks if k["e"] in ids]
        if not mine:
            continue
        timed = [k for k in mine if k.get("d") and k["d"] >= MIN_DURATION]
        k = min(timed, key=lambda x: x["d"]) if timed else None
        newest = max(mine, key=lambda x: x["t"])
        name = newest.get("n") if newest.get("n") and not str(newest.get("n")).startswith("Boss ") else b["n"]
        rows.append({"n": name, "d": k["d"] if k else None, "t": k["t"] if k else None,
                     "new": bool(k and id(k) in last_evening), "killed": True})
    lo, hi = (dg.get("lvl") or [None, None])[:2]
    lvl = f" (Level {lo}–{hi})" if lo and hi else ""
    return {"key": dg["key"], "title": DUNGEON_PREFIX + dg.get("name", dg["key"]) + lvl, "rows": rows, "full": None,
            "dungeon": True, "total": len(dg.get("bosses") or [])}


def board_text(board: dict) -> str:
    """Beschreibung des Kärtchens (Discord-Zeitstempel <t:…:d> zeigen das Datum in der Zeitzone des Lesers)."""
    lines = []
    for r in board["rows"]:
        if r["d"] is not None:
            lines.append(f"**{r['n']}** – **{fmt(r['d'])}**{' 🆕' if r['new'] else ''} · <t:{r['t']}:d>")
        elif r["killed"]:
            lines.append(f"**{r['n']}** – gelegt, keine Kampfdauer gemessen")
        else:
            lines.append(f"{r['n']} – noch kein Kill")
    if board.get("dungeon"):
        lines.append("")
        lines.append(f"{len(board['rows'])} von {board['total']} Bossen gelegt")
    if board.get("full"):
        lines.append("")
        lines.append(f"🏁 Ganzer Raid (erster Pull bis letzter Boss): **{fmt(board['full']['d'])}** · "
                     f"<t:{board['full']['t']}:d>")
    lines.append("")
    lines.append("🆕 = Rekord vom letzten Besuch" if board.get("dungeon") else "🆕 = Rekord vom letzten Raidabend")
    text = "\n".join(lines)
    return text if len(text) <= 4000 else text[:3990] + "\n…"


HEADERS = {"raid": ("_kopf_raids", "## 🏰 Raids"), "dungeon": ("_kopf_dungeons", "## 🗝️ Dungeons"),
           "other": ("_kopf_weitere", "## ❔ Ohne Zuordnung")}


def with_headers(boards: list[dict]) -> list[dict]:
    """Raids und Dungeons getrennt (Entscheid des Nutzers 15.11. 16:05): vor jedem Abschnitt eine Überschrift, nur wenn
    der Abschnitt Tafeln hat. Reihenfolge wie boards(): Dungeons, ohne Zuordnung, Raids zuletzt."""
    out, last = [], None
    for b in boards:
        kind = "dungeon" if b.get("dungeon") else ("other" if b["key"] == OTHER else "raid")
        if kind != last:
            key, text = HEADERS[kind]
            out.append({"key": key, "header": text})
            last = kind
        out.append(b)
    return out


def board_hash(board: dict) -> str:
    """Gleicher Inhalt = gleicher Hash -> keine unnötige Bearbeitung."""
    if board.get("header"):
        return hashlib.sha256(board["header"].encode()).hexdigest()[:16]
    return hashlib.sha256((board["title"] + "\n" + board_text(board)).encode()).hexdigest()[:16]


def is_old_record_line(content: str | None) -> bool:
    """Alte Einzelzeilen bis Bot 1.5.135 ("⏱️ **Neuer Rekord: …"), die beim Umstellen einmal gelöscht werden."""
    return bool(content) and content.startswith("⏱️ **Neuer Rekord: ")


def cutoff_end_of_day(text: str, tz) -> float | None:
    """ "TT.MM.JJJJ" -> Zeitpunkt direkt nach dem Ende dieses Tages (00:00 des Folgetags) in der Zeitzone tz.
    "bis und mit dem 14.11." heisst: alles vor dem 15.11. 00:00. None = ungültiges Datum."""
    from datetime import datetime, timedelta
    try:
        d = datetime.strptime((text or "").strip(), "%d.%m.%Y")
    except ValueError:
        return None
    return (d + timedelta(days=1)).replace(tzinfo=tz).timestamp()


def cleanup_candidates(messages, cutoff: float, keep_ids: set) -> list:
    """Nachrichten zum Löschen: vor cutoff, nicht angeheftet, keine aktuelle Tafel/Überschrift (keep_ids)."""
    out = []
    for m in messages:
        if m.id in keep_ids or getattr(m, "pinned", False):
            continue
        if m.created_at.timestamp() < cutoff:
            out.append(m)
    return out

