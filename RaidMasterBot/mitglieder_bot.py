"""Mitglieder-Bereich und Bewerbung (D-3 Schritt 17, ab Bot 1.5.163): /mitgliederbereich einrichten (Vorschau,
dann bestaetigen:True), /mitglied aufnehmen|entfernen, Bewerbungs-Kanal mit Karte, Bewerbung per Formular und
privatem Thread; neue Kanäle in den Mitglieder-Kategorien hält der Bot automatisch dicht.

UNVERÄNDERT aus bot.py verschoben: der ganze Abschnitt "Mitglieder-Bereich und Bewerbung" (maintain_member_area bis
handle_apply_button, samt beiden bot.tree.add_command). Logik und Texte stehen in member_area.py.
bot.py importiert dieses Modul nach "grund.bot = bot" (zwei Befehlsgruppen werden beim Import angemeldet) und
übernimmt maintain_member_area und handle_apply_button. Weg A (Antwort der Prüf-Sitzung 15.11. 20:48).
"""
from __future__ import annotations

import time

import discord
from discord import app_commands

import grund
import member_area
import server_setup
from bot_hilfen import apply_card_view, ensure_member_role
from grund import NO_PING, bot_guild, channel_by_id, is_admin, post_bot_log
from kern import cfg, log, save_config, state
from willkommen_bot import ensure_welcome

bot = grund.bot
assert bot is not None, "mitglieder_bot erst nach grund.bot = bot importieren"


# ---------------------------------------------------------------------------
# Mitglieder-Bereich und Bewerbung (ab Bot 1.5.115, Discord-Projekt DC2/DC3, Freigabe des Nutzers 12.11.2026)
# Logik und Texte in member_area.py. Eingerichtet wird nur von Hand mit /mitgliederbereich einrichten (Vorschau, dann
# bestaetigen:True); danach hält der Bot neue Kanäle in den Mitglieder-Kategorien automatisch dicht.
# ---------------------------------------------------------------------------

async def maintain_member_area() -> list[str]:
    """Nach der Einrichtung: Kanäle, die neu dazukamen und noch für alle sichtbar sind, nur für Mitglieder freigeben."""
    guild = bot_guild()
    if guild is None or not cfg.get("member_area"):
        return []
    perms = guild.me.guild_permissions
    if not (perms.manage_roles and perms.manage_channels):
        return []
    roles = member_area.member_roles(guild)
    if not roles:
        return []
    report = []
    for item in member_area.plan_items(guild):
        try:
            if await member_area.gate_item(item, guild, roles):
                report.append(member_area._label(item))
        except discord.HTTPException as e:
            report.append(f"⚠️ {item.name}: {e}")
    return report


async def ensure_apply_channel(guild) -> discord.TextChannel:
    """Kategorie 📝 BEWERBUNG mit #bewerbung (fehlt sie: anlegen, unter 📜 REGELN) und die Karte mit dem Knopf."""
    ch = server_setup.find_channel(guild.text_channels, member_area.APPLY_CHANNEL)
    if ch is None:
        cat = server_setup._find(guild.categories, member_area.APPLY_CATEGORY)
        if cat is None:
            cat = await guild.create_category(member_area.APPLY_CATEGORY, reason=member_area.REASON)
        ch = await guild.create_text_channel(member_area.APPLY_CHANNEL, category=cat, topic=member_area.APPLY_TOPIC,
                                             overwrites=member_area.apply_overwrites(guild, guild.me),
                                             reason=member_area.REASON)
        try:
            await server_setup.place_first(guild, member_area.APPLY_CATEGORY, member_area.REASON)
        except discord.HTTPException:
            pass
    cfg["apply_channel_id"] = ch.id
    save_config()
    await ensure_apply_card(ch)
    return ch


async def ensure_apply_card(ch):
    text = member_area.apply_card_text(cfg.get("guild_name") or ch.guild.name)
    msg_id = state.data.get("apply_card_message")
    if msg_id:
        try:
            await ch.get_partial_message(int(msg_id)).edit(content=text, view=apply_card_view(), allowed_mentions=NO_PING)
            return
        except discord.HTTPException:
            pass
    msg = await ch.send(text, view=apply_card_view(), allowed_mentions=NO_PING)
    state.data["apply_card_message"] = msg.id
    state.save()


mitgliederbereich_group = app_commands.Group(name="mitgliederbereich",
                                             description="Gildenbereich nur für Mitglieder, Bewerbung für Neue")


@mitgliederbereich_group.command(name="einrichten",
                                 description="Mitglieder-Bereich und #bewerbung einrichten – zuerst Vorschau (Gildenleitung)")
@app_commands.describe(bestaetigen="True = wirklich ausführen; ohne = nur Vorschau, nichts wird geändert")
async def member_area_cmd(inter: discord.Interaction, bestaetigen: bool = False):
    if not is_admin(inter.user):
        await inter.response.send_message("Das dürfen nur der Gildenchef und die Offiziere.", ephemeral=True)
        return
    await inter.response.defer(ephemeral=True, thinking=True)
    guild = inter.guild
    perms = guild.me.guild_permissions
    if not (perms.manage_roles and perms.manage_channels):
        await inter.followup.send("Dem Bot fehlen die Rechte **Rollen verwalten** und **Kanäle verwalten**.", ephemeral=True)
        return
    items = member_area.plan_items(guild)
    new_members = member_area.members_without_role(guild)
    complete = member_area.members_complete(guild)
    has_role = discord.utils.get(guild.roles, name=member_area.MEMBER_ROLE) is not None
    has_apply = server_setup.find_channel(guild.text_channels, member_area.APPLY_CHANNEL) is not None
    if not bestaetigen or not complete:
        await inter.followup.send(member_area.preview_text(guild, items, new_members, has_role, has_apply, complete),
                                  ephemeral=True)
        return
    done = []
    role = await ensure_member_role(guild)
    if not has_role:
        done.append("Rolle **Mitglied** angelegt")
    given = 0
    for m in new_members:
        try:
            await m.add_roles(role, reason=member_area.REASON)
            given += 1
        except discord.HTTPException as e:
            done.append(f"⚠️ {m.display_name}: Rolle nicht vergeben ({e})")
    if given:
        done.append(f"Rolle **Mitglied** an {given} Mitglieder vergeben")
    ch = await ensure_apply_channel(guild)
    done.append(f"Bewerbung in {ch.mention}")
    roles = member_area.member_roles(guild)
    n = 0
    for item in items:
        try:
            if await member_area.gate_item(item, guild, roles):
                n += 1
        except discord.HTTPException as e:
            done.append(f"⚠️ {item.name}: {e}")
    done.append(f"{n} Kategorien/Kanäle nur noch für Mitglieder")
    cfg["member_area"] = True
    save_config()
    try:
        done.append(await ensure_welcome(update=True))
    except Exception:  # noqa: BLE001
        log.exception("Willkommenstext nicht aktualisiert")
    log.info("Mitglieder-Bereich eingerichtet von %s", inter.user)
    await inter.followup.send("✅ **Mitglieder-Bereich eingerichtet**\n• " + "\n• ".join(done), ephemeral=True)
    try:
        await post_bot_log(f"🔐 Mitglieder-Bereich eingerichtet von {inter.user.display_name}: " + "; ".join(done))
    except Exception:  # noqa: BLE001
        pass


bot.tree.add_command(mitgliederbereich_group)

mitglied_group = app_commands.Group(name="mitglied", description="Rolle Mitglied vergeben oder entfernen")


@mitglied_group.command(name="aufnehmen", description="Rolle Mitglied geben, Gast entfernen (Gildenleitung)")
async def member_add_cmd(inter: discord.Interaction, wer: discord.Member):
    if not is_admin(inter.user):
        await inter.response.send_message("Das dürfen nur der Gildenchef und die Offiziere.", ephemeral=True)
        return
    await inter.response.defer(ephemeral=True, thinking=True)
    await inter.followup.send(await admit_member(inter.guild, wer, inter.user), ephemeral=True)


@mitglied_group.command(name="entfernen", description="Rolle Mitglied entfernen (Gildenleitung)")
async def member_remove_cmd(inter: discord.Interaction, wer: discord.Member):
    if not is_admin(inter.user):
        await inter.response.send_message("Das dürfen nur der Gildenchef und die Offiziere.", ephemeral=True)
        return
    role = discord.utils.get(inter.guild.roles, name=member_area.MEMBER_ROLE)
    if role is None or role not in wer.roles:
        await inter.response.send_message(f"{wer.display_name} hat die Rolle Mitglied nicht.", ephemeral=True)
        return
    await wer.remove_roles(role, reason=f"{member_area.REASON} ({inter.user})")
    await inter.response.send_message(f"Rolle **Mitglied** bei {wer.display_name} entfernt.", ephemeral=True)


bot.tree.add_command(mitglied_group)


async def admit_member(guild, member, by) -> str:
    role = await ensure_member_role(guild)
    guest = discord.utils.get(guild.roles, name=member_area.GUEST_ROLE)
    await member.add_roles(role, reason=f"{member_area.REASON} ({by})")
    if guest is not None and guest in member.roles:
        await member.remove_roles(guest, reason=f"{member_area.REASON} ({by})")
    try:
        await member.send(f"🎉 Willkommen in der Gilde **{cfg.get('guild_name') or guild.name}**! Du siehst jetzt den ganzen "
                          "Gildenbereich im Discord. Registriere deinen Charakter einmal mit `/charakter`.")
    except discord.HTTPException:
        pass
    return f"✅ {member.display_name} ist jetzt **Mitglied**."


class ApplyModal(discord.ui.Modal):
    def __init__(self):
        super().__init__(title="Bewerbung")
        self.char = discord.ui.TextInput(label="Charaktername", max_length=40)
        self.klasse = discord.ui.TextInput(label="Klasse", max_length=30, placeholder="z. B. Krieger, Priester …")
        self.stufe = discord.ui.TextInput(label="Stufe", max_length=5, placeholder="z. B. 23")
        self.zeiten = discord.ui.TextInput(label="Spielzeiten und WoW-Erfahrung", style=discord.TextStyle.paragraph,
                                           required=False, max_length=800)
        self.quelle = discord.ui.TextInput(label="Wie hast du uns gefunden? (freiwillig)", required=False, max_length=200)
        for i in (self.char, self.klasse, self.stufe, self.zeiten, self.quelle):
            self.add_item(i)

    async def on_submit(self, inter: discord.Interaction):
        await inter.response.defer(ephemeral=True, thinking=True)
        ch = await channel_by_id(cfg.get("apply_channel_id")) or server_setup.find_channel(
            inter.guild.text_channels, member_area.APPLY_CHANNEL)
        if ch is None:
            await inter.followup.send("Die Bewerbung ist gerade nicht eingerichtet – schreib bitte einem Offizier.", ephemeral=True)
            return
        answers = {"char": self.char.value, "klasse": self.klasse.value, "stufe": self.stufe.value,
                   "zeiten": self.zeiten.value, "quelle": self.quelle.value}
        try:
            thread = await ch.create_thread(name=member_area.thread_name(self.char.value, inter.user.display_name),
                                            type=discord.ChannelType.private_thread, invitable=False,
                                            auto_archive_duration=10080, reason="Bewerbung")
            await thread.add_user(inter.user)
            officer = discord.utils.get(inter.guild.roles, name="Offizier")
            v = discord.ui.View(timeout=None)
            v.add_item(discord.ui.Button(label="Aufnehmen", emoji="✅", style=discord.ButtonStyle.success,
                                         custom_id=f"rmapply:ok:{inter.user.id}"))
            v.add_item(discord.ui.Button(label="Ablehnen", emoji="✖️", style=discord.ButtonStyle.secondary,
                                         custom_id=f"rmapply:no:{inter.user.id}"))
            await thread.send(member_area.application_text(inter.user.mention, officer.mention if officer else "Offiziere",
                                                           answers), view=v,
                              allowed_mentions=discord.AllowedMentions(roles=True, users=True, everyone=False))
        except discord.HTTPException as e:
            log.warning("Bewerbungs-Thread nicht angelegt: %s", e)
            await inter.followup.send("Das hat leider nicht geklappt – schreib bitte direkt einem Offizier.", ephemeral=True)
            return
        state.data.setdefault("applications", {})[str(inter.user.id)] = {"thread": thread.id, "ts": int(time.time()),
                                                                          "status": "offen"}
        state.save()
        await inter.followup.send(f"✅ Danke! Deine Bewerbung steht in {thread.mention} – dort melden wir uns.", ephemeral=True)


async def handle_apply_button(inter: discord.Interaction, action: str, arg: str):
    if action == "start":
        role = discord.utils.get(inter.guild.roles, name=member_area.MEMBER_ROLE)
        if role is not None and role in getattr(inter.user, "roles", []):
            await inter.response.send_message("Du bist schon Mitglied – schön, dass du da bist!", ephemeral=True)
            return
        old = (state.data.get("applications") or {}).get(str(inter.user.id))
        if old and old.get("status") == "offen":
            th = inter.guild.get_thread(int(old["thread"])) if old.get("thread") else None
            if th is not None and not th.archived:
                await inter.response.send_message(f"Deine Bewerbung läuft schon: {th.mention}", ephemeral=True)
                return
        await inter.response.send_modal(ApplyModal())
        return
    if not is_admin(inter.user):
        await inter.response.send_message("Das entscheiden die Offiziere.", ephemeral=True)
        return
    apps = state.data.setdefault("applications", {})
    entry = apps.setdefault(arg, {})
    if entry.get("status") in ("aufgenommen", "abgelehnt"):
        await inter.response.send_message(f"Schon erledigt: {entry['status']}.", ephemeral=True)
        return
    await inter.response.defer()
    try:
        await inter.message.edit(view=None)
    except discord.HTTPException:
        pass
    member = inter.guild.get_member(int(arg))
    if member is None:
        try:
            member = await inter.guild.fetch_member(int(arg))
        except discord.HTTPException:
            member = None
    if action == "ok":
        if member is None:
            await inter.followup.send("Die Person ist nicht mehr auf dem Server.")
            return
        await admit_member(inter.guild, member, inter.user)
        entry["status"] = "aufgenommen"
        state.save()
        await inter.followup.send(f"✅ {member.mention} ist aufgenommen (von {inter.user.display_name}) – willkommen in der Gilde!",
                                  allowed_mentions=discord.AllowedMentions(users=True, roles=False, everyone=False))
        return
    entry["status"] = "abgelehnt"
    state.save()
    await inter.followup.send("Danke für deine Bewerbung und dein Interesse an unserer Gilde! Leider passt es im Moment "
                              f"nicht. Alles Gute in Azeroth! (geschlossen von {inter.user.display_name})",
                              allowed_mentions=NO_PING)
    if isinstance(inter.channel, discord.Thread):
        try:
            await inter.channel.edit(archived=True, locked=True, reason="Bewerbung abgelehnt")
        except discord.HTTPException:
            pass
