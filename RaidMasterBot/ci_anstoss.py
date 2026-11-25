"""D-CI2 (ab Bot 1.5.197, Auftrag Supervisor 25.11.2026 14:28; Entscheid des Nutzers ~13:50): Der Bot stösst bei jeder neuen
Nachricht in #testberichte den GitHub-Workflow "Testberichte" an, damit ein Bericht aus dem Spiel spätestens nach ~20 Minuten im
Repo liegt. Beleg (warum): Der Zeitplan des Workflows lief am 25.11. von 00:00–12:42 UTC nur 1× (GitHub lässt geplante Läufe aus).
Der Zeitplan bleibt als Rückfall.

- Aufruf: POST https://api.github.com/repos/<update_repo>/actions/workflows/testberichte.yml/dispatches {"ref": "main"}
  (Antwort 204). update_repo aus config.json (andreasuhlmann78-create/raidmaster).
- Höchstens alle 5 Minuten: Kommt eine Nachricht innerhalb der Sperre, wird EIN Anstoss für das Ende der Sperre vorgemerkt –
  weitere Pakete in dieser Zeit fasst er zusammen.
- Zugang: Fine-grained-Token (nur raidmaster, "Actions: Read and write"), trägt der NUTZER auf dem Bot-Server in config.json
  unter "github_actions_token" ein. Der Bot liest ihn bei jedem Anstoss frisch aus der Datei (kein Neustart nötig) und schreibt
  ihn nirgends hin (kein Log, keine Meldung). Fehlt er: einmal je Start eine Zeile in #bot-log.
- 401/403/404: einmal in #bot-log melden und nicht wiederholen, bis ein ANDERER Token eingetragen ist (state.json
  "ci_anstoss_fehler": {"status", "token": erste 12 Zeichen des SHA-256 – nicht der Token}). Andere Fehler (Netz, 5xx): nur
  Protokoll, die nächste Nachricht versucht es wieder.
"""
from __future__ import annotations

import asyncio
import hashlib
import json
import time

from kern import CONFIG_PATH, cfg, log, state

SPERRE = 300                      # Sekunden zwischen zwei Anstössen
WORKFLOW = "testberichte.yml"
TOKEN_KEY = "github_actions_token"
API = "https://api.github.com"

_last = 0.0                       # Zeitpunkt des letzten Anstosses (time.monotonic)
_pending: asyncio.Task | None = None
_missing_told = False


def read_token() -> str:
    """Token frisch aus config.json (der Nutzer trägt ihn bei laufendem Bot ein), sonst aus der geladenen Konfiguration."""
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            v = json.load(f).get(TOKEN_KEY)
    except (OSError, ValueError):
        v = None
    return str(v or cfg.get(TOKEN_KEY) or "").strip()


def token_id(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()[:12]


async def _post(url: str, token: str) -> int:
    """Ein Aufruf; liefert den HTTP-Status (in Tests ersetzt)."""
    import aiohttp
    headers = {"Authorization": "Bearer " + token, "Accept": "application/vnd.github+json",
               "X-GitHub-Api-Version": "2022-11-28", "User-Agent": "RaidMasterBot"}
    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=20)) as session:
        async with session.post(url, headers=headers, json={"ref": "main"}) as resp:
            return resp.status


async def _bot_log(text: str):
    from grund import post_bot_log
    await post_bot_log(text)


async def dispatch() -> str:
    """Einen Anstoss jetzt. Liefert "ok", "kein_token", "gesperrt", "fehler_<status>" oder "netz"."""
    global _missing_told
    repo = (cfg.get("update_repo") or "").strip()
    token = read_token()
    if not repo or not token:
        if not _missing_told:
            _missing_told = True
            await _bot_log("ℹ️ Testberichte: kein Anstoss des Workflows – in config.json fehlt \"github_actions_token\" "
                           "(der Zeitplan des Workflows läuft weiter).")
        return "kein_token"
    bad = state.data.get("ci_anstoss_fehler") or {}
    if bad.get("token") == token_id(token):
        return "gesperrt"
    url = f"{API}/repos/{repo}/actions/workflows/{WORKFLOW}/dispatches"
    try:
        status = await _post(url, token)
    except Exception as e:  # noqa: BLE001 – Netz; die nächste Nachricht versucht es wieder
        log.warning("D-CI2: Anstoss nicht möglich (%s)", type(e).__name__)
        return "netz"
    if status in (200, 201, 204):
        log.info("D-CI2: Workflow Testberichte angestossen")
        return "ok"
    if status in (401, 403, 404):
        state.data["ci_anstoss_fehler"] = {"status": status, "token": token_id(token)}
        state.save()
        await _bot_log(f"⚠️ Testberichte: GitHub lehnt den Anstoss ab (Antwort {status}). Bitte den Token in config.json "
                       f"(\"github_actions_token\": nur raidmaster, Actions: Read and write) prüfen. Bis ein anderer Token "
                       f"eingetragen ist, versuche ich es nicht wieder; der Zeitplan läuft weiter.")
        return f"fehler_{status}"
    log.warning("D-CI2: GitHub antwortet %d – nächster Versuch bei der nächsten Nachricht", status)
    return f"fehler_{status}"


async def _later(delay: float):
    global _pending, _last
    try:
        await asyncio.sleep(delay)
        _last = time.monotonic()
        await dispatch()
    finally:
        _pending = None


async def on_testbericht() -> str:
    """Von on_message für jede neue Nachricht in #testberichte. Liefert "jetzt", "vorgemerkt" oder "schon_vorgemerkt"."""
    global _last, _pending
    now = time.monotonic()
    if _pending is not None and not _pending.done():
        return "schon_vorgemerkt"
    if not _last or now - _last >= SPERRE:
        _last = now
        await dispatch()
        return "jetzt"
    _pending = asyncio.get_running_loop().create_task(_later(SPERRE - (now - _last)))
    return "vorgemerkt"
