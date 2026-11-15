"""Server-Betrieb (D-3 Schritt 21, ab Bot 1.5.168): #testberichte aufräumen (tb_cleanup_loop), tägliche
Datensicherung (backup_loop), Spielsymbole-Liste alle 14 Tage neu und Selbstprüfung (icon_map_loop,
run_self_check), Bot-Daten aus einer Sicherung übernehmen (/daten-import).

UNVERÄNDERT aus bot.py verschoben: der ganze Abschnitt tb_cleanup_loop bis import_cmd (199 Zeilen, samt
Kommentaren). Die Schleifen werden weiter in RaidBot.setup_hook gestartet (bot.py übernimmt die Namen).
bot.py importiert dieses Modul nach "grund.bot = bot" (/daten-import wird beim Import angemeldet).
Weg A (Antwort der Prüf-Sitzung 15.11. 20:48).
"""
from __future__ import annotations

import asyncio
import io
import json
import os
import time
import zipfile

import discord
from discord import app_commands
from discord.ext import tasks

import grund
import raidmaster_data as rmd
import self_check
import tb_aufraeumen
from grund import bot_guild, channel_by_id, is_admin, post_bot_log, restart_soon
from kern import BASE, DATA_DIR, ICON_LISTFILE_URL, ICON_MAP_FRESH, cfg, log, state

bot = grund.bot
assert bot is not None, "betrieb_bot erst nach grund.bot = bot importieren"


@tasks.loop(minutes=30)
async def tb_cleanup_loop():
    """#testberichte: nur Nachrichten löschen, die die Abholung verarbeitet hat (testberichte/abgeholt.json im Repo)
    und die älter als 1 Stunde sind (ab Bot 1.5.111). Sonst wird dort nichts gelesen, beantwortet oder gepostet."""
    repo = cfg.get("update_repo")
    guild = bot_guild()
    if not repo or guild is None:
        return
    try:
        import aiohttp
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=20)) as session:
            async with session.get(tb_aufraeumen.raw_url(repo)) as resp:
                if resp.status != 200:
                    return
                ids = tb_aufraeumen.parse_ids(await resp.text())
        done = state.data.setdefault("tb_deleted", [])
        n, note = await tb_aufraeumen.cleanup(guild, ids, done)
        state.save()
        if n:
            log.info("#testberichte: %d abgeholte Nachricht(en) gelöscht", n)
        if note and not state.data.get("tb_note_shown"):
            state.data["tb_note_shown"] = True
            state.save()
            await post_bot_log("🧹 " + note)
    except Exception as e:  # noqa: BLE001 – Netz usw., nächster Versuch in 30 Minuten
        log.warning("#testberichte aufräumen: %s", e)


@tb_cleanup_loop.before_loop
async def before_tb_cleanup():
    await bot.wait_until_ready()
    await asyncio.sleep(120)


# ---------------------------------------------------------------------------
# Server-Betrieb: tägliche Datensicherung
# ---------------------------------------------------------------------------

def make_data_backup() -> str | None:
    if not os.path.isdir(DATA_DIR):
        return None
    folder = os.path.join(BASE, "backup")
    os.makedirs(folder, exist_ok=True)
    path = os.path.join(folder, time.strftime("daten-%Y-%m-%d.zip"))
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zf:
        for fn in sorted(os.listdir(DATA_DIR)):
            full = os.path.join(DATA_DIR, fn)
            if os.path.isfile(full) and fn.endswith((".json", ".lua")):
                zf.write(full, fn)
    keep = max(1, int(cfg.get("backup_days") or 7))
    old = sorted(f for f in os.listdir(folder) if f.startswith("daten-") and f.endswith(".zip"))
    for f in old[:-keep]:
        try:
            os.remove(os.path.join(folder, f))
        except OSError:
            pass
    return path


@tasks.loop(hours=1)
async def backup_loop():
    if time.time() - float(state.data.get("last_backup") or 0) < 23 * 3600:
        return
    path = await asyncio.to_thread(make_data_backup)
    state.data["last_backup"] = int(time.time())
    state.save()
    if not path:
        return
    ch = await channel_by_id(cfg.get("data_channel_id"))
    if ch and os.path.getsize(path) < 8 * 1024 * 1024:
        try:
            await ch.send("💾 Tägliche Sicherung der Bot-Daten (Raids, Charaktere, DKP-Datei).",
                          file=discord.File(path))
        except discord.HTTPException as e:
            log.warning("Sicherung konnte nicht gepostet werden: %s", e)


@backup_loop.before_loop
async def before_backup():
    await bot.wait_until_ready()


# ---------------------------------------------------------------------------
# Spielsymbole: Datei-ID -> Symbolname aus der Community-Listfile (alle 14 Tage neu, damit auch neue
# Symbole von WoW Forever erkannt werden). Gespeichert wird nur der kleine Auszug Interface/Icons.
# ---------------------------------------------------------------------------
async def refresh_icon_map() -> int:
    import aiohttp
    import gzip
    found: dict[str, str] = {}
    timeout = aiohttp.ClientTimeout(total=900)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.get(ICON_LISTFILE_URL) as resp:
            if resp.status != 200:
                raise RuntimeError(f"HTTP {resp.status}")
            buf = b""
            async for chunk in resp.content.iter_chunked(1 << 16):
                buf += chunk
                *lines, buf = buf.split(b"\n")
                found.update(rmd.icon_fileids_from_listfile(x.decode("utf-8", "ignore") for x in lines))
            if buf:
                found.update(rmd.icon_fileids_from_listfile([buf.decode("utf-8", "ignore")]))
    if len(found) < 1000:
        raise RuntimeError(f"nur {len(found)} Symbole gefunden")
    os.makedirs(DATA_DIR, exist_ok=True)
    tmp = ICON_MAP_FRESH + ".tmp"
    with gzip.open(tmp, "wt", encoding="utf-8") as f:
        json.dump(found, f, separators=(",", ":"))
    os.replace(tmp, ICON_MAP_FRESH)
    rmd.ICON_FILEIDS.update(found)
    # Symbole, die bisher unbekannt waren, beim nächsten Mal neu nachschlagen
    for key in [k for k, v in (state.data.get("item_icons") or {}).items() if not v]:
        state.data["item_icons"].pop(key, None)
    for key in [k for k, v in (state.data.get("item_emojis") or {}).items() if not v]:
        state.data["item_emojis"].pop(key, None)
    state.save()
    return len(found)


async def run_self_check() -> list[str]:
    """TU5 (ab 1.5.125): Grundregeln am echten Server prüfen (nur lesen). Protokoll "GRUNDREGEL VERLETZT …",
    #bot-befehle nur, wenn sich die Liste geändert hat (nie doppelt)."""
    guild = bot_guild()
    if guild is None:
        return []
    found = self_check.check(guild, cfg)
    for v in found:
        log.warning("GRUNDREGEL VERLETZT %s", v)
    key = "|".join(sorted(found))
    if key != state.data.get("selfcheck_last", ""):
        state.data["selfcheck_last"] = key
        state.save()
        if found:
            await post_bot_log("🧪 **Grundregel verletzt** (nur gelesen, nichts geändert):\n• " + "\n• ".join(found[:15]))
    return found


@tasks.loop(hours=6)
async def icon_map_loop():
    try:
        await run_self_check()
    except Exception:  # noqa: BLE001
        log.exception("Selbstprüfung fehlgeschlagen")
    try:
        age = time.time() - os.path.getmtime(ICON_MAP_FRESH) if os.path.isfile(ICON_MAP_FRESH) else None
    except OSError:
        age = None
    if age is not None and age < 14 * 86400:
        return
    try:
        n = await refresh_icon_map()
        log.info("Symbol-Liste aktualisiert: %d Spielsymbole.", n)
    except Exception as e:  # noqa: BLE001
        log.info("Symbol-Liste nicht aktualisiert: %s", e)


@icon_map_loop.before_loop
async def before_icon_map():
    await bot.wait_until_ready()


IMPORT_FILES = ("raids.json", "profiles.json", "state.json", "RaidMaster.lua")


@bot.tree.command(name="daten-import", description="Bot-Daten aus einer Sicherung übernehmen, z. B. beim Umzug auf den Server (Gildenleitung)")
@app_commands.describe(datei="Sicherungs-ZIP aus #bot-daten (daten-JJJJ-MM-TT.zip)")
async def import_cmd(inter: discord.Interaction, datei: discord.Attachment):
    if not is_admin(inter.user):
        await inter.response.send_message("Das dürfen nur der Gildenchef und die Offiziere.", ephemeral=True)
        return
    if not datei.filename.lower().endswith(".zip") or datei.size > 25 * 1024 * 1024:
        await inter.response.send_message("Bitte die Sicherungs-ZIP anhängen.", ephemeral=True)
        return
    await inter.response.defer(ephemeral=True, thinking=True)
    raw = await datei.read()
    try:
        with zipfile.ZipFile(io.BytesIO(raw)) as zf:
            names = {os.path.basename(n): n for n in zf.namelist() if os.path.basename(n) in IMPORT_FILES}
            if "raids.json" not in names and "profiles.json" not in names:
                await inter.followup.send("In der ZIP sind keine Bot-Daten (raids.json / profiles.json).", ephemeral=True)
                return
            contents = {}
            for base_name, member in names.items():
                data = zf.read(member)
                if base_name.endswith(".json"):
                    json.loads(data.decode("utf-8"))
                contents[base_name] = data
    except (zipfile.BadZipFile, ValueError, UnicodeDecodeError) as e:
        await inter.followup.send(f"Die Sicherung ist beschädigt: {e}", ephemeral=True)
        return
    await asyncio.to_thread(make_data_backup)
    os.makedirs(DATA_DIR, exist_ok=True)
    for base_name, data in contents.items():
        with open(os.path.join(DATA_DIR, base_name), "wb") as f:
            f.write(data)
    await inter.followup.send(
        f"✅ Übernommen: {', '.join(sorted(contents))}. Der Bot startet neu, um die Daten zu laden.", ephemeral=True)
    log.info("Daten-Import von %s: %s", inter.user, ", ".join(sorted(contents)))
    asyncio.create_task(restart_soon())
