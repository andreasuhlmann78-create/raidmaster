"""Selbst-Update (D-3 Schritt 20, ab Bot 1.5.167): Update-ZIP einspielen (/update mit Datei), alle 30 Minuten auf
GitHub nach einer neuen Version suchen, nach dem Neustart das Ergebnis melden. Immer nur EIN Update gleichzeitig
(update_lock); nach einem Update mit Bot-Änderung wird nichts mehr eingespielt, bis der Neustart erfolgt
(_restart_pending, "global" – wandert mit allen Funktionen, die ihn setzen und lesen).

UNVERÄNDERT aus bot.py verschoben (samt Kommentaren direkt darüber): update_lock, _restart_pending, apply_update,
_apply_update, check_github, _check_github, update_loop, before_update, confirm_later, report_update_result,
/update. Entpacken und Kopieren: updater.py. Neustart: grund.restart_soon (setzt grund.EXIT_CODE).
bot.py importiert dieses Modul nach "grund.bot = bot" (/update wird beim Import angemeldet) und übernimmt
update_loop und report_update_result. Weg A (Antwort der Prüf-Sitzung 15.11. 20:48).
"""
from __future__ import annotations

import asyncio
import os

import discord
from discord import app_commands
from discord.ext import tasks

import grund
import updater
from ankuendigung_bot import check_addon_release
from grund import is_admin, post_bot_log, restart_soon
from kern import BASE, cfg, log, state

bot = grund.bot
assert bot is not None, "update_bot erst nach grund.bot = bot importieren"


# Immer nur EIN Update gleichzeitig (ab Bot 1.5.100): Bis 1.5.99 konnten /update und die automatische Prüfung
# gleichzeitig laufen. Beide entpackten in denselben Ordner update/tmp, der zweite löschte ihn dem ersten unter den
# Füssen weg ("[Errno 2] No such file or directory: …/update/tmp/…").
update_lock = asyncio.Lock()
_restart_pending = False      # Update mit Bot-Änderung installiert, Neustart steht bevor: nichts mehr einspielen


async def apply_update(data: bytes, source: str, ref: str = "", note: str = "") -> str:
    """Installiert eine Update-ZIP (z. B. /update datei:). Wartet, falls gerade ein anderes Update läuft."""
    async with update_lock:
        return await _apply_update(data, source, ref, note)


async def _apply_update(data: bytes, source: str, ref: str = "", note: str = "") -> str:
    """Installiert eine Update-ZIP. Liefert eine Meldung; startet bei Bot-Änderungen neu. Nur mit update_lock aufrufen."""
    global _restart_pending
    if _restart_pending:
        return "⏳ Ein Update ist schon installiert, der Bot startet gleich neu – danach bitte nochmal versuchen."
    try:
        result = await asyncio.to_thread(updater.install_zip, data, BASE, source, ref)
    except updater.UpdateError as e:
        if ref:
            state.data["failed_sha"] = ref
            state.save()
        text = f"❌ Update ({source}) nicht installiert: {e}"
        await post_bot_log(text)
        return text
    parts = [f"⬇️ **Update** ({source}{' · `' + ref[:7] + '`' if ref else ''})" + (f": {note[:200]}" if note else "")]
    if result.get("addon_version"):
        parts.append(f"Addon: RaidMaster {result['addon_version']}")
    for r in result.get("rejected") or []:
        errs = r.get("errors") or []
        parts.append(f"🛑 **Addon-Prüfung:** `{r.get('file')}` NICHT veröffentlicht ({len(errs)} Fehler):")
        for e in errs[:3]:
            parts.append(f"  • {e[:300]}")
        if len(errs) > 3:
            parts.append(f"  • … und {len(errs) - 3} weitere (Bericht: addon-check/bericht.md im Repo)")
    if result.get("rejected"):
        parts.append("Bitte beheben und als neue Version hochladen – bis dahin bleibt die bisherige Version in Discord.")
    if result.get("announce_removed"):
        names = result["announce_removed"]
        parts.append(f"🗑️ Im Repo gelöscht: {', '.join(names[:10])}{' …' if len(names) > 10 else ''} – "
                     "die Beiträge dazu entferne ich im Discord.")
    if result.get("addon_check") is False:
        parts.append("⚠️ Addon-Prüfung nicht gefunden (addon-check/addon_check.py fehlt im Repo) – ZIPs ungeprüft übernommen.")
    if result["bot_changed"]:
        parts.append(f"Bot: {result['old_version']} → {result['version']} · geändert: {', '.join(result['bot_changed'][:12])}")
        parts.append("Der Bot startet in wenigen Sekunden neu.")
    else:
        parts.append("Bot unverändert.")
        if ref:
            state.data["installed_sha"] = ref
            state.save()
    text = "\n".join(parts)
    await post_bot_log(text)
    if result["bot_changed"]:
        _restart_pending = True
        asyncio.create_task(restart_soon())
    else:
        await check_addon_release()
    return text


async def check_github(manual: bool = False) -> str:
    """Neue Version auf GitHub suchen und einspielen. Läuft gerade ein Update, wird gewartet und danach neu geprüft
    (dann ist meist schon alles aktuell)."""
    async with update_lock:
        if _restart_pending:
            return "⏳ Ein Update ist schon installiert, der Bot startet gleich neu."
        return await _check_github(manual)


async def _check_github(manual: bool = False) -> str:
    repo = (cfg.get("update_repo") or "").strip()
    if not repo:
        return "Kein GitHub-Repository eingetragen (`update_repo` in config.json)."
    token = (cfg.get("update_token") or "").strip() or None
    branch = cfg.get("update_branch") or "main"
    import aiohttp
    timeout = aiohttp.ClientTimeout(total=120)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        latest = await updater.github_latest(session, repo, branch, token)
        sha = latest["sha"]
        if not sha or sha == state.data.get("installed_sha"):
            return f"✅ Aktuell (Version {updater.bot_version(BASE)}, Commit `{sha[:7]}`)."
        # gerade erst installiert und neu gestartet, aber noch nicht bestätigt (confirm_later nach 150 s): nicht noch
        # einmal einspielen. Bis 1.5.107 entstand so eine Neustart-Schleife alle ~70 s (ab Bot 1.5.108).
        pending = updater.read_json(updater.pending_path(BASE)) or {}
        if sha == pending.get("ref"):
            return f"⏳ Version {updater.bot_version(BASE)} (Commit `{sha[:7]}`) ist eben installiert worden und startet gerade."
        if sha == state.data.get("failed_sha") and not manual:
            return "Letztes Update war fehlerhaft – warte auf eine neue Version."
        data = await updater.github_zip_to_file(session, repo, sha, token, BASE)   # DC-UPL1: auf die Platte, nicht in den Speicher
    try:
        return await _apply_update(data, "GitHub", sha, latest["message"].splitlines()[0] if latest["message"] else "")
    finally:
        try:
            os.remove(data)
        except OSError:
            pass


@tasks.loop(minutes=30)
async def update_loop():
    if not cfg.get("update_repo"):
        return
    try:
        await check_github(False)
    except updater.UpdateError as e:
        log.warning("Update-Prüfung: %s", e)
    except Exception as e:  # noqa: BLE001 – Netzwerkfehler usw.
        log.warning("Update-Prüfung fehlgeschlagen: %s", e)


@update_loop.before_loop
async def before_update():
    await bot.wait_until_ready()
    await asyncio.sleep(60)


async def confirm_later():
    await asyncio.sleep(150)
    pending = updater.confirm_pending(BASE)
    if pending and pending.get("ref"):
        state.data["installed_sha"] = pending["ref"]
        state.save()


async def report_update_result():
    failed = updater.take_failed(BASE)
    if failed:
        if failed.get("ref"):
            state.data["failed_sha"] = failed["ref"]
            state.save()
        await post_bot_log(f"❌ Das Update auf {failed.get('version')} ist beim Start abgestürzt ({failed.get('reason')}). "
                           f"Die vorherige Version {updater.bot_version(BASE)} läuft wieder.")
    pending = updater.read_json(updater.pending_path(BASE))
    if pending:
        await post_bot_log(f"✅ Update installiert – RaidMaster-Bot **{updater.bot_version(BASE)}** läuft.")
        asyncio.create_task(confirm_later())


@bot.tree.command(name="update", description="Update prüfen bzw. eine Update-ZIP einspielen (Gildenleitung)")
@app_commands.describe(datei="Optional: Update-ZIP (RaidMaster-Paket). Leer = auf GitHub nach neuer Version suchen")
async def update_cmd(inter: discord.Interaction, datei: discord.Attachment | None = None):
    if not is_admin(inter.user):
        await inter.response.send_message("Das dürfen nur der Gildenchef und die Offiziere.", ephemeral=True)
        return
    await inter.response.defer(ephemeral=True, thinking=True)
    try:
        if datei:
            if not datei.filename.lower().endswith(".zip") or datei.size > 25 * 1024 * 1024:
                await inter.followup.send("Bitte eine ZIP-Datei (max. 25 MB) anhängen.", ephemeral=True)
                return
            text = await apply_update(await datei.read(), f"Upload von {inter.user.display_name}", "", datei.filename)
        else:
            text = await check_github(True)
    except updater.UpdateError as e:
        text = f"❌ {e}"
    except Exception as e:  # noqa: BLE001
        log.exception("Update fehlgeschlagen")
        text = f"❌ Update fehlgeschlagen: {e}"
    await inter.followup.send(text[:1990], ephemeral=True)
