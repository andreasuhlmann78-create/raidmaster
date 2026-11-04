#!/usr/bin/env bash
# RaidMaster-Bot: neuen Discord-Token eintragen und auf den neuesten Stand bringen – alles in einem Schritt.
# Gebraucht, wenn Discord den Token zurückgesetzt hat (z. B. "connected more than 1000 times").
#
# Auf dem Server (SSH) ausführen:
#   curl -fsSL https://raw.githubusercontent.com/andreasuhlmann78-create/raidmaster/main/RaidMasterBot/neuer_token.sh | sudo bash
#
# Das Skript
#   1. stoppt den Bot und zeigt, ob eine Intent-Schleife die Ursache war,
#   2. fragt nach dem neuen Token (Eingabe bleibt unsichtbar) und trägt ihn in config.json ein,
#   3. spielt mit install.sh den neuesten Stand ein (config.json und Daten bleiben) und startet den Bot,
#   4. zeigt 40 Sekunden lang das Protokoll, bis "Angemeldet als …" erscheint.
# Der Token wird nirgends ausgegeben und nicht gespeichert ausser in config.json.
set -euo pipefail

REPO="andreasuhlmann78-create/raidmaster"
DIR="/opt/raidmaster"
SERVICE="raidmaster"
CFG="$DIR/config.json"

say() { printf '\n\033[1;33m== %s\033[0m\n' "$*"; }

if [ "$(id -u)" -ne 0 ]; then
  echo "Bitte mit sudo ausführen (siehe oben)." >&2
  exit 1
fi
if [ ! -f "$CFG" ]; then
  echo "$CFG fehlt – ist der Bot auf diesem Server installiert?" >&2
  exit 1
fi

say "1/4 Bot stoppen"
systemctl stop "$SERVICE" || true

say "Ursache: Meldungen zu Intents und Neustarts seit heute früh"
journalctl -u "$SERVICE" --since "today 05:00" --no-pager 2>/dev/null \
  | grep -iE "intent|Neustart|Starter|LoginFailure|Improper token" | tail -n 15 || echo "(keine passenden Meldungen)"

say "2/4 Neuen Token eintragen"
echo "Den neuen Token aus dem Discord-Entwicklerportal einfügen (Bot -> Reset Token) und Enter drücken."
echo "Die Eingabe bleibt unsichtbar."
TOKEN=""
while [ -z "$TOKEN" ]; do
  read -rsp "Neuer Bot-Token: " TOKEN < /dev/tty
  echo
  TOKEN="$(printf '%s' "$TOKEN" | tr -d '[:space:]')"
  if [ "${#TOKEN}" -lt 50 ]; then
    echo "Das sieht nicht wie ein Bot-Token aus (zu kurz). Bitte nochmal."
    TOKEN=""
  fi
done
cp -p "$CFG" "$CFG.vor-neuem-token"
PY="$DIR/.venv/bin/python"
[ -x "$PY" ] || PY="python3"
RM_TOKEN="$TOKEN" "$PY" - "$CFG" <<'PY'
import json, os, sys
path = sys.argv[1]
with open(path, encoding="utf-8") as f:
    cfg = json.load(f)
cfg["token"] = os.environ["RM_TOKEN"]
with open(path, "w", encoding="utf-8") as f:
    json.dump(cfg, f, ensure_ascii=False, indent=2)
mc = cfg.get("message_content_intent")
print("Token eingetragen. message_content_intent in config.json:", "an" if mc else "aus")
if mc:
    print("-> Im Entwicklerportal unter Bot -> Privileged Gateway Intents den Message Content Intent EINSCHALTEN.")
PY
unset TOKEN RM_TOKEN
chmod 600 "$CFG"

say "3/4 Neuesten Stand einspielen und Bot starten"
curl -fsSL "https://raw.githubusercontent.com/$REPO/main/RaidMasterBot/install.sh" | bash -s "$REPO"

say "4/4 Protokoll (40 Sekunden) – warten auf \"Angemeldet als …\""
timeout 40 journalctl -u "$SERVICE" -f -n 0 --no-pager || true
echo
if journalctl -u "$SERVICE" --since "-2min" --no-pager | grep -q "Angemeldet als"; then
  echo "✅ Der Bot ist wieder online (Version $(cat "$DIR/VERSION" 2>/dev/null || echo ?))."
  echo "Letzter Schritt: auf GitHub im Repo raidmaster unter Settings -> Secrets and variables -> Actions"
  echo "das Secret DISCORD_BOT_TOKEN mit demselben neuen Token überschreiben (für die Discord-Prüfung)."
else
  echo "⚠️ Noch keine Anmeldung gesehen. Protokoll ansehen mit:  sudo journalctl -u $SERVICE -n 50 --no-pager"
  echo "Die alte Einstellung liegt in $CFG.vor-neuem-token."
fi
