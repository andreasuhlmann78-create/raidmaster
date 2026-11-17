"""Markt-Tabellen für AHSentinel (Entscheid des Nutzers 14.11.2026 09:01: täglich neu rechnen, das Addon schlägt nur nach).

Aufruf:  python3 -I markt_tabellen.py [--tages <Ordner>] <AHSentinel.lua> [weitere AHSentinel.lua ...] <ausgabe.lua>
  --tages: Ordner mit den anonymen Tages-Zusammenfassungen der Bot-Sammelstelle (testberichte/markt/tages/<JJJJ-MM-TT>.json,
  D-KERN1) -> zusätzlicher Teil "alle" (Masterplan AHSentinel E: Daten ALLER einsendenden Spieler). Ohne --tages wird
  raidmaster/testberichte/markt/tages genommen, falls es den Ordner gibt; sonst kein Teil "alle" (alles andere wie bisher).
Liest die SavedVariables (privates Daten-Repo), rechnet Wellen je Stufenband, Verkaufsquote je Warengruppe und Preisstufe,
Entzauber-Gewinn je Gruppe (DE30b-Mindestgewinn) und Sniper-/Kaufgewinn je Preisstufe. Schreibt nur Zahlen, keine Namen.
Format: shared/markt-tabellen/README.md. Regeln wie im Addon (Waves.lua, PR2, DE30b, SN-M) – Summe/Summe, nie Median über
Zufallsbeute. Jeder Teil mit n (Fallzahl).
Teil "kern" (16.11.2026): Vorwissen je Weg und Zelle aus den Zählern des MARKT-KERNs (kern_daten.py; Regeln dort).
"""
import sys, re, time, json, collections, statistics as st
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
from lupa.lua51 import LuaRuntime

sys.path.insert(0, str(Path(__file__).resolve().parent))
import kern_daten  # noqa: E402  (Teil "kern": Austausch mit dem MARKT-KERN, Nutzer 16.11.2026 04:51)

Z = ZoneInfo("Europe/Zurich")
BANDS = [("5-25", [10940, 10938, 10939, 10998, 10978]), ("26-35", [11083, 11082, 11134, 11084, 11138]),
         ("36-45", [11137, 11135, 11174, 11139, 11177]), ("46-55", [11176, 11175, 16202, 11178, 14343]),
         ("56-60", [16204, 16203, 14344, 20725])]          # gleich wie AHSentinel Waves.lua (0.65.139)
P_F = ["t", "id", "q", "a", "pr", "rel", "d", "Q", "qs", "S", "ss", "u", "p", "W", "N", "net", "v", "g", "r", "sq", "sh",
       "sp", "x", "ex", "rs", "cr", "cg", "ub", "pw"]
B_F = ["t", "id", "q", "pr", "way", "ev", "src", "v", "g", "r", "rq", "rv", "rk", "mv", "aid"]
D_F = ["t", "id", "ev", "g", "dk", "src", "n", "lv", "c", "bp"]
BASE = 1760000000                                          # Forecast.lua: t = BASE + t × 60
PRICE_BANDS = [0.90, 0.97, 1.03, 1.10, 99.0]               # Preis / Marktwert (wie PR1/PR2)
BUY_BANDS = [0.6, 0.7, 0.8, 0.9, 99.0]                     # Kaufpreis / Wert (wie SN-M)


def num(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def decode(s, fields):
    p = s.split(";")[1:]
    return {fields[j]: (p[j] if j < len(p) else "") for j in range(len(fields))}


def load(path):
    lua = LuaRuntime(unpack_returned_tuples=True)
    lua.execute(open(path, encoding="utf-8", errors="replace").read())
    return lua.globals().AHSentinelDB


TEST_ID_MIN = 990000000        # Test-IDs der Testroutinen (SANDBOX-2, 17.11.2026): nie ein echtes Item, nie in die Tabellen


def series_of(db):
    """Preisverlauf je Item: [(t, preis)] – gleiche Regeln wie verlauf_auspacken.py (PD7 hz delta-kodiert, Flag 0 =
    bestätigt; history ohne unbestätigte/Sync-Punkte u/s)."""
    rx = re.compile(r"(\d+),([\d.e+\-]+),([\d.e+\-]*),(\d*),(\d*)")
    out = collections.defaultdict(list)
    for mk in db.markets.keys():
        m = db.markets[mk]
        if not m.data:
            continue
        for id_ in m.data.keys():
            if int(id_) >= TEST_ID_MIN:
                continue
            d = m.data[id_]
            if d.hz:
                prev = 0
                for dt, p, q, c, f in rx.findall(d.hz):
                    prev += int(dt)
                    if (int(f) if f else 0) == 0:
                        out[int(id_)].append((prev, float(p)))
            h = d.history
            if h:
                for i in range(1, len(h) + 1):
                    e = h[i]
                    if e is None or e.u or e.s:
                        continue
                    if e.t and e.p:
                        out[int(id_)].append((int(e.t), float(e.p)))
    return out


class _Journal:
    """Zusammengeführtes Journal mehrerer Stände (siehe merge_journals) – so gebaut, wie die Rechnungen db.forecast.list lesen."""
    def __init__(self, entries):
        self.forecast = type("F", (), {})()
        self.forecast.list = {i + 1: s for i, s in enumerate(entries)}


KEY_FIELDS = {"P": 6, "B": 4, "D": 3}         # P: t id q a pr rel · B: t id q pr · D: t id ev – ändern sich nie (nur Ergebnisfelder)


def _newest_t(db):
    L = db.forecast and db.forecast.list
    best = 0
    if L:
        for i in range(1, len(L) + 1):
            s = L[i]
            if s:
                try:
                    best = max(best, int(s.split(";")[1]))
                except (IndexError, ValueError):
                    pass
    return best


def merge_journals(dbs):
    """Alle Stände (Tages-Sicherungen, beide Rechner) zu EINEM Journal ohne Doppelte (Nutzer 16.11.2026 04:52: "über alle Daten
    verfügen"). Das Journal im Addon hält nur die neuesten 3000 Einträge – ältere Fälle stehen nur noch in älteren Ständen.
    Schlüssel = Art + Felder, die sich nach dem Schreiben nie ändern (KEY_FIELDS). Ein Schlüssel kommt aus dem NEUESTEN Stand,
    der ihn hat – mit allen seinen Vorkommen (zwei gleiche Einstellungen in derselben Minute bleiben zwei) und dem neuesten
    Ergebnis (r, sq …). Ältere Stände füllen nur Schlüssel, die im neueren fehlen."""
    order = sorted(dbs, key=_newest_t, reverse=True)
    taken, out = set(), []
    for db in order:
        L = db.forecast and db.forecast.list
        if not L:
            continue
        here = collections.defaultdict(list)
        for i in range(1, len(L) + 1):
            s = L[i]
            if not s or s[0] not in KEY_FIELDS:
                continue
            p = s.split(";")
            here[(s[0],) + tuple(p[1:1 + KEY_FIELDS[s[0]]])].append(s)
        for k, ss in here.items():
            if k not in taken:
                taken.add(k)
                out.extend(ss)
    out.sort(key=lambda s: int(s.split(";")[1]) if s.split(";")[1].isdigit() else 0)
    return _Journal(out)


def waves(series):
    res = {}
    for key, mats in BANDS:
        per = []
        for i in mats:
            pts = series.get(i)
            if not pts:
                continue
            d = collections.defaultdict(list)
            for t, p in pts:
                if p > 0:
                    d[datetime.fromtimestamp(t, Z).date()].append(p)
            dm = {k: st.median(v) for k, v in d.items()}
            if len(dm) >= 3:
                per.append(dm)
        if not per:
            continue
        last = max(k for dm in per for k in dm)
        # angefangener letzter Tag zählt nicht (Teil-Tag: morgens höher, Tageszyklus R7) – nur ganze Tage
        days = sorted({k for dm in per for k in dm if k < last})[-10:]          # Fenster 10 Tage wie Waves.lua
        idx = []
        for dd in days:
            vals = [dm[dd] / dm[min(k for k in dm if k >= days[0])] for dm in per if dd in dm]
            if vals:
                idx.append(st.mean(vals))
        state = "offen"
        if len(idx) >= 3 and all(idx[-i] < idx[-i - 1] * 0.85 for i in (1, 2)):
            state = "welle"
        elif len(idx) >= 4 and all(abs(idx[-i] / idx[-i - 1] - 1) <= 0.10 for i in (1, 2, 3)):
            state = "durch"
        elif len(idx) >= 3 and all(idx[-i] > idx[-i - 1] * 1.10 for i in (1, 2)):
            state = "steigt"                                      # nur Hinweis (Erholung), Addon kennt es noch nicht
        res[key] = {"zustand": state, "index": round(idx[-1], 3) if idx else None, "tage": len(idx)}
    return res


def sell_quotes(dbs):
    cells = collections.defaultdict(lambda: [0, 0])
    for db in dbs:
        L = db.forecast and db.forecast.list
        if not L:
            continue
        for i in range(1, len(L) + 1):
            s = L[i]
            if not s or s[0] != "P":
                continue
            e = decode(s, P_F)
            if e["r"] in ("", "u", "c") or num(e["p"]) is None:     # wie Fc:Count: Abbruch zensiert, nur mit Vorhersage
                continue
            rel = num(e["rel"])
            if rel is None:
                continue
            band = next(b for b in PRICE_BANDS if rel <= b)
            c = cells[(e["g"] or "misc", band)]
            c[0] += 1
            c[1] += max(0.0, min(1.0, (num(e["sq"]) or 0) / max(1.0, num(e["q"]) or 1)))   # wie Fc:PostOutcome (Anteil verkauft)
    out = collections.defaultdict(list)
    for (g, b), (n, k) in sorted(cells.items()):
        out[g].append({"bis": b, "n": n, "quote": round(k / n, 3)})
    return out


def de_groups(dbs):
    acc = collections.defaultdict(lambda: [0, 0.0, 0.0, 0.0])       # n, Summe Beute, Summe Vorhersage, Summe Kaufpreis
    accb = collections.defaultdict(lambda: [0, 0.0, 0.0])           # mit Kaufpreis: n, Beute, Kauf
    for db in dbs:
        L = db.forecast and db.forecast.list
        if not L:
            continue
        for i in range(1, len(L) + 1):
            s = L[i]
            if not s or s[0] != "D":
                continue
            e = decode(s, D_F)
            lv, ev, bp, dk = num(e["lv"]), num(e["ev"]), num(e["bp"]), e["dk"]
            if not dk or lv is None or not ev or e["c"] == "0":
                continue
            a = acc[dk]
            a[0] += 1; a[1] += lv; a[2] += ev
            if bp and bp > 0:
                b = accb[dk]; b[0] += 1; b[1] += lv; b[2] += bp
    out = {}
    for dk, (n, slv, sev, _) in acc.items():
        tab = slv / sev if sev else None                              # Beute / Vorhersage (KF2: Summe/Summe)
        nb, blv, bbp = accb.get(dk, (0, 0, 0))
        gain = (blv / bbp - 1) if bbp else None
        if nb >= 30 and gain is not None:
            mindest = 0.20 if gain >= 0.20 else 0.30                  # DE30b gemessen gut / schlecht
        elif tab is not None and abs(tab - 1) <= 0.10:
            mindest = 0.20                                            # ungemessen, Tabelle verlässlich
        else:
            mindest = 0.25                                            # Tabelle weicht ab
        out[dk] = {"n": n, "tabelle": round(tab, 3) if tab else None, "nKauf": nb,
                   "gewinn": round(gain, 3) if gain is not None else None, "mindest": mindest}
    return out


def buy_bands(dbs):
    cells = collections.defaultdict(lambda: [0, 0.0, 0.0])
    for db in dbs:
        L = db.forecast and db.forecast.list
        if not L:
            continue
        for i in range(1, len(L) + 1):
            s = L[i]
            if not s or s[0] != "B":
                continue
            e = decode(s, B_F)
            pr, ev, rq, rv = num(e["pr"]), num(e["ev"]), num(e["rq"]) or 0, num(e["rv"])
            if not pr or not ev or rq <= 0 or rv is None:
                continue
            b = next(x for x in BUY_BANDS if pr / ev <= x)
            c = cells[b]; c[0] += 1; c[1] += pr * rq; c[2] += rv
    return [{"bis": b, "n": n, "gewinn": round(rv / cost - 1, 3)} for b, (n, cost, rv) in sorted(cells.items()) if cost]


ALLE_TAGE = 14                 # so viele Tage (neueste Dateien) fliessen in "alle" ein
ALLE_MAX_BYTES = 40 * 1024     # Teil "alle" höchstens so gross (ganze Datei < 50 KB, README)
ALLE_FELDER = ["preis", "absatzMin", "absatzMax", "quellen", "tage", "scans"]
ALLE_MIN_QUELLEN = 2           # mindestens so viele einsendende Spieler an einem Tag (sonst eigene Daten doppelt)


def alle(tages_dir, max_bytes=ALLE_MAX_BYTES, keep=ALLE_TAGE):
    """Teil "alle" aus den Tages-Zusammenfassungen der Sammelstelle (Bot D-KERN1, Format GSMARKTT1).
    Je Fraktion und Item: preis = Median der Tages-Mediane (Kupfer), absatzMin/absatzMax = Abgänge je Tag als Spanne,
    Summe/Summe über die Tage gewichtet mit der Vergleichsdauer des Tages (vergleich_h), quellen = höchste Quellenzahl an
    einem Tag (Untergrenze der verschiedenen Spieler – die Sammelstelle gibt keine Kennungen heraus), tage, scans.
    Nur Items mit Preis. Zu gross -> Items mit den wenigsten Scans weglassen, Anzahl in "weggelassen" (nie still)."""
    files = []
    if tages_dir and Path(tages_dir).is_dir():                 # nur Dateien <JJJJ-MM-TT>.json, die neuesten keep
        files = sorted(p for p in Path(tages_dir).glob("*.json") if re.match(r"^\d{4}-\d{2}-\d{2}\.json$", p.name))[-keep:]
    days, acc = [], {}
    for fp in files:
        try:
            d = json.loads(fp.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if d.get("format") != "GSMARKTT1" or not isinstance(d.get("fraktionen"), dict):
            continue
        fel = d.get("felder") or []
        ix = {n: i for i, n in enumerate(fel)}
        need = ["scans", "quellen", "preis_median", "absatz_min_tag", "absatz_max_tag"]
        if any(n not in ix for n in need):
            continue
        days.append((int(d.get("von") or 0), int(d.get("bis") or 0)))
        for fac, fr in d["fraktionen"].items():
            if fac not in ("H", "A", "N") or not isinstance(fr, dict):
                continue
            w = num(fr.get("vergleich_h")) or 0.0
            for iid, row in (fr.get("items") or {}).items():
                try:
                    iid = int(iid)
                except (TypeError, ValueError):
                    continue
                if iid >= TEST_ID_MIN:
                    continue
                if not isinstance(row, list) or len(row) < len(fel):
                    continue
                e = acc.setdefault(fac, {}).setdefault(iid, {"p": [], "lo": 0.0, "hi": 0.0, "w": 0.0, "q": 0, "t": 0, "n": 0})
                n, q, p = num(row[ix["scans"]]) or 0, num(row[ix["quellen"]]) or 0, num(row[ix["preis_median"]])
                lo, hi = num(row[ix["absatz_min_tag"]]), num(row[ix["absatz_max_tag"]])
                e["t"] += 1
                e["n"] += int(n)
                e["q"] = max(e["q"], int(q))
                if p and p > 0:
                    e["p"].append(p)
                if lo is not None and hi is not None and w > 0:
                    e["lo"] += lo * w
                    e["hi"] += hi * w
                    e["w"] += w
    if not days:
        return None
    out = {"v": 1, "tage": len(days), "von": min(a for a, _ in days), "bis": max(b for _, b in days),
           "felder": list(ALLE_FELDER), "weggelassen": 0}
    rows = []                      # (scans, fac, iid, zeile)
    out["ohneAbsatz"], out["eineQuelle"] = 0, 0
    for fac, items in acc.items():
        for iid, e in items.items():
            if not e["p"]:
                continue
            lo = round(e["lo"] / e["w"], 2) if e["w"] else None
            hi = round(e["hi"] / e["w"], 2) if e["w"] else None
            # 16.11. 03:0x (erste echte Tagesdatei): AHSentinel nutzt aus "alle" nur den Absatz – Items ohne gemessenen Absatz
            # tragen nichts bei; und eine einzige Quelle ist meist der Spieler selbst (eigene Daten doppelt gezählt). Beides
            # weglassen und zählen (nie still).
            if lo is None or hi is None:
                out["ohneAbsatz"] += 1
                continue
            if e["q"] < ALLE_MIN_QUELLEN:
                out["eineQuelle"] += 1
                continue
            rows.append((e["n"], fac, iid, [int(round(st.median(e["p"]))), lo, hi, e["q"], e["t"], e["n"]]))
    rows.sort(key=lambda r: (-r[0], r[1], r[2]))
    keepn = len(rows)

    def build(k):
        o = dict(out)
        for fac in ("H", "A", "N"):
            sel = {iid: z for _, f, iid, z in rows[:k] if f == fac}
            if sel:
                o[fac] = dict(sorted(sel.items()))
        o["weggelassen"] = len(rows) - k
        return o
    res = build(keepn)
    while keepn > 0 and len(lua_val(res)) > max_bytes:
        keepn = max(0, keepn - max(1, keepn // 20))     # je Runde 5 % der Items mit den wenigsten Scans weg
        res = build(keepn)
    return res


def lua_val(v, ind=""):
    if isinstance(v, dict):
        inner = ind + "  "
        parts = []
        for k, x in v.items():
            if isinstance(k, int):
                key = f"[{k}]"                                   # Item-ID: Zahl-Schlüssel (AHSentinel schlägt mit Zahl nach)
            else:
                key = f'["{k}"]' if not re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", str(k)) else str(k)
            parts.append(f"{inner}{key} = {lua_val(x, inner)},")
        return "{\n" + "\n".join(parts) + f"\n{ind}}}"
    if isinstance(v, list):
        return "{ " + ", ".join(lua_val(x, ind) for x in v) + " }"
    if v is None:
        return "nil"
    if isinstance(v, str):
        return '"' + v.replace('"', '') + '"'
    if isinstance(v, float):
        return f"{v:.6g}"
    return str(v)


def main():
    args = sys.argv[1:]
    # ohne --tages: der Ordner der Sammelstelle im Repo, falls vorhanden (so nimmt die tägliche Aufgabe "alle" ohne Änderung mit)
    std = Path(__file__).resolve().parents[2] / "testberichte" / "markt" / "tages"
    tages = str(std) if std.is_dir() else None
    if args[:1] == ["--tages"]:
        if len(args) < 2:
            print(__doc__)
            sys.exit(1)
        tages, args = args[1], args[2:]
    if len(args) < 1 or (len(args) < 2 and not tages):
        print(__doc__)
        sys.exit(1)
    dbs = [load(p) for p in args[:-1]]
    ser = collections.defaultdict(set)
    for db in dbs:
        for k, v in series_of(db).items():
            ser[k].update(v)                                   # gleiche Punkte aus mehreren Ständen nur einmal
    ser = {k: sorted(v) for k, v in ser.items()}
    jdb = [merge_journals(dbs)]                                # Journale aller Stände ohne Doppelte
    datenbis = max((t for v in ser.values() for t, _ in v), default=0)
    tab = {"v": 1, "erstellt": int(time.time()), "datenBis": datenbis, "wellen": waves(ser),
           "verkauf": dict(sell_quotes(jdb)), "entzaubern": de_groups(jdb), "kaufen": buy_bands(jdb)}
    al = alle(tages) if tages else None
    if al:
        tab["alle"] = al
    kern, kinfo = kern_daten.kern_teil(kern_daten.newest_stores(dbs))
    if kern:
        tab["kern"] = kern                                     # Kern.lua K:TableCell: kern[Weg][Zelle] = { p, n }
    tab["kernInfo"] = {"quellen": kinfo["quellen"], "zellen": sum(len(c) for c in (kern or {}).values())}
    text = ("-- GoldSentinelMarktTabellen (Prüf-Sitzung, täglich neu; nur Zahlen, keine Namen). Format: shared/markt-tabellen/"
            "README.md\nGoldSentinelMarktTabellen = " + lua_val(tab) + "\n")
    open(args[-1], "w", encoding="utf-8").write(text)
    print(f"geschrieben: {args[-1]} ({len(text)} Bytes) · Wellen {len(tab['wellen'])} · Verkauf-Gruppen {len(tab['verkauf'])}"
          f" · Entzauber-Gruppen {len(tab['entzaubern'])} · Kauf-Stufen {len(tab['kaufen'])}")
    for k, w in tab["wellen"].items():
        print(f"  Band {k}: {w}")
    for k, d in tab["entzaubern"].items():
        print(f"  Entzaubern {k}: {d}")
    print("  Kaufen:", tab["kaufen"])
    print("  Verkauf:", {g: v for g, v in tab["verkauf"].items()})
    print(f"  Kern: {tab['kernInfo']} · Wege: {kinfo['wege']}")
    if al:
        print(f"  Alle: {al['tage']} Tage, Items " + ", ".join(f"{f} {len(al[f])}" for f in ("H", "A", "N") if f in al)
              + f", weggelassen {al['weggelassen']}")


if __name__ == "__main__":
    main()
