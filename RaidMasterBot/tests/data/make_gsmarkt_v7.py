#!/usr/bin/env python3
"""Erzeugt gsmarkt_v7_export.txt: eine echte Export-Zeile von shared/GoldSentinelMarkt.lua (Version 7) für die Bot-Tests
(KEEP90 / D-KERN1: "eine v7-Exportzeile aus shared/tests als Eingabe").

Nimmt die Lua-Nachbildung aus shared/tests/test_goldsentinelmarkt.py (MOCK, Client) und den Ablauf des v7-Tests:
6108 Items mit Zufallswerten (Samen 7), zwei Feeds im Abstand von 1200 s. Keine Namen (die Lua-Datei exportiert keine).
Braucht lupa (pip install lupa) – nur zum Erzeugen; die Bot-Tests lesen die fertige Datei.
Aufruf im Repo: python3 RaidMasterBot/tests/data/make_gsmarkt_v7.py
"""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
TEST = ROOT / "shared/tests/test_goldsentinelmarkt.py"
src = TEST.read_text(encoding="utf-8")
head = src[:src.index("\ndef set_auctions(")]                 # MOCK, check, Client – ohne die Prüfungen
ns = {"__file__": str(TEST)}
exec(compile(head, str(TEST), "exec"), ns)
c = ns["Client"]("Fixture", 51)
c.run('DBF = {}; GoldSentinelMarkt.Attach("AHSentinel", DBF)')
c.run("""
math.randomseed(7)
ITEMS = {}
for i = 1, 6108 do ITEMS[2000 + i*3] = { preis = math.random(5, 2000000), menge = math.random(1,200), n = math.random(1,40), abg = (i % 2 == 0) and math.random(0,30) or nil, abgV = 2 } end
GoldSentinelMarkt.Feed("AHSentinel", TIME, 21102, ITEMS, 1800)
while GoldSentinelMarkt.feedJob do GoldSentinelMarkt.FeedPortion(4) end
GoldSentinelMarkt.lastFull = nil
GoldSentinelMarkt.Feed("AHSentinel", TIME + 1200, 21102, ITEMS, 1200)
while GoldSentinelMarkt.feedJob do GoldSentinelMarkt.FeedPortion(4) end
""")
line = c.ev("GoldSentinelMarkt.store.export[#GoldSentinelMarkt.store.export]")
ver = c.ev("GoldSentinelMarkt.VERSION")
assert ver == 7, ver
assert line.startswith("GSMARKT1|1|"), line[:30]
out = Path(__file__).with_name("gsmarkt_v7_export.txt")
out.write_text(line + "\n", encoding="utf-8")
print(f"{out.name}: {len(line)} Zeichen, Kopf {line[:60]}")
