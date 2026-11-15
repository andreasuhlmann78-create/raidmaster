"""Privatnachrichten über den Bot (D-3 Schritt 6, ab Bot 1.5.151): /pn mit Formular (PnModal).

UNVERÄNDERT aus bot.py verschoben. Vorlagen und Text-Regeln stehen in pn.py; hier nur das, was Discord braucht.
bot.py importiert dieses Modul erst NACH "grund.bot = bot" (der Befehl /pn wird beim Import angemeldet) und
übernimmt PnModal und pn_cmd mit Namen. Weg A (Antwort der Prüf-Sitzung 15.11. 20:48).
"""
from __future__ import annotations

import discord
from discord import app_commands

import grund
import pn
from grund import is_creator
from kern import cfg, log

bot = grund.bot
assert bot is not None, "pn_bot erst nach grund.bot = bot importieren"


class PnModal(discord.ui.Modal):
    """/pn: Text prüfen/schreiben, dann senden (ab 1.5.133)."""
    def __init__(self, member: discord.Member, text: str):
        super().__init__(title=f"PN an {member.display_name}"[:45])
        self.member = member
        self.text = discord.ui.TextInput(label="Nachricht", style=discord.TextStyle.paragraph, default=text[:pn.MAX_LEN],
                                         max_length=pn.MAX_LEN)
        self.add_item(self.text)

    async def on_submit(self, inter: discord.Interaction):
        msg = pn.nachricht(inter.user.display_name, self.text.value, cfg.get("guild_name"))
        if not msg:
            await inter.response.send_message("Leere Nachricht – nichts geschickt.", ephemeral=True)
            return
        try:
            await self.member.send(msg, allowed_mentions=discord.AllowedMentions.none())
        except discord.Forbidden:
            await inter.response.send_message(f"{self.member.mention} nimmt keine Privatnachrichten vom Bot an "
                                              "(Privatsphäre-Einstellung). Nichts geschickt.", ephemeral=True)
            return
        except discord.HTTPException as e:
            await inter.response.send_message(f"Senden fehlgeschlagen ({e.status}).", ephemeral=True)
            return
        log.info(pn.log_line(self.member.id, self.text.value))
        await inter.response.send_message(f"✅ PN an {self.member.mention} geschickt.", ephemeral=True)


@bot.tree.command(name="pn", description="Gildenleitung: einem Mitglied eine Privatnachricht über den Bot schicken")
@app_commands.describe(mitglied="Empfänger", vorlage="Vorlage zum Vorausfüllen (im Formular noch änderbar)")
@app_commands.choices(vorlage=[app_commands.Choice(name=v, value=k) for k, v in pn.VORLAGEN_NAMEN.items()])
async def pn_cmd(inter: discord.Interaction, mitglied: discord.Member, vorlage: app_commands.Choice[str] | None = None):
    if not is_creator(inter.user):
        await inter.response.send_message("Nur für den Gildenchef und die Offiziere.", ephemeral=True)
        return
    if mitglied.bot:
        await inter.response.send_message("An Bots werden keine PNs geschickt.", ephemeral=True)
        return
    await inter.response.send_modal(PnModal(mitglied, pn.vorlage(vorlage.value if vorlage else None)))
