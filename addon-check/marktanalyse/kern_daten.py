"""Austausch mit dem MARKT-KERN von AHSentinel (Entscheid des Nutzers 16.11.2026 04:51: "du und der Kern tauschen Daten aus
und gleichen ab – du wertest das Ganze aus").

Richtung Kern -> Prüf-Sitzung: die Zähler des Kerns (AHSentinelDB.kern, Kern.lua: c[Weg][Zelle][Tag] = {Fälle, Treffer},
e[Weg][Tag] = Bewertung) kommen mit jedem Daten-Hochladen ins private Daten-Repo. Dieses Modul liest sie mit denselben Regeln
wie Kern.lua (L4 Gewicht: ≤ 14 Tage 1, ≤ 30 Tage 0,5, älter 0; P2 Show; P4 Rückfall).
Richtung Prüf-Sitzung -> Kern: Teil "kern" der Markt-Tabellen (GoldSentinelMarktTabellen.kern[Weg][Zelle] = { p, n }),
den Kern.lua K:TableCell schon liest (KERN-T1 (3), Vorwissen L2 mit k = 2).

Welche Wege in den Teil "kern" dürfen (Regel, begründet):
- "markt" (fremde Auktionen aus Vollscans) und "gilde": Wissen über den MARKT, für jeden Spieler gleich gültig. Nur wenn der
  Weg in den Daten geprüft gut ist (useful: n ≥ 30, Brier besser als die Grundlinie, Brier < 0,20) – ungeprüftes Wissen wird
  nicht weitergegeben. show() bildet K:Show des Addons nach (nur für die Auswertung).
- NICHT "sell": eigene Verkäufe stehen schon im Teil "verkauf" (gleiche Fälle) – zweimal als Vorwissen = doppelt gezählt.
- NICHT "marktu", "buy*": keine Wahrscheinlichkeiten (Kern.lua liest sie nie über K:Estimate).
Je Zelle erst ab KERN_MIN_N gewichteten Fällen (wie SHOW_MIN). Doppelt zählen beim Einsender selbst: sein Vorwissen hat nur das
Gewicht k = 2 gegen seine eigenen n Fälle (Estimate: (y + 2·prior) / (n + 2)) – bei n ≥ 30 höchstens 2/32 = 6 %.
"""
import math

HALF_DAYS, MAX_DAYS = 14, 30
SHOW_MIN, BRIER_MAX, P4_DAYS, P4_MIN = 30, 0.20, 7, 10
KERN_WAYS = ("markt", "gilde")
KERN_MIN_N = 30
DAY = 86400


def _items(t):
    """Lua-Tabelle (lupa) oder dict -> (Schlüssel, Wert)"""
    if t is None:
        return []
    if isinstance(t, dict):
        return list(t.items())
    return list(t.items())


def kern_of(db):
    """{"c": {Weg: {Zelle: {Tag: (n, y)}}}, "e": {Weg: {Tag: [8 Zahlen]}}} oder None"""
    k = db.kern if db is not None else None
    if k is None:
        return None
    c, e = {}, {}
    for way, cells in _items(k.c):
        w = c.setdefault(str(way), {})
        for cell, days in _items(cells):
            z = w.setdefault(str(cell), {})
            for d, v in _items(days):
                if v is None:
                    continue
                z[int(d)] = (float(v[1] or 0), float(v[2] or 0))
    for way, evs in _items(k.e):
        w = e.setdefault(str(way), {})
        for d, v in _items(evs):
            if v is None:
                continue
            w[int(d)] = [float(v[i] or 0) if v[i] is not None else 0.0 for i in range(1, 9)]
    return {"c": c, "e": e}


def day_start(t, tz="Europe/Zurich"):
    """wie A:DayStart (Ortszeit-Mitternacht)"""
    import datetime
    from zoneinfo import ZoneInfo
    d = datetime.datetime.fromtimestamp(t, ZoneInfo(tz))
    return int(d.replace(hour=0, minute=0, second=0, microsecond=0).timestamp())


def newest_day(kd):
    days = [d for w in kd["c"].values() for z in w.values() for d in z]
    days += [d for w in kd["e"].values() for d in w]
    return max(days) if days else 0


def weight(day, today):
    age = (today - day) / DAY
    if age > MAX_DAYS:
        return 0.0
    if age > HALF_DAYS:
        return 0.5
    return 1.0


def counts(kd, way, cell, today):
    n = y = 0.0
    for d, (a, b) in kd["c"].get(way, {}).get(cell, {}).items():
        g = weight(d, today)
        n, y = n + g * a, y + g * b
    return n, y


def evaluate(kd, way, today, days=MAX_DAYS):
    r = dict(n=0.0, bN=0.0, bB=0.0, hN=0.0, hB=0.0, nO=0.0, bO=0.0, hO=0.0)
    frm = today - (days - 1) * DAY
    for d, ev in kd["e"].get(way, {}).items():
        if d >= frm:
            for i, k in enumerate(("n", "bN", "bB", "hN", "hB", "nO", "bO", "hO")):
                r[k] += ev[i]
    return r


def fallback(kd, way, today, first=None):
    """wie Kern.lua K:Fallback (seit 0.65.256, KERN-P4-1): erst wenn der Weg seit mindestens 7 Tagen bewertet wird
    (kern.first[way] <= heute - 6 Tage) und über die letzten 7 Tage n >= P4_MIN und Brier schlechter als die Grundlinie."""
    f = evaluate(kd, way, today, P4_DAYS)
    if not first or first > today - (P4_DAYS - 1) * DAY:
        return False, f
    return (f["n"] >= P4_MIN and f["bN"] > f["bB"]), f


def show(kd, way, today, first=None):
    """wie Kern.lua K:Show seit 0.65.256 (KERN-P2-1: Grundlinie nach Brier, nicht nach Treffern) -> (ok, Grund, Bewertung).
    first = kern.first[way] (Tag der ersten Bewertung) – ohne first nie Rückfall (wie im Addon)."""
    r = evaluate(kd, way, today)
    if r["n"] < SHOW_MIN:
        return False, "lernt noch", r
    if fallback(kd, way, today, first)[0]:
        return False, "Rückfall (7 Tage unter der Grundlinie)", r
    if r["bN"] >= r["bB"]:
        return False, "schlägt die Grundlinie nicht", r
    if r["bN"] / r["n"] >= BRIER_MAX:
        return False, "Brier zu hoch", r
    return True, "zeigen", r


def useful(kd, way, today):
    """Darf der Weg weitergegeben werden? Regel der Prüf-Sitzung (nicht K:Show, siehe Befund KERN-P2-1): n ≥ 30 und Brier
    besser als die Grundlinie ("immer nein") und Brier < 0,20. Der Treffer-Vergleich bei 0,5 taugt für seltene Ereignisse
    nicht: bei Quoten um 5 % trifft "immer nein" fast immer, die Vorhersage kann ihn praktisch nie schlagen."""
    r = evaluate(kd, way, today)
    if r["n"] < SHOW_MIN:
        return False, "lernt noch (n %.0f)" % r["n"]
    if r["bN"] >= r["bB"]:
        return False, "Brier %.4f nicht besser als Grundlinie %.4f" % (r["bN"] / r["n"], r["bB"] / r["n"])
    if r["bN"] / r["n"] >= BRIER_MAX:
        return False, "Brier %.4f ≥ 0,20" % (r["bN"] / r["n"])
    return True, "weitergegeben (Brier %.4f, Grundlinie %.4f, n %.0f)" % (r["bN"] / r["n"], r["bB"] / r["n"], r["n"])


def _journal_t(db):
    """Jüngste Zeit im Journal (Forecast) – 0, wenn keins da ist."""
    try:
        import markt_tabellen
        return markt_tabellen._newest_t(db) or 0
    except Exception:
        return 0


def newest_stores(dbs):
    """Je Kern-Speicher (erkannt an kern.since) nur den neuesten Stand – mehrere Tages-Sicherungen desselben Rechners sind
    derselbe Speicher und dürfen nie summiert werden; verschiedene Speicher (zweiter Rechner) zählen je einmal."""
    best = {}
    for db in dbs:
        k = kern_of(db)
        if not k:
            continue
        since = db.kern.since
        # Gleichstand am Kern-Tag (z. B. ohne neue Tagesfälle): der Stand mit dem jüngsten Journal-Eintrag gewinnt
        # (Befund 16.11. 14:40: sonst blieb der ältere Rechner-Stand stehen und der Neuaufbau KERN-S1b fehlte im Abgleich).
        day = (newest_day(k), _journal_t(db))
        if since not in best or day > best[since][0]:
            best[since] = (day, db)
    return [db for _, db in best.values()]


def kern_teil(dbs):
    """Teil "kern" ({Weg: {Zelle: {"p", "n"}}}) und Info ({"quellen", "wege": {Weg: Grund}}). Summe über alle Dateien."""
    kds = [k for k in (kern_of(db) for db in dbs) if k]
    info = {"quellen": len(kds), "wege": {}}
    if not kds:
        return None, info
    sums = {}
    for kd in kds:
        today = newest_day(kd)
        for way in KERN_WAYS:
            if way not in kd["c"]:
                continue
            ok, why = useful(kd, way, today)
            prev = info["wege"].get(way)
            info["wege"][way] = why if not prev or prev == why else prev + " / " + why
            if not ok:
                continue
            for cell in kd["c"][way]:
                n, y = counts(kd, way, cell, today)
                s = sums.setdefault(way, {}).setdefault(cell, [0.0, 0.0])
                s[0], s[1] = s[0] + n, s[1] + y
    out = {}
    for way, cells in sorted(sums.items()):
        for cell, (n, y) in sorted(cells.items()):
            if n >= KERN_MIN_N:
                out.setdefault(way, {})[cell] = {"p": round(max(0.0, min(1.0, y / n)), 4), "n": int(round(n))}
    return (out or None), info


def wilson(y, n, z=1.96):
    if n <= 0:
        return 0.0, 1.0
    p = y / n
    d = 1 + z * z / n
    m = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return max(0.0, m - h), min(1.0, m + h)
