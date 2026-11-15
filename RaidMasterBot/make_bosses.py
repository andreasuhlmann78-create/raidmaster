#!/usr/bin/env python3
"""Erzeugt bosses.json für die Rekord-Tafeln der Ruhmeshalle (ab Bot 1.5.136) aus den Raid-Daten des Addons.

Quelle: RaidMaster/Data.lua (Molten Core, eigene Raids von WoW Forever) und RaidMaster/RaidData.lua (alle anderen
Raids, Encounter-IDs aus DBM). Übernommen werden nur Raids, die auf WoW Forever laufen (games enthält "forever"), und
von jedem Schlüssel nur die erste Fassung (z. B. Naxxramas Classic, nicht Wotlk).
Je Raid: Schlüssel und Bosse in der Reihenfolge des Addons (Encounter-IDs + deutscher Name). Eigene Raids von WoW
Forever (Barrow Deeps, Hyjalgipfel) haben noch keine Bossliste – das Addon lernt die Bosse beim ersten Kampf.

Aufruf (im Repo):  python3 RaidMasterBot/make_bosses.py           -> schreibt RaidMasterBot/bosses.json
                   python3 RaidMasterBot/make_bosses.py --check   -> Fehlercode 1, wenn bosses.json veraltet ist
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


def build(addon_dir: str = ADDON) -> dict:
    raids, seen = [], set()
    for fn in ("Data.lua", "RaidData.lua"):                     # Data.lua zuerst: MC und die eigenen Forever-Raids
        with open(os.path.join(addon_dir, fn), encoding="utf-8") as f:
            for r in parse(f.read()):
                if "forever" not in r["games"] or r["key"] in seen:
                    continue
                seen.add(r["key"])
                raids.append({"key": r["key"], "bosses": r["bosses"]})
    return {"_info": "Erzeugt von make_bosses.py aus RaidMaster/Data.lua und RaidData.lua – nicht von Hand ändern. "
                     "Nur Raids von WoW Forever; Bosse in der Reihenfolge des Addons.",
            "raids": raids}


def dump(d: dict) -> str:
    return json.dumps(d, ensure_ascii=False, indent=1) + "\n"


def main(argv) -> int:
    want = dump(build())
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
    print(f"bosses.json geschrieben ({len(json.loads(want)['raids'])} Raids).")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
