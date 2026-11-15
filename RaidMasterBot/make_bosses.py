#!/usr/bin/env python3
"""Erzeugt bosses.json für die Rekord-Tafeln der Ruhmeshalle (ab Bot 1.5.136) aus den Raid-Daten des Addons.

Quelle: RaidMaster/Data.lua (Molten Core, eigene Raids von WoW Forever) und RaidMaster/RaidData.lua (alle anderen
Raids, Encounter-IDs aus DBM). Übernommen werden nur Raids, die auf WoW Forever laufen (games enthält "forever"), und
von jedem Schlüssel nur die erste Fassung (z. B. Naxxramas Classic, nicht Wotlk).
Je Raid: Schlüssel und Bosse in der Reihenfolge des Addons (Encounter-IDs + deutscher Name). Eigene Raids von WoW
Forever (Barrow Deeps, Hyjalgipfel) haben noch keine Bossliste – das Addon lernt die Bosse beim ersten Kampf.

Dungeons (ab 1.5.137, Entscheid des Nutzers 15.11.2026 15:15: "hole dir die Infos wegen Dungeons und Level"):
- Encounter-IDs, Instanz-IDs und Boss-Reihenfolge aus Deadly Boss Mods (github.com/DeadlyBossMods/dbm-dungeons):
  DBM-Party-Vanilla (Classic + Shared; ohne Retail-Fassungen und ohne Season of Discovery) und DBM-Party-Forever
  (die 9 neuen Dungeons von WoW Forever). Reihenfolge = Ladereihenfolge der .toc. Steht "IsClassic() and X or Y",
  werden beide IDs übernommen (eine ID gehört immer genau zu einem Boss, mehr IDs schaden nicht).
- Deutsche Namen und Levelbereiche (Empfehlung, keine Mindeststufe):
  neue Forever-Dungeons: Blizzard (news.blizzard.com/de-de/article/24301455),
  klassische Dungeons: PC Games (pcgames.de, "WoW Forever: Alle Dungeons und ihre Level im Überblick"), gleiche Werte
  wie warcrafttavern.com/forever/guides/dungeons. Mehrteilige Dungeons (Kloster, Düsterbruch, Stratholme) haben eine
  Tafel; Level = niedrigster bis höchster Flügel.
- Die Dungeon-Daten werden nur mit --dbm <Ordner von dbm-dungeons> neu erzeugt, sonst aus bosses.json übernommen.

Aufruf (im Repo):  python3 RaidMasterBot/make_bosses.py [--dbm <Pfad>]  -> schreibt RaidMasterBot/bosses.json
                   python3 RaidMasterBot/make_bosses.py --check         -> Fehlercode 1, wenn bosses.json veraltet ist
"""
from __future__ import annotations

import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ADDON = os.path.join(HERE, "..", "RaidMaster")
OUT = os.path.join(HERE, "bosses.json")
START = re.compile(r"^(?:Add|Data\.AddRaid)\(\{")
KEY = re.compile(r'\bkey = "([a-z0-9]+)"')
GAMES = re.compile(r'\bgames = "([^"]*)"')
BOSS = re.compile(r"^\s*\{ e = \{ ([0-9, ]+) \}")
DE = re.compile(r'\bde = "((?:[^"\\]|\\.)*)"')
NAME_L = re.compile(r'\bname = L\["((?:[^"\\]|\\.)*)"\]')


def blocks(text: str):
    """Je Raid-Definition: (Kopfzeilen bis 'bosses', Bosszeilen)."""
    cur = None
    for line in text.splitlines():
        if START.match(line):
            if cur:
                yield cur
            cur = [line]
        elif cur is not None:
            cur.append(line)
    if cur:
        yield cur


def parse(text: str) -> list[dict]:
    out = []
    for lines in blocks(text):
        head = " ".join(lines[:3])
        k, g = KEY.search(head), GAMES.search(head)
        if not k:
            continue
        bosses = []
        for ln in lines:
            m = BOSS.match(ln)
            if not m:
                continue
            ids = [int(x) for x in m.group(1).replace(" ", "").split(",") if x]
            names = DE.findall(ln)
            name = names[-1] if names else None                  # "de = …" am Ende der Bosszeile
            if not name:
                nl = NAME_L.search(ln)
                name = nl.group(1) if nl else f"Boss {ids[0]}"
            bosses.append({"e": ids, "n": name})
        out.append({"key": k.group(1), "games": (g.group(1) if g else "").split(), "bosses": bosses})
    return out


# DBM-Ordner -> (Schlüssel, deutscher Name, Level von, Level bis)
DUNGEONS = {
    "DBM-Party-Vanilla/Classic/RagefireChasm": ("rfc", "Ragefireabgrund", 13, 18),
    "DBM-Party-Vanilla/Shared/WailingCaverns": ("wc", "Höhlen des Wehklagens", 15, 24),
    "DBM-Party-Vanilla/Shared/Deadmines": ("dm", "Die Todesminen", 17, 26),
    "DBM-Party-Vanilla/Classic/Shadowfangkeep": ("sfk", "Burg Schattenfang", 20, 30),
    "DBM-Party-Vanilla/Classic/BlackfathomDeeps": ("bfd", "Tiefschwarze Grotte", 24, 32),
    "DBM-Party-Vanilla/Classic/StormwindStockaid": ("stocks", "Das Verlies", 24, 32),
    "DBM-Party-Vanilla/Shared/Gnomeregan": ("gnomer", "Gnomeregan", 29, 38),
    "DBM-Party-Vanilla/Classic/RazorfenKraul": ("rfk", "Kral der Klingenhauer", 29, 38),
    "DBM-Party-Vanilla/Shared/ScarletMonastery_Old": ("sm", "Scharlachrotes Kloster", 30, 46),
    "DBM-Party-Vanilla/Classic/RazorfenDowns": ("rfd", "Hügel der Klingenhauer", 37, 46),
    "DBM-Party-Vanilla/Shared/Uldaman": ("ulda", "Uldaman", 41, 51),
    "DBM-Party-Vanilla/Shared/ZulFarrak": ("zf", "Zul'Farrak", 44, 54),
    "DBM-Party-Vanilla/Shared/Maraudon": ("mara", "Maraudon", 46, 55),
    "DBM-Party-Vanilla/Shared/SunkenTemple": ("st", "Versunkener Tempel", 50, 60),
    "DBM-Party-Vanilla/Shared/BlackrockDepths": ("brd", "Schwarzfelstiefen", 52, 60),
    "DBM-Party-Vanilla/Shared/DireMaul": ("dire", "Düsterbruch", 54, 60),
    "DBM-Party-Vanilla/Shared/LowerBlackrockSpire": ("lbrs", "Untere Schwarzfelsspitze", 55, 60),
    "DBM-Party-Vanilla/Shared/Stratholme": ("strat", "Stratholme", 58, 60),
    "DBM-Party-Vanilla/Shared/Scholomance_Old": ("scholo", "Scholomance", 58, 60),
    "DBM-Party-Vanilla/Classic/UpperBlackrockSpire": ("ubrs", "Obere Schwarzfelsspitze", 59, 60),
    "DBM-Party-Forever/HallofThanes": ("thanen", "Halle der Thanen", 13, 18),
    "DBM-Party-Forever/RuinsofLordaeron": ("lordaeron", "Ruinen von Lordaeron", 15, 20),
    "DBM-Party-Forever/ExcavationSite": ("ausgrabung", "Ausgrabungsstätte", 24, 29),
    "DBM-Party-Forever/CityofDalaran": ("dalaran", "Stadt Dalaran", 28, 33),
    "DBM-Party-Forever/TheDrownedCity": ("versunken", "Die Versunkene Stadt", 35, 40),
    "DBM-Party-Forever/KroldokStronghold": ("kroldok", "Festung Krol'dok", 40, 45),
    "DBM-Party-Forever/AlcazPrison": ("alcaz", "Alcaz-Gefängnis", 48, 53),
    "DBM-Party-Forever/BlackmawHold": ("schwarzschlund", "Schwarzschlundfeste", 55, 60),
    "DBM-Party-Forever/TheShapersTerrace": ("former", "Terrasse des Formers", 58, 60),
}
TOCS = ("DBM-Party-Vanilla/DBM-Party-Vanilla.toc", "DBM-Party-Forever/DBM-Party-Forever.toc")
ENC = re.compile(r"^mod:SetEncounterID\((.*)\)", re.M)
ZONE = re.compile(r"^mod:SetZone\((\d+)\)", re.M)
NEWMOD = re.compile(r'DBM:NewMod\("?([^",]+)"?,')
LOCNAME = re.compile(r'GetModLocalization\("([^"]+)"\)\s*L:SetGeneralLocalization\{\s*name\s*=\s*"((?:[^"\\]|\\.)*)"')


def loads_on_forever(tag: str) -> bool:
    """Toc-Bedingung wie DBM: WoW Forever lädt wie Classic ("vanilla")."""
    m = re.search(r"\[(Allow|Exclude)LoadGameType ([^\]]*)\]", tag or "")
    if not m:
        return True
    kinds = {x.strip() for x in m.group(2).split(",")}
    return ("vanilla" in kinds) if m.group(1) == "Allow" else ("vanilla" not in kinds)


def build_dungeons(dbm_dir: str) -> list[dict]:
    names = {}
    for loc in ("DBM-Party-Vanilla/Classic/localization.en.lua", "DBM-Party-Forever/localization.en.lua"):
        with open(os.path.join(dbm_dir, loc), encoding="utf-8") as f:
            names.update(dict(LOCNAME.findall(f.read())))
    found: dict[str, list[dict]] = {}
    zones: dict[str, set] = {}
    for toc in TOCS:
        base = os.path.dirname(toc)
        with open(os.path.join(dbm_dir, toc), encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "localization" in line or not line.split()[0].endswith(".lua"):
                    continue
                rel, tag = line.split(" ", 1) if " " in line else (line, "")
                if not loads_on_forever(tag):
                    continue
                path = base + "/" + rel.replace("\\", "/")
                folder = os.path.dirname(path)
                if folder not in DUNGEONS:
                    continue
                with open(os.path.join(dbm_dir, path), encoding="utf-8") as f2:
                    src = f2.read()
                enc, mod = ENC.search(src), NEWMOD.search(src)
                if not enc or not mod:
                    continue                                  # z. B. seltene Gegner ohne Encounter
                ids = list(dict.fromkeys(int(x) for x in re.findall(r"\b(\d+)\b", enc.group(1))))
                z = ZONE.search(src)
                if z:
                    zones.setdefault(folder, set()).add(int(z.group(1)))
                # Name: englische DBM-Lokalisierung; bei Mods mit Journal-Nummer (z. B. NewMod(474, …)) aus dem
                # Dateinamen ("LadyAnacondra" -> "Lady Anacondra"). Nur Ersatz: die Tafel zeigt den Namen aus dem Spiel.
                fname = re.sub(r"(?<=[a-z])(the|of)(?=[A-Z])", r" \1 ", os.path.splitext(os.path.basename(path))[0])
                fname = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", " ", fname).replace("  ", " ").strip()
                found.setdefault(folder, []).append({"e": ids, "n": names.get(mod.group(1), fname)})
    out = []
    for folder, (key, name, lo, hi) in DUNGEONS.items():
        if folder not in found:
            raise SystemExit(f"DBM-Ordner ohne Bosse: {folder}")
        out.append({"key": "dg-" + key, "name": name, "lvl": [lo, hi], "zone": sorted(zones.get(folder, [])),
                    "bosses": found[folder]})
    out.sort(key=lambda d: (d["lvl"][0], d["lvl"][1], d["name"]))
    return out


def build(addon_dir: str = ADDON) -> dict:
    raids, seen = [], set()
    for fn in ("Data.lua", "RaidData.lua"):                     # Data.lua zuerst: MC und die eigenen Forever-Raids
        with open(os.path.join(addon_dir, fn), encoding="utf-8") as f:
            for r in parse(f.read()):
                if "forever" not in r["games"] or r["key"] in seen:
                    continue
                seen.add(r["key"])
                raids.append({"key": r["key"], "bosses": r["bosses"]})
    return {"_info": "Erzeugt von make_bosses.py aus RaidMaster/Data.lua und RaidData.lua (Raids) und Deadly Boss Mods "
                     "(Dungeons, englische Bossnamen) – nicht von Hand ändern. Nur WoW Forever. Quellen der Dungeon-"
                     "Namen und Level: siehe make_bosses.py.",
            "raids": raids}


def dump(d: dict) -> str:
    return json.dumps(d, ensure_ascii=False, indent=1) + "\n"


def current_dungeons() -> list:
    try:
        with open(OUT, encoding="utf-8") as f:
            return json.load(f).get("dungeons") or []
    except (OSError, ValueError):
        return []


def main(argv) -> int:
    d = build()
    d["dungeons"] = (build_dungeons(argv[argv.index("--dbm") + 1]) if "--dbm" in argv else current_dungeons())
    want = dump(d)
    if "--check" in argv:
        try:
            with open(OUT, encoding="utf-8") as f:
                have = f.read()
        except OSError:
            have = ""
        if have != want:
            print("bosses.json ist veraltet – python3 RaidMasterBot/make_bosses.py ausführen.")
            return 1
        print("bosses.json ist aktuell.")
        return 0
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(want)
    print(f"bosses.json geschrieben ({len(d['raids'])} Raids, {len(d['dungeons'])} Dungeons, "
          f"{sum(len(x['bosses']) for x in d['dungeons'])} Dungeon-Bosse).")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
