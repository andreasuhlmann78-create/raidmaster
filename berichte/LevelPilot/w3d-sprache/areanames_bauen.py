#!/usr/bin/env python3
"""LevelPilot W3D – sprachfreie Unterzonen: Data/AreaNames.lua aus wago.tools AreaTable (je Client-Sprache).

Auftrag: offen-levelpilot.txt, Antwort W3D-Sprache (Supervisor 15.11. 21:48).
Eingabe: ein Ordner mit AreaTable-<locale>.csv (wago.tools db2 AreaTable, Zweig wowf, CSV-Export je Sprache:
deDE enUS esES esMX frFR itIT koKR ptBR ruRU zhCN zhTW). Gebraucht werden die Spalten ID, AreaName_lang, ParentAreaID.
Ausgewählt: die Städte mit Ebenen und alle Unterzonen darunter (rekursiv). Ausgabe: Lua-Tabelle
LP.AreaNames = { [ID] = { deDE = "…", enUS = "…", … } } mit Quelle, Build und Datum im Kopf. Keine Spieldateien im Addon:
nur Namen und Nummern aus der öffentlichen Tabelle (wie die Questdaten).

Aufruf: python3 areanames_bauen.py <csv-ordner> <ausgabe AreaNames.lua> --build <Build> [--extra ID,ID,…]
"""
import csv, os, sys, datetime

SPRACHEN = ["deDE", "enUS", "esES", "esMX", "frFR", "itIT", "koKR", "ptBR", "ruRU", "zhCN", "zhTW"]
# AreaTable-IDs der Städte (Classic): Unterstadt, Donnerfels, Orgrimmar, Eisenschmiede, Sturmwind, Darnassus
STAEDTE = [1497, 1638, 1637, 1537, 1519, 1657]


def lesen(pfad):
    with open(pfad, encoding="utf-8-sig", newline="") as f:
        r = csv.DictReader(f)
        spalten = {k.lower(): k for k in r.fieldnames or []}
        idk = spalten.get("id")
        namek = spalten.get("areaname_lang") or spalten.get("areaname")
        parentk = spalten.get("parentareaid")
        if not (idk and namek and parentk):
            raise SystemExit(f"FEHLER: {pfad}: Spalten ID, AreaName_lang, ParentAreaID fehlen ({r.fieldnames})")
        return {int(row[idk]): (row[namek], int(row[parentk] or 0)) for row in r if row[idk].strip()}


def main():
    if len(sys.argv) < 3 or "--build" not in sys.argv:
        print(__doc__); sys.exit(1)
    ordner, aus = sys.argv[1], sys.argv[2]
    build = sys.argv[sys.argv.index("--build") + 1]
    extra = [int(x) for x in sys.argv[sys.argv.index("--extra") + 1].split(",")] if "--extra" in sys.argv else []
    tabellen = {}
    for loc in SPRACHEN:
        p = os.path.join(ordner, f"AreaTable-{loc}.csv")
        if os.path.isfile(p):
            tabellen[loc] = lesen(p)
    if "enUS" not in tabellen:
        raise SystemExit("FEHLER: AreaTable-enUS.csv fehlt (Bezug für die Auswahl)")
    basis = tabellen["enUS"]
    kinder = {}
    for i, (_, parent) in basis.items():
        kinder.setdefault(parent, []).append(i)
    wahl, offen = set(), list(STAEDTE) + extra
    while offen:
        i = offen.pop()
        if i in wahl or i not in basis:
            continue
        wahl.add(i)
        offen += kinder.get(i, [])
    # Prüfung: derselbe Name darf in einer Sprache nicht zwei IDs meinen (sonst wäre der Schlüssel mehrdeutig)
    doppelt = []
    for loc, t in tabellen.items():
        seen = {}
        for i in sorted(wahl):
            n = t.get(i, ("", 0))[0]
            if n and n in seen and seen[n] != i:
                doppelt.append(f"{loc}: „{n}“ = {seen[n]} und {i}")
            seen.setdefault(n, i)
    stand = datetime.date.today().isoformat()
    with open(aus, "w", encoding="utf-8", newline="\n") as f:
        f.write("-- LevelPilot - sprachfreie Unterzonen (W3D): Unterzonen-Name in allen Client-Sprachen -> AreaTable-ID\n")
        f.write(f"-- Quelle: wago.tools db2 AreaTable, Zweig wowf, Build {build}, erzeugt {stand} mit\n")
        f.write("-- berichte/LevelPilot/w3d-sprache/areanames_bauen.py. Nur Städte mit Ebenen und ihre Unterzonen.\n")
        f.write(f"-- Sprachen: {', '.join(sorted(tabellen))} · Einträge: {len(wahl)}\n\nlocal _, LP = ...\nLP.AreaNames = {{\n")
        for i in sorted(wahl):
            teile = []
            for loc in SPRACHEN:
                n = tabellen.get(loc, {}).get(i, ("", 0))[0]
                if n:
                    teile.append(f'{loc} = "{n.replace(chr(92), chr(92) * 2).replace(chr(34), chr(92) + chr(34))}"')
            f.write(f"    [{i}] = {{ {', '.join(teile)} }},\n")
        f.write("}\n")
    print(f"{len(wahl)} Unterzonen, {len(tabellen)} Sprachen -> {aus}")
    for d in doppelt:
        print("WARNUNG doppelter Name " + d)


if __name__ == "__main__":
    main()
