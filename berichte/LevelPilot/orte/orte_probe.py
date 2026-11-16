"""ORT-1 O1 Probe: NPC-Ort (Datenpaket, Forever-Rahmen) -> Gebiets-ID aus den Spieldateien (Forever und Era)."""
import csv, json, re, sys
R = "/home/claude/raidmaster"
GEB = R + "/shared/werkzeuge/strassen/daten/gebiete/"
UI = {"forever": R + "/berichte/LevelPilot/strassen/UiMapAssignment-wowf-1.60.1.csv",
      "era": R + "/berichte/LevelPilot/strassen/UiMapAssignment-classic-era.csv"}
# Forever-Rahmen -> Era (Umkehr von forever_maps.lua: x' = sx*x+ox)
FM = {1412: (0.8348002068, 7.0074531087, 0.8349418225, 13.1538732772), 1423: (0.8997577709, -1.6464926382, 0.9004358591, -3.7790494664),
      1433: (0.9999996626, -5.0863745842, 1.0, 0.0), 1453: (0.7736792385, 19.6804496463, 0.7738268670, 24.4332878075)}

def grenzen(pfad):
    g = {}
    for r in csv.DictReader(open(pfad, encoding="utf-8")):
        m = int(r["UiMapID"])
        if m in g or r["WMOGroupID"] not in ("0", ""):
            continue
        g[m] = (int(r["MapID"]), float(r["Region_0"]), float(r["Region_1"]), float(r["Region_3"]), float(r["Region_4"]))
    return g

def welt(gz, x, y):
    inst, minx, miny, maxx, maxy = gz
    return inst, maxx - (y / 100.0) * (maxx - minx), maxy - (x / 100.0) * (maxy - miny)

class Gebiete:
    def __init__(self, fl):
        self.k = json.load(open(GEB + "gebiete_%s.json" % fl))["karten"]
        self.a = json.load(open(GEB + "areatable_%s.json" % fl))
        self.g = grenzen(UI[fl])
    def at(self, m, x, y):
        gz = self.g.get(m)
        if not gz: return None
        inst, wx, wy = welt(gz, x, y)
        ty = (17066.667 - wx) / 533.333
        tx = (17066.667 - wy) / 533.333
        key = "%d_%d" % (int(ty), int(tx))   # Schlüssel "Zeile_Spalte" = ty_tx (geprüft: Nordhain 48_32)
        tile = self.k.get(str(inst), {}).get(key)
        if not tile: return None
        row = int((ty - int(ty)) * 16); col = int((tx - int(tx)) * 16)
        return tile[row * 16 + col]
    def name(self, aid):
        a = self.a.get(str(aid)); return a and a["name"]

def to_era(m, x, y):
    f = FM.get(m)
    if not f: return x, y
    return (x - f[1]) / f[0], (y - f[3]) / f[2]

if __name__ == "__main__":
    fo, er = Gebiete("forever"), Gebiete("era")
    for m, x, y, what in [(1429, 48.9, 41.6, "McBride"), (1429, 43.8, 65.8, "Farley Goldhain"), (1411, 43.3, 68.5, "Tal der Prüfungen"),
                          (1412, 44.2, 76.1, "Camp Narache"), (1420, 30.2, 71.7, "Todesend"), (1438, 58.6, 44.6, "Schattenhain"),
                          (1426, 29.9, 71.2, "Coldridge")]:
        a1 = fo.at(m, x, y); xe, ye = to_era(m, x, y); a2 = er.at(m, xe, ye)
        print(what, "Forever", a1, fo.name(a1), "| Era", a2, er.name(a2))
