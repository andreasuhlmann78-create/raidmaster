"""MN7 – Sammelstelle für Marktdaten (ab Bot 1.5.131, anweisung-marktdaten-netz.txt Teil 3).

Quelle: Zeilen "GSMARKT1|…" aus shared/GoldSentinelMarkt.lua (Export), die der Uploader (MN6) schickt – im Upload an
#bot-daten (SavedVariables .lua/.lua.gz) oder im Paket an #testberichte (paket-*.json.gz, {"items": [...]}).

Format (Version 1):
  GSMARKT1|<Version>|<Fraktion H/A/N>|<Scan-Zeit>|<Auktionen>|<Items>|<Vergleich in Sek., 0 = keiner>|<Einträge>
  Kopf dezimal; Einträge "id,preis,menge,auktionen,abgänge,abgängeVorsichtig" durch ";" getrennt, jedes Feld Base36.
  preis = tiefster Stückpreis in Kupfer; abgänge = Obergrenze (gekauft ODER abgebrochen); abgängeVorsichtig =
  Untergrenze (ohne Abbrechen/Neu-Einstellen). Für Entscheidungen gilt die UNTERGRENZE.

Regeln:
- Keine Namen: die Zeilen enthalten keine; als Quelle wird nur ein kurzer Hash der Webhook-ID gezählt.
- Je Fraktion und Scan-Zeit nur EIN Scan (PC und Laptop schicken denselben Scan doppelt) – weitere Quellen erhöhen
  nur den Zähler.
- Je Item (über ein Zeitfenster, Standard 7 Tage, je Fraktion): Preisverlauf, Angebot, Absatz je Tag als Spanne
  (Untergrenze/Obergrenze, hochgerechnet über die Summe der Vergleichsdauern), Umschlag (Absatz je Tag / Auktionen im
  Angebot), Abdeckung (Stunden der Woche, in denen ein Scan mit dem Item lag).
- Wöchentlicher Bericht (Markdown) – der Bot legt ihn als Anhang in #testberichte, der Workflow markt-bericht.yml
  speichert ihn unter testberichte/markt/.
Alles ohne Discord testbar (tests/test_market.py, T-MN7).
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
from datetime import datetime

LINE_RE = re.compile(r"GSMARKT1\|[0-9A-Za-z.\-]{1,16}\|[HAN]\|\d{1,12}\|\d{1,9}\|\d{1,9}\|\d{1,9}\|[0-9a-zA-Z,;]*")
FACTIONS = {"H": "Horde", "A": "Allianz", "N": "Neutral"}
MAX_LINE = 2 * 1024 * 1024
MAX_ENTRIES = 50_000
MAX_INPUT = 64 * 1024 * 1024        # entpackt
KEEP_DAYS = 35
FUTURE_SLACK = 3600
WEEK = 7 * 86400
REPORT_PREFIX = "GSMARKTW1"         # Dateiname des Wochenberichts: GSMARKTW1-<JJJJ>-W<KW>.md


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
    """Quelle ohne Namen: kurzer Hash der Webhook-ID."""
    return hashlib.sha256(f"gsmarkt:{webhook_id}".encode()).hexdigest()[:10]


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

    def add(self, scan: dict, source: str, now: float | None = None) -> str:
        """Einen Scan ablegen. Rückgabe: "neu", "doppelt" oder "abgelehnt" (zu alt / Zukunft)."""
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
        os.makedirs(self.scans, exist_ok=True)
        path = os.path.join(self.scans, k + ".json.gz")
        tmp = path + ".tmp"
        with gzip.open(tmp, "wt", encoding="utf-8") as f:
            json.dump({str(i): v for i, v in scan["e"].items()}, f, separators=(",", ":"))
        os.replace(tmp, path)
        self.index["scans"][k] = {"f": scan["f"], "t": scan["t"], "auk": scan["auk"], "items": scan["items"],
                                  "cmp": scan["cmp"], "ver": scan["ver"], "n": len(scan["e"]), "q": [source],
                                  "an": int(now)}
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
               if since <= h["t"] <= until and (faction is None or h["f"] == faction)]
        return sorted(out, key=lambda kh: kh[1]["t"])


def ingest_text(store: Store, text: str, source: str, now: float | None = None) -> dict:
    """Alle Zeilen eines Textes ablegen. Zählt neu/doppelt/abgelehnt/ungültig."""
    res = {"neu": 0, "doppelt": 0, "abgelehnt": 0, "ungueltig": 0}
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
    d = datetime.fromtimestamp(t)
    return d.weekday() * 24 + d.hour


def aggregate(store: Store, faction: str, since: float, until: float) -> dict:
    """Je Item über das Fenster: Preisverlauf, Angebot, Absatz-Spanne je Tag, Umschlag, Abdeckung."""
    heads = store.heads(since, until, faction)
    cmp_total = sum(h["cmp"] for _, h in heads if h["cmp"] > 0)
    hours = {hour_of_week(h["t"]) for _, h in heads}
    sources = {q for _, h in heads for q in h["q"]}
    items: dict[int, dict] = {}
    hour_lo = [0] * 24          # Abgänge (Untergrenze) je Stunde des Tages
    hour_cmp = [0] * 24
    for k, h in heads:
        hw = hour_of_week(h["t"])
        if h["cmp"] > 0:
            hour_cmp[hw % 24] += h["cmp"]
        for iid, (p, m, a, ab, abv) in store.entries(k).items():
            it = items.setdefault(iid, {"preise": [], "menge": [], "auk": [], "ab": 0, "abv": 0, "h": set()})
            if a > 0 or m > 0:
                it["preise"].append((h["t"], p))
                it["menge"].append(m)
                it["auk"].append(a)
            it["h"].add(hw)
            if h["cmp"] > 0:
                it["ab"] += ab
                it["abv"] += abv
                hour_lo[hw % 24] += abv
    days = cmp_total / 86400 if cmp_total else 0
    out = {}
    for iid, it in items.items():
        lo = it["abv"] / days if days else None
        hi = it["ab"] / days if days else None
        auk = statistics.median(it["auk"]) if it["auk"] else 0
        preise = [p for _, p in it["preise"] if p > 0]
        out[iid] = {
            "preis_letzt": it["preise"][-1][1] if it["preise"] else None,
            "preis_min": min(preise) if preise else None,
            "preis_max": max(preise) if preise else None,
            "preis_median": statistics.median(preise) if preise else None,
            "verlauf": it["preise"],
            "menge": statistics.median(it["menge"]) if it["menge"] else 0,
            "auktionen": auk,
            "absatz_min": lo, "absatz_max": hi,
            "umschlag": (lo / auk) if (lo is not None and auk) else None,
            "abdeckung": len(it["h"]),
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


def report_name(now: datetime) -> str:
    return f"{REPORT_PREFIX}-{week_key(now)}.md"


def report(store: Store, now_ts: float, top: int = 25, window: int = WEEK) -> str:
    since = now_ts - window
    d0 = datetime.fromtimestamp(since).strftime("%d.%m.%Y %H:%M")
    d1 = datetime.fromtimestamp(now_ts).strftime("%d.%m.%Y %H:%M")
    lines = [f"# Marktdaten WoW Forever – Woche {week_key(datetime.fromtimestamp(now_ts))}", "",
             f"Zeitraum {d0} bis {d1} (Zeit des Bot-Servers). Quelle: Vollscans der Spieler (GSMARKT1, MN7). "
             "Keine Namen. Absatz = verschwundene Auktionen je Tag, hochgerechnet über die Vergleichsdauer: "
             "**Untergrenze** (ohne Abbrechen/Neu-Einstellen, gilt für Entscheidungen) – Obergrenze (inkl. "
             "Abbrechen). Umschlag = Untergrenze / Auktionen im Angebot (Median). Abdeckung = Stunden der Woche "
             "(von 168) mit einem Scan.", "",
             f"Doppelte Scans (gleiche Fraktion und Scan-Zeit) seit Beginn verworfen: {int(store.index.get('dupes', 0))}.",
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


def weekly_due(now: datetime, last_week: str | None) -> bool:
    """Montag und in dieser Kalenderwoche noch nicht berichtet."""
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
