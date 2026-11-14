"""Plausibilität der AHSentinel-Buchhaltung gegen den Markt (Supervisor, Entscheid des Nutzers 14.11. 14:46 "solche Sachen verhindern").

Aufruf:  python3 -I buchhaltung_plausi.py <AHSentinel.lua>
Prüft ohne Namen, nur Item-IDs und Zahlen:
  P1 Verteilung beim Entzaubern: Faktor Einstand/Markt je Material gegen das Tagesmittel aller verkauften Materialien;
     ×1,33 darüber oder ×0,75 darunter = WARNUNG (Beispiel 14.11.: Seelenstaub Faktor 1,65, Essenzen 0,3–0,5).
  P2 Entzaubern: Summe der Material-Einstände je Tag = Summe der Einstände der entzauberten Teile (Umbuchung verliert nichts).
  P3 Gewinn je Gruppe = Summe Erlös − Summe Einsatz (keine Teil-Zahl mit anderem Vorzeichen ohne Hinweis).
Ausgabe: Zeilen "OK"/"WARNUNG" mit Zahlen; Exit 1 bei WARNUNG.
"""
import sys, re, collections, datetime, statistics as st
from lupa.lua51 import LuaRuntime


def load(path):
    lua = LuaRuntime(unpack_returned_tuples=True)
    lua.execute(open(path, encoding="utf-8", errors="replace").read())
    return lua.globals().AHSentinelDB


def day(t):
    return datetime.datetime.fromtimestamp(int(t or 0)).strftime("%Y-%m-%d")


def prices(db):
    rx = re.compile(r"(\d+),([\d.e+\-]+),([\d.e+\-]*),(\d*),(\d*)")
    out = collections.defaultdict(lambda: collections.defaultdict(list))
    for mk in db.markets.keys():
        m = db.markets[mk]
        if not m.data:
            continue
        for i in m.data.keys():
            d = m.data[i]
            if d.hz:
                prev = 0
                for dt, p, q, c, f in rx.findall(d.hz):
                    prev += int(dt)
                    if (int(f) if f else 0) == 0:
                        out[int(i)][day(prev)].append(float(p))
            h = d.history
            if h:
                for k in range(1, len(h) + 1):
                    e = h[k]
                    if e and e.t and e.p and not e.u and not e.s:
                        out[int(i)][day(e.t)].append(float(e.p))
    return {i: {d: st.median(v) for d, v in dd.items()} for i, dd in out.items()}


def main():
    if len(sys.argv) < 2:
        print(__doc__); sys.exit(2)
    db = load(sys.argv[1])
    pr = prices(db)
    L = db.books.log
    warn = 0
    # P1: verkaufte Ware mit Einstand -> Einstand/Stück gegen Marktpreis am Tag des letzten Entzauberns/Kaufs davor
    de_days = collections.defaultdict(list)
    sold = collections.defaultdict(lambda: [0, 0, 0])
    for k in range(1, len(L) + 1):
        e = L[k]
        if e is None:
            continue
        if e.k == "de":
            de_days["all"].append(day(e.t))
        if e.k == "sale" and e.id and (e.cost or 0) > 0 and (e.q or 0) > 0:
            paid = (e.q or 0) - (e.free or 0)          # Stücke ohne Einkauf (Kosten 0) nicht mitteln
            if paid <= 0:
                continue
            s = sold[(int(e.id), day(e.ti or e.t))]
            s[0] += paid; s[1] += e.cost; s[2] += (e.rev or 0) * paid / e.q
    dd = sorted(set(de_days["all"]))
    rows = []
    for (iid, d), (q, cost, rev) in sorted(sold.items()):
        per = cost / q
        ref_days = [x for x in dd if x <= d][-2:] or [d]
        refs = [pr.get(iid, {}).get(x) for x in ref_days if pr.get(iid, {}).get(x)]
        if refs:
            rows.append((d, iid, q, per, st.median(refs), rev / q, ref_days))
    # Einstand unter Markt ist normal (billig gekauft = Gewinn). Fehler ist eine SCHIEFE Verteilung: alle Materialien aus
    # denselben Entzauberungen müssen etwa denselben Faktor Einstand/Markt haben. Abweichung > 33 % vom Tagesmittel = WARNUNG.
    byday = collections.defaultdict(list)
    for r in rows:
        byday[r[0]].append(r)
    for d, rs in sorted(byday.items()):
        tq = sum(r[2] * r[4] for r in rs)
        mean = sum(r[2] * r[3] for r in rs) / tq if tq else 0
        for (_, iid, q, per, ref, revq, rdays) in rs:
            f = per / ref
            rel = f / mean if mean else 1
            bad = q >= 5 and len(rs) > 1 and (rel > 1.33 or rel < 0.75)
            warn += bad
            print(f"P1 {'WARNUNG' if bad else 'OK'} {d} Item {iid}: {q} Stück · Einstand Ø {per:.0f}c · Markt {ref:.0f}c · "
                  f"Faktor {f:.2f} (Tagesmittel {mean:.2f}, ×{rel:.2f}) · Erlös Ø {revq:.0f}c")
    print(f"ERGEBNIS: {warn} WARNUNG(EN)")
    sys.exit(1 if warn else 0)


if __name__ == "__main__":
    main()
