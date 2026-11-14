"""Markt-Tabellen für AHSentinel (Entscheid des Nutzers 14.11.2026 09:01: täglich neu rechnen, das Addon schlägt nur nach).

Aufruf:  python3 -I markt_tabellen.py <AHSentinel.lua> [weitere AHSentinel.lua ...] <ausgabe.lua>
Liest die SavedVariables (privates Daten-Repo), rechnet Wellen je Stufenband, Verkaufsquote je Warengruppe und Preisstufe,
Entzauber-Gewinn je Gruppe (DE30b-Mindestgewinn) und Sniper-/Kaufgewinn je Preisstufe. Schreibt nur Zahlen, keine Namen.
Format: shared/markt-tabellen/README.md. Regeln wie im Addon (Waves.lua, PR2, DE30b, SN-M) – Summe/Summe, nie Median über
Zufallsbeute. Jeder Teil mit n (Fallzahl).
"""
import sys, re, time, collections, statistics as st
from datetime import datetime
from zoneinfo import ZoneInfo
from lupa.lua51 import LuaRuntime

Z = ZoneInfo("Europe/Zurich")
BANDS = [("5-25", [10940, 10938, 10939, 10998, 10978]), ("26-35", [11083, 11082, 11134, 11084, 11138]),
         ("36-45", [11137, 11135, 11174, 11139, 11177]), ("46-55", [11176, 11175, 16202, 11178, 14343]),
         ("56-60", [16204, 16203, 14344, 20725])]          # gleich wie AHSentinel Waves.lua (0.65.139)
P_F = ["t", "id", "q", "a", "pr", "rel", "d", "Q", "qs", "S", "ss", "u", "p", "W", "N", "net", "v", "g", "r", "sq", "sh",
       "sp", "x", "ex", "rs", "cr", "cg", "ub", "pw"]
B_F = ["t", "id", "q", "pr", "way", "ev", "src", "v", "g", "r", "rq", "rv", "rk", "mv", "aid"]
D_F = ["t", "id", "ev", "g", "dk", "src", "n", "lv", "c", "bp"]
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


def lua_val(v, ind=""):
    if isinstance(v, dict):
        inner = ind + "  "
        parts = []
        for k, x in v.items():
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
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)
    dbs = [load(p) for p in sys.argv[1:-1]]
    ser = collections.defaultdict(list)
    for db in dbs:
        for k, v in series_of(db).items():
            ser[k].extend(v)
    datenbis = max((t for v in ser.values() for t, _ in v), default=0)
    tab = {"v": 1, "erstellt": int(time.time()), "datenBis": datenbis, "wellen": waves(ser),
           "verkauf": dict(sell_quotes(dbs)), "entzaubern": de_groups(dbs), "kaufen": buy_bands(dbs)}
    text = ("-- GoldSentinelMarktTabellen (Prüf-Sitzung, täglich neu; nur Zahlen, keine Namen). Format: shared/markt-tabellen/"
            "README.md\nGoldSentinelMarktTabellen = " + lua_val(tab) + "\n")
    open(sys.argv[-1], "w", encoding="utf-8").write(text)
    print(f"geschrieben: {sys.argv[-1]} ({len(text)} Bytes) · Wellen {len(tab['wellen'])} · Verkauf-Gruppen {len(tab['verkauf'])}"
          f" · Entzauber-Gruppen {len(tab['entzaubern'])} · Kauf-Stufen {len(tab['kaufen'])}")
    for k, w in tab["wellen"].items():
        print(f"  Band {k}: {w}")
    for k, d in tab["entzaubern"].items():
        print(f"  Entzaubern {k}: {d}")
    print("  Kaufen:", tab["kaufen"])
    print("  Verkauf:", {g: v for g, v in tab["verkauf"].items()})


if __name__ == "__main__":
    main()
