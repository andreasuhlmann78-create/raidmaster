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
import re
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

# Raids mit eigener Kategorie: Topf-Schlüssel (wie im Addon), Name, Emoji, Kanal-Präfix.
# Stehen in forever_raids.json (neue Raids von WoW Forever einfach dort ergänzen – der Bot legt dann alles an).
_DEFAULT_RAIDS = [
    {"key": "mc", "name": "Molten Core", "emoji": "🔥", "prefix": "mc", "size": 40, "forever": True},
    {"key": "ony", "name": "Onyxias Hort", "emoji": "🐉", "prefix": "onyxia", "size": 40, "forever": True},
    {"key": "barrow", "name": "Barrow Deeps", "emoji": "🌲", "prefix": "barrow", "size": 10, "forever": True},
    {"key": "hyjal", "name": "Hyjalgipfel", "emoji": "🌋", "prefix": "hyjal", "size": 20, "forever": True},
]


def _load_raids() -> list[dict]:
    import json
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "forever_raids.json")
    try:
        with open(path, encoding="utf-8") as f:
            raw = json.load(f).get("raids") or []
    except (OSError, ValueError):
        return list(_DEFAULT_RAIDS)
    out, seen = [], set()
    for r in raw:
        key = str(r.get("key") or "").strip().lower()
        if not key or key in seen or not r.get("name"):
            continue
        seen.add(key)
        prefix = re.sub(r"[^a-z0-9-]", "", str(r.get("prefix") or key).lower()) or key
        extra = []
        for e in r.get("extra_channels") or []:
            name = re.sub(r"[^a-z0-9-]", "", str((e or {}).get("name") or "").lower()).strip("-")
            if name:
                mode = e.get("mode") if e.get("mode") in ("readonly", "botonly") else None
                extra.append(("text", f"{prefix}-{name}", e.get("topic") or None, mode))
        out.append({"key": key, "name": str(r["name"]), "emoji": r.get("emoji") or "🗡️", "prefix": prefix,
                    "size": int(r.get("size") or 40), "forever": bool(r.get("forever")), "extra": extra})
    return out or list(_DEFAULT_RAIDS)


RAID_DEFS = _load_raids()
# Zusätzliche Textkanäle je Raid aus forever_raids.json ("extra_channels"), z. B. #mc-feuerresi
RAID_EXTRA = {r["key"]: r.get("extra") or [] for r in RAID_DEFS}
RAIDS = [(r["key"], r["name"], r["emoji"], r["prefix"]) for r in RAID_DEFS]

# Raids mit eigenem Einteilungs-Kanal unter ⚔️ RAID-ORGA (die Raids von WoW Forever)
ASSIGN_RAIDS = [r["key"] for r in RAID_DEFS if r["forever"]]
RAID_ORGA = "⚔️ RAID-ORGA"


def assignment_channel_name(key: str) -> str:
    prefix = next((p for k, _, _, p in RAIDS if k == key), None) or slug(key)
    return f"einteilung-{prefix}"


def _assignment_channels() -> list:
    out = []
    for key in ASSIGN_RAIDS:
        name = next((n for k, n, _, _ in RAIDS if k == key), key)
        out.append(("text", assignment_channel_name(key),
                    f"Einteilung {name}: Aufstellung, Gruppen, Heil-, Entfluch- und CC-Einteilung (automatisch vom Bot)", "readonly"))
    return out


# Raidgröße je Raid: so viele Plätze hat der Sprachkanal des Raids (unbekannte/eigene Raids: 40)
RAID_SIZES = {r["key"]: r["size"] for r in RAID_DEFS}


def raid_size(key: str, cfg: dict | None = None) -> int:
    """Plätze im Raid (für den Sprachkanal). In config.json änderbar: "raid_sizes": {"mc": 40}."""
    custom = ((cfg or {}).get("raid_sizes") or {}).get(key)
    try:
        n = int(custom) if custom else RAID_SIZES.get(key, 40)
    except (TypeError, ValueError):
        n = RAID_SIZES.get(key, 40)
    return max(1, min(99, n))           # Discord erlaubt 1–99 Plätze


# Ältere Kanalnamen -> neue Namen in den Raid-Kategorien (wird nur umbenannt, wenn das Ziel fehlt)
RENAMES = {
    "einteilung": "einteilung-mc",
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
            # je Raid ein eigener Einteilungs-Kanal (siehe ASSIGN_RAIDS), wird unten eingesetzt
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
            ("text", "buffsentinel", "BuffSentinel – Buff-Erinnerungen, Proc-Buttons und Cooldowns für alle WoW-Versionen",
             "officers_only"),
        ],
    },
]

for _cat in BASE_TOP:
    if _cat["name"] == RAID_ORGA:
        _cat["channels"] = _assignment_channels() + [c for c in _cat["channels"] if not c[1].startswith("einteilung")]

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


def raid_category(key: str, name: str, emoji: str = "🗡️", prefix: str | None = None, cfg: dict | None = None) -> dict:
    """Kategorie eines Raids mit Anmeldung (inkl. Registrier-Knopf), Sprachkanal, Taktik, DKP und Loot.
    Der Sprachkanal hat so viele Plätze wie der Raid (MC 40, Hyjal 20, Barrow Deeps 10 ...)."""
    p = prefix or slug(name)
    return {
        "name": f"{emoji} {name.upper()}", "mode": None, "raid": key, "prefix": p, "voice_limit": raid_size(key, cfg),
        "channels": [
            ("text", f"{p}-anmeldung", f"Anmeldung {name} – per Knopf", "readonly"),
            ("voice", f"🔊 {name}", None, None),
            ("text", f"{p}-taktik", f"Taktik und Fragen zu {name}", None),
            *RAID_EXTRA.get(key, []),
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
            limit = cat_def.get("voice_limit")
            if kind == "voice" and limit and getattr(channel, "user_limit", 0) != limit:
                await channel.edit(user_limit=limit, reason=reason)
                report.append(f"👥 🔊 {name}: höchstens {limit} Personen (Raidgröße)")
        else:
            kwargs = {"category": category, "reason": reason}
            if ch_ow:
                kwargs["overwrites"] = ch_ow if mode == "officers" else {**(cat_ow or {}), **ch_ow}
            if kind == "text":
                if topic:
                    kwargs["topic"] = topic
                channel = await guild.create_text_channel(name, **kwargs)
            else:
                if cat_def.get("voice_limit"):
                    kwargs["user_limit"] = cat_def["voice_limit"]
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
        f"🏡 **Willkommen bei {name}!**\n\n"
        "Schön, dass du den Weg zu uns gefunden hast! Wir sind eine Horde-Gilde auf WoW Forever – eine Gemeinschaft "
        "von Leuten, die gern zusammen spielen, sich gegenseitig helfen und dabei viel lachen. Egal ob du gerade erst "
        "losgelegt hast, einen Twink hochspielst oder längst Stufe 60 bist: Hier bist du richtig.\n\n"
        "🍻 **Was dich bei uns erwartet**\n"
        f"• **Gemeinsam statt allein:** Quests, Dungeons und Elitegebiete machen zusammen mehr Spaß – Mitspieler findest du in {ch('gruppensuche')}.\n"
        "• **Hilfe ohne schiefe Blicke:** Fragen sind ausdrücklich erwünscht, egal wie einfach sie dir vorkommen.\n"
        f"• **Handwerk und Handel:** Rezepte und Materialien tauschen in {ch('handwerk-und-handel')}. Wer was herstellen "
        "kann, verrät dir `/handwerk` – zum Beispiel `/handwerk Feuerschutz`.\n"
        "• **Einfach mal reinschauen:** In den Sprachkanälen ist abends oft jemand zum Quatschen.\n"
        f"• **Zusammen feiern:** Jeder Erfolg der Gilde landet in {ch('ruhmeshalle')}.\n\n"
        "⚔️ **Und wenn du raiden willst**\n"
        "Wir sind Casual-Raider: Wir raiden gemütlich und mit Spaß, ohne Druck und ohne Tryhard – von Molten Core bis zu den "
        f"neuen Raids. Kein Muss, aber jederzeit willkommen. Angemeldet wird per Knopf, unser Addon RaidMaster aus {ch('raid-addon')} "
        f"nimmt dir im Raid die Arbeit ab, und wie wir Punkte und Beute verteilen, steht in {ch('regeln')}.\n\n"
        "👋 **So geht's los**\n"
        f"**1.** Stell dich kurz in {ch('allgemein')} vor – wer bist du, was spielst du?\n"
        f"**2.** Lies in {ch('verhaltensregeln')}, wie wir miteinander umgehen.\n"
        "**3.** Registriere deinen Charakter einmal mit `/charakter` – dann kennt dich jeder und dein Name leuchtet in deiner Klassenfarbe.\n\n"
        f"Fragen? Sprich einfach einen {officer} an – wir helfen gern, bei Problemen mit dem Addon auch in {ch('addon-hilfe')}.\n\n"
        "Schön, dass du da bist. Für die Horde! 🔥"
    )


def _rules_text(s: dict) -> str:
    first = " (beim ersten Kill doppelt)" if s.get("firstKillDouble", True) else ""
    return (
        "💎 **So funktionieren unsere DKP**\n\n"
        "Damit die Beute fair verteilt wird, sammelst du im Raid Punkte (DKP) und bietest damit auf die Items, die du dir "
        "wünschst. Klingt kompliziert, ist es aber nicht – das Addon RaidMaster rechnet alles für dich mit.\n\n"
        "🪙 **Punkte sammeln**\n"
        "• **Jeder Raid hat eigene DKP** – Punkte aus Molten Core gelten nur in Molten Core usw.\n"
        f"• **Dabei sein lohnt sich:** pünktlich zum Start **+{s.get('dkpStart', 10)}**, jeder Boss **+10** "
        f"(besondere wie Ragnaros **+20**){first}, bis zum Schluss geblieben **+{s.get('dkpEnd', 10)}**.\n"
        "• **Ersatzbank:** Wer bereitsteht, bekommt beim Raidstart einmalig **+10 DKP** als Dankeschön.\n"
        "• **Immer im Blick:** Nach jedem Raid schickt dir der Bot deine Punkte per Direktnachricht (abbestellen mit "
        "`/dkp-nachricht aus`), sonst hilft `/dkp`.\n\n"
        "🎁 **Bieten**\n"
        "• Epische Items werden **offen versteigert** – das Gebotsfenster öffnet sich bei dir von selbst.\n"
        f"• Mindestgebot **{s.get('minBid', 10)} DKP**, jedes neue Gebot mindestens **+{s.get('bidIncrement', 5)}**, "
        f"Zeit **{s.get('auctionTime', 30)} Sekunden**. Das höchste Gebot gewinnt.\n"
        "• **Tipp:** Fährst du mit der Maus über ein Item, zeigt dir RaidMaster, was es bisher gekostet hat.\n"
        "• Ohne Addon geht's auch: `/w <Plündermeister> !bid 50` flüstern.\n\n"
        "🧵 **Handwerksmaterial gehört der Gilde** – mehr dazu in der nächsten Nachricht.\n\n"
        "📌 **Gut zu wissen**\n"
        f"• **Verfall:** Jeden Mittwoch sinken alle DKP um **{s.get('decayPct', 10)} %** – so bleibt es für Neue fair.\n"
        "• **Main vor Twink:** Twinks bekommen ein Item nur, wenn kein Main bietet. Twink eintragen: `/twink hinzufügen`.\n"
        "• Legendäre Items vergibt die Gildenleitung nach eigener Regel, und sie kann die Werte jederzeit anpassen."
    )


def _raid_rules_texts() -> list[str]:
    """Raid-Regeln in zwei Beiträgen (Discord nimmt höchstens 2000 Zeichen pro Nachricht)."""
    return [(
        "⚔️ **So raiden wir**\n\n"
        "Wir sind Casual-Raider: Spaß geht vor Bestzeit, und ein Wipe ist kein Weltuntergang. Damit der Abend für alle "
        "entspannt bleibt, gibt's ein paar einfache Absprachen.\n\n"
        "📅 **Vor dem Raid**\n"
        "• **Bis 24 Stunden vorher anmelden** im Anmelde-Kanal des Raids – so können wir die Gruppen planen. Später geht's "
        "nach kurzer Absprache mit der Raidleitung.\n"
        "• **Doch keine Zeit?** Kein Problem, einfach abmelden. Der Bot fragt dann von selbst jemanden von der Ersatzbank.\n"
        "• **Ein paar Minuten vor dem Start** online sein – dann geht's pünktlich los.\n"
        "• Ausrüstung repariert, ein paar **Tränke und Essen** dabei. Fläschchen sind nett, aber kein Muss – und auf "
        "Weltbuffs warten wir nicht (die gibt's auf WoW Forever im Raid ohnehin nicht).\n"
        "• In Molten Core hilft etwas **Feuerwiderstand** – die Raidleitung sagt dir, wenn du ihn brauchst.\n"
        "• **Hilfreich:** RaidMaster aus #raid-addon und ein Boss-Addon (DBM oder BigWigs). Einen Blick in die Taktik "
        "und in den **Einteilungs-Kanal** deines Raids (unter ⚔️ RAID-ORGA) zu werfen, schadet auch nicht.\n\n"
        "🎧 **Im Raid**\n"
        "• Komm in den **Sprachkanal** – zuhören reicht, ein Mikro ist kein Muss. Bei Ansagen kurz ruhig sein.\n"
        "• Die **Raidleitung** sagt an. Taktik und Symbole kommen bei dir als Schlachtzugwarnung mitten auf den "
        "Bildschirm – du musst nichts auswendig können.\n"
        "• **Bereitschafts-Check** kurz beantworten, mit dem **Pull-Timer** geht's los – bitte nicht vorher pullen.\n"
        "• Kurz weg? „AFK“ in den Raidchat, und Pausen gibt's auch.\n"
        "• **Symbole:** zuerst Totenkopf, dann Kreuz – den Mond nicht angreifen, der schläft.\n"
        "• **Nach einem Wipe** laufen wir gemeinsam zurück, lachen kurz und versuchen es nochmal. Schuldige suchen wir nicht."
    ), (
        "🎁 **Beute und Ersatzbank**\n\n"
        "🎲 **Beute im Raid**\n"
        "• **Biete auf das, was du selbst nutzt** – nicht zum Verkaufen oder Entzaubern.\n"
        "• **Gebote gelten:** Wer gewinnt, bekommt das Item, die DKP werden abgezogen.\n"
        "• Was niemand will, geht an den Entzauberer oder in die Gildenbank.\n"
        "• Fragen zur Beute flüsterst du dem Plündermeister, so bleibt der Raidchat frei.\n\n"
        "🪑 **Früher gehen & Ersatzbank**\n"
        "• Musst du **früher weg**, sag kurz Bescheid. Die Punkte fürs Raidende gibt's fürs Bleiben bis zum Schluss.\n"
        "• **Auf der Ersatzbank** bleibst du im Discord erreichbar – wird ein Platz frei, kommt die Einladung zu dir.\n\n"
        "Die Raidleitung kann diese Absprachen anpassen. Viel Spaß beim Raiden! 🍻"
    )]


def materials_text(materials: dict | None = None, recipes: dict | None = None) -> str:
    """Eigene Nachricht in #regeln: Handwerksmaterial je Raid (bekannt + von RaidMaster erfasst) und wofür man es braucht.
    materials: {Topf: [Name, ...]}, recipes: {Material (klein): [„Rezept (Beruf)“, ...]}"""
    materials = materials or {}
    recipes = recipes or {}
    lines = ["🧵 **Handwerksmaterial gehört der Gilde**", "",
             "Materialien aus unseren Raids werden **nicht versteigert**, sie kommen in die **Gildenbank**. Du willst daraus "
             "etwas herstellen? Einfach einen Offizier fragen – dafür ist es da. Weiterverkaufen ist nicht drin.", ""]
    for key in ASSIGN_RAIDS:
        r = next((x for x in RAID_DEFS if x["key"] == key), None)
        if not r:
            continue
        mats = materials.get(key) or []
        if not mats:
            lines.append(f"{r['emoji']} **{r['name']}:** _noch unbekannt – RaidMaster trägt sie hier ein, sobald etwas droppt._")
            continue
        lines.append(f"{r['emoji']} **{r['name']}:** " + ", ".join(mats))
        for m in mats:
            used = recipes.get(m.lower()) or []
            if used:
                more = f" und {len(used) - 5} weitere" if len(used) > 5 else ""
                lines.append(f"   ↳ _{m}_ für: " + ", ".join(used[:5]) + more)
    lines += ["", "_Neue Materialien und Rezepte ergänzt der Bot automatisch – aus der Beute, die RaidMaster erfasst, "
              "und aus den Berufen der Addon-Nutzer._"]
    text = "\n".join(lines)
    if len(text) > 1990:
        text = text[:1980].rsplit("\n", 1)[0] + "\n…"
    return text


def material_examples(materials: dict | None = None, n: int = 4) -> str:
    """Ein paar bekannte Materialien als Beispiel für Regeltexte, z. B. „Kernleder, Lavakern, Feuerkern“."""
    out = []
    for key in ASSIGN_RAIDS:
        for m in (materials or {}).get(key) or []:
            if m not in out:
                out.append(m)
    return ", ".join(out[:n]) if out else "Handwerksmaterialien"


def rules_posts(dkp_settings: dict | None = None, materials: dict | None = None, recipes: dict | None = None) -> list[str]:
    """Beiträge in #regeln: DKP-Regeln, Handwerksmaterial und Raid-Regeln (der Bot hält sie aktuell)."""
    s = dict(DEFAULT_DKP)
    s.update(dkp_settings or {})
    return [_rules_text(s), materials_text(materials, recipes)] + _raid_rules_texts()


def assignment_intro_text(key: str) -> str:
    """Fester Beitrag im Einteilungs-Kanal eines Raids: wie die Einteilung entsteht, dazu ein Grundplan."""
    r = next((x for x in RAID_DEFS if x["key"] == key), None) or {"name": key, "emoji": "📋"}
    head = (f"🗂️ **Einteilung {r['name']} – so läuft's**\n\n"
            f"Hier postet der Bot die Einteilung aus **RaidMaster** (Raid › Einteilung › oben „{r['name']}“ wählen › "
            "„Einteilung erstellen“): wer heilt wen, wer entflucht und bannt, wer unterbricht und kontrolliert. "
            "Tanks heißen dabei **MT** (Maintank) und **OT1, OT2 …** (Offtanks). Deine eigenen Aufgaben bekommst du "
            "zusätzlich per Direktnachricht und beim Pull groß auf den Bildschirm.\n\n")
    plans = {
        "ony": ("📌 **Grundplan, bis die Raidleitung Namen einträgt**\n"
                "• **Phase 1 (100–65 %):** MT tankt Onyxia, Kopf zur Wand. Nahkampf an der Flanke – nie vor ihr (Feueratem) "
                "oder hinter ihr (Schwanzhieb). Fernkampf und Heiler auf Abstand.\n"
                "• **Phase 2 (65–40 %):** Onyxia fliegt. Fernkampf auf sie, verteilt stehen (Feuerball). Bei **Tiefem Atem** "
                "raus aus der Flugbahn. OT1 und OT2 sammeln die **Welpen** an den Seiten, Magier helfen mit Flächenschaden.\n"
                "• **Phase 3 (ab 40 %):** Sie landet, der MT übernimmt sofort. Gegen die **Furcht**: Furchtschutz auf den MT, "
                "Erdstoß-Totem. Nicht in die **Lavaspalten** treten und die **Eier** nicht aufwecken."),
        "mc": ("📌 **Gut zu wissen**\n"
               "• Die Einteilung deckt alle Bosse ab – von Lucifron bis Ragnaros, auch Baron Geddon.\n"
               "• Die ausführliche Taktik je Boss steht in **#mc-taktik**."),
    }
    plan = plans.get(key) or ("📌 **Neue Bosse**\n"
                              "• Solange die Bosse noch nicht bekannt sind, gibt es eine **allgemeine Boss-Einteilung**: MT auf den Boss, "
                              "OTs auf Adds und für den Tankwechsel, die Reihenfolge fürs Unterbrechen und wer Gegner kontrolliert.\n"
                              f"• Taktiken kommen nach und nach in **#{r.get('prefix', key)}-taktik**.")
    return head + plan


def _raid_howto_text(name: str, key: str | None = None) -> str:
    where = f"**#{assignment_channel_name(key)}**" if key in ASSIGN_RAIDS else "im **Einteilungs-Kanal** unter ⚔️ RAID-ORGA"
    return (
        f"📋 **Anmeldung {name}**\n\n"
        "Hier erscheinen alle geplanten Raids – such dir einen aus und klick auf den passenden Knopf: "
        "**Anmelden**, **Ersatzbank**, **Vielleicht** oder **Abmelden**.\n\n"
        "💡 **Gut zu wissen**\n"
        "• **Bis 24 Stunden vorher anmelden** – dann können wir die Gruppen in Ruhe planen.\n"
        "• **Klasse, Rolle oder Charakter ändern:** Knopf **Charakter ändern** oder `/charakter`. Mit einem Twink "
        "meldest du dich über `/twink wechseln` an.\n"
        f"• **Erinnerung:** Vor dem Raid meldet sich der Bot bei dir, deine Gruppe und Aufgaben siehst du in {where}.\n"
        "• **Ersatzbank:** Sagt jemand ab, fragt dich der Bot per Direktnachricht – ein Klick auf **Ich komme!** und du bist dabei."
    )


def _pug_howto_text() -> str:
    return (
        "🎲 **PUG-Raids – mitspielen ohne Gildenbeitritt**\n\n"
        "Bei unseren PUG-Raids kann jeder mitmachen, auch ohne in der Gilde zu sein. Locker, freundlich und mit fairer Beute.\n\n"
        "✨ **So geht's**\n"
        "• **Einmal registrieren** (Knopf unten) – dann sagt dir der Bot bei jedem neuen PUG-Raid Bescheid.\n"
        "• **Anmelden** per Knopf direkt am Raid.\n"
        "• **Beute:** Soft Reserve über **softres.it** (Tanks und Heiler 3 Items, DDs 2) – den Link findest du am Raid.\n"
        "• **Einladung im Spiel:** dem Raidleiter `inv` flüstern, solange er Werbung macht.\n"
        "• **Regeln** zu Soft Reserve, Würfeln und Verhalten im Raid stehen in **#pug-regeln** – kurz lesen lohnt sich.\n\n"
        "Kleine Überraschung: Im Raid wirst du mit Namen begrüßt. 😉 Das Addon **RaidMaster** aus **#raid-addon** "
        "ist praktisch, aber kein Muss."
    )


def _bot_commands_text() -> str:
    return (
        "🛠️ **Hier darfst du Bot-Befehle ausprobieren**\n\n"
        "Tipp einfach `/` und such dir einen Befehl aus – die vollständige, immer aktuelle Liste steht in **#befehlsliste**.\n\n"
        "🔎 **Ein paar Lieblinge**\n"
        "• `/dkp` – dein Punktestand in allen Raids\n"
        "• `/beute boss` – was ein Boss bei uns schon fallen gelassen hat\n"
        "• `/rekorde` und `/erfolge` – Bestzeiten der Gilde und deine Erfolge\n"
        "• `/berufe` – wer welchen Beruf hat\n"
        "• `/bank` – was gerade in der Gildenbank liegt"
    )


def raid_registration_text(name: str) -> str:
    return (
        f"📝 **Bei {name} dabei sein?**\n"
        "Einmal registrieren, fertig: Klasse, Rolle und Charakternamen festlegen – danach meldest du dich bei jedem "
        f"{name}-Raid mit einem Klick an. Deine Skillung trägt das Addon RaidMaster später von selbst nach."
    )


def pug_registration_text() -> str:
    return (
        "🎲 **Neu hier und Lust auf einen PUG-Raid?**\n"
        "Klick auf den Knopf: Du bekommst die Rolle **Gast**, legst deinen Charakter fest und erfährst als Erstes, "
        "wenn ein neuer PUG-Raid ansteht."
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
            if msg.author.id == guild.me.id and text.startswith(("**PUG-Raids", "🎲 **PUG-Raids")) and text != current:
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
        msg = await channel.send(pug_registration_text(), view=view)
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
        msg = await channel.send(raid_registration_text(name), view=view)
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
    raids = [raid_category(*r, cfg=cfg) for r in raid_list(extra_pools)]
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
        texts[f"{r['prefix']}-anmeldung"] = _raid_howto_text(next((n for k, n, _, _ in RAIDS if k == r["raid"]),
                                                                  r["name"].split(" ", 1)[1].title()), r["raid"])
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
    cfg["assignment_channels"] = {k: created[assignment_channel_name(k)].id for k in ASSIGN_RAIDS
                                  if assignment_channel_name(k) in created}
    for key, ch_name in (("assignment_channel_id", "einteilung-mc"),
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


async def ensure_assignment_channels(guild: discord.Guild, cfg: dict) -> list[str]:
    """⚔️ RAID-ORGA: je Raid ein Einteilungs-Kanal. Der alte #einteilung wird zu #einteilung-mc (Verlauf bleibt)."""
    reason = "RaidMaster: Einteilung je Raid"
    report: list[str] = []
    old = _find(guild.text_channels, "einteilung")
    if old and not _find(guild.text_channels, "einteilung-mc"):
        await old.edit(name="einteilung-mc", topic=_assignment_channels()[0][2], reason=reason)
        report.append("✏️ #einteilung in #einteilung-mc umbenannt")
    cat_def = next(c for c in BASE_TOP if c["name"] == RAID_ORGA)
    created: dict = {}
    await _ensure_category(guild, cat_def, _known_roles(guild), report, created, set(), reason)
    cfg["assignment_channels"] = {k: created[assignment_channel_name(k)].id for k in ASSIGN_RAIDS
                                  if assignment_channel_name(k) in created}
    if "einteilung-mc" in created:
        cfg["assignment_channel_id"] = created["einteilung-mc"].id
    return [r for r in report if r.startswith(("✅", "✏️"))]


async def ensure_raid_extra_channels(guild: discord.Guild, cfg: dict) -> list[str]:
    """Zusätzliche Kanäle aus forever_raids.json ("extra_channels") in schon vorhandenen Raid-Kategorien anlegen."""
    reason = "RaidMaster: zusätzlicher Raid-Kanal"
    report: list[str] = []
    roles = _known_roles(guild)
    for key, name, emoji, prefix in RAIDS:
        extra = RAID_EXTRA.get(key) or []
        if not extra or key not in (cfg.get("raid_channels") or {}):
            continue   # neue Raids bekommen die Kanäle über ensure_raid
        # Kategorie des Taktik-Kanals nehmen (falls sie umbenannt wurde), sonst den Standardnamen
        ids = cfg["raid_channels"][key] or {}
        anchor = next((guild.get_channel(int(ids[k])) for k in ("tactics", "signup", "dkp") if ids.get(k)), None)
        cat_name = anchor.category.name if anchor and anchor.category else f"{emoji} {name.upper()}"
        cat_def = {"name": cat_name, "mode": None, "raid": key, "prefix": prefix, "channels": extra}
        created: dict = {}
        await _ensure_category(guild, cat_def, roles, report, created, set(), reason)
        await _hide_from_guests(guild, cat_def, roles, created, report, reason)
    return [r for r in report if r.startswith(("✅", "↪️"))]


async def ensure_raid(guild: discord.Guild, cfg: dict, key: str, name: str, emoji: str = "🗡️",
                      prefix: str | None = None) -> list[str]:
    """Kategorie für einen Raid anlegen (neu erkannter Raid oder neu in der Raidliste)."""
    report: list[str] = []
    roles = _known_roles(guild)
    created: dict = {}
    new_names: set[str] = set()
    raid_def = raid_category(key, name, emoji, prefix, cfg)
    await _ensure_category(guild, raid_def, roles, report, created, new_names, "RaidMaster: neuer Raid")
    await _hide_from_guests(guild, raid_def, roles, created, report, "RaidMaster: neuer Raid")
    sign = created.get(f"{raid_def['prefix']}-anmeldung")
    if sign and sign.name in new_names:
        try:
            await sign.send(_raid_howto_text(name, key))
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


# Kategorien der Regel-Kanäle: Standard 📜 REGELN, ein Eintrag mit "category" kommt in eine eigene Kategorie
# (z. B. 🏦 GILDENBANK). Position: (Kategorie, steht direkt unter ...)
RULE_CATEGORY_PLACE = {RULES_CATEGORY: "📌 INFO", "🏦 GILDENBANK": "💬 ALLGEMEIN"}


async def ensure_rules_category(guild: discord.Guild, cfg: dict) -> list[str]:
    """Kategorien mit den Kanälen aus guild_rules.json anlegen (fehlende ergänzen, Rechte setzen).
    Standard: 📜 REGELN, alle lesen, nur Offiziere schreiben. Ein Eintrag kann eine eigene Kategorie ("category")
    und eigene Rechte ("mode", z. B. "botonly") haben – Kanäle werden dorthin verschoben, Inhalt bleibt."""
    rules = guild_rules()
    if not rules:
        return []
    reason = "RaidMaster: Gildenregeln"
    roles = _known_roles(guild)
    report: list[str] = []
    created: dict = {}
    groups: dict[str, list[dict]] = {}
    for c in rules:
        groups.setdefault(c.get("category") or RULES_CATEGORY, []).append(c)
    for cat_name, entries in groups.items():
        # REGELN bleiben wie bisher auch für Gäste sichtbar, andere Kategorien (Gildenbank) nur für die Gilde
        cat_def = {"name": cat_name, "mode": "officers_write" if cat_name == RULES_CATEGORY else None,
                   "guest": cat_name == RULES_CATEGORY or any(c.get("guest") for c in entries),
                   "channels": [("text", c["key"], c.get("topic"), c.get("mode", "officers_write")) for c in entries]}
        mine: dict = {}
        category = await _ensure_category(guild, cat_def, roles, report, mine, set(), reason)
        created.update(mine)
        # Rechte immer wie vorgesehen halten
        if cat_def["mode"]:
            ow = _overwrites(cat_def["mode"], guild, roles)
            try:
                if category.overwrites != ow:
                    await category.edit(overwrites=ow, reason=reason)
            except discord.HTTPException:
                pass
        for c in entries:
            ch = mine.get(c["key"])
            ow = _overwrites(c.get("mode", "officers_write"), guild, roles)
            try:
                if ch and ow and ch.overwrites != ow:
                    await ch.edit(overwrites=ow, reason=reason)
            except discord.HTTPException:
                pass
        await _hide_from_guests(guild, cat_def, roles, mine, report, reason)
        if RULE_CATEGORY_PLACE.get(cat_name):
            await _place_after(guild, cat_name, RULE_CATEGORY_PLACE[cat_name], report, reason)
    cfg["rules_channels"] = {name: ch.id for name, ch in created.items()}
    return [r for r in report if r.startswith(("✅", "↪️", "↕️"))]
