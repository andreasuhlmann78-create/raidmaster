"""Skillung (D-3 Schritt 25, ab Bot 1.5.172): die im Spiel eingelesene Skillung in Profil und Raid-Anmeldungen
übernehmen (Rolle Tank/Heiler/Nahkampf/Fernkampf) und das Mitglied per PN informieren.

UNVERÄNDERT aus bot.py verschoben: sync_specs. bot.py importiert dieses Modul nach "grund.bot = bot" und
übernimmt sync_specs (nach jedem Upload). Weg A (Antwort der Prüf-Sitzung 15.11. 20:48).
"""
from __future__ import annotations

import discord

import grund
import raidmaster_data as rmd
from kern import book, cfg, log
from raidanzeige_bot import update_raid_message

bot = grund.bot
assert bot is not None, "skillung_bot erst nach grund.bot = bot importieren"


async def sync_specs():
    """Skillungen aus dem Addon in die Discord-Profile übernehmen."""
    changes = book.apply_specs(rmd.specs_from_db(bot.dkp_db))
    if not changes:
        return
    log.info("Skillungen übernommen: %s", ", ".join(f"{c['name']} {rmd.spec_short(c['spec'])}" for c in changes))
    ids = {str(c["user_id"]) for c in changes}
    for raid in book.open_raids():
        if ids & set(raid["signups"].keys()):
            await update_raid_message(raid)
    if not cfg.get("notify_spec_changes", True):
        return
    for c in changes:
        if c["old_role"] == c["role"] or not c["old_role"]:
            continue
        spec = c["spec"]
        text = (f"🧬 Deine Skillung aus dem Spiel wurde übernommen: **{c['name']} – {spec['label']}**" + (f" ({spec['points']})" if spec.get("points") else "") + ".\n"
                f"Deine Rolle für Raids ist jetzt **{rmd.ROLES.get(c['role'], c['role'])}** "
                f"(vorher {rmd.ROLES.get(c['old_role'], c['old_role'])}). Ändern kannst du das jederzeit mit `/charakter`.")
        try:
            user = bot.get_user(c["user_id"]) or await bot.fetch_user(c["user_id"])
            await user.send(text)
        except discord.HTTPException:
            pass
