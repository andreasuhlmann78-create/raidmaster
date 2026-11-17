#!/bin/bash
# 12 Charaktere (6 Training wie Zeitberichte, 6 Gegenprobe andere Klassen), Forever 1–60, Bewertung = Zeit + 0,5 × Grinden
cd "$(dirname "$0")"
run(){ local d=$1 grp=$2 who=$3 env=$4; echo "$d $grp $who: $(env WORLDHOOK=$PWD/sim/world_hook.lua SIMDIR=$PWD/sim FOREVER=1 $env PACKDIR=/home/claude/lp31238/LevelPilot_Data timeout 1500 ./lua51 test26.lua $d 0 $who 2>&1 | grep -E 'Geschätzte Spielzeit|Zeitaufteilung' | tr '\n' ' ')"; }
for d in ${DIRS}; do
  run $d T "Orc WARRIOR Horde" "LVL=13 MAP=1413 PX=51.5 PY=30.3" & run $d T "Tauren WARRIOR Horde" "LVL=6 MAP=1412 PX=45 PY=55" &
  run $d T "Scourge PRIEST Horde" "LVL=6 MAP=1420 PX=61 PY=52" & wait
  run $d T "Human WARRIOR Alliance" "LVL=10 MAP=1429 PX=48 PY=42" & run $d T "NightElf HUNTER Alliance" "LVL=6 MAP=1438 PX=56 PY=60" &
  run $d T "Dwarf WARRIOR Alliance" "LVL=6 MAP=1426 PX=46 PY=52" & wait
  run $d G "Orc ROGUE Horde" "LVL=13 MAP=1413 PX=51.5 PY=30.3" & run $d G "Tauren DRUID Horde" "LVL=6 MAP=1412 PX=45 PY=55" &
  run $d G "Scourge MAGE Horde" "LVL=6 MAP=1420 PX=61 PY=52" & wait
  run $d G "Human MAGE Alliance" "LVL=10 MAP=1429 PX=48 PY=42" & run $d G "NightElf DRUID Alliance" "LVL=6 MAP=1438 PX=56 PY=60" &
  run $d G "Dwarf PALADIN Alliance" "LVL=6 MAP=1426 PX=46 PY=52" & wait
done
