"""ORT-1 O1: Gebietskarte (Ort je 1 % x 1 % der Zonenkarte) aus den Spieldateien -> LevelPilot_Data/Data/Orte.lua.
Je Spielversion im eigenen Kartenrahmen (Forever: wowf-UiMapAssignment, Era: classic-era). Zelle (i, j) = Kartenpunkt
(i + 0,5 %, j + 0,5 %) -> Welt -> 33-yd-Kartenstück -> AreaTable-ID (Schlüssel "ty_tx", siehe orte_probe.py).
Aufruf: python3 orte_bauen.py <Ausgabe Orte.lua>"""
import json, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import orte_probe as op

ZONEN = list(range(1411, 1459))      # Aussenzonen und Städte Kalimdor/Östliche Königreiche (uiMap 1411–1458)
N = 100

def zone_rows(geb, m):
    gz = geb.g.get(m)
    if not gz or gz[0] not in (0, 1):
        return None
    rows, hit = [], 0
    for j in range(N):            # y (Zeile)
        cells = []
        for i in range(N):        # x (Spalte)
            a = geb.at(m, i + 0.5, j + 0.5) or 0
            if a: hit += 1
            cells.append(a)
        # Lauflänge: "id" oder "id*n"
        out, k = [], 0
        while k < N:
            v, n = cells[k], 1
            while k + n < N and cells[k + n] == v: n += 1
            out.append(str(v) if n == 1 else "%d*%d" % (v, n))
            k += n
        rows.append(",".join(out))
    return ";".join(rows), hit

def main(out):
    used, data = set(), {}
    for fl in ("forever", "era"):
        geb = op.Gebiete(fl)
        data[fl] = {}
        for m in ZONEN:
            r = zone_rows(geb, m)
            if r and r[1] > 0:
                data[fl][m] = r[0]
                for part in r[0].replace(";", ",").split(","):
                    used.add(int(part.split("*")[0]))
        data[fl + "_area"] = geb.a
    lines = ["-- LevelPilot Data – Orte (Gebiets-ID je 1 % x 1 % der Zonenkarte), aus den Spieldateien (ADT, AreaTable), ORT-1, Datenpaket 1.6.3",
             "-- automatisch erzeugt mit berichte/LevelPilot/orte/orte_bauen.py; Zeilen = y 0..99, je Zeile x 0..99, \"id*n\" = n gleiche",
             "local D = LevelPilotData", "D.ORTE = { forever = {}, era = {} }", "D.ORTA = {}"]
    same = 0
    for fl in ("forever", "era"):
        for m in sorted(data[fl]):
            if fl == "era" and data["forever"].get(m) == data[fl][m]:
                same += 1                  # gleich wie Forever: im Spiel D.ORTE.forever nehmen
                continue
            lines.append('D.ORTE.%s[%d]="%s"' % (fl, m, data[fl][m]))
    lines.insert(4, "-- Era: nur Zonen, die sich von Forever unterscheiden (%d gleich); sonst gilt D.ORTE.forever" % same)
    names = {}
    for fl in ("forever", "era"):
        for k, a in data[fl + "_area"].items():
            k = int(k)
            if k in used and k not in names:
                names[k] = a
    for k in sorted(names):
        a = names[k]
        lines.append('D.ORTA[%d]={%d,%d,"%s"}' % (k, a.get("eltern", 0), a.get("stufe", 0), a["name"].replace('"', "'")))
    open(out, "w", encoding="utf-8").write("\n".join(lines) + "\n")
    print("Zonen forever", len(data["forever"]), "era", len(data["era"]), "Gebiete", len(names), "Bytes", os.path.getsize(out))

if __name__ == "__main__":
    main(sys.argv[1])
