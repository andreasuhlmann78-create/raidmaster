#!/usr/bin/env bash
# MN8: Blizzard-API-Zugang auf dem Bot-Server eintragen und die Messung starten (nur lesen).
# Auf dem Server (SSH) ausführen:
#   curl -fsSL https://raw.githubusercontent.com/andreasuhlmann78-create/raidmaster/main/RaidMasterBot/blizzard_zugang.sh | sudo bash
# Zugang neu eingeben (z. B. nach "Antwortcode 401"):  … | sudo bash -s neu
# Fragt Client-ID und Geheimnis unsichtbar ab, speichert sie NUR in /opt/raidmaster/config.json (nie im Repo, nie im
# Protokoll), führt blizzard_api_check.py aus und legt den Bericht unter /opt/raidmaster/data/mn8-bericht.txt ab.
set -euo pipefail
DIR="/opt/raidmaster"; CFG="$DIR/config.json"
[ "$(id -u)" -eq 0 ] || { echo "Bitte mit sudo ausführen." >&2; exit 1; }
[ -f "$CFG" ] || { echo "$CFG fehlt." >&2; exit 1; }
PY="$DIR/.venv/bin/python"; [ -x "$PY" ] || PY="python3"
read -rp "Realm-Name (oder Teil davon), leer = alle: " REALM < /dev/tty
NEU="${1:-}"
if [ "$NEU" = "neu" ] || ! "$PY" -c "import json,sys;c=json.load(open('$CFG'));sys.exit(0 if c.get('blizzard_client_id') and c.get('blizzard_client_secret') else 1)"; then
  echo "Client-ID und Geheimnis von develop.battle.net (API-Zugang) einfügen – die Eingabe bleibt unsichtbar."
  read -rsp "Client-ID: " CID < /dev/tty; echo
  CID="$(printf '%s' "$CID" | tr -cd '[:alnum:]')"
  echo "Client-ID: ${#CID} Zeichen erkannt (erwartet 32)."
  read -rsp "Client-Geheimnis: " SEC < /dev/tty; echo
  SEC="$(printf '%s' "$SEC" | tr -cd '[:alnum:]')"
  echo "Client-Geheimnis: ${#SEC} Zeichen erkannt (erwartet 32)."
  cp -p "$CFG" "$CFG.vor-blizzard"
  BZ_ID="$CID" BZ_SEC="$SEC" "$PY" - "$CFG" <<'PY'
import json, os, sys
p = sys.argv[1]
c = json.load(open(p, encoding="utf-8"))
c["blizzard_client_id"] = os.environ["BZ_ID"].strip()
c["blizzard_client_secret"] = os.environ["BZ_SEC"].strip()
json.dump(c, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print("Zugang in config.json eingetragen.")
PY
  unset CID SEC
  chmod 600 "$CFG"
fi
curl -fsSL "https://raw.githubusercontent.com/andreasuhlmann78-create/raidmaster/main/RaidMasterBot/blizzard_api_check.py" \
  -o "$DIR/blizzard_api_check.py"
ARGS=(); [ -n "$REALM" ] && ARGS=(--realm "$REALM")
"$PY" "$DIR/blizzard_api_check.py" "${ARGS[@]}" | tee "$DIR/data/mn8-bericht.txt" || true
echo
echo "Bericht gespeichert: $DIR/data/mn8-bericht.txt (enthält keine Zugangsdaten)."
