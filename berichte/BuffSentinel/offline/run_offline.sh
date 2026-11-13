#!/bin/sh
# BuffSentinel – Offline-Testroutine (TU9) für alle Versionen und Sprachen.
#   sh berichte/BuffSentinel/offline/run_offline.sh [download/BuffSentinel-x.y.z.zip]
# Ohne Angabe: die neueste download/BuffSentinel-*.zip im raidmaster-Repo. Braucht Lua 5.1–5.4 (lua5.1, luajit, lua);
# ohne Lua: python3 berichte/BuffSentinel/offline/run_offline.py (lupa).
HERE="$(cd "$(dirname "$0")" && pwd)"
REPO="$(cd "$HERE/../../.." && pwd)"
ZIP="${1:-$(ls "$REPO"/download/BuffSentinel-*.zip 2>/dev/null | sort -V | tail -1)}"
[ -f "$ZIP" ] || { echo "Keine BuffSentinel-ZIP gefunden"; exit 2; }
TMP="$(mktemp -d)"; unzip -q "$ZIP" -d "$TMP" || exit 2
LUA=""
for c in lua5.1 luajit lua5.4 lua; do if command -v "$c" >/dev/null 2>&1; then LUA="$c"; break; fi; done
if [ -z "$LUA" ]; then echo "Kein Lua gefunden – python3 $HERE/run_offline.py verwenden"; rm -rf "$TMP"; exit 2; fi
fail=0
for fl in forever era tbc; do
  for lo in deDE enUS; do
    BS_ROOT="$TMP/BuffSentinel/" BS_TESTS="$HERE" "$LUA" "$HERE/run_offline.lua" "$fl" "$lo" || fail=1
  done
done
rm -rf "$TMP"
[ $fail -eq 0 ] && echo "ALLE KOMBINATIONEN: PASS" || echo "ALLE KOMBINATIONEN: FAIL"
exit $fail
