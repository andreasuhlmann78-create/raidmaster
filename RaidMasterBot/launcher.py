"""
RaidMaster-Bot – Starter.

Startet bot.py und hält ihn am Laufen:
- Beendet sich der Bot mit Code 42 (Update installiert), wird er sofort neu gestartet –
  bei geänderter requirements.txt vorher mit "pip install".
- Stürzt eine frisch installierte Version innerhalb von 2 Minuten ab, wird automatisch die
  vorherige Version wiederhergestellt.
- Bei anderen Abstürzen wird nach einer kurzen Pause neu gestartet.
- Code 0 (normal beendet) oder Strg+C beendet auch den Starter.

Auf dem Server startet systemd diesen Starter, unter Windows start.bat.
"""

from __future__ import annotations

import os
import subprocess
import sys
import time

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

import updater  # noqa: E402

CONFIG_ERROR = 3     # wie in bot.py: config.json unvollständig -> nicht neu starten
CRASH_WINDOW = 120   # Sekunden: Absturz so kurz nach einem Update -> zurück zur alten Version


def log(msg: str):
    print(time.strftime("%H:%M:%S") + " [Starter] " + msg, flush=True)


def pip_install():
    req = os.path.join(BASE, "requirements.txt")
    if not os.path.isfile(req):
        return
    log("Neue Abhängigkeiten – pip install ...")
    subprocess.run([sys.executable, "-m", "pip", "install", "-q", "-r", req], cwd=BASE)


def main() -> int:
    fast_crashes = 0
    while True:
        started = time.time()
        try:
            code = subprocess.run([sys.executable, os.path.join(BASE, "bot.py")], cwd=BASE).returncode
        except KeyboardInterrupt:
            log("Beendet.")
            return 0
        runtime = time.time() - started
        if code == updater.RESTART_CODE:
            pending = updater.read_json(updater.pending_path(BASE)) or {}
            if pending.get("requirements"):
                pip_install()
            log("Neustart nach Update ...")
            fast_crashes = 0
            continue
        if code == 0:
            log("Bot wurde beendet.")
            return 0
        if code == CONFIG_ERROR:
            log("Einstellungen unvollständig – bitte config.json prüfen. Der Starter wird beendet.")
            return code
        if os.path.isfile(updater.pending_path(BASE)) and runtime < CRASH_WINDOW:
            log(f"Neue Version ist abgestürzt (Code {code}) – stelle die vorherige Version wieder her.")
            try:
                updater.rollback_pending(BASE, f"Absturz nach {int(runtime)} s (Code {code})")
                pip_install()
            except Exception as e:  # noqa: BLE001
                log(f"Wiederherstellen fehlgeschlagen: {e}")
            continue
        fast_crashes = fast_crashes + 1 if runtime < 60 else 0
        wait = min(300, 10 * (2 ** min(fast_crashes, 5)))
        log(f"Bot wurde unerwartet beendet (Code {code}). Neustart in {wait} s ...")
        try:
            time.sleep(wait)
        except KeyboardInterrupt:
            return 0


if __name__ == "__main__":
    sys.exit(main())
