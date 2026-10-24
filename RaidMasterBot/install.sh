#!/usr/bin/env bash
# RaidMaster-Bot – Installation auf einem Linux-Server (Ubuntu 22.04/24.04 oder Debian 12)
#
# Aufruf direkt aus GitHub (empfohlen):
#   curl -fsSL https://raw.githubusercontent.com/BENUTZER/REPO/main/RaidMasterBot/install.sh | sudo bash -s BENUTZER/REPO
# oder aus einem entpackten RaidMaster-Paket im Ordner RaidMasterBot:
#   sudo bash install.sh
#
# Ein erneuter Aufruf aktualisiert die Installation; config.json und data/ bleiben erhalten.

set -euo pipefail

REPO="${1:-}"
BRANCH="${BRANCH:-main}"
DIR=/opt/raidmaster
SERVICE=raidmaster
SRC_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" 2>/dev/null && pwd || echo "")"

say() { printf '\n\033[1;33m==> %s\033[0m\n' "$*"; }

if [ "$(id -u)" -ne 0 ]; then
  echo "Bitte mit sudo starten: sudo bash install.sh"
  exit 1
fi

say "Pakete installieren (Python, unzip, curl) ..."
export DEBIAN_FRONTEND=noninteractive
apt-get update -q
apt-get install -y -q python3 python3-venv python3-pip unzip curl ca-certificates

say "Benutzer 'raidmaster' und Ordner $DIR anlegen ..."
id raidmaster >/dev/null 2>&1 || useradd --system --home-dir "$DIR" --shell /usr/sbin/nologin raidmaster
mkdir -p "$DIR"

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

if [ -n "$SRC_DIR" ] && [ -f "$SRC_DIR/bot.py" ] && [ -z "$REPO" ]; then
  say "Dateien aus $SRC_DIR übernehmen ..."
  SRC="$SRC_DIR"
elif [ -n "$REPO" ]; then
  say "Neueste Version von GitHub ($REPO) laden ..."
  AUTH=()
  if [ -n "${GITHUB_TOKEN:-}" ]; then AUTH=(-H "Authorization: Bearer $GITHUB_TOKEN"); fi
  curl -fsSL "${AUTH[@]}" -H "User-Agent: RaidMaster-Installer" \
    "https://api.github.com/repos/$REPO/zipball/$BRANCH" -o "$TMP/repo.zip"
  unzip -q "$TMP/repo.zip" -d "$TMP/repo"
  SRC="$(dirname "$(find "$TMP/repo" -name bot.py -path '*RaidMasterBot*' | head -n1)")"
  if [ -z "$SRC" ] || [ ! -f "$SRC/bot.py" ]; then
    echo "Im Repository wurde der Ordner RaidMasterBot nicht gefunden."
    exit 1
  fi
  # Addon-Ordner mitnehmen, damit der Bot die Addon-ZIP für #raid-addon bauen kann
  ADDON_SRC="$(dirname "$(find "$TMP/repo" -name RaidMaster.toc | head -n1)" 2>/dev/null || true)"
else
  echo "Aufruf: sudo bash install.sh BENUTZER/REPO   (oder im entpackten Ordner RaidMasterBot ohne Angabe)"
  exit 1
fi

say "Bot-Dateien kopieren ..."
for f in "$SRC"/*; do
  name="$(basename "$f")"
  case "$name" in
    config.json|data|addon|backup|update|.venv|venv|__pycache__) continue ;;
  esac
  rm -rf "$DIR/$name"
  cp -r "$f" "$DIR/$name"
done
mkdir -p "$DIR/data" "$DIR/addon" "$DIR/backup"

if [ -n "${ADDON_SRC:-}" ] && [ -f "$ADDON_SRC/RaidMaster.toc" ]; then
  VERSION="$(grep -m1 -oP '##\s*Version:\s*\K[0-9.]+' "$ADDON_SRC/RaidMaster.toc" || true)"
  if [ -n "$VERSION" ] && [ ! -f "$DIR/addon/RaidMaster-$VERSION.zip" ]; then
    say "Addon $VERSION für #raid-addon packen ..."
    (cd "$(dirname "$ADDON_SRC")" && python3 -c "
import os, sys, zipfile
src, out = sys.argv[1], sys.argv[2]
with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as z:
    for d, _, files in os.walk(src):
        for f in files:
            full = os.path.join(d, f)
            z.write(full, os.path.join('RaidMaster', os.path.relpath(full, src)))
" "$ADDON_SRC" "$DIR/addon/RaidMaster-$VERSION.zip")
  fi
fi

say "Python-Umgebung einrichten ..."
[ -x "$DIR/.venv/bin/python" ] || python3 -m venv "$DIR/.venv"
"$DIR/.venv/bin/pip" install -q --disable-pip-version-check -r "$DIR/requirements.txt"

if [ ! -f "$DIR/config.json" ]; then
  say "Einstellungen"
  cp "$DIR/config.example.json" "$DIR/config.json"
  read -rp "Bot-Token (aus dem Discord-Entwicklerportal): " TOKEN < /dev/tty
  read -rp "Server-ID (Rechtsklick auf den Discord-Server -> Server-ID kopieren): " GUILD < /dev/tty
  "$DIR/.venv/bin/python" - "$DIR/config.json" "$TOKEN" "$GUILD" "$REPO" "${GITHUB_TOKEN:-}" <<'PY'
import json, sys
path, token, guild, repo, gh = sys.argv[1:6]
with open(path, encoding="utf-8") as f:
    cfg = json.load(f)
cfg["token"] = token.strip()
cfg["guild_id"] = int(guild.strip() or 0)
cfg["savedvariables_path"] = ""
if repo:
    cfg["update_repo"] = repo
if gh:
    cfg["update_token"] = gh
with open(path, "w", encoding="utf-8") as f:
    json.dump(cfg, f, indent=2, ensure_ascii=False)
PY
elif [ -n "$REPO" ]; then
  "$DIR/.venv/bin/python" - "$DIR/config.json" "$REPO" <<'PY'
import json, sys
path, repo = sys.argv[1:3]
with open(path, encoding="utf-8") as f:
    cfg = json.load(f)
cfg.setdefault("update_repo", repo)
if not cfg["update_repo"]:
    cfg["update_repo"] = repo
with open(path, "w", encoding="utf-8") as f:
    json.dump(cfg, f, indent=2, ensure_ascii=False)
PY
fi

chown -R raidmaster:raidmaster "$DIR"
chmod 600 "$DIR/config.json"

say "Dienst einrichten (startet automatisch, auch nach einem Neustart des Servers) ..."
cat > /etc/systemd/system/$SERVICE.service <<EOF
[Unit]
Description=RaidMaster Discord-Bot
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=raidmaster
WorkingDirectory=$DIR
ExecStart=$DIR/.venv/bin/python $DIR/launcher.py
Restart=always
RestartSec=10
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable $SERVICE >/dev/null
systemctl restart $SERVICE
sleep 5

say "Fertig!"
systemctl --no-pager --lines=8 status $SERVICE || true
cat <<EOF

Nützliche Befehle:
  Protokoll ansehen:   sudo journalctl -u $SERVICE -f
  Neu starten:         sudo systemctl restart $SERVICE
  Stoppen:             sudo systemctl stop $SERVICE
  Einstellungen:       sudo nano $DIR/config.json   (danach neu starten)

Updates installiert der Bot ab jetzt selbst aus GitHub.
EOF
