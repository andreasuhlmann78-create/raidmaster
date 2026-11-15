#!/usr/bin/env python3
"""LevelPilot W3D – sprachfreie Unterzonen: Data/AreaNames.lua aus wago.tools AreaTable + WMOAreaTable (je Client-Sprache).

Auftrag: offen-levelpilot.txt, Antwort W3D-Sprache (Supervisor 15.11. 21:48) und Antwort Frage Tabelle (22:03):
die Viertel von Unterstadt (und Räume von Orgrimmar/Eisenschmiede) stehen nur in WMOAreaTable; dieselbe Ebene kann in zwei
Gebäuden (WMOID 1150/20736) verschiedene Namen tragen ("Magieviertel" / "Das Magieviertel").

Schlüssel:
- AreaTable-Unterzone einer Stadt:  "<ID>"                       (z. B. "1638" Donnerfels selbst, Kinder mit eigener ID)
- WMOAreaTable-Raum:                "<AreaTableID>:<enUS-Name>"  (gleiche AreaTableID + gleicher enUS-Name = gleiche Ebene)
Eingabe: Ordner mit AreaTable-<locale>.csv (ID, AreaName_lang, ParentAreaID) und WMOAreaTable-<locale>.csv
(ID, AreaName_lang, WMOID, WMOGroupID, AreaTableID), Zweig wowf. Ausgabe Lua:
LP.AreaNames = { ["<Schlüssel>"] = { deDE = "Anzeige", enUS = "…", …, alt = { weitere Namen derselben Ebene } } }
Nur Namen und Nummern aus der öffentlichen Tabelle (wie die Questdaten), keine Spieldateien.

Aufruf: python3 areanames_bauen.py <csv-ordner> <ausgabe AreaNames.lua> --build <Build> [--extra ID,ID,…]
"""
import csv, os, sys, datetime, collections

SPRACHEN = ["deDE", "enUS", "esES", "esMX", "frFR", "itIT", "koKR", "ptBR", "ruRU", "zhCN", "zhTW"]
# AreaTable-IDs der Städte (Classic): Unterstadt, Donnerfels, Orgrimmar, Eisenschmiede, Sturmwind, Darnassus
STAEDTE = [1497, 1638, 1637, 1537, 1519, 1657]


def lesen(pfad, spalten_noetig):
    with open(pfad, encoding="utf-8-sig", newline="") as f:
        r = csv.DictReader(f)
        fehlt = [s for s in spalten_noetig if s not in (r.fieldnames or [])]
        if fehlt:
            raise SystemExit(f"FEHLER: {pfad}: Spalten {fehlt} fehlen ({r.fieldnames})")
        return [row for row in r if (row.get("ID") or "").strip()]


def lua_str(s):
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'


def main():
    if len(sys.argv) < 3 or "--build" not in sys.argv:
        print(__doc__); sys.exit(1)
    ordner, aus = sys.argv[1], sys.argv[2]
    build = sys.argv[sys.argv.index("--build") + 1]
    extra = [int(x) for x in sys.argv[sys.argv.index("--extra") + 1].split(",")] if "--extra" in sys.argv else []
    area, wmo = {}, {}
    for loc in SPRACHEN:
        p = os.path.join(ordner, f"AreaTable-{loc}.csv")
        if os.path.isfile(p):
            area[loc] = {int(r["ID"]): (r["AreaName_lang"], int(r["ParentAreaID"] or 0))
                         for r in lesen(p, ["ID", "AreaName_lang", "ParentAreaID"])}
        p = os.path.join(ordner, f"WMOAreaTable-{loc}.csv")
        if os.path.isfile(p):
            wmo[loc] = {int(r["ID"]): (r["AreaName_lang"], int(r["AreaTableID"] or 0))
                        for r in lesen(p, ["ID", "AreaName_lang", "AreaTableID"])}
    if "enUS" not in area or "enUS" not in wmo:
        raise SystemExit("FEHLER: AreaTable-enUS.csv und WMOAreaTable-enUS.csv werden gebraucht (Bezug für die Schlüssel)")
    # 1) Städte und ihre AreaTable-Unterzonen (rekursiv)
    kinder = collections.defaultdict(list)
    for i, (_, parent) in area["enUS"].items():
        kinder[parent].append(i)
    gebiete, offen = set(), list(STAEDTE) + extra
    while offen:
        i = offen.pop()
        if i in gebiete or i not in area["enUS"]:
            continue
        gebiete.add(i)
        offen += kinder.get(i, [])
    eintraege = {}          # Schlüssel -> { loc: [Namen] }
    def dazu(key, loc, name):
        if not name:
            return
        e = eintraege.setdefault(key, collections.defaultdict(list))
        if name not in e[loc]:
            e[loc].append(name)
    for i in gebiete:
        for loc, t in area.items():
            dazu(str(i), loc, t.get(i, ("", 0))[0])
    # 2) WMO-Räume dieser Gebiete: Schlüssel = AreaTableID + enUS-Name; alle Namen je Sprache sammeln
    for wid, (en, aid) in wmo["enUS"].items():
        if aid not in gebiete or not en:
            continue
        key = f"{aid}:{en}"
        for loc, t in wmo.items():
            dazu(key, loc, t.get(wid, ("", 0))[0])
    # 3) Prüfung: derselbe Name in einer Sprache für verschiedene Schlüssel
    namen = collections.defaultdict(set)
    for key, e in eintraege.items():
        for loc, ns in e.items():
            for n in ns:
                namen[(loc, n)].add(key)
    doppelt = sorted((loc, n, sorted(ks)) for (loc, n), ks in namen.items() if len(ks) > 1)
    stand = datetime.date.today().isoformat()
    with open(aus, "w", encoding="utf-8", newline="\n") as f:
        f.write("-- LevelPilot - sprachfreie Unterzonen (W3D): Unterzonen-/Raum-Name in allen Client-Sprachen -> Schluessel\n")
        f.write(f"-- Quelle: wago.tools db2 AreaTable + WMOAreaTable, Zweig wowf, Build {build}, erzeugt {stand} mit\n")
        f.write("-- berichte/LevelPilot/w3d-sprache/areanames_bauen.py. Nur Staedte mit Ebenen (Unterstadt, Donnerfels, Orgrimmar,\n")
        f.write("-- Eisenschmiede, Sturmwind, Darnassus) und ihre Unterzonen/Raeume. Schluessel: \"<AreaID>\" bzw. \"<AreaID>:<enUS-Name>\".\n")
        f.write(f"-- Sprachen: {', '.join(sorted(area))} · Eintraege: {len(eintraege)} · gleiche Namen fuer mehrere Schluessel: {len(doppelt)}\n")
        f.write("\nlocal _, LP = ...\nLP.AreaNames = {\n")
        for key in sorted(eintraege, key=lambda k: (int(k.split(":")[0]), k)):
            e = eintraege[key]
            teile, alt = [], []
            for loc in SPRACHEN:
                ns = e.get(loc) or []
                if ns:
                    teile.append(f"{loc} = {lua_str(ns[0])}")
                    alt += [n for n in ns[1:] if n not in alt]
            if alt:
                teile.append("alt = { " + ", ".join(lua_str(n) for n in alt) + " }")
            f.write(f"    [{lua_str(key)}] = {{ {', '.join(teile)} }},\n")
        f.write("}\n")
    print(f"{len(gebiete)} Gebiete, {len(eintraege)} Schlüssel, {len(area)} Sprachen -> {aus}")
    for loc, n, ks in doppelt[:40]:
        print(f"HINWEIS gleicher Name {loc} „{n}“ -> {ks} (im Spiel gilt der kleinste Schlüssel)")
    if len(doppelt) > 40:
        print(f"… und {len(doppelt) - 40} weitere")


if __name__ == "__main__":
    main()
