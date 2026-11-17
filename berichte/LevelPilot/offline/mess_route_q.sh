#!/bin/bash
# ROUTE-Q: 6 Völker × Forever/Era, virtuelle Reise 1–60 (lua/mess_route_q.lua, Nachbau lua/mock2.lua, echte Kartengrenzen lua/sim/).
# Aufruf: PACKDIR=<LevelPilot_Data> [LUA51=lua51] bash mess_route_q.sh <LevelPilot-Ordner (absolut)>
cd "$(dirname "$0")/lua"
A=$1
L=${LUA51:-lua51}
run(){ env $1 LVL=1 MAP=$3 PX=$4 PY=$5 PACKDIR=${PACKDIR:?LevelPilot_Data-Ordner} timeout 2400 $L mess_route_q.lua $A 0 $2 WARRIOR $6 2>/dev/null; }
for fl in FOREVER=1 FLAVOR=era; do
  run $fl Human 1429 48.2 42.9 Alliance & run $fl Dwarf 1426 29.9 71.2 Alliance & wait
  run $fl NightElf 1438 58.6 44.6 Alliance & run $fl Orc 1411 43.3 68.5 Horde & wait
  run $fl Scourge 1420 30.2 71.7 Horde & run $fl Tauren 1412 44.2 76.1 Horde & wait
done
