"""Markt-Überwachung AHSentinel (wöchentlich) – Messungen a, b, d, e, f mit gleicher Methode wie 16.11.2026.

Aufruf: python3 -I markt_ueberwachung.py <questie foreverItemDB.lua> <Data_Forever.lua> <bis JJJJ-MM-TT> <AHSentinel.lua ...>
Nur zusammengefasste Zahlen, keine Namen. Märkte: nur "|Horde" (Neutral = eigenes AH), Sicherungsmärkte (mergedInto) übersprungen,
Preispunkte aller Stände ohne Doppelte (id, t). Journale ohne Doppelte (Schlüssel wie markt_tabellen.merge_journals).
"""
import sys, re, json, collections, statistics as st
from datetime import datetime, date, timedelta
from zoneinfo import ZoneInfo
from lupa.lua51 import LuaRuntime

Z = ZoneInfo("Europe/Zurich")
BASE = 1760000000
TEST_ID_MIN = 990000000
B_F = ["t", "id", "q", "pr", "way", "ev", "src", "v", "g", "r", "rq", "rv", "rk", "mv", "aid"]
P_F = ["t", "id", "q", "a", "pr", "rel", "d", "Q", "qs", "S", "ss", "u", "p", "W", "N", "net", "v", "g", "r", "sq", "sh",
       "sp", "x", "ex", "rs", "cr", "cg", "ub", "pw"]
KEY_FIELDS = {"P": 6, "B": 4, "D": 3}

# Material ohne benötigte Stufe -> Band (wie 16.11.: Staub/Essenz/Splitter, Stoffe, Erze/Barren, Kräuter, Leder, Steine)
MAT = {}
for ids, b in [
    ([10940, 10938, 10939, 10998, 10978, 2589, 2592, 2770, 2771, 2775, 2840, 3576, 2841, 2842, 2835, 2836, 2447, 765, 2449, 785,
      2450, 2452, 2453, 3820, 2318, 2319, 783, 4232], 0),
    ([11083, 11082, 11134, 11084, 11138, 11137, 11135, 11174, 11139, 11177, 4306, 4338, 2772, 3858, 3575, 3859, 3860, 3577,
      2838, 7912, 3355, 3369, 3356, 3357, 3818, 3821, 3358, 3819, 4625, 8831, 8836, 8838, 4234, 4304, 4235, 8169], 1),
    ([11176, 11175, 16202, 11178, 14343, 16204, 16203, 14344, 20725, 14047, 14256, 10620, 12359, 12365, 8839, 8845, 8846,
      13464, 13463, 13465, 13466, 13467, 13468, 8170, 8171], 2)]:
    for i in ids:
        MAT[i] = b
BANDNAMES = ["1–25", "26–45", "46–60"]


def zday(ts):
    return datetime.fromtimestamp(ts, Z).date()


def load(path):
    lua = LuaRuntime(unpack_returned_tuples=True)
    lua.execute(open(path, encoding="utf-8", errors="replace").read())
    return lua.globals().AHSentinelDB


rx = re.compile(r"(\d+),([\d.e+\-]+),([\d.e+\-]*),(\d*),(\d*)")


def extract(path):
    """Preispunkte (Horde, ohne Sicherung), Journal-Einträge, Absatz/Leiter/own, vendorBuy aus EINEM Stand."""
    db = load(path)
    pts = collections.defaultdict(dict)
    for mk in db.markets.keys():
        m = db.markets[mk]
        if not m.data or m.mergedInto or not str(mk).endswith("|Horde"):
            continue
        for id_ in m.data.keys():
            iid = int(id_)
            if iid >= TEST_ID_MIN:
                continue
            d = m.data[id_]
            if d.hz:
                prev = 0
                for dt, p, q, c, f in rx.findall(d.hz):
                    prev += int(dt)
                    if (int(f) if f else 0) == 0:
                        pts[iid][prev] = (float(p), float(q) if q else None)
            h = d.history
            if h:
                for i in range(1, len(h) + 1):
                    e = h[i]
                    if e is None or e.u or e.s:
                        continue
                    if e.t and e.p:
                        pts[iid][int(e.t)] = (float(e.p), float(e.q) if e.q else None)
    jl = []
    L = db.forecast and db.forecast.list
    if L:
        for i in range(1, len(L) + 1):
            s = L[i]
            if s and s[0] in KEY_FIELDS:
                jl.append(s)
    fs = db.fullScan
    sold, ladder, own = {}, {}, None
    if fs:
        if fs.sold:
            for k in fs.sold.keys():
                sold[int(k)] = str(fs.sold[k])
        if fs.ladder:
            for k in fs.ladder.keys():
                ladder[int(k)] = str(fs.ladder[k])
        if fs.own:
            own = (fs.own.gone or 0, fs.own.sold or 0)
    vb = {}
    if db.vendorBuy:
        for k in db.vendorBuy.keys():
            try:
                vb[int(k)] = float(db.vendorBuy[k])
            except (TypeError, ValueError):
                pass
    ma1 = (db.core.ma1.n, db.core.ma1.wrong) if db.core and db.core.ma1 else None
    return dict(pts=pts, jl=jl, sold=sold, ladder=ladder, own=own, vb=vb, ma1=ma1)


def merge_j(stores):
    def newest(jl):
        b = 0
        for s in jl:
            try:
                b = max(b, int(s.split(";")[1]))
            except (IndexError, ValueError):
                pass
        return b
    taken, out = set(), []
    for jl in sorted(stores, key=newest, reverse=True):
        here = collections.defaultdict(list)
        for s in jl:
            p = s.split(";")
            here[(s[0],) + tuple(p[1:1 + KEY_FIELDS[s[0]]])].append(s)
        for k, ss in here.items():
            if k not in taken:
                taken.add(k)
                out.extend(ss)
    return out


def dec(s, F):
    p = s.split(";")[1:]
    return {F[j]: (p[j] if j < len(p) else "") for j in range(len(F))}


def num(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def pct(a, n):
    return round(100 * a / n) if n else 0


def main():
    qdb, data_forever, bis = sys.argv[1], sys.argv[2], date.fromisoformat(sys.argv[3])
    paths = sys.argv[4:]
    out = {}
    # --- Stufen aus QuestieDB
    txt = open(qdb, encoding="utf-8", errors="replace").read()
    body = txt[txt.index("QuestieDB.itemData = [[") + len("QuestieDB.itemData = [["):txt.rindex("]]")]
    lua = LuaRuntime(unpack_returned_tuples=True)
    T = lua.execute(body)
    lvl = {}
    for k in T.keys():
        r = T[k]
        rl = r[10]
        if rl and int(rl) > 0:
            lvl[int(k)] = int(rl)
    # --- Stände lesen
    allp = collections.defaultdict(dict)
    stores, per = [], []
    for p in paths:
        x = extract(p)
        for iid, d in x["pts"].items():
            allp[iid].update(d)
        stores.append(x["jl"])
        per.append((p, x))
        print("gelesen", p.split("goldsentinel-daten/")[-1], "Items", len(x["pts"]), "Journal", len(x["jl"]), file=sys.stderr)
    npts = sum(len(d) for d in allp.values())
    tmin = min(t for d in allp.values() for t in d)
    tmax = max(t for d in allp.values() for t in d)
    out["daten"] = dict(items=len(allp), punkte=npts, von=str(zday(tmin)), bis=str(datetime.fromtimestamp(tmax, Z)))
    # --- Tagesmedian je Item (volle Tage bis 'bis')
    med = {}
    for iid, d in allp.items():
        byd = collections.defaultdict(list)
        for t, (p, q) in d.items():
            dd = zday(t)
            if dd <= bis and p > 0:
                byd[dd].append(p)
        if byd:
            med[iid] = {k: st.median(v) for k, v in byd.items()}
    # --- a) MA6
    cases = []   # (ergebnistag, art, outcome, item, gleichgerichtet)
    for iid, m in med.items():
        for d0, v0 in m.items():
            d3 = d0 + timedelta(days=3)
            d4 = d0 + timedelta(days=4)
            if d3 not in m or d4 not in m:
                continue
            c3 = m[d3] / v0 - 1
            if -0.15 <= c3 <= 0.15:
                continue
            art = "fall" if c3 < 0 else "anstieg"
            nx = m[d4] / m[d3] - 1
            if abs(nx) <= 0.02:
                o = "gleich"
            elif (nx < 0) == (art == "fall"):
                o = "weiter"
            else:
                o = "dreht"
            seq = [m.get(d0 + timedelta(days=i)) for i in range(4)]
            gg = None not in seq and all(((seq[i + 1] < seq[i]) if art == "fall" else (seq[i + 1] > seq[i])) for i in range(3))
            cases.append((d4, art, o, iid, gg))

    def summ(sel):
        r = {}
        for art in ("fall", "anstieg"):
            c = [x for x in sel if x[1] == art]
            n = len(c)
            cnt = collections.Counter(x[2] for x in c)
            r[art] = dict(n=n, items=len({x[3] for x in c}), weiter=pct(cnt["weiter"], n), gleich=pct(cnt["gleich"], n),
                          dreht=pct(cnt["dreht"], n))
        return r
    dvon = min(x[0] for x in cases) if cases else None
    out["ma6"] = {
        "gesamt": summ(cases), "von": str(dvon),
        "letzte14": summ([x for x in cases if x[0] > bis - timedelta(days=14)]),
        "bis15": summ([x for x in cases if x[0] <= date(2026, 11, 15)]),
        "neu16_22": summ([x for x in cases if date(2026, 11, 16) <= x[0] <= bis]),
        "gleichgerichtet_neu": summ([x for x in cases if x[4] and date(2026, 11, 16) <= x[0] <= bis]),
        "je_tag": {str(d): summ([x for x in cases if x[0] == d]) for d in sorted({x[0] for x in cases}) if d >= date(2026, 11, 14)},
    }
    # --- b) Bänder (Kette)
    def band(iid):
        l = lvl.get(iid)
        if l:
            return 0 if l <= 25 else (1 if l <= 45 else 2)
        return MAT.get(iid)
    days = sorted({d for m in med.values() for d in m})
    bands = {}
    for b in range(3):
        its = [i for i in med if band(i) == b]
        nmat = sum(1 for i in its if i not in lvl)
        idx, chain, rows = 1.0, {}, {}
        started = False
        for i in range(1, len(days)):
            d, dp = days[i], days[i - 1]
            rr = [med[x][d] / med[x][dp] for x in its if d in med[x] and dp in med[x]]
            if len(rr) >= 20:
                started = True
                r = st.median(rr)
                idx *= r
                chain[str(d)] = (round(idx, 3), len(rr), round(100 * (r - 1), 1))
            elif started:
                chain[str(d)] = (round(idx, 3), len(rr), None)
        lastr = [v[2] for k, v in sorted(chain.items()) if v[2] is not None][-4:]
        g = 1.0
        for x in lastr:
            g *= 1 + x / 100
        trend = 100 * (g ** (1 / len(lastr)) - 1) if lastr else None
        bands[BANDNAMES[b]] = dict(items=len(its), material=nmat, tage=len(chain), kette=chain,
                                   trend4=round(trend, 1) if trend is not None else None)
    out["baender"] = bands
    # --- d) Journal
    J = merge_j(stores)
    out["journal"] = dict(eintraege=len(J), B=sum(1 for s in J if s[0] == "B"), D=sum(1 for s in J if s[0] == "D"),
                          P=sum(1 for s in J if s[0] == "P"))
    wk0 = datetime(2026, 11, 16, tzinfo=Z).timestamp()
    wk1 = datetime.combine(bis + timedelta(days=1), datetime.min.time(), Z).timestamp()

    def tt(e):
        return BASE + int(e["t"]) * 60

    Bs = [dec(s, B_F) for s in J if s[0] == "B"]
    for e in Bs:
        e["ts"] = tt(e)
    jt = [e["ts"] for e in Bs]
    out["journal"]["B_von"] = str(datetime.fromtimestamp(min(jt), Z)) if jt else None
    out["journal"]["B_bis"] = str(datetime.fromtimestamp(max(jt), Z)) if jt else None

    def agg(lst):
        done = [e for e in lst if num(e["rv"]) is not None and (num(e["rq"]) or 0) > 0 and num(e["pr"])]
        cost = sum(num(e["pr"]) * num(e["rq"]) for e in done)
        rev = sum(num(e["rv"]) for e in done)
        win = sum(1 for e in done if num(e["rv"]) > num(e["pr"]) * num(e["rq"]))
        evs = sum((num(e["ev"]) or 0) * num(e["rq"]) for e in done)
        return dict(kaeufe=len(lst), fertig=len(done), einsatz_g=round(cost / 1e4, 2), erloes_g=round(rev / 1e4, 2),
                    rendite=round(100 * (rev / cost - 1), 1) if cost else None, mit_gewinn=pct(win, len(done)),
                    ev_g=round(evs / 1e4, 2), erloes_vs_ev=round(100 * (rev / evs - 1), 1) if evs else None)
    wk = [e for e in Bs if wk0 <= e["ts"] < wk1]
    prev = [e for e in Bs if e["ts"] < wk0]
    out["wege_woche"] = {w: agg([e for e in wk if e["way"] == w]) for w in sorted({e["way"] for e in wk})}
    out["wege_vorher"] = {w: agg([e for e in prev if e["way"] == w]) for w in sorted({e["way"] for e in prev})}
    out["quellen_woche"] = {s: agg([e for e in wk if e["src"] == s]) for s in sorted({e["src"] for e in wk})}
    out["woche_je_tag"] = {str(d): agg([e for e in wk if zday(e["ts"]) == d]) for d in sorted({zday(e["ts"]) for e in wk})}
    bb = collections.defaultdict(list)
    for e in wk:
        if e["way"] == "d" and num(e["ev"]) and num(e["pr"]):
            r = num(e["pr"]) / num(e["ev"])
            k = "<=0,7" if r <= 0.7 else "<=0,8" if r <= 0.8 else "<=0,833" if r <= 1 / 1.2 else "<=0,85" if r <= 0.85 else "<=0,9" if r <= 0.9 else ">0,9"
            bb[k].append(e)
    out["de_stufen_woche"] = {k: agg(v) for k, v in sorted(bb.items())}
    bb = collections.defaultdict(list)
    for e in Bs:
        if num(e["ev"]) and num(e["pr"]):
            r = num(e["pr"]) / num(e["ev"])
            k = "<=0,7" if r <= 0.7 else "<=0,8" if r <= 0.8 else "<=0,9" if r <= 0.9 else ">0,9"
            bb[k].append(e)
    out["kaufstufen_alle"] = {k: agg(v) for k, v in sorted(bb.items())}
    tops = collections.Counter(e["id"] for e in wk if e["way"] == "d")
    out["de_top_items_woche"] = tops.most_common(5)
    # Einstellungen
    Ps = [dec(s, P_F) for s in J if s[0] == "P"]
    for e in Ps:
        e["ts"] = tt(e)
    pw = [e for e in Ps if wk0 <= e["ts"] < wk1]
    res = [e for e in pw if e["r"] not in ("", "u", "c") and num(e["p"]) is not None]
    out["einstellen_woche"] = dict(n=len(pw), dauer=dict(collections.Counter(e["d"] for e in pw)),
                                   ergebnis=dict(collections.Counter(e["r"] for e in pw)), gewertet=len(res),
                                   verkauft=pct(sum(min(1, (num(e["sq"]) or 0) / max(1, num(e["q"]) or 1)) for e in res), len(res)),
                                   vorhergesagt=pct(sum(num(e["p"]) for e in res), len(res)))
    # --- e) Absatz-Plausibilität je Stand (nur neueste Stände mit sold)
    eres = {}
    for p, x in per:
        if "aktuell/" not in p or not x["sold"]:
            continue
        gone, sold = x["own"] or (0, 0)
        f = max(0.2, min(1, sold / gone)) if gone >= 5 else 1
        meas = over = over_raw = u3 = bad = 0
        ex = []
        for iid, s in x["sold"].items():
            m = re.match(r"^([\d.]*);(\d+);(\d+);(\d+);(\d+);(\d+)(.*)$", s)
            if not m:
                continue
            rate = num(m.group(1))
            pairs, first, last = int(m.group(2)), int(m.group(3)), int(m.group(4))
            rest = m.group(7).split(";")
            if len(rest) >= 4 and rest[3] and int(rest[3] or 0) > 0:
                bad += 1
            if rate is None or pairs < 3 or last - first < 3 * 86400:
                continue
            lad = x["ladder"].get(iid)
            sup = None
            if lad:
                parts = lad.split(";")
                sup = num(parts[2]) if len(parts) > 2 else None
            if not sup:
                continue
            meas += 1
            r = rate * f
            if r > sup:
                over += 1
                ex.append((iid, round(r), int(sup)))
            if rate > sup:
                over_raw += 1
            if r / 24 > 0.25 * sup:
                u3 += 1
        ex.sort(key=lambda z: -z[1] / max(1, z[2]))
        key = p.split("aktuell/")[1].split("/")[0]
        eres[key] = dict(items=len(x["sold"]), gemessen=meas, faktor=round(f, 3), own=x["own"], ueber_angebot=over,
                         anteil=round(100 * over / meas, 1) if meas else None, roh=over_raw, u3=u3, unplausibel_zaehler=bad,
                         beispiele=ex[:8], ma1=x["ma1"])
    out["absatz"] = eres
    # --- f) Herstellen
    lua2 = LuaRuntime(unpack_returned_tuples=True)
    lua2.execute("ns = {Flavor=\"forever\"}\n" + open(data_forever, encoding="utf-8", errors="replace").read().replace("local _, ns = ...", ""))
    R = lua2.globals().ns.RecipeRows
    vb = {}
    for p, x in per:
        for k, v in x["vb"].items():
            vb[k] = min(v, vb.get(k, v))

    def craft(day):
        res = [[0, 0], [0, 0], [0, 0]]
        extreme = [0, 0, 0]
        for i in range(1, len(R) + 1):
            r = R[i]
            if r[2] not in (185, 171):
                continue
            learn = int(r[7] or 1)
            b = 0 if learn <= 124 else (1 if learn <= 224 else 2)
            pid, mn, mx = r[11], r[12] or 1, r[13] or 1
            pp = med.get(int(pid), {}).get(day) if pid else None
            if not pp:
                continue
            prod = pp * 0.95 * (mn + mx) / 2
            z = r[17]
            cost, ok = 0, True
            if not z:
                continue
            for j in range(1, len(z) + 1, 2):
                zid, zn = int(z[j]), z[j + 1]
                a = med.get(zid, {}).get(day)
                v = vb.get(zid)
                c = min([x for x in (a, v) if x]) if (a or v) else None
                if not c:
                    ok = False
                    break
                cost += c * zn
            if not ok or cost <= 0:
                continue
            g = prod / cost - 1
            res[b][1] += 1
            if g > 0.10:
                res[b][0] += 1
            if g > 3:
                extreme[0] += 1
            if g < -0.9:
                extreme[1] += 1
            extreme[2] += 1
        return res, extreme
    out["herstellen"] = {str(d): craft(d) for d in (date(2026, 11, 15), bis) if any(d in m for m in med.values())}
    print(json.dumps(out, ensure_ascii=False, indent=1, default=str))


if __name__ == "__main__":
    main()
