"""Raidfähigkeit im Offizierskanal (ab Bot 1.5.125, Auftrag RP-D, Entscheid des Nutzers 13.11.2026, GuildSentinel RP8).

Quelle: GuildSentinelDB.raidReady aus dem letzten Upload (der Uploader gibt nur dieses Feld weiter, RaidMaster RP-U):
    { raid, phase, aktiv, groesse, tanks, tanksSoll, heiler, heilerSoll, pct, wochen, t }   – OHNE Namen.
Optional (falls GuildSentinel es mitschickt): vorschlag = "Übergang" | "Raid" | "Aufbau" (Vorschlag zur Umstellung).

Regeln:
- einmal pro Woche, am Montag (Zeitzone des Bots), im Offizierskanal:
  "Raidfähig (Onyxia): 23/40 aktiv · Tanks 2/4 · Heiler 5/10 · Phase Aufbau · Schätzung ~3 Wochen"
- schlägt GuildSentinel eine Umstellung vor: sofort einmal "GuildSentinel schlägt Phase Übergang vor – im Spiel bestätigen"
- keine Namen (nur die bekannten Felder werden gelesen), nie doppelt (Merker in state), nur Offizierskanal.
Die Funktionen sind ohne Discord testbar (tests/test_raid_ready.py, T-RP-D).
"""
from __future__ import annotations

from datetime import datetime

FIELDS_INT = ("aktiv", "groesse", "tanks", "tanksSoll", "heiler", "heilerSoll", "pct", "wochen", "t")
FIELDS_TEXT = ("raid", "phase", "vorschlag")
# GuildSentinel schreibt die Schlüssel build / trans / raid (RaidReady.lua PHASE_NAME); deutsche Wörter bleiben gültig
PHASES = {"build": "Aufbau", "trans": "Übergang", "aufbau": "Aufbau", "uebergang": "Übergang", "übergang": "Übergang",
          "raid": "Raid"}
RAID_NAMES = {"mc": "Molten Core", "onyxia": "Onyxia", "ony": "Onyxia", "bwl": "Pechschwingenhort",
              "zg": "Zul'Gurub", "aq20": "Ruinen von Ahn'Qiraj", "aq40": "Tempel von Ahn'Qiraj", "naxx": "Naxxramas",
              "barrow": "Barrow Deeps", "hyjal": "Hyjalgipfel",
              "kara": "Karazhan", "gruul": "Gruuls Unterschlupf", "mag": "Magtheridons Kammer",
              "ssc": "Höhle des Schlangenschreins", "tk": "Festung der Stürme"}
STALE_NOTE_DAYS = 7      # älter: "(Stand <Datum>)" anhängen
STALE_SKIP_DAYS = 14     # älter: nicht posten (RP-D3)


def _int(v) -> int | None:
    try:
        if isinstance(v, bool):
            return None
        n = int(float(v))
        return n if n >= 0 else None
    except (TypeError, ValueError):
        return None


def _text(v) -> str | None:
    if not isinstance(v, str):
        return None
    v = v.strip()
    return v[:40] if v else None


def parse(db) -> dict | None:
    """raidReady aus GuildSentinelDB (dict) lesen. Nur bekannte Felder, Zahlen ≥ 0, Text gekürzt. None = nicht brauchbar."""
    rr = db.get("raidReady") if isinstance(db, dict) else None
    if not isinstance(rr, dict):
        return None
    out = {}
    for k in FIELDS_INT:
        n = _int(rr.get(k))
        if n is not None:
            out[k] = n
    for k in FIELDS_TEXT:
        s = _text(rr.get(k))
        if s is not None:
            out[k] = s
    if "aktiv" not in out or "groesse" not in out or out["groesse"] <= 0:
        return None
    return out


def phase_label(p: str | None) -> str:
    if not p:
        return "?"
    return PHASES.get(p.strip().casefold(), p.strip())


def raid_label(r: str | None) -> str:
    if not r:
        return "Raid"
    return RAID_NAMES.get(r.strip().casefold(), r.strip())


def age_days(rr: dict, now_ts: float) -> float | None:
    t = rr.get("t")
    return None if not t else max(0.0, (now_ts - t) / 86400)


def too_old(rr: dict, now_ts: float) -> bool:
    """RP-D3: Stand älter als 14 Tage -> nicht als aktuell posten."""
    a = age_days(rr, now_ts)
    return a is not None and a > STALE_SKIP_DAYS


def weekly_text(rr: dict, now_ts: float | None = None) -> str:
    parts = [f"📊 **Raidfähig ({raid_label(rr.get('raid'))}):** {rr['aktiv']}/{rr['groesse']} aktiv"]
    if "tanks" in rr and "tanksSoll" in rr:
        parts.append(f"Tanks {rr['tanks']}/{rr['tanksSoll']}")
    if "heiler" in rr and "heilerSoll" in rr:
        parts.append(f"Heiler {rr['heiler']}/{rr['heilerSoll']}")
    parts.append(f"Phase {phase_label(rr.get('phase'))}")
    w = rr.get("wochen")
    parts.append(f"Schätzung ~{w} Woche{'n' if w != 1 else ''}" if w else "Schätzung: messe noch")
    text = " · ".join(parts)
    a = age_days(rr, now_ts) if now_ts is not None else None
    if a is not None and a > STALE_NOTE_DAYS:
        text += f" (Stand {datetime.fromtimestamp(rr['t']).strftime('%d.%m.%Y')})"
    return text


def suggestion_text(rr: dict) -> str | None:
    """Hinweis, wenn GuildSentinel eine andere Phase vorschlägt als die aktuelle."""
    v = rr.get("vorschlag")
    if not v or phase_label(v) == phase_label(rr.get("phase")):
        return None
    return f"🔔 GuildSentinel schlägt **Phase {phase_label(v)}** vor – im Spiel bestätigen (Offizier, GuildSentinel → Rekrutierung)."


def week_key(now: datetime) -> str:
    y, w, _ = now.isocalendar()
    return f"{y}-W{w:02d}"


def weekly_due(now: datetime, last_week: str | None) -> bool:
    """Montag und in dieser Kalenderwoche noch nicht gepostet."""
    return now.weekday() == 0 and last_week != week_key(now)


def suggestion_key(rr: dict) -> str | None:
    """Merker gegen Doppelposts: derselbe Vorschlag zur selben Phase wird nur einmal gemeldet."""
    if not suggestion_text(rr):
        return None
    return f"{phase_label(rr.get('phase'))}->{phase_label(rr.get('vorschlag'))}"
