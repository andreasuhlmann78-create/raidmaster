"""
RaidMaster-Bot – automatische Einrichtung des Discord-Servers.

Legt Rollen, Kategorien, Kanäle und Berechtigungen an. Jeder Raid bekommt eine
eigene Kategorie (Anmeldung, Taktik, DKP, Loot). Bereits vorhandene Rollen und
Kanäle (gleicher Name) werden wiederverwendet, nichts wird gelöscht.
Der Befehl kann daher gefahrlos mehrmals ausgeführt werden.
"""

from __future__ import annotations

import asyncio
import os
import discord

# ---------------------------------------------------------------------------
# Aufbau
# ---------------------------------------------------------------------------

ROLES = [
    # Name, Farbe, getrennt anzeigen
    ("Offizier", 0xFF8C1A, True),
    ("Raidleitung", 0xE74C3C, True),
    ("Raider", 0x2ECC71, True),
    ("Gast", 0x95A5A6, False),
]
MENTIONABLE = {"Gast"}   # PUG-Spieler werden bei neuen PUG-Raids angepingt

# Raids mit eigener Kategorie: Topf-Schlüssel (wie im Addon), Name, Emoji, Kanal-Präfix
RAIDS = [
    ("mc", "Molten Core", "🔥", "mc"),
    ("ony", "Onyxias Hort", "🐉", "onyxia"),
    ("barrow", "Barrow Deeps", "🌲", "barrow"),
    ("hyjal", "Hyjalgipfel", "🌋", "hyjal"),
    ("bwl", "Pechschwingenhort", "🖤", "bwl"),
    ("zg", "Zul'Gurub", "🐍", "zg"),
    ("aq20", "Ruinen von Ahn'Qiraj", "🪲", "aq20"),
    ("aq40", "Tempel von Ahn'Qiraj", "🐞", "aq40"),
    ("naxx", "Naxxramas", "💀", "naxx"),
]

# Ältere Kanalnamen -> neue Namen in den Raid-Kategorien (wird nur umbenannt, wenn das Ziel fehlt)
RENAMES = {
    "raid-anmeldung": "mc-anmeldung",
    "raid-taktik": "mc-taktik",
    "loot": "mc-loot",
    "dkp-stand": "mc-dkp",
    "dkp-molten-core": "mc-dkp",
    "dkp-onyxia": "onyxia-dkp",
    "dkp-barrow-deeps": "barrow-dkp",
    "dkp-hyjal": "hyjal-dkp",
}

# Modus einer Kategorie bzw. eines Kanals:
#   None       = normale Rechte (alle dürfen schreiben)
#   "readonly" = alle lesen, nur Offiziere/Raidleitung und der Bot schreiben
#   "botonly"  = alle lesen, nur der Bot schreibt
#   "private"  = nur Offiziere/Raidleitung und der Bot sehen den Bereich
#   "officers" = ausschließlich die Rolle Offizier (und der Bot) sieht den Kanal
#   "hidden"   = nur der Bot (und Admins) sehen den Kanal
#   "officers_readonly" = Offiziere/Raidleitung lesen, nur der Bot schreibt
#   "officers_only" = nur die Rolle Offizier (und der Bot) sieht und schreibt
#   "officers_write" = alle lesen, nur die Rolle Offizier (und der Bot, Admins) schreibt
BASE_TOP = [
    {
        "name": "📌 INFO", "mode": "readonly", "guest": True,
        "channels": [
            ("text", "willkommen", "Begrüßung und Infos zur Gilde", None),
            ("text", "regeln", "Gilden-, DKP- und Lootregeln", None),
            ("text", "ankündigungen", "Neuigkeiten, Raidzeiten und Änderungen", None),
        ],
    },
    {
        "name": "⚔️ RAID-ORGA", "mode": None,
        "channels": [
            ("text", "einteilung", "Aufstellung, Gruppen, Heil-, Entfluch- und CC-Einteilung (automatisch vom Bot)", "readonly"),
        ],
    },
    {
        # direkt unter RAID-ORGA; auch Gäste (PUG) sehen sie, damit sie das Addon laden können
        "name": "🧩 RAID-ADDON", "mode": None, "guest": True, "after": "⚔️ RAID-ORGA",
        "channels": [
            ("text", "raid-addon", "Download der aktuellen RaidMaster-Addon-Version (automatisch vom Bot)", "botonly"),
            ("text", "addon-hilfe", "Fragen, Probleme und Wünsche zum RaidMaster-Addon", None),
        ],
    },
    {
        # eigene Addons von GoldSentinel – nur für Offiziere, direkt unter RAID-ADDON
        "name": "Addon's by GoldSentinel", "mode": "officers_only", "after": "🧩 RAID-ADDON",
        "old_names": ["🛠️ Addons by GoldSentinel"],
        "channels": [
            ("text", "aktionshaus", "AH Analyzer Pro – Auktionshaus-Analyse (nur Offiziere)", "officers_only"),
        ],
    },
]

BASE_BOTTOM = [
    {
        "name": "🎲 PUG", "mode": None, "guest": True,
        "channels": [
            ("text", "pug-anmeldung", "PUG-Raids – Anmeldung per Knopf, Soft Reserve über softres.it", "readonly"),
            ("text", "pug-chat", "Absprachen für PUG-Raids", None),
            ("voice", "PUG-Raid", None, None),
        ],
    },
    {
        "name": "💬 ALLGEMEIN", "mode": None,
        "channels": [
            ("text", "allgemein", "Plaudern über alles", None),
            ("text", "handwerk-und-handel", "Berufe, Rezepte und Auktionshaus", None),
            ("text", "gruppensuche", "Dungeons, Quests und Twinks", None),
        ],
    },
    {
        "name": "🔊 SPRACHE", "mode": None,
        "channels": [
            ("voice", "Raid", None, None),
            ("voice", "Allgemein", None, None),
            ("voice", "AFK", None, None),
        ],
    },
    {
        "name": "🔒 OFFIZIERE", "mode": "private",
        "channels": [
            ("text", "offiziere", "Absprachen der Gildenleitung", None),
            ("text", "befehlsliste", "Alle Bot-Befehle – wird vom Bot automatisch aktuell gehalten", "officers_readonly"),
            ("text", "bot-befehle", "Zum Testen von Bot-Befehlen", None),
            ("text", "bot-daten", "Daten aus dem Spiel (Uploader) und Update-Meldungen – nur für den Bot", "hidden"),
            ("voice", "Offiziere", None, "officers"),
        ],
    },
]

DEFAULT_DKP = {
    "dkpStart": 10, "dkpEnd": 10, "firstKillDouble": True, "minBid": 10,
    "bidIncrement": 5, "auctionTime": 30, "decayPct": 10,
}


def slug(name: str) -> str:
    s = name.lower().replace("ä", "ae").replace("ö", "oe").replace("ü", "ue").replace("ß", "ss")
    s = "".join(ch if ch.isalnum() else "-" for ch in s)
    while "--" in s:
        s = s.replace("--", "-")
    return s.strip("-")[:60] or "raid"


def raid_category(key: str, name: str, emoji: str = "🗡️", prefix: str | None = None) -> dict:
    """Kategorie eines Raids mit Anmeldung (inkl. Registrier-Knopf), Sprachkanal, Taktik, DKP und Loot."""
    p = prefix or slug(name)
    return {
        "name": f"{emoji} {name.upper()}", "mode": None, "raid": key, "prefix": p,
        "channels": [
            ("text", f"{p}-anmeldung", f"Anmeldung {name} – per Knopf", "readonly"),
            ("voice", f"🔊 {name}", None, None),
            ("text", f"{p}-taktik", f"Taktik und Fragen zu {name}", None),
            ("text", f"{p}-dkp", f"DKP-Stand {name} (automatisch vom RaidMaster-Bot)", "botonly"),
            ("text", f"{p}-loot", f"Loot-Protokoll {name} (automatisch vom RaidMaster-Bot)", "botonly"),
        ],
    }


def raid_list(extra_pools: dict | None = None) -> list[tuple[str, str, str, str]]:
    raids = list(RAIDS)
    known = {r[0] for r in raids}
    for key, name in (extra_pools or {}).items():
        if key not in known:
            raids.append((key, name, "🗡️", slug(name)))
    return raids


# ---------------------------------------------------------------------------
# Hilfen
# ---------------------------------------------------------------------------

def _find(items, name: str):
    name = name.casefold()
    for item in items:
        if item.name.casefold() == name:
            return item
    return None


def _bot_overwrite() -> discord.PermissionOverwrite:
    return discord.PermissionOverwrite(view_channel=True, send_messages=True, embed_links=True,
                                       attach_files=True, read_message_history=True)


def _overwrites(mode: str | None, guild: discord.Guild, roles: dict) -> dict | None:
    if mode is None:
        return None
    everyone = guild.default_role
    ow = {guild.me: _bot_overwrite()}
    leaders = [roles.get("Offizier"), roles.get("Raidleitung")]
    if mode == "readonly":
        ow[everyone] = discord.PermissionOverwrite(send_messages=False)
        for r in leaders:
            if r:
                ow[r] = discord.PermissionOverwrite(send_messages=True)
    elif mode == "botonly":
        ow[everyone] = discord.PermissionOverwrite(send_messages=False)
    elif mode == "private":
        ow[everyone] = discord.PermissionOverwrite(view_channel=False)
        for r in leaders:
            if r:
                ow[r] = discord.PermissionOverwrite(view_channel=True, send_messages=True)
    elif mode == "hidden":
        ow[everyone] = discord.PermissionOverwrite(view_channel=False)
    elif mode == "officers_only":
        ow[everyone] = discord.PermissionOverwrite(view_channel=False)
        if roles.get("Raidleitung"):
            ow[roles["Raidleitung"]] = discord.PermissionOverwrite(view_channel=False)
        if roles.get("Offizier"):
            ow[roles["Offizier"]] = discord.PermissionOverwrite(view_channel=True, send_messages=True,
                                                                read_message_history=True, attach_files=True)
    elif mode == "officers_write":
        ow[everyone] = discord.PermissionOverwrite(view_channel=True, send_messages=False, add_reactions=True,
                                                   create_public_threads=False, create_private_threads=False,
                                                   send_messages_in_threads=False)
        if roles.get("Raidleitung"):
            ow[roles["Raidleitung"]] = discord.PermissionOverwrite(send_messages=False)
        if roles.get("Offizier"):
            ow[roles["Offizier"]] = discord.PermissionOverwrite(view_channel=True, send_messages=True, manage_messages=True,
                                                                embed_links=True, attach_files=True)
    elif mode == "officers_readonly":
        ow[everyone] = discord.PermissionOverwrite(view_channel=False, send_messages=False)
        for r in leaders:
            if r:
                ow[r] = discord.PermissionOverwrite(view_channel=True, send_messages=False, add_reactions=False,
                                                    create_public_threads=False, create_private_threads=False,
                                                    send_messages_in_threads=False)
    elif mode == "officers":
        ow[everyone] = discord.PermissionOverwrite(view_channel=False, connect=False)
        if roles.get("Raidleitung"):
            ow[roles["Raidleitung"]] = discord.PermissionOverwrite(view_channel=False, connect=False)
        if roles.get("Offizier"):
            ow[roles["Offizier"]] = discord.PermissionOverwrite(view_channel=True, connect=True, speak=True)
    return ow


def _known_roles(guild: discord.Guild) -> dict:
    return {name: _find(guild.roles, name) for name, _, _ in ROLES if _find(guild.roles, name)}


async def _ensure_category(guild, cat_def: dict, roles: dict, report: list, created: dict, new_names: set, reason: str):
    cat_name = cat_def["name"]
    category = _find(guild.categories, cat_name)
    if not category:
        for old in cat_def.get("old_names", []):
            old_cat = _find(guild.categories, old)
            if old_cat:
                await old_cat.edit(name=cat_name, reason=reason)
                report.append(f"✏️ Kategorie **{old}** in **{cat_name}** umbenannt")
                category = old_cat
                break
    cat_ow = _overwrites(cat_def["mode"], guild, roles)
    if category:
        report.append(f"• Kategorie **{cat_name}** war schon vorhanden")
    else:
        kwargs = {"reason": reason}
        if cat_ow:
            kwargs["overwrites"] = cat_ow
        category = await guild.create_category(cat_name, **kwargs)
        report.append(f"✅ Kategorie **{cat_name}** angelegt")

    for kind, name, topic, mode in cat_def["channels"]:
        pool = guild.text_channels if kind == "text" else guild.voice_channels
        channel = _find(pool, name)
        ch_ow = _overwrites(mode, guild, roles) if mode else None
        if channel:
            if channel.category_id != category.id:
                await channel.edit(category=category, sync_permissions=False, reason=reason)
                report.append(f"↪️ {'#' if kind == 'text' else '🔊 '}{name} in {cat_name} verschoben")
            else:
                report.append(f"• {'#' if kind == 'text' else '🔊 '}{name} war schon vorhanden")
            if mode == "officers" and ch_ow:
                await channel.edit(overwrites=ch_ow, reason=reason)
                report.append(f"🔒 {'#' if kind == 'text' else '🔊 '}{name}: nur noch für Offiziere")
        else:
            kwargs = {"category": category, "reason": reason}
            if ch_ow:
                kwargs["overwrites"] = ch_ow if mode == "officers" else {**(cat_ow or {}), **ch_ow}
            if kind == "text":
                if topic:
                    kwargs["topic"] = topic
                channel = await guild.create_text_channel(name, **kwargs)
            else:
                channel = await guild.create_voice_channel(name, **kwargs)
            new_names.add(name)
            report.append(f"✅ {'#' if kind == 'text' else '🔊 '}{name} angelegt")
        created[name] = channel
    return category


async def _place_after(guild, name: str, after: str, report: list, reason: str):
    cat = _find(guild.categories, name)
    anchor = _find(guild.categories, after)
    if not cat or not anchor:
        return
    ordered = sorted(guild.categories, key=lambda c: c.position)
    if ordered.index(cat) == ordered.index(anchor) + 1:
        return
    try:
        await cat.edit(position=anchor.position + 1, reason=reason)
        report.append(f"↕️ Kategorie **{name}** unter **{after}** verschoben")
        await asyncio.sleep(1.5)   # Discord meldet die neuen Positionen kurz verzögert
    except discord.HTTPException:
        report.append(f"⚠️ Kategorie **{name}** konnte nicht verschoben werden")


async def _hide_from_guests(guild, cat_def: dict, roles: dict, created: dict, report: list, reason: str):
    """Rolle Gast sieht nur INFO und PUG: alle anderen Kategorien und ihre Kanäle für Gast ausblenden.
    Gildenmitglieder sind davon nicht betroffen (sie haben die Rolle Gast nicht)."""
    guest = roles.get("Gast")
    if not guest or cat_def.get("guest"):
        return 0
    targets = []
    category = _find(guild.categories, cat_def["name"])
    if category:
        targets.append(category)
    for _, name, _, _ in cat_def["channels"]:
        if name in created:
            targets.append(created[name])
    changed = 0
    for t in targets:
        if t.overwrites_for(guest).view_channel is False:
            continue
        try:
            await t.set_permissions(guest, view_channel=False, reason=reason)
            changed += 1
        except discord.HTTPException:
            report.append(f"⚠️ {t.name}: Gast konnte nicht ausgeblendet werden")
    return changed


def _store_raid_channels(cfg: dict, raid_def: dict, created: dict):
    p = raid_def["prefix"]
    ids = {}
    voice_name = next((n for k, n, _, _ in raid_def["channels"] if k == "voice"), None)
    for kind, ch_name in (("signup", f"{p}-anmeldung"), ("voice", voice_name), ("tactics", f"{p}-taktik"),
                          ("dkp", f"{p}-dkp"), ("loot", f"{p}-loot")):
        if ch_name in created:
            ids[kind] = created[ch_name].id
    cfg.setdefault("raid_channels", {})[raid_def["raid"]] = ids
    # Kompatibilität mit älteren Einträgen
    if "dkp" in ids:
        cfg.setdefault("dkp_channels", {})[raid_def["raid"]] = ids["dkp"]


# ---------------------------------------------------------------------------
# Texte
# ---------------------------------------------------------------------------

def welcome_text(guild_name: str, channels: dict | None = None, officer_role_id: int | None = None) -> str:
    """Einladender Willkommenstext für #willkommen. channels: {Kanalname: ID} für klickbare Verweise."""
    channels = channels or {}

    def ch(name: str) -> str:
        return f"<#{channels[name]}>" if channels.get(name) else f"**#{name}**"

    officer = f"<@&{officer_role_id}>" if officer_role_id else "**Offizier**"
    name = guild_name or "unserer Gilde"
    return (
        f"⚔️ **Willkommen bei {name} auf WoW Forever!** ⚔️\n\n"
        "Schön, dass du da bist! Wir sind eine Gilde, die gemeinsam Raids erlebt – mit Plan, fairer Lootverteilung "
        "und vor allem mit Spaß. Ob erfahrener Raider oder frisch auf Stufe 60: Bei uns findest du deinen Platz.\n\n"
        "🏰 **Unsere Raids**\n"
        "🔥 Molten Core · 🐉 Onyxias Hort · 🌲 Barrow Deeps · 🌋 Hyjalgipfel\n"
        "Jeder Raid hat seine eigene Kategorie mit Anmeldung, Sprachkanal, Taktik, DKP-Stand und Loot.\n\n"
        "🚀 **So startest du in 3 Schritten**\n"
        f"**1.** Lies kurz die {ch('regeln')} – dort steht auch, wie unser DKP-System funktioniert.\n"
        f"**2.** Geh in die Anmeldung deines Raids (z. B. {ch('mc-anmeldung')}) und klick auf **📝 Charakter registrieren**. "
        "Klasse, Rolle und Name einmal eintragen – danach meldest du dich mit einem Klick an.\n"
        f"**3.** Lade dir unser Addon **RaidMaster** aus {ch('raid-addon')} herunter. Damit siehst du deine DKP, "
        "bietest auf Items und bekommst deine Aufgaben im Raid direkt angezeigt.\n\n"
        "💎 **Loot bei uns: DKP**\n"
        "Für Pünktlichkeit, jeden Boss und das Raidende gibt es DKP. Damit bietest du im Raid offen auf die Items, "
        "die du dir wünschst – transparent und fair für alle. Deinen Stand siehst du jederzeit im DKP-Kanal deines "
        "Raids oder mit `/dkp`.\n\n"
        "🤝 **Was uns wichtig ist**\n"
        "• Pünktlich und vorbereitet zum Raid (Tränke, Buffs, Taktik gelesen)\n"
        "• Freundlicher Umgang – auch wenn mal etwas schiefgeht\n"
        "• Absagen rechtzeitig per Knopf, damit wir planen können\n\n"
        "❓ **Fragen?**\n"
        f"Schreib einfach in {ch('allgemein')} oder sprich einen {officer} an. "
        f"Bei Problemen mit dem Addon hilft {ch('addon-hilfe')}.\n\n"
        "Wir freuen uns auf viele gemeinsame Bosskills mit dir! 🍻"
    )


def _rules_text(s: dict) -> str:
    first = " (beim ersten Kill doppelt)" if s.get("firstKillDouble", True) else ""
    return (
        "**DKP-Regeln** 🔥\n\n"
        "__Punkte sammeln__\n"
        "• Jeder Raid hat **eigene DKP** – Punkte aus Molten Core gelten nur in Molten Core usw.\n"
        f"• Pünktlich zum Raidstart: **+{s.get('dkpStart', 10)} DKP**\n"
        f"• Jeder Bosskill: **+10 DKP**, besondere Bosse mehr (z. B. Ragnaros **+20**){first}\n"
        f"• Bis zum Raidende dabei: **+{s.get('dkpEnd', 10)} DKP**\n"
        "• Wer auf der Ersatzbank bereitsteht, erhält beim Raidstart einmalig **+10 DKP** (danach keine weiteren Punkte).\n\n"
        "__Items ersteigern__\n"
        "• Epische Items werden mit **offenen Geboten** versteigert – das Gebotsfenster öffnet sich automatisch.\n"
        f"• Mindestgebot **{s.get('minBid', 10)} DKP**, jedes neue Gebot mindestens **+{s.get('bidIncrement', 5)}**, "
        f"Dauer **{s.get('auctionTime', 30)} Sekunden**.\n"
        "• Das höchste Gebot gewinnt, die DKP werden sofort abgezogen.\n"
        "• Ohne Addon: im Spiel `/w <Plündermeister> !bid 50` flüstern.\n\n"
        "__Sonstiges__\n"
        f"• **Verfall:** Jeden Mittwoch nach dem Raid-Reset werden alle DKP um **{s.get('decayPct', 10)} %** reduziert "
        "(gegen Horten) – automatisch, in allen Raids.\n"
        "• **Main vor Twink:** Twinks gewinnen ein Item nur, wenn kein Main bietet. Twinks meldest du mit `/twink` an.\n"
        "• Legendäre Items vergibt die Gildenleitung nach eigener Regel.\n"
        "• Die Gildenleitung kann Werte jederzeit anpassen."
    )


def _raid_rules_texts() -> list[str]:
    """Raid-Regeln in zwei Beiträgen (Discord nimmt höchstens 2000 Zeichen pro Nachricht)."""
    return [(
        "**Raid-Regeln** ⚔️\n\n"
        "__Vor dem Raid__\n"
        "• **Anmelden** im Anmelde-Kanal des Raids – oder rechtzeitig **abmelden**. Wer absagt, macht Platz für die Ersatzbank.\n"
        "• **15 Minuten vor Raidstart** online, eingeladen und am Instanzeingang.\n"
        "• Ausrüstung **repariert**, Taschen frei, genug **Reagenzien, Tränke, Essen** (Jäger: Munition) dabei.\n"
        "• **Fläschchen und Elixiere** nach Möglichkeit. Weltbuffs gibt es auf WoW Forever im Raid nicht – darauf wird nicht gewartet.\n"
        "• Molten Core: **Feuerwiderstand** nach Ansage der Raidleitung.\n"
        "• Addons: **RaidMaster** (aktuelle Version aus #raid-addon) und ein **Boss-Addon** (DBM oder BigWigs) – Pull- und Pausen-Timer laufen darüber.\n"
        "• **Taktik** im Taktik-Kanal des Raids lesen und deine Aufgabe in **#einteilung** nachschauen.\n\n"
        "__Im Raid__\n"
        "• Im **Sprachkanal** sein. Zuhören ist Pflicht, Mikrofon nur bei Bedarf – bei Ansagen herrscht Ruhe.\n"
        "• Es gilt, was der **Raidleiter** ansagt. Schlachtzugwarnungen (Taktik, Symbole) beachten.\n"
        "• **Bereitschafts-Check** sofort beantworten. Kurz weg? „AFK“ in den Raidchat – Pausen macht der Raidleiter.\n"
        "• **Nicht selbst pullen** – auf Ansage bzw. Pull-Timer warten.\n"
        "• Ziele nach **Symbolen**: zuerst Totenkopf, dann Kreuz. Kontrollierte Gegner (z. B. Mond) nicht angreifen.\n"
        "• Nach einem **Wipe**: auf Ansage gemeinsam zurücklaufen, nicht einzeln loslaufen. Kein Schuldzuweisen im Chat – "
        "Fehler bespricht die Raidleitung danach."
    ), (
        "**Raid-Regeln – Loot und Ersatzbank** 🎁\n\n"
        "__Loot im Raid__\n"
        "• Nur auf Items **bieten, die du selbst nutzt** – nicht zum Verkaufen oder Entzaubern.\n"
        "• **Gebote sind verbindlich.** Wer gewinnt, bekommt das Item und die DKP werden abgezogen.\n"
        "• Items ohne Gebot gehen an den Entzauberer bzw. in die Gildenbank.\n"
        "• Fragen zum Loot an den Plündermeister flüstern, nicht in den Raidchat.\n\n"
        "__Früher gehen & Ersatzbank__\n"
        "• Wer **früher gehen** muss, sagt es vorher an. Die Punkte für das Raidende bekommt nur, wer bis zum Schluss bleibt.\n"
        "• **Ersatzbank:** während des Raids im Discord erreichbar sein und bei einer Einladung zügig kommen.\n"
        "• Die Raidleitung kann diese Regeln jederzeit anpassen."
    )]


def rules_posts(dkp_settings: dict | None = None) -> list[str]:
    """Beiträge in #regeln: DKP-Regeln und Raid-Regeln (je eine Nachricht, der Bot hält sie aktuell)."""
    s = dict(DEFAULT_DKP)
    s.update(dkp_settings or {})
    return [_rules_text(s)] + _raid_rules_texts()


def _raid_howto_text(name: str) -> str:
    return (
        f"**Anmeldung {name}** 📋\n"
        "• Offiziere erstellen Raids mit `/raid erstellen` – sie erscheinen automatisch hier.\n"
        "• Klicke unter dem Raid auf **Anmelden**, **Ersatzbank**, **Vielleicht** oder **Abmelden**.\n"
        "• Mit **Charakter ändern** oder `/charakter` wechselst du Klasse, Rolle oder Namen.\n"
        "• Vor dem Raid erinnert dich der Bot, die Aufstellung steht in **#einteilung**."
    )


def _pug_howto_text() -> str:
    return (
        "**PUG-Raids** 🎲\n"
        "• Offiziere erstellen PUG-Raids mit `/raid erstellen` und **modus: PUG-Raid**.\n"
        "• Einmal registrieren (Knopf unten), dann bei jedem Raid per Knopf anmelden.\n"
        "• Soft Reserve und Loot laufen über **softres.it** – den Link findest du direkt am Raid.\n"
        "• Das Addon **RaidMaster** aus **#raid-addon** ist empfohlen, aber kein Muss."
    )


def _bot_commands_text() -> str:
    return (
        "**Bot-Befehle für die Gildenleitung**\n"
        "`/raid erstellen` (mit Raid-Auswahl) · `/raid aufstellung` · `/raid liste` · `/raid schliessen` · `/raid oeffnen` · "
        "`/raid absagen` · `/raid export` · `/raid taktik`\n"
        "`/dkp` · `/dkpliste` · `/addon`\n"
        "`/raidmaster-status` – zeigt Datenstand, Uploads und installierte Version\n"
        "`/pug-einladung` – Einladungslink für PUG-Spieler (Rolle Gast)\n"
        "`/willkommen` – Willkommenstext in #willkommen posten/aktualisieren (Admins)\n"
        "`/uploader` – Einrichtung für den Daten-Uploader auf dem PC der Raidleitung (Admins)\n"
        "`/update` – Update jetzt prüfen bzw. eine Update-ZIP einspielen (Admins)\n"
        "`/raidmaster-einrichten` – Kanäle und Rollen erneut prüfen/ergänzen"
    )


async def _replace_old_pug_text(channel, guild, report: list):
    """Veraltete PUG-Anleitung des Bots durch die aktuelle ersetzen."""
    if not channel:
        return
    current = _pug_howto_text()
    found = False
    try:
        async for msg in channel.history(limit=50):
            text = msg.content or ""
            if msg.author.id == guild.me.id and text.startswith("**PUG-Raids") and text != current:
                await msg.delete()
                found = True
        if found:
            await channel.send(current)
            report.append("✏️ PUG-Anleitung in #pug-anmeldung aktualisiert (softres.it)")
    except (discord.HTTPException, AttributeError):
        pass


async def _post_pug_registration(channel, cfg: dict, report: list):
    if not channel or cfg.get("pug_reg_message"):
        return
    view = discord.ui.View(timeout=None)
    view.add_item(discord.ui.Button(label="Als PUG-Spieler registrieren", emoji="🎲",
                                    style=discord.ButtonStyle.success, custom_id="rm:pugreg:0"))
    try:
        msg = await channel.send(
            "**Neu hier und willst bei unseren PUG-Raids mitspielen?** 🎲\n"
            "Klick auf den Knopf: Du bekommst die Rolle **Gast**, legst deinen Charakter fest und wirst "
            "bei jedem neuen PUG-Raid benachrichtigt.", view=view)
        cfg["pug_reg_message"] = msg.id
        report.append("✅ Registrierung für PUG-Spieler in #pug-anmeldung gepostet")
    except discord.HTTPException:
        report.append("⚠️ PUG-Registrierung konnte nicht gepostet werden")


async def _post_raid_registration(channel, cfg: dict, key: str, name: str, report: list):
    """Fester Registrier-Knopf in der Anmeldung eines Raids (für Gildenspieler, ohne Rolle Gast)."""
    posted = cfg.setdefault("raid_reg_messages", {})
    if not channel or posted.get(key):
        return
    view = discord.ui.View(timeout=None)
    view.add_item(discord.ui.Button(label="Charakter registrieren", emoji="📝",
                                    style=discord.ButtonStyle.success, custom_id=f"rm:raidreg:{key}"))
    try:
        msg = await channel.send(
            f"**Bei {name} dabei sein?** 📝\n"
            "Einmal registrieren: Klasse, Rolle und Charakternamen festlegen. Danach meldest du dich bei jedem "
            f"{name}-Raid mit einem Klick an. Deine Skillung übernimmt das Addon RaidMaster automatisch.", view=view)
        posted[key] = msg.id
        report.append(f"✅ Registrier-Knopf in #{channel.name} gepostet")
    except discord.HTTPException:
        report.append(f"⚠️ Registrier-Knopf in #{getattr(channel, 'name', '?')} konnte nicht gepostet werden")


# ---------------------------------------------------------------------------
# Einrichtung
# ---------------------------------------------------------------------------

async def run_setup(guild: discord.Guild, invoker: discord.Member, cfg: dict, dkp_settings: dict | None = None,
                    extra_pools: dict | None = None) -> list[str]:
    reason = "RaidMaster-Einrichtung"
    report: list[str] = []
    settings = dict(DEFAULT_DKP)
    settings.update(dkp_settings or {})

    # Rollen
    roles: dict[str, discord.Role] = {}
    for name, color, hoist in ROLES:
        role = _find(guild.roles, name)
        if role:
            report.append(f"• Rolle **{name}** war schon vorhanden")
            if name in MENTIONABLE and not role.mentionable:
                try:
                    await role.edit(mentionable=True, reason=reason)
                except discord.HTTPException:
                    pass
        else:
            role = await guild.create_role(name=name, colour=discord.Colour(color), hoist=hoist,
                                           mentionable=name in MENTIONABLE, reason=reason)
            report.append(f"✅ Rolle **{name}** angelegt")
        roles[name] = role

    officer = roles.get("Offizier")
    if officer and officer not in invoker.roles:
        try:
            await invoker.add_roles(officer, reason=reason)
            report.append("✅ Dir wurde die Rolle **Offizier** gegeben")
        except discord.HTTPException:
            report.append("⚠️ Konnte dir die Rolle Offizier nicht geben – bitte selbst zuweisen")

    # Alte Kanalnamen auf die neue Struktur umbenennen
    for old, new in RENAMES.items():
        ch = _find(guild.text_channels, old)
        if ch and not _find(guild.text_channels, new):
            await ch.edit(name=new, reason=reason)
            report.append(f"✏️ #{old} in #{new} umbenannt")

    created: dict = {}
    new_names: set[str] = set()
    raids = [raid_category(*r) for r in raid_list(extra_pools)]
    for cat_def in BASE_TOP + raids + BASE_BOTTOM:
        await _ensure_category(guild, cat_def, roles, report, created, new_names, reason)
    # Kategorien mit fester Position (z. B. RAID-ADDON direkt unter RAID-ORGA)
    for cat_def in BASE_TOP + raids + BASE_BOTTOM:
        if cat_def.get("after"):
            await _place_after(guild, cat_def["name"], cat_def["after"], report, reason)
    hidden = 0
    for cat_def in BASE_TOP + raids + BASE_BOTTOM:
        hidden += await _hide_from_guests(guild, cat_def, roles, created, report, reason)
    if hidden:
        report.append(f"✅ Rolle **Gast** sieht nur noch INFO und PUG ({hidden} Kanäle/Kategorien ausgeblendet)")

    # Begrüßungs- und Infotexte nur in neu angelegte Kanäle
    texts = {
        "regeln": _rules_text(settings),
        "pug-anmeldung": _pug_howto_text(),
        "bot-befehle": _bot_commands_text(),
    }
    for r in raids:
        texts[f"{r['prefix']}-anmeldung"] = _raid_howto_text(r["name"].split(" ", 1)[1].title())
    for name, text in texts.items():
        ch = created.get(name)
        if ch and name in new_names:
            try:
                await ch.send(text)
            except discord.HTTPException:
                report.append(f"⚠️ Text in #{name} konnte nicht gepostet werden")

    await _replace_old_pug_text(created.get("pug-anmeldung"), guild, report)
    await _post_pug_registration(created.get("pug-anmeldung"), cfg, report)
    for r in raids:
        await _post_raid_registration(created.get(f"{r['prefix']}-anmeldung"), cfg, r["raid"],
                                      r["name"].split(" ", 1)[1].title(), report)

    # Einstellungen des Bots aktualisieren
    for r in raids:
        _store_raid_channels(cfg, r, created)
    mc = cfg.get("raid_channels", {}).get("mc", {})
    if mc.get("dkp"):
        cfg["dkp_channel_id"] = mc["dkp"]
    if mc.get("loot"):
        cfg["loot_channel_id"] = mc["loot"]
    old_chats = [c.name for c in guild.text_channels
                 if any(c.name == f"{r['prefix']}-chat" for r in raids)]
    if old_chats:
        report.append("ℹ️ Die Raid-Chats sind jetzt Sprachkanäle. Die alten Textkanäle "
                      + ", ".join(f"#{n}" for n in old_chats) + " kannst du löschen.")
    if _find(guild.text_channels, "softreserve"):
        report.append("ℹ️ #softreserve wird nicht mehr gebraucht (Soft Reserve wurde entfernt) – du kannst den Kanal löschen.")
    cfg.pop("softreserve_channel_id", None)
    for key, ch_name in (("assignment_channel_id", "einteilung"),
                         ("officer_channel_id", "offiziere"), ("addon_channel_id", "raid-addon"),
                         ("announce_channel_id", "ankündigungen"), ("pug_channel_id", "pug-anmeldung"),
                         ("data_channel_id", "bot-daten"), ("botcmd_channel_id", "bot-befehle"),
                         ("welcome_channel_id", "willkommen"), ("command_list_channel_id", "befehlsliste"),
                         ("aktionshaus_channel_id", "aktionshaus")):
        if ch_name in created:
            cfg[key] = created[ch_name].id
    creator_roles = list(cfg.get("raid_creator_roles") or [])
    for r in ("Offizier", "Raidleitung"):
        if r not in creator_roles:
            creator_roles.append(r)
    cfg["raid_creator_roles"] = creator_roles
    report.append("✅ Alle Kanäle in der config.json eingetragen")

    report.append("")
    report.append("Fertig! Weise deinen Offizieren die Rolle **Offizier** zu. Leere alte Kategorien "
                  "(z. B. „📊 DKP“, „⚔️ RAID“, „Textkanäle“) kannst du löschen.")
    return report


async def ensure_raid(guild: discord.Guild, cfg: dict, key: str, name: str, emoji: str = "🗡️",
                      prefix: str | None = None) -> list[str]:
    """Kategorie für einen Raid anlegen (neu erkannter Raid oder neu in der Raidliste)."""
    report: list[str] = []
    roles = _known_roles(guild)
    created: dict = {}
    new_names: set[str] = set()
    raid_def = raid_category(key, name, emoji, prefix)
    await _ensure_category(guild, raid_def, roles, report, created, new_names, "RaidMaster: neuer Raid")
    await _hide_from_guests(guild, raid_def, roles, created, report, "RaidMaster: neuer Raid")
    sign = created.get(f"{raid_def['prefix']}-anmeldung")
    if sign and sign.name in new_names:
        try:
            await sign.send(_raid_howto_text(name))
        except discord.HTTPException:
            pass
    await _post_raid_registration(sign, cfg, key, name, report)
    _store_raid_channels(cfg, raid_def, created)
    return report


# ---------------------------------------------------------------------------
# Gildenregeln (Zusammenleben in der Gilde, nicht Raid): eigene Kategorie unter INFO.
# Alle lesen, nur Offiziere, Admins und der Bot schreiben. Texte stehen in guild_rules.json.
# ---------------------------------------------------------------------------
RULES_CATEGORY = "📜 REGELN"


def guild_rules() -> list[dict]:
    import json
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "guild_rules.json")
    try:
        with open(path, encoding="utf-8") as f:
            return [c for c in (json.load(f).get("channels") or []) if c.get("key")]
    except (OSError, ValueError):
        return []


async def ensure_rules_category(guild: discord.Guild, cfg: dict) -> list[str]:
    """Kategorie 📜 REGELN mit den Kanälen aus guild_rules.json anlegen (fehlende ergänzen, Rechte setzen)."""
    rules = guild_rules()
    if not rules:
        return []
    reason = "RaidMaster: Gildenregeln"
    roles = _known_roles(guild)
    cat_def = {"name": RULES_CATEGORY, "mode": "officers_write",
               "channels": [("text", c["key"], c.get("topic"), "officers_write") for c in rules]}
    report: list[str] = []
    created: dict = {}
    category = await _ensure_category(guild, cat_def, roles, report, created, set(), reason)
    # Rechte immer auf "nur Offiziere schreiben" halten
    ow = _overwrites("officers_write", guild, roles)
    try:
        if category.overwrites != ow:
            await category.edit(overwrites=ow, reason=reason)
    except discord.HTTPException:
        pass
    for name, ch in created.items():
        try:
            if ch.overwrites != ow:
                await ch.edit(overwrites=ow, reason=reason)
        except discord.HTTPException:
            pass
    await _place_after(guild, RULES_CATEGORY, "📌 INFO", report, reason)
    cfg["rules_channels"] = {name: ch.id for name, ch in created.items()}
    return [r for r in report if r.startswith(("✅", "↪️", "↕️"))]
