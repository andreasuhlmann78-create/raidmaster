"""Server-Einrichtung (D-3 Schritt 35, ab Bot 1.5.182): /raidmaster-einrichten – legt Kanäle, Rollen und
Berechtigungen an (server_setup.run_setup), danach Addon-Version, Willkommen, Befehlsliste und DKP-Regeln.

UNVERÄNDERT aus bot.py verschoben. bot.py importiert dieses Modul erst NACH "grund.bot = bot" (der Befehl wird
beim Import angemeldet). Weg A (Antwort der Prüf-Sitzung 15.11. 20:48).
"""
from __future__ import annotations

import grund

bot = grund.bot
assert bot is not None, "einrichten_bot erst nach grund.bot = bot importieren"

import discord  # noqa: E402

import raidmaster_data as rmd  # noqa: E402
import server_setup  # noqa: E402
from kern import cfg, log, save_config  # noqa: E402
from grund import is_admin  # noqa: E402
from ankuendigung_bot import check_addon_release  # noqa: E402
from befehlsliste_bot import ensure_command_list  # noqa: E402
from regeln_bot import ensure_dkp_rules  # noqa: E402
from willkommen_bot import ensure_welcome  # noqa: E402

@bot.tree.command(name="raidmaster-einrichten", description="Legt Kanäle, Rollen und Berechtigungen für die Gilde automatisch an")
async def setup_cmd(inter: discord.Interaction):
    member = inter.user
    if not is_admin(member):
        await inter.response.send_message("Die Einrichtung dürfen nur der Gildenchef und die Offiziere starten.", ephemeral=True)
        return
    me = inter.guild.me
    missing = []
    if not me.guild_permissions.manage_channels:
        missing.append("Kanäle verwalten")
    if not me.guild_permissions.manage_roles:
        missing.append("Rollen verwalten")
    if missing:
        await inter.response.send_message(
            "Dem Bot fehlen dafür einmalig die Rechte: **" + "**, **".join(missing) + "**.\n"
            "So gibst du sie ihm: **Servereinstellungen → Rollen → Raidmaster tool → Berechtigungen** → "
            "die genannten Rechte einschalten → speichern. Danach `/raidmaster-einrichten` erneut ausführen.\n"
            "Nach der Einrichtung kannst du die Rechte wieder ausschalten.",
            ephemeral=True)
        return
    await inter.response.defer(ephemeral=True, thinking=True)
    settings = None
    if bot.dkp_data and isinstance(bot.dkp_data.get("settings"), dict):
        settings = bot.dkp_data["settings"]
    try:
        extra = {k: rmd.pool_name(k, bot.dkp_data) for k in rmd.pool_list(bot.dkp_data or {}) if k not in rmd.POOLS}
        report = await server_setup.run_setup(inter.guild, member, cfg, settings, extra)
        cfg.setdefault("raid_names", {}).update(extra)
        save_config()
        await check_addon_release()
        report.append(await ensure_welcome(update=True))
        report.append(await ensure_command_list())
        report += await ensure_dkp_rules()
    except discord.Forbidden:
        await inter.followup.send("Discord hat eine Aktion verweigert. Prüfe, ob die Rolle **Raidmaster tool** in "
                                  "**Servereinstellungen → Rollen** möglichst weit oben steht, und versuche es erneut.", ephemeral=True)
        return
    text = "\n".join(report)
    while text:
        part, text = text[:1900], text[1900:]
        await inter.followup.send(part, ephemeral=True)
    log.info("Server-Einrichtung durch %s abgeschlossen.", member)
