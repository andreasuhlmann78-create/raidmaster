"""MN7 – Sammelstelle für Marktdaten (ab Bot 1.5.131, anweisung-marktdaten-netz.txt Teil 3; 1.5.132: D-MN7a–f).

Quelle: Zeilen "GSMARKT1|…" aus shared/GoldSentinelMarkt.lua (Export), die der Uploader (MN6) schickt – im Upload an
#bot-daten (SavedVariables .lua/.lua.gz) oder im Paket an #testberichte (paket-*.json.gz, {"items": [...],
"quelle": "<16 Hex>"}; "quelle" ab Uploader 2.3.7, fehlt bei älteren).

Format (Export-Format 1):
  GSMARKT1|<Format>|<Fraktion H/A/N>|<Scan-Zeit>|<Auktionen>|<Items>|<Vergleich in Sek., 0 = keiner>|<Einträge>
  Kopf dezimal; Einträge "id,preis,menge,auktionen,abgänge,abgängeVorsichtig" durch ";" getrennt, jedes Feld Base36.
  preis = tiefster Stückpreis in Kupfer; abgänge = Obergrenze (gekauft ODER abgebrochen); abgängeVorsichtig =
  Untergrenze (ohne Abbrechen/Neu-Einstellen). Für Entscheidungen gilt die UNTERGRENZE.
  <Items> zählt nur Items im Angebot; ganz ausverkaufte Items (GoldSentinelMarkt v2) kommen als zusätzliche
  Einträge "id,0,0,0,abgänge,abgängeVorsichtig" dazu. Also: Einträge >= <Items>, sonst ist die Zeile abgeschnitten.

Regeln:
- Keine Namen: die Zeilen enthalten keine. Als Quelle zählt ein kurzer Hash der Zufallskennung "quelle" aus dem Paket
  (D-MN7a), ohne sie ein Hash der Webhook-ID (ältere Uploader).
- Je Fraktion und Scan-Zeit nur EIN Scan (PC und Laptop schicken denselben Scan doppelt) – weitere Quellen erhöhen
  nur den Zähler.
- Grenzen (D-MN7c): höchstens MAX_NEW_PER_SOURCE_HOUR neue Scans je Quelle und Stunde, höchstens MAX_SCANS Scans und
  MAX_STORE_BYTES gepackt in der Ablage. Darüber: "begrenzt" (nicht abgelegt, im Protokoll gezählt).
- Je Item (je Fraktion, über ein Zeitfenster): Preise (letzter, min, max, Median), Angebot, Absatz je Tag als Spanne
  (Untergrenze/Obergrenze, hochgerechnet über die Summe der Vergleichsdauern), Umschlag (Untergrenze / Auktionen im
  Angebot), Abdeckung (Stunden der Woche, in denen ein Scan mit dem Item lag). Kein Verlauf je Scan im Speicher
  (D-MN7f): Zahlen in kompakten Arrays.
- Zeit: alles in der Zeitzone des Bots (TZ, vom Bot gesetzt; D-MN7d).
- Wochenbericht montags für die ABGESCHLOSSENE Kalenderwoche (Montag 00:00 bis Montag 00:00), Name nach dieser Woche
  (Montag 16.11.2026 -> GSMARKTW1-2026-W46.md). Zwischenbericht (/marktdaten bericht:True): letzte 7 Tage, eigener
  Name GSMARKTW1-<Woche>-zwischen-<MMTT-HHMM>.md, überschreibt den Wochenbericht nie.
Alles ohne Discord testbar (tests/test_market.py, T-MN7, T-D-MN7a/c/d/f).
"""
from __future__ import annotations

import gzip
import hashlib
import io
import json
import os
import re
import statistics
import time
from array import array
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

LINE_RE = re.compile(r"GSMARKT1\|[0-9A-Za-z.\-]{1,16}\|[HAN]\|\d{1,12}\|\d{1,9}\|\d{1,9}\|\d{1,9}\|[0-9a-zA-Z,;]*")
QUELLE_RE = re.compile(r'"quelle"\s*:\s*"([0-9a-f]{16})"')
FACTIONS = {"H": "Horde", "A": "Allianz", "N": "Neutral"}
MAX_LINE = 3 * 1024 * 1024          # D-MN7f: wie der Uploader (uploader.py, 3 MB)
MAX_ENTRIES = 50_000
MAX_INPUT = 64 * 1024 * 1024        # entpackt
KEEP_DAYS = 35
FUTURE_SLACK = 3600
WEEK = 7 * 86400
MAX_NEW_PER_SOURCE_HOUR = 30        # D-MN7c: ein Vollscan dauert Minuten – 30 je Stunde ist weit über dem Normalfall
MAX_SCANS = 20_000                  # D-MN7c: Ablage gesamt (35 Tage)
MAX_STORE_BYTES = 3 * 1024 ** 3     # D-MN7c: 3 GB gepackt
REPORT_PREFIX = "GSMARKTW1"         # Wochenbericht: GSMARKTW1-<JJJJ>-W<KW>.md

TZ = ZoneInfo("Europe/Zurich")      # der Bot setzt seine Zone mit set_tz()


def set_tz(name: str):
    global TZ
    TZ = ZoneInfo(name)


def _dt(ts: float) -> datetime:
    return datetime.fromtimestamp(ts, TZ)


# ---------------------------------------------------------------------------
# Lesen
# ---------------------------------------------------------------------------
def _b36(s: str) -> int:
    return int(s, 36)


def parse_line(line: str) -> dict | None:
    """Eine GSMARKT1-Zeile lesen. None = ungültig. Ergebnis: {ver, f, t, auk, items, cmp, e: {id: [p,m,a,ab,abv]}}."""
    if not isinstance(line, str) or len(line) > MAX_LINE:
        return None
    parts = line.split("|")
    if len(parts) != 8 or parts[0] != "GSMARKT1" or parts[2] not in FACTIONS:
        return None
    try:
        t, auk, items, cmp_ = (int(x) for x in parts[3:7])
    except ValueError:
        return None
    if t <= 0:
        return None
    entries = {}
    if parts[7]:
        raw = parts[7].split(";")
        if len(raw) > MAX_ENTRIES:
            return None
        for r in raw:
            if not r:
                continue
            f = r.split(",")
            if len(f) != 6:
                return None
            try:
                v = [_b36(x) for x in f]
            except ValueError:
                return None
            iid, rest = v[0], v[1:]
            if iid <= 0:
                return None
            rest[4] = min(rest[4], rest[3])          # Untergrenze nie über der Obergrenze
            entries[iid] = rest
    if len(entries) < items:                         # D-MN7c: Kopf zählt mehr Items als Einträge da sind
        return None
    return {"ver": parts[1], "f": parts[2], "t": t, "auk": auk, "items": items, "cmp": cmp_, "e": entries}


def find_lines(text: str) -> list[str]:
    """Alle GSMARKT1-Zeilen in einem Text (SavedVariables, JSON-Paket, Nachricht)."""
    return LINE_RE.findall(text or "")


def text_from_bytes(name: str, data: bytes) -> str:
    """Anhang lesen: .gz entpacken (begrenzt), sonst als Text."""
    if name.lower().endswith(".gz") or data[:2] == b"\x1f\x8b":
        try:
            with gzip.GzipFile(fileobj=io.BytesIO(data)) as g:
                data = g.read(MAX_INPUT + 1)
        except (OSError, EOFError):
            return ""
        if len(data) > MAX_INPUT:
            return ""
    return data.decode("utf-8", errors="replace")


def source_key(webhook_id) -> str:
    """Quelle ohne Namen (ältere Uploader): kurzer Hash der Webhook-ID."""
    return hashlib.sha256(f"gsmarkt:{webhook_id}".encode()).hexdigest()[:10]


def source_from_text(text: str) -> str | None:
    """D-MN7a: Zufallskennung "quelle" (16 Hex) aus dem Paket – gehasht, nie im Klartext abgelegt. None = kein Feld."""
    m = QUELLE_RE.search(text or "")
    return hashlib.sha256(f"gsmarkt-q:{m.group(1)}".encode()).hexdigest()[:10] if m else None


# ---------------------------------------------------------------------------
# Ablegen
# ---------------------------------------------------------------------------
class Store:
    """Ablage unter <dir>: index.json (je Scan Kopf + Quellen) und scans/<F>-<t>.json.gz (Einträge)."""

    def __init__(self, base: str):
        self.base = base
        self.scans = os.path.join(base, "scans")
        self.index_path = os.path.join(base, "index.json")
        self.index = self._load()

    def _load(self) -> dict:
        try:
            with open(self.index_path, encoding="utf-8") as f:
                d = json.load(f)
            return d if isinstance(d, dict) and isinstance(d.get("scans"), dict) else {"scans": {}, "dupes": 0}
        except (OSError, ValueError):
            return {"scans": {}, "dupes": 0}

    def save(self):
        os.makedirs(self.base, exist_ok=True)
        tmp = self.index_path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(self.index, f, separators=(",", ":"))
        os.replace(tmp, self.index_path)

    @staticmethod
    def key(scan: dict) -> str:
        return f"{scan['f']}-{scan['t']}"

    def bytes_total(self) -> int:
        return sum(int(h.get("b", 0)) for h in self.index["scans"].values())

    def new_by_source(self, source: str, now: float, window: int = 3600) -> int:
        return sum(1 for h in self.index["scans"].values()
                   if h["q"] and h["q"][0] == source and now - window <= h.get("an", 0) <= now)

    def add(self, scan: dict, source: str, now: float | None = None) -> str:
        """Einen Scan ablegen. Rückgabe: "neu", "doppelt", "abgelehnt" (zu alt / Zukunft) oder "begrenzt"."""
        now = time.time() if now is None else now
        if scan["t"] > now + FUTURE_SLACK or scan["t"] < now - KEEP_DAYS * 86400:
            return "abgelehnt"
        k = self.key(scan)
        head = self.index["scans"].get(k)
        if head is not None:
            if source not in head["q"]:
                head["q"].append(source)
            self.index["dupes"] = int(self.index.get("dupes", 0)) + 1
            return "doppelt"
        if (self.new_by_source(source, now) >= MAX_NEW_PER_SOURCE_HOUR or len(self.index["scans"]) >= MAX_SCANS
                or self.bytes_total() >= MAX_STORE_BYTES):
            self.index["begrenzt"] = int(self.index.get("begrenzt", 0)) + 1
            return "begrenzt"
        os.makedirs(self.scans, exist_ok=True)
        path = os.path.join(self.scans, k + ".json.gz")
        tmp = path + ".tmp"
        with gzip.open(tmp, "wt", encoding="utf-8") as f:
            json.dump({str(i): v for i, v in scan["e"].items()}, f, separators=(",", ":"))
        os.replace(tmp, path)
        self.index["scans"][k] = {"f": scan["f"], "t": scan["t"], "auk": scan["auk"], "items": scan["items"],
                                  "cmp": scan["cmp"], "ver": scan["ver"], "n": len(scan["e"]), "q": [source],
                                  "an": int(now), "b": os.path.getsize(path)}
        return "neu"

    def prune(self, now: float | None = None) -> int:
        now = time.time() if now is None else now
        old = [k for k, h in self.index["scans"].items() if h["t"] < now - KEEP_DAYS * 86400]
        for k in old:
            self.index["scans"].pop(k, None)
            try:
                os.remove(os.path.join(self.scans, k + ".json.gz"))
            except OSError:
                pass
        return len(old)

    def entries(self, k: str) -> dict:
        try:
            with gzip.open(os.path.join(self.scans, k + ".json.gz"), "rt", encoding="utf-8") as f:
                return {int(i): v for i, v in json.load(f).items()}
        except (OSError, ValueError, EOFError):
            return {}

    def heads(self, since: float, until: float, faction: str | None = None) -> list[tuple[str, dict]]:
        out = [(k, h) for k, h in self.index["scans"].items()
               if since <= h["t"] < until and (faction is None or h["f"] == faction)]
        return sorted(out, key=lambda kh: kh[1]["t"])


def ingest_text(store: Store, text: str, source: str, now: float | None = None) -> dict:
    """Alle Zeilen eines Textes ablegen. Zählt neu/doppelt/abgelehnt/begrenzt/ungültig."""
    res = {"neu": 0, "doppelt": 0, "abgelehnt": 0, "begrenzt": 0, "ungueltig": 0}
    for line in find_lines(text):
        scan = parse_line(line)
        if scan is None:
            res["ungueltig"] += 1
            continue
        res[store.add(scan, source, now)] += 1
    return res


# ---------------------------------------------------------------------------
# Zusammenführen
# ---------------------------------------------------------------------------
def hour_of_week(t: float) -> int:
    d = _dt(t)
    return d.weekday() * 24 + d.hour


class _Item:
    """Kompakt (D-MN7f): Arrays statt Listen von Tupeln, kein Verlauf je Scan."""
    __slots__ = ("preise", "menge", "auk", "letzt", "ab", "abv", "h")

    def __init__(self):
        self.preise, self.menge, self.auk = array("q"), array("q"), array("q")
        self.letzt, self.ab, self.abv, self.h = None, 0, 0, set()


def aggregate(store: Store, faction: str, since: float, until: float) -> dict:
    """Je Item über das Fenster [since, until): Preise, Angebot, Absatz-Spanne je Tag, Umschlag, Abdeckung."""
    heads = store.heads(since, until, faction)
    cmp_total = sum(h["cmp"] for _, h in heads if h["cmp"] > 0)
    hours = {hour_of_week(h["t"]) for _, h in heads}
    sources = {q for _, h in heads for q in h["q"]}
    items: dict[int, _Item] = {}
    hour_lo = [0] * 24          # Abgänge (Untergrenze) je Stunde des Tages
    hour_cmp = [0] * 24
    for k, h in heads:
        hw = hour_of_week(h["t"])
        if h["cmp"] > 0:
            hour_cmp[hw % 24] += h["cmp"]
        for iid, (p, m, a, ab, abv) in store.entries(k).items():
            it = items.get(iid)
            if it is None:
                it = items[iid] = _Item()
            if a > 0 or m > 0:                       # ausverkauft (0,0,0): zählt nur beim Absatz
                if p > 0:
                    it.preise.append(p)
                it.letzt = p
                it.menge.append(m)
                it.auk.append(a)
            it.h.add(hw)
            if h["cmp"] > 0:
                it.ab += ab
                it.abv += abv
                hour_lo[hw % 24] += abv
    days = cmp_total / 86400 if cmp_total else 0
    out = {}
    for iid, it in items.items():
        lo = it.abv / days if days else None
        hi = it.ab / days if days else None
        auk = statistics.median(it.auk) if it.auk else 0
        out[iid] = {
            "preis_letzt": it.letzt,
            "preis_min": min(it.preise) if it.preise else None,
            "preis_max": max(it.preise) if it.preise else None,
            "preis_median": statistics.median(it.preise) if it.preise else None,
            "menge": statistics.median(it.menge) if it.menge else 0,
            "auktionen": auk,
            "absatz_min": lo, "absatz_max": hi,
            "umschlag": (lo / auk) if (lo is not None and auk) else None,
            "abdeckung": len(it.h),
        }
    return {"items": out, "scans": len(heads), "quellen": len(sources), "abdeckung": len(hours),
            "vergleich_tage": days, "stunden": [(hour_lo[i] / (hour_cmp[i] / 86400)) if hour_cmp[i] else None
                                                for i in range(24)]}


# ---------------------------------------------------------------------------
# Bericht
# ---------------------------------------------------------------------------
def gold(c) -> str:
    if c is None:
        return "–"
    c = int(round(c))
    g, s, k = c // 10000, (c // 100) % 100, c % 100
    return (f"{g}g {s:02d}s" if g else f"{s}s {k:02d}c" if s else f"{k}c")


def _n(x, nd=1) -> str:
    if x is None:
        return "–"
    return f"{x:.{nd}f}".replace(".", ",") if nd else str(int(round(x)))


def week_key(now: datetime) -> str:
    y, w, _ = now.isocalendar()
    return f"{y}-W{w:02d}"


def last_week_window(now: datetime) -> tuple[float, float, str]:
    """D-MN7d: abgeschlossene Kalenderwoche vor now (Montag 00:00 bis Montag 00:00 in TZ) und ihr Name."""
    now = now.astimezone(TZ) if now.tzinfo else now.replace(tzinfo=TZ)
    start_this = (now - timedelta(days=now.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
    start_last = (start_this - timedelta(days=7))
    start_last = start_last.replace(tzinfo=None).replace(tzinfo=TZ)   # Zeitumstellung: wieder 00:00 Ortszeit
    return start_last.timestamp(), start_this.timestamp(), week_key(start_last)


def report_name(now: datetime, zwischen: bool = False) -> str:
    """Montagsbericht: nach der abgeschlossenen Woche (16.11.2026 -> 2026-W46). Zwischenbericht: eigener Name."""
    if zwischen:
        return f"{REPORT_PREFIX}-{week_key(now)}-zwischen-{now.strftime('%m%d-%H%M')}.md"
    return f"{REPORT_PREFIX}-{last_week_window(now)[2]}.md"


def report(store: Store, now_ts: float, top: int = 25, window: int = WEEK, since: float | None = None,
           title: str | None = None) -> str:
    """Bericht über [since, now_ts). Ohne since: die letzten window Sekunden."""
    since = now_ts - window if since is None else since
    d0 = _dt(since).strftime("%d.%m.%Y %H:%M")
    d1 = _dt(now_ts).strftime("%d.%m.%Y %H:%M")
    head = title or f"Woche {week_key(_dt(since))}"
    lines = [f"# Marktdaten WoW Forever – {head}", "",
             f"Zeitraum {d0} bis {d1} ({TZ.key}). Quelle: Vollscans der Spieler (GSMARKT1, MN7). "
             "Keine Namen. Absatz = verschwundene Auktionen je Tag, hochgerechnet über die Vergleichsdauer: "
             "**Untergrenze** (ohne Abbrechen/Neu-Einstellen, gilt für Entscheidungen) – Obergrenze (inkl. "
             "Abbrechen). Umschlag = Untergrenze / Auktionen im Angebot (Median). Abdeckung = Stunden der Woche "
             "(von 168) mit einem Scan.", "",
             f"Doppelte Scans (gleiche Fraktion und Scan-Zeit) seit Beginn verworfen: {int(store.index.get('dupes', 0))}"
             f" · wegen Grenzen nicht abgelegt: {int(store.index.get('begrenzt', 0))}.",
             ""]
    any_data = False
    for f, fname in FACTIONS.items():
        ag = aggregate(store, f, since, now_ts)
        if not ag["scans"]:
            continue
        any_data = True
        lines += [f"## {fname}", "",
                  f"- Scans: {ag['scans']} · Quellen: {ag['quellen']} · Abdeckung: {ag['abdeckung']}/168 Stunden · "
                  f"Vergleichsdauer gesamt: {_n(ag['vergleich_tage'] * 24)} Stunden · Items: {len(ag['items'])}"]
        prof = [f"{h:02d}h {_n(v, 0)}" for h, v in enumerate(ag["stunden"]) if v is not None]
        if prof:
            lines.append("- Absatz (Untergrenze, alle Items) je Tag, nach Stunde des Scans: " + " · ".join(prof))
        lines.append("")
        rows = [(iid, it) for iid, it in ag["items"].items() if it["absatz_min"] is not None]
        rows.sort(key=lambda r: (-(r[1]["absatz_min"] or 0), -(r[1]["absatz_max"] or 0), r[0]))
        if not rows:
            lines += ["_Noch keine Vergleichsscans – Absatz wird gemessen, sobald zwei Scans aufeinander folgen._", ""]
            continue
        lines += [f"### Top {min(top, len(rows))} nach Absatz-Untergrenze", "",
                  "| Item | Absatz/Tag (unten – oben) | Umschlag/Tag | Preis letzt | Preis min – max | Angebot (Menge / Auktionen) | Abdeckung h |",
                  "|---:|---|---:|---:|---|---|---:|"]
        for iid, it in rows[:top]:
            lines.append(f"| [{iid}](https://www.wowhead.com/classic/item={iid}) | {_n(it['absatz_min'])} – "
                         f"{_n(it['absatz_max'])} | {_n(it['umschlag'], 2)} | {gold(it['preis_letzt'])} | "
                         f"{gold(it['preis_min'])} – {gold(it['preis_max'])} | {_n(it['menge'], 0)} / "
                         f"{_n(it['auktionen'], 0)} | {it['abdeckung']} |")
        lines.append("")
    if not any_data:
        lines += ["_In diesem Zeitraum sind keine Marktdaten angekommen (Uploader MN6 schickt GSMARKT1-Zeilen)._", ""]
    return "\n".join(lines)


def weekly_report(store: Store, now: datetime, top: int = 25) -> tuple[str, str]:
    """Montagsbericht: (Dateiname, Text) für die abgeschlossene Kalenderwoche."""
    since, until, wk = last_week_window(now)
    return report_name(now), report(store, until, top=top, since=since, title=f"Woche {wk}")


def interim_report(store: Store, now: datetime, top: int = 25) -> tuple[str, str]:
    """Zwischenbericht (/marktdaten bericht:True): letzte 7 Tage, eigener Name."""
    return (report_name(now, zwischen=True),
            report(store, now.timestamp(), top=top, title=f"Zwischenbericht {now.strftime('%d.%m.%Y %H:%M')}"))


def weekly_due(now: datetime, last_week: str | None) -> bool:
    """Montag und in dieser Kalenderwoche noch nicht berichtet (Merker = Woche des Montags)."""
    return now.weekday() == 0 and last_week != week_key(now)


# ---------------------------------------------------------------------------
# Monatliche Blizzard-Prüfung (MN8 wiederholen, nur bei Änderung berichten)
# ---------------------------------------------------------------------------
def realm_fingerprint(list_output: str) -> str:
    """Nur die Namespace-Zeilen ("- …") und das FOREVER-Ergebnis zählen – nicht Antwortcodes des Tokens."""
    keep = [ln.strip() for ln in (list_output or "").splitlines()
            if ln.startswith("- ") or ln.startswith("FOREVER")]
    return hashlib.sha256("\n".join(keep).encode()).hexdigest()[:16] if keep else ""


def month_key(now: datetime) -> str:
    return f"{now.year}-{now.month:02d}"
