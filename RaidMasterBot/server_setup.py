"""
RaidMaster-Bot – automatische Einrichtung des Discord-Servers.

Legt Rollen, Kategorien, Kanäle und Berechtigungen an. Jeder Raid bekommt eine
eigene Kategorie (Anmeldung, Taktik, DKP, Loot). Bereits vorhandene Rollen und
Kanäle (gleicher Name) werden wiederverwendet, nichts wird gelöscht.
Der Befehl kann daher gefahrlos mehrmals ausgeführt werden.
"""

from __future__ import annotations

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
BASE_TOP = [
    {
        "name": "📌 INFO", "mode": "readonly", "guest": True,
        "channels": [
            ("text", "willkommen", "Begrüßung und Infos zur Gilde", None),
            ("text", "regeln", "Gilden-, DKP- und Lootregeln", None),
            ("text", "ankündigungen", "Neuigkeiten, Raidzeiten und Änderungen", None),
            ("text", "raid-addon", "Download der aktuellen RaidMaster-Addon-Version (automatisch vom Bot)", "botonly"),
        ],
    },
    {
        "name": "⚔️ RAID-ORGA", "mode": None,
        "channels": [
            ("text", "einteilung", "Aufstellung, Gruppen, Heil-, Entfluch- und CC-Einteilung (automatisch vom Bot)", "readonly"),
        ],
    },
]

BASE_BOTTOM = [
    {
        "name": "🎲 PUG", "mode": None, "guest": True,
        "channels": [
            ("text", "pug-anmeldung", "PUG-Raids mit Soft Reserve – Anmeldung per Knopf", "readonly"),
            ("text", "softreserve", "Soft Reserves der PUG-Raids – eintragen mit /sr oder Knopf am Raid", "botonly"),
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
    """Kategorie eines Raids mit Anmeldung (inkl. Registrier-Knopf), Chat, Taktik, DKP und Loot."""
    p = prefix or slug(name)
    return {
        "name": f"{emoji} {name.upper()}", "mode": None, "raid": key, "prefix": p,
        "channels": [
            ("text", f"{p}-anmeldung", f"Anmeldung {name} – per Knopf", "readonly"),
            ("text", f"{p}-chat", f"Austausch und Absprachen zu {name}", None),
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
    for kind, ch_name in (("signup", f"{p}-anmeldung"), ("chat", f"{p}-chat"), ("tactics", f"{p}-taktik"),
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

def _welcome_text() -> str:
    return (
        "**Willkommen in unserer Gilde!** 👋\n\n"
        "• Regeln und DKP-System findest du in **#regeln**.\n"
        "• Jeder Raid hat eine eigene Kategorie: Anmeldung, Chat, Taktik, DKP-Stand und Loot (z. B. **#mc-anmeldung**).\n"
        "• Einmal registrieren: Knopf **Charakter registrieren** in der Anmeldung deines Raids.\n"
        "• Melde dich per Knopf an – beim ersten Mal gibst du Klasse, Rolle und Charakternamen an, danach reicht ein Klick.\n"
        "• Deine DKP pro Raid: im jeweiligen DKP-Kanal oder mit `/dkp`.\n"
        "• Das Addon **RaidMaster** gibt es immer aktuell in **#raid-addon**."
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
        "• Wer auf der Ersatzbank bereitsteht, erhält die Punkte ebenfalls.\n\n"
        "__Items ersteigern__\n"
        "• Epische Items werden mit **offenen Geboten** versteigert – das Gebotsfenster öffnet sich automatisch.\n"
        f"• Mindestgebot **{s.get('minBid', 10)} DKP**, jedes neue Gebot mindestens **+{s.get('bidIncrement', 5)}**, "
        f"Dauer **{s.get('auctionTime', 30)} Sekunden**.\n"
        "• Das höchste Gebot gewinnt, die DKP werden sofort abgezogen.\n"
        "• Ohne Addon: im Spiel `/w <Plündermeister> !bid 50` flüstern.\n\n"
        "__Sonstiges__\n"
        f"• Jede Woche werden alle DKP um **{s.get('decayPct', 10)} %** reduziert (gegen Horten).\n"
        "• Legendäre Items vergibt die Gildenleitung nach eigener Regel.\n"
        "• Die Gildenleitung kann Werte jederzeit anpassen."
    )


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
        "**PUG-Raids mit Soft Reserve** 🎲\n"
        "• Offiziere erstellen PUG-Raids mit `/raid erstellen` und **modus: PUG-Raid mit Soft Reserve**.\n"
        "• Anmelden per Knopf wie gewohnt. Mit **Soft Reserve** trägst du deine Wunsch-Items per **Item-ID** ein "
        "(steht bei Wowhead in der Adresse: item=12345). Alternativ `/sr`.\n"
        "• Alle Reservierungen siehst du in **#softreserve**.\n"
        "• Im Raid: Reservierte Items würfeln nur die Reservierer aus, alles andere: Bedarf `/roll`, Gier `/roll 99`.\n"
        "• Im Spiel kannst du auch im RaidMaster-Addon (Seite **Soft Reserve**) reservieren oder dem Leiter `!sr 12345` flüstern."
    )


def _bot_commands_text() -> str:
    return (
        "**Bot-Befehle für die Gildenleitung**\n"
        "`/raid erstellen` (mit Raid-Auswahl) · `/raid aufstellung` · `/raid liste` · `/raid schliessen` · `/raid oeffnen` · "
        "`/raid absagen` · `/raid export` · `/raid taktik`\n"
        "`/sr` – Soft Reserve für PUG-Raids · `/dkp` · `/dkpliste` · `/addon`\n"
        "`/raidmaster-status` – zeigt Datenstand, Uploads und installierte Version\n"
        "`/uploader` – Einrichtung für den Daten-Uploader auf dem PC der Raidleitung (Admins)\n"
        "`/update` – Update jetzt prüfen bzw. eine Update-ZIP einspielen (Admins)\n"
        "`/raidmaster-einrichten` – Kanäle und Rollen erneut prüfen/ergänzen"
    )


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
    hidden = 0
    for cat_def in BASE_TOP + raids + BASE_BOTTOM:
        hidden += await _hide_from_guests(guild, cat_def, roles, created, report, reason)
    if hidden:
        report.append(f"✅ Rolle **Gast** sieht nur noch INFO und PUG ({hidden} Kanäle/Kategorien ausgeblendet)")

    # Begrüßungs- und Infotexte nur in neu angelegte Kanäle
    texts = {
        "willkommen": _welcome_text(),
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
    for key, ch_name in (("softreserve_channel_id", "softreserve"), ("assignment_channel_id", "einteilung"),
                         ("officer_channel_id", "offiziere"), ("addon_channel_id", "raid-addon"),
                         ("announce_channel_id", "ankündigungen"), ("pug_channel_id", "pug-anmeldung"),
                         ("data_channel_id", "bot-daten"), ("botcmd_channel_id", "bot-befehle")):
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


async def ensure_raid(guild: discord.Guild, cfg: dict, key: str, name: str) -> list[str]:
    """Kategorie für einen neu erkannten Raid anlegen (vom Bot automatisch aufgerufen)."""
    report: list[str] = []
    roles = _known_roles(guild)
    created: dict = {}
    new_names: set[str] = set()
    raid_def = raid_category(key, name)
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
