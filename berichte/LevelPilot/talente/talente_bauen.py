#!/usr/bin/env python3
"""LevelPilot – Data/TalentBuilds.lua aus builds.py + Talent.csv/TalentTab (wowf) erzeugen und PRÜFEN.

Prüft je Klasse: 51 Punkte; jeder Punkt erlaubt in der Reihenfolge (Reihe t braucht 5*t Punkte im Baum vorher; Vorbedingung
mit Rang erfüllt; nicht über den Höchstrang); Talent gehört zur Klasse; Waffen-Alternativen im selben Baum, an der Stelle erlaubt.
Ausgabe: LP.TalentBuilds[KLASSE] = { { tab, reihe, spalte, ränge, "Satz de", "Satz en" [, alt = { {tab,reihe,spalte,{Unterklassen}}, … }] } }
(tab/reihe/spalte 1-basiert wie GetTalentInfo). Aufruf: python3 talente_bauen.py <ausgabe.lua>
"""
import csv, os, sys, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from builds import B
D = os.path.dirname(os.path.abspath(__file__))
T = {int(r["ID"]): r for r in csv.DictReader(open(os.path.join(D, "Talent.csv"), encoding="utf-8-sig"))}
TAB = {int(r["ID"]): r for r in csv.DictReader(open(os.path.join(D, "TalentTab-enUS.csv"), encoding="utf-8-sig"))}
SP = {r["SpellID"]: r for r in csv.DictReader(open(os.path.join(D, "TalentSpells.csv"), encoding="utf-8-sig"))}
KLASSE = {"WARRIOR": 1, "PALADIN": 2, "HUNTER": 4, "ROGUE": 8, "PRIEST": 16, "SHAMAN": 64, "MAGE": 128, "WARLOCK": 256, "DRUID": 1024}

def info(tid):
    t = T[tid]
    tab = TAB[int(t["TabID"])]
    ranks = sum(1 for i in range(9) if t[f"SpellRank_{i}"] not in ("0", ""))
    name = SP.get(t["SpellRank_0"], {}).get("Name_deDE") or f"#{tid}"
    return dict(mask=int(tab["ClassMask"]), tab=int(tab["OrderIndex"]) + 1, tier=int(t["TierID"]), col=int(t["ColumnIndex"]),
                max=ranks, pre=int(t["PrereqTalent_0"]), prerank=int(t["PrereqRank_0"]) + 1, name=name)

fehler = []
out = ["-- LevelPilot - eigene Level-Builds je Klasse (LP-N1 Punkt 1). Erzeugt mit berichte/LevelPilot/talente/talente_bauen.py",
       "-- aus builds.py (eigene Auswahl und eigene Begründungen) und den Talentbäumen WoW Forever (wago.tools, Zweig wowf,",
       "-- Build 1.60.1.70938). Je Eintrag: Baum, Reihe, Spalte (1-basiert wie GetTalentInfo), Ränge, Satz de, Satz en.",
       "", "local _, LP = ...", "LP.TalentBuilds = {"]
for klasse, liste in B.items():
    rang = collections.Counter(); proBaum = collections.Counter(); punkte = 0
    out.append(f"    {klasse} = {{")
    for e in liste:
        if e[0] == "WAFFE":
            _, alts, std, n, de, en = e
            ids = [std] + [a for a in alts if a != std]
        else:
            tid, n, de, en = e
            ids, alts = [tid], None
        i = info(ids[0])
        for tid in ids:
            j = info(tid)
            if j["mask"] != KLASSE[klasse]:
                fehler.append(f"{klasse}: Talent {tid} gehört nicht zur Klasse")
            if j["tab"] != i["tab"]:
                fehler.append(f"{klasse}: Alternative {tid} nicht im Baum von {ids[0]}")
            if proBaum[j["tab"]] < 5 * j["tier"] or j["max"] < n or (j["pre"] and rang[j["pre"]] < j["prerank"]):
                fehler.append(f"{klasse}: Alternative {tid} an dieser Stelle nicht erlaubt (Reihe/Ränge/Vorbedingung)")
        for k in range(n):
            punkte += 1
            if proBaum[i["tab"]] < 5 * i["tier"]:
                fehler.append(f"{klasse} Punkt {punkte} (Level {punkte + 9}): {i['name']} Reihe {i['tier'] + 1} braucht {5 * i['tier']} Punkte im Baum, vorhanden {proBaum[i['tab']]}")
            if i["pre"] and rang[i["pre"]] < i["prerank"]:
                fehler.append(f"{klasse} Punkt {punkte}: {i['name']} braucht Vorbedingung {info(i['pre'])['name']} {i['prerank']}")
            rang[ids[0]] += 1; proBaum[i["tab"]] += 1
            if rang[ids[0]] > i["max"]:
                fehler.append(f"{klasse}: {i['name']} über Höchstrang {i['max']}")
        esc = lambda s: s.replace("\\", "\\\\").replace('"', '\\"')
        alt = ""
        if alts:
            alt = ", alt = { " + ", ".join(f"{{ {info(a)['tab']}, {info(a)['tier'] + 1}, {info(a)['col'] + 1}, {{ {', '.join(map(str, subs))} }} }}" for a, subs in alts.items()) + " }"
        out.append(f'        {{ {i["tab"]}, {i["tier"] + 1}, {i["col"] + 1}, {n}, "{esc(de)}", "{esc(en)}"{alt} }},   -- {i["name"]}')
    out.append("    },")
    if punkte != 51:
        fehler.append(f"{klasse}: {punkte} Punkte statt 51")
    print(f"{klasse}: {punkte} Punkte, Bäume {dict(proBaum)}")
out.append("}")
if fehler:
    for f in fehler:
        print("FEHLER " + f)
    sys.exit(1)
open(sys.argv[1], "w", encoding="utf-8", newline="\n").write("\n".join(out) + "\n")
print("OK ->", sys.argv[1])
