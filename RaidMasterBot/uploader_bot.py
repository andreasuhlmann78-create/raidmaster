"""Uploader-Versand (D-3 Schritt 9, ab Bot 1.5.154): /uploader – Programm und Einrichtungsdateien per Direktnachricht,
an ein Mitglied (fuer:) oder nur die ZIP an alle Offiziere (an_offiziere:), neueste Uploader-ZIP besorgen.

UNVERÄNDERT aus bot.py verschoben. Webhooks/Einrichtung stehen in uploader_setup.py, Versionen in
uploader_version.py, Offiziers-Auswahl in pn.py; hier nur das, was Discord braucht.
bot.py importiert dieses Modul erst NACH "grund.bot = bot" (/uploader wird beim Import angemeldet) und übernimmt
die Namen. Weg A (Antwort der Prüf-Sitzung 15.11. 20:48).
"""
from __future__ import annotations

import asyncio
import io
import json
import os
import re

import discord
from discord import app_commands

import grund
import pn
import uploader_alt_bot
import uploader_setup
import uploader_version
from grund import bot_guild, channel_by_id, is_admin
from kern import ADDON_DIR, cfg, log, save_config

bot = grund.bot
assert bot is not None, "uploader_bot erst nach grund.bot = bot importieren"


async def ensure_fresh_uploader() -> tuple[str | None, str | None]:
    """D-UP1 (ab 1.5.128): Version der Uploader-ZIP mit dem Repo vergleichen; ist das Repo neuer, nur die ZIP aus
    download/ holen (geprüft, dann ersetzt). Liefert (Version der ZIP, Version im Repo). Netzfehler: Repo-Version None."""
    path = os.path.join(ADDON_DIR, "RaidMasterUploader.zip")
    have = uploader_version.file_version(path) if os.path.isfile(path) else None
    repo = (cfg.get("update_repo") or "").strip()
    if not repo:
        return have, None
    import aiohttp
    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30)) as session:
            async with session.get(uploader_version.raw_url(repo, "RaidMasterUploader/uploader.py")) as resp:
                want = uploader_version.parse_version(await resp.text()) if resp.status == 200 else None
            if not uploader_version.is_older(have, want):
                return have, want
            async with session.get(uploader_version.raw_url(repo, "download/RaidMasterUploader.zip")) as resp:
                data = await resp.read() if resp.status == 200 else b""
    except Exception as e:  # noqa: BLE001 – Netz: alte ZIP bleibt, Warnung in der Antwort
        log.warning("Uploader-Version nicht geprüft: %s", e)
        return have, None
    got = uploader_version.zip_version(data)
    if got and not uploader_version.is_older(got, have):
        os.makedirs(ADDON_DIR, exist_ok=True)
        with open(path + ".tmp", "wb") as f:
            f.write(data)
        os.replace(path + ".tmp", path)
        log.info("Uploader-ZIP aktualisiert: %s -> %s", have, got)
        have = got
    return have, want


def uploader_package() -> str | None:
    """RaidMasterUploader.zip (kommt mit jedem Update aus dem Ordner download des Repositorys)."""
    path = os.path.join(ADDON_DIR, "RaidMasterUploader.zip")
    return path if os.path.isfile(path) else None


@bot.tree.command(name="uploader", description="Daten-Uploader per Direktnachricht: Programm + Einrichtungsdatei (Gildenleitung)")
@app_commands.describe(nur_programm="Nur das Programm (RaidMasterUploader.zip) schicken, ohne neue Einrichtungsdatei – z. B. für ein Update",
                       fuer="Optional: für dieses Mitglied (bekommt alles selbst per PN, mit eigenem #sync-daten); leer = für dich",
                       an_offiziere="Nur die neueste Uploader-ZIP per PN an alle Offiziere (ihre Einrichtungsdateien bleiben)")
async def uploader_cmd(inter: discord.Interaction, nur_programm: bool = False, fuer: discord.Member | None = None,
                       an_offiziere: bool = False):
    if not is_admin(inter.user):
        await inter.response.send_message("Das dürfen nur der Gildenchef und die Offiziere.", ephemeral=True)
        return
    if an_offiziere:
        await uploader_to_officers(inter)
        return
    # ab 1.5.134 (Wunsch des Nutzers 14.11.): /uploader fuer:@Mitglied – die geheimen Dateien gehen direkt an das Mitglied,
    # mit seinem EIGENEN privaten #sync-daten (nie die sync_config.json eines anderen weitergeben)
    target = fuer or inter.user
    if getattr(target, "bot", False):
        await inter.response.send_message("An Bots wird kein Uploader geschickt.", ephemeral=True)
        return
    other = target.id != inter.user.id
    if nur_programm:
        await inter.response.defer(ephemeral=True, thinking=True)
        have, want = await ensure_fresh_uploader()
        pkg = uploader_package()
        if not pkg:
            await inter.followup.send("RaidMasterUploader.zip liegt noch nicht auf dem Server – nach dem nächsten Update (`/update`) erneut.",
                                      ephemeral=True)
            return
        vnote = uploader_version.note(have, want)
        try:
            await target.send(f"📦 **RaidMaster-Uploader {have or ''}**. Entpacken und die alten Dateien ersetzen – "
                              "deine `uploader_config.json` im Ordner behalten.\n" + ADDONS_AUTO_TIPP + "\n" + vnote,
                              file=discord.File(pkg, filename="RaidMasterUploader.zip"))
            uploader_alt_bot.note_given(target.id, have)          # D-UPALT: keine PN "veraltet" für diese Version
            await inter.followup.send(("Ich habe " + target.mention + " den Uploader per Direktnachricht geschickt. 📬 "
                                       if other else "Ich habe dir den Uploader per Direktnachricht geschickt. 📬 ")
                                      + vnote, ephemeral=True)
        except discord.HTTPException:
            if other:
                await inter.followup.send(f"{target.mention} nimmt keine Direktnachrichten vom Bot an (Privatnachrichten "
                                          "von Servermitgliedern erlauben). Nichts geschickt.", ephemeral=True)
                return
            await inter.followup.send("Direktnachricht nicht möglich (Privatnachrichten von Servermitgliedern erlauben) – hier die Datei. "
                                      + vnote, file=discord.File(pkg, filename="RaidMasterUploader.zip"), ephemeral=True)
        return
    ch = await channel_by_id(cfg.get("data_channel_id"))
    if not isinstance(ch, discord.TextChannel):
        await inter.response.send_message("Der Kanal **#bot-daten** fehlt noch – bitte zuerst `/raidmaster-einrichten` ausführen.", ephemeral=True)
        return
    if not ch.permissions_for(ch.guild.me).manage_webhooks:
        await inter.response.send_message(
            "Dem Bot fehlt das Recht **Webhooks verwalten**: Servereinstellungen → Rollen → Raidmaster tool → "
            "Berechtigungen → „Webhooks verwalten“ einschalten → speichern. Danach `/uploader` erneut.", ephemeral=True)
        return
    await inter.response.defer(ephemeral=True, thinking=True)
    # zwei Webhooks: #bot-daten (Spieldaten) und #testberichte (Testberichte der GoldSentinel-Addons)
    data_url, test_url, notes = await uploader_setup.setup_uploader_hooks(ch.guild, ch, cfg, f"/uploader von {inter.user}")
    # Abgleich PC/Laptop (ab 1.5.113): privater Kanal #sync-daten nur für dich, Webhook + Index -> sync_config.json
    sync_conf, sync_notes = await uploader_setup.setup_sync(ch.guild, target, cfg, f"/uploader von {inter.user}")
    notes += sync_notes
    save_config()
    conf = uploader_setup.uploader_config(data_url, test_url, bot.user.id)
    conf_bytes = json.dumps(conf, indent=2).encode("utf-8")
    have, want = await ensure_fresh_uploader()
    notes.append(uploader_version.note(have, want))
    pkg = uploader_package()
    text = setup_text(pkg, conf, sync_conf, notes)

    def files():
        out = [discord.File(io.BytesIO(conf_bytes), filename="uploader_config.json")]
        if sync_conf:
            out.append(discord.File(io.BytesIO(json.dumps(sync_conf, indent=2).encode("utf-8")),
                                    filename="sync_config.json"))
        if pkg:
            out.insert(0, discord.File(pkg, filename="RaidMasterUploader.zip"))
        return out
    # privat per Direktnachricht (nur du siehst sie); geht das nicht, hier nur für dich sichtbar
    if other:
        text = (f"✉️ **{inter.user.display_name}** (Gildenleitung) schickt dir den Daten-Uploader.\n\n" + text)
    try:
        await send_parts(target.send, text, files())
        if pkg:
            uploader_alt_bot.note_given(target.id, uploader_version.file_version(pkg))   # D-UPALT
        await inter.followup.send(("Ich habe " + target.mention + " den Uploader und die Einrichtungsdateien per "
                                   "**Direktnachricht** geschickt. 📬" if other else
                                   "Ich habe dir den Uploader und die Einrichtungsdatei per **Direktnachricht** geschickt. 📬"),
                                  ephemeral=True)
    except discord.HTTPException:
        if other:   # die Dateien nie an jemand anderen umleiten
            await inter.followup.send(f"{target.mention} nimmt keine Direktnachrichten vom Bot an (Privatnachrichten von "
                                      "Servermitgliedern erlauben). Nichts geschickt.", ephemeral=True)
            return
        async def eph(content, files=None):
            if files is not None:
                await inter.followup.send(content, files=files, ephemeral=True)
            else:
                await inter.followup.send(content, ephemeral=True)
        await send_parts(eph, text + "\n\n_(Direktnachricht nicht möglich – bitte Privatnachrichten von Servermitgliedern erlauben.)_",
                         files())


# D-UPDOC2 (1.5.197) -> DC-UPD1 (ab 1.5.199, Supervisor 27.11. 07:50; Uploader 2.3.29 = RM-UPD2, Entscheide des Nutzers 27.11.
# 07:08–07:12): Uploader und Addons aktualisieren sich selbst (nur stabile Versionen) – kein .bat und kein j mehr nötig.
ADDONS_AUTO_TIPP = ("🔄 **Uploader und Addons aktualisieren sich selbst** (ab Uploader 2.3.29, nur stabile Versionen) – nichts "
                    "anklicken. Ausschalten mit **Addons-automatisch-aus.bat** im Uploader-Ordner. Uploader 2.3.24–2.3.28 fragen "
                    "einmal mit j nach 2.3.29.\n"
                    "*The uploader and add-ons update themselves (from uploader 2.3.29, stable versions only) – nothing to click. "
                    "To turn it off, run **Addons-automatisch-aus.bat** in the uploader folder. Uploaders 2.3.24–2.3.28 ask once "
                    "(press j) for 2.3.29.*")


def hook_ids(conf: dict | None, sync_conf: dict | None = None) -> str:
    """D-UPCFG1 (ab 1.5.197): die Kanal-Kennungen wie im Uploader-Fenster (UP-CFG1, einstellungen.py ids): nur die Zahl der
    Webhook-Adresse, NIE der Schlüssel dahinter."""
    def hid(url):
        m = re.match(r"^https://(?:(?:ptb|canary)\.)?(?:discord\.com|discordapp\.com)/api/webhooks/(\d{5,25})/", str(url or ""))
        return m.group(1) if m else None
    parts = []
    if conf and hid(conf.get("webhook_url")):
        parts.append(f"Daten {hid(conf.get('webhook_url'))}")
    if conf and hid(conf.get("test_webhook_url")):
        parts.append(f"Testberichte {hid(conf.get('test_webhook_url'))}")
    if sync_conf and hid(sync_conf.get("sync_webhook_url")):
        parts.append(f"#sync-daten {hid(sync_conf.get('sync_webhook_url'))}")
    return ", ".join(parts)


def setup_text(pkg, conf: dict, sync_conf: dict | None, notes: list[str]) -> str:
    """Text der /uploader-Direktnachricht (Einrichtung). Ab 1.5.197 als eigene Funktion (Tests): mit dem Schritt
    Addons-automatisch-an.bat (D-UPDOC2) und den Kanal-Kennungen (D-UPCFG1). Kann länger als eine Discord-Nachricht sein –
    gesendet wird in Teilen (send_parts)."""
    return ("**Daten-Uploader einrichten** (auf dem PC, auf dem du WoW spielst):\n"
            + ("1. **RaidMasterUploader.zip** entpacken, z. B. nach Dokumente.\n" if pkg else
               "1. Den Ordner **RaidMasterUploader** aus dem RaidMaster-Paket nehmen (die ZIP liegt noch nicht auf dem Server).\n")
            + ("2. **uploader_config.json** und **sync_config.json** in diesen Ordner legen.\n" if sync_conf else
               "2. **uploader_config.json** in diesen Ordner legen.\n")
            + "3. `uploader.bat` doppelklicken – beim ersten Start sucht er deine RaidMaster-Datei selbst.\n"
            "4. Fertig: Nach jedem `/reload` oder Ausloggen sind DKP, Einteilung, Skillungen und Erstkill-Screenshots nach wenigen Sekunden im Discord.\n"
            + ("5. **Abgleich PC/Laptop:** an jedem Rechner dasselbe – beide Dateien hineinlegen und einmal "
               "`Autostart-einrichten.bat` doppelklicken. Mehr ist nicht nötig: Der Uploader gleicht deine Addon-Daten "
               "von selbst ab (WoW einfach normal starten; `GoldSentinel-WoW.bat` brauchst du nicht mehr). Die Daten "
               "liegen in deinem privaten Kanal #sync-daten – Mitglieder mit der Discord-Berechtigung "
               "**Administrator** sehen jeden Kanal, also auch diesen.\n"
               if sync_conf else "")
            + (ADDONS_AUTO_TIPP + "\n" if pkg else "")
            + ("🔎 Kanal-Kennungen (zum Vergleich mit der Frage im Uploader-Fenster): " + hook_ids(conf, sync_conf) + "\n"
               if hook_ids(conf, sync_conf) else "")
            + "⚠️ uploader_config.json und sync_config.json enthalten geheime Links – nicht weitergeben."
            + ("\n\n" + "\n".join("ℹ️ " + n for n in notes) if notes else ""))


async def send_parts(send, text: str, files=None):
    """Text in Teilen <= 1900 Zeichen (announce_reihe.split_parts); die Dateien hängen am ersten Teil."""
    from announce_reihe import split_parts
    parts = split_parts(text) or [""]
    await send(parts[0], files=files) if files is not None else await send(parts[0])
    for part in parts[1:]:
        await send(part)


async def uploader_to_officers(inter: discord.Interaction):
    """/uploader an_offiziere:True (ab 1.5.135, Wunsch des Nutzers 15.11.): nur die neueste RaidMasterUploader.zip per
    PN an alle Offiziere (ohne den Absender). Keine Einrichtungsdateien – die bestehende uploader_config.json und
    sync_config.json bleiben im Ordner. Gesperrte PN: nichts umleiten, nur melden. Protokoll nur mit Zahlen."""
    await inter.response.defer(ephemeral=True, thinking=True)
    have, want = await ensure_fresh_uploader()
    pkg = uploader_package()
    if not pkg:
        await inter.followup.send("RaidMasterUploader.zip liegt noch nicht auf dem Server – nach dem nächsten Update "
                                  "(`/update`) erneut.", ephemeral=True)
        return
    guild = inter.guild or bot_guild()
    targets = pn.offiziere(guild.members if guild else [], inter.user.id)
    if not targets:
        await inter.followup.send("Keine Offiziere gefunden (Rolle „Offizier“) – nichts geschickt.", ephemeral=True)
        return
    vnote = uploader_version.note(have, want)
    text = (f"📦 **RaidMaster-Uploader {have or ''}** – neue Version von {inter.user.display_name} (Gildenleitung).\n"
            "Entpacken und die alten Dateien im Ordner **RaidMasterUploader** ersetzen. Deine `uploader_config.json` "
            "und `sync_config.json` im Ordner behalten (nicht löschen). Danach `uploader.bat` neu starten.\n"
            + ADDONS_AUTO_TIPP + "\n" + vnote)
    ok, blocked = [], []
    for m in targets:
        try:
            await m.send(text, file=discord.File(pkg, filename="RaidMasterUploader.zip"),
                         allowed_mentions=discord.AllowedMentions.none())
            ok.append(m)
            uploader_alt_bot.note_given(m.id, have)               # D-UPALT
        except discord.HTTPException:
            blocked.append(m)
        await asyncio.sleep(1)          # Discord: nicht zu schnell hintereinander
    log.info("Uploader %s an Offiziere: %d geschickt, %d ohne PN", have or "?", len(ok), len(blocked))
    lines = [f"📬 Uploader **{have or '?'}** an {len(ok)} von {len(targets)} Offizieren geschickt."]
    if ok:
        lines.append("Bekommen: " + ", ".join(m.mention for m in ok))
    if blocked:
        lines.append("⚠️ Keine PN möglich (Privatnachrichten von Servermitgliedern erlauben): "
                     + ", ".join(m.mention for m in blocked) + " – nichts umgeleitet.")
    lines.append(vnote)
    await inter.followup.send("\n".join(lines)[:1900], ephemeral=True, allowed_mentions=discord.AllowedMentions.none())
