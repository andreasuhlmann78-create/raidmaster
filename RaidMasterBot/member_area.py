"""Mitglieder-Bereich und Bewerbung (ab Bot 1.5.115, Auftrag Discord-Projekt DC2/DC3, Freigabe des Nutzers 12.11.2026).

Ziel: Wer dem Discord ohne Rolle beitritt (öffentliches Serverprofil), sieht nur noch INFO, REGELN, PUG, RAID-ADDON und
📝 BEWERBUNG. Alles andere (💬 ALLGEMEIN, 🗝️ DUNGEONS, 🏦 GILDENBANK, ⚔️ RAID-ORGA, Raid-Kategorien) sehen nur die
Rollen Mitglied, Raider, Raidleitung und Offizier.

Regeln:
- Eingerichtet wird nur mit /mitgliederbereich einrichten (erst Vorschau, dann bestaetigen:True) – nie automatisch.
  Danach merkt sich der Bot cfg["member_area"] = True und hält neu angelegte Kanäle in diesen Kategorien ebenso dicht.
- Angefasst werden nur Kategorien/Kanäle, die @everyone heute sieht. Was schon versteckt ist (Offiziere,
  Addon's by GoldSentinel, noch nicht angekündigte Raids), bleibt genau so.
- Pro Kanal: @everyone "Kanal ansehen" = aus; Mitglied/Raider/Raidleitung/Offizier und der Bot (ab 1.5.116, damit er
  den Kanal auch ohne Administrator-Recht sieht) "Kanal ansehen" = an, aber nur wenn
  für die Rolle nichts eingetragen ist (ein ausdrückliches "aus", z. B. Raidleitung, bleibt). Andere Einstellungen der
  Kanäle (nur lesen, nur Bot schreibt …) bleiben unverändert.
- Mitglieder ohne Rolle (ausser Gast und Bots) bekommen beim Einrichten die Rolle Mitglied, damit niemand den Zugang
  verliert. Dafür braucht der Bot den "Server Members Intent" – sonst wird nicht eingerichtet.
- Nichts wird gelöscht.

Die Funktionen bekommen Discord-Objekte und lassen sich offline mit Attrappen testen (tests/test_mitgliederbereich.py).
"""
from __future__ import annotations

import discord

MEMBER_ROLE = "Mitglied"
MEMBER_ROLES = ("Mitglied", "Raider", "Raidleitung", "Offizier")
GUEST_ROLE = "Gast"

APPLY_CATEGORY = "📝 BEWERBUNG"
APPLY_CHANNEL = "bewerbung"
APPLY_TOPIC = "Neu hier? Auf „Bewerben“ klicken – ein Offizier meldet sich bei dir."
APPLY_AFTER = "📜 REGELN"   # bis 1.5.123; ab 1.5.124 steht 📝 BEWERBUNG ganz oben (Wunsch des Nutzers 13.11.)

# Kategorien, die alle sehen dürfen (auch ohne Rolle) – werden nie angefasst
OPEN_CATEGORIES = ("📌 INFO", "📜 REGELN", "🎲 PUG", "🧩 RAID-ADDON", APPLY_CATEGORY)

REASON = "RaidMaster: Mitglieder-Bereich"


def _fold(s: str) -> str:
    return (s or "").strip().casefold()


def _role(guild, name: str):
    return next((r for r in guild.roles if _fold(r.name) == _fold(name)), None)


def member_roles(guild) -> list:
    return [r for r in (_role(guild, n) for n in MEMBER_ROLES) if r is not None]


def is_open_category(name: str) -> bool:
    return _fold(name) in {_fold(c) for c in OPEN_CATEGORIES}


def visible_to_everyone(item, guild) -> bool:
    return item.overwrites_for(guild.default_role).view_channel is not False


def plan_items(guild) -> list:
    """Kategorien und Kanäle, die heute @everyone sieht und künftig nur Mitglieder sehen sollen."""
    out = []
    for cat in sorted(guild.categories, key=lambda c: c.position):
        if is_open_category(cat.name):
            continue
        if visible_to_everyone(cat, guild):
            out.append(cat)
        for ch in sorted(getattr(cat, "channels", []) or [], key=lambda c: c.position):
            if visible_to_everyone(ch, guild):
                out.append(ch)
    # Kanäle ohne Kategorie (ab 1.5.118, Befund N1): gelten nicht als offen und werden ebenso dicht gemacht
    for ch in sorted(getattr(guild, "channels", []) or [], key=lambda c: c.position):
        if getattr(ch, "type", None) == discord.ChannelType.category or getattr(ch, "category_id", None) is not None:
            continue
        if visible_to_everyone(ch, guild):
            out.append(ch)
    return out


def _viewers(guild, roles: list) -> list:
    """Mitglieder-Rollen plus der Bot selbst – sonst verlöre der Bot ohne Administrator-Recht den Kanal."""
    me = getattr(guild, "me", None)
    return list(roles) + ([me] if me is not None and me not in roles else [])


def gate_overwrites(ow: dict | None, guild, roles: list | None = None) -> dict:
    """Rechte-Satz (wie aus server_setup._overwrites) für den Mitglieder-Bereich ergänzen: @everyone sieht nichts,
    Mitglieder-Rollen sehen (ein ausdrückliches 'aus' einer Rolle bleibt). Gibt einen neuen dict zurück."""
    out = {k: discord.PermissionOverwrite(**dict(iter(v))) for k, v in (ow or {}).items()}
    everyone = guild.default_role
    e = out.get(everyone) or discord.PermissionOverwrite()
    e.view_channel = False
    out[everyone] = e
    for r in _viewers(guild, roles if roles is not None else member_roles(guild)):
        o = out.get(r) or discord.PermissionOverwrite()
        if o.view_channel is None:
            o.view_channel = True
        out[r] = o
    return out


async def gate_item(item, guild, roles: list, reason: str = REASON) -> bool:
    """Einen Kanal bzw. eine Kategorie dicht machen. Zuerst Mitglieder-Rollen freigeben, dann @everyone sperren
    (so verliert kein Mitglied zwischendurch den Kanal). True = etwas geändert."""
    changed = False
    for r in _viewers(guild, roles):
        o = item.overwrites_for(r)
        if o.view_channel is None:
            o.view_channel = True
            await item.set_permissions(r, overwrite=o, reason=reason)
            changed = True
    e = item.overwrites_for(guild.default_role)
    if e.view_channel is not False:
        e.view_channel = False
        await item.set_permissions(guild.default_role, overwrite=e, reason=reason)
        changed = True
    return changed


def members_without_role(guild) -> list:
    """Menschen ohne Mitglieder-Rolle und ohne Gast – sie bekommen beim Einrichten 'Mitglied'."""
    keep = {_fold(n) for n in MEMBER_ROLES + (GUEST_ROLE,)}
    out = []
    for m in guild.members:
        if getattr(m, "bot", False) or m.id == guild.owner_id:
            continue
        if any(_fold(r.name) in keep for r in m.roles):
            continue
        out.append(m)
    return out


def members_complete(guild) -> bool:
    """Kennt der Bot alle Mitglieder? (ohne Server Members Intent nur sich selbst)"""
    count = getattr(guild, "member_count", None) or 0
    return count > 0 and len(guild.members) >= count


def _label(item) -> str:
    kind = getattr(item, "type", None)
    if kind == discord.ChannelType.category:
        return f"Kategorie **{item.name}**"
    if kind == discord.ChannelType.voice:
        return f"🔊 {item.name}"
    return f"#{item.name}"


def preview_text(guild, items: list, new_members: list, has_role: bool, has_apply: bool, complete: bool) -> str:
    lines = ["**Vorschau Mitglieder-Bereich** – noch ist nichts geändert.", ""]
    if not complete:
        lines += ["⛔ Der Bot sieht nicht alle Mitglieder (Server Members Intent aus). Bitte zuerst im "
                  "Discord-Entwicklerportal → Bot → Privileged Gateway Intents **Server Members Intent** einschalten "
                  "und den Bot neu starten – sonst könnten Mitglieder ohne Rolle den Zugang verlieren.", ""]
    lines.append(("• Rolle **Mitglied** ist schon da" if has_role else "• Rolle **Mitglied** wird angelegt (ohne Sonderrechte)"))
    lines.append(("• #bewerbung ist schon da" if has_apply else
                  f"• Kategorie **{APPLY_CATEGORY}** mit #{APPLY_CHANNEL} wird angelegt (alle sehen sie, Knopf „Bewerben“)"))
    if new_members:
        names = ", ".join(m.display_name for m in new_members[:25])
        more = f" und {len(new_members) - 25} weitere" if len(new_members) > 25 else ""
        lines.append(f"• Rolle **Mitglied** bekommen ({len(new_members)}): {names}{more}")
    else:
        lines.append("• Alle Mitglieder haben schon eine passende Rolle")
    if items:
        lines.append(f"• Nur noch für Mitglied/Raider/Raidleitung/Offizier sichtbar ({len(items)}):")
        shown = [_label(i) for i in items[:40]]
        lines.append("  " + ", ".join(shown) + (f" … (+{len(items) - 40})" if len(items) > 40 else ""))
    else:
        lines.append("• Keine Kanäle mehr offen für alle – der Bereich ist schon dicht")
    lines += ["", "Weiter für alle sichtbar: " + ", ".join(OPEN_CATEGORIES),
              "Ausführen: `/mitgliederbereich einrichten bestaetigen:True`"]
    text = "\n".join(lines)
    return text if len(text) <= 1990 else text[:1980] + " …"


def apply_overwrites(guild, me) -> dict:
    """Rechte für #bewerbung: alle sehen den Kanal und schreiben nur in ihrem eigenen (privaten) Thread;
    Offiziere sehen alles und verwalten die Threads; der Bot darf private Threads anlegen."""
    ow = {
        guild.default_role: discord.PermissionOverwrite(
            view_channel=True, send_messages=False, add_reactions=False, create_public_threads=False,
            create_private_threads=False, send_messages_in_threads=True, read_message_history=True),
        me: discord.PermissionOverwrite(
            view_channel=True, send_messages=True, embed_links=True, read_message_history=True,
            create_private_threads=True, send_messages_in_threads=True, manage_threads=True),
    }
    officer = _role(guild, "Offizier")
    if officer is not None:
        ow[officer] = discord.PermissionOverwrite(view_channel=True, send_messages=True, send_messages_in_threads=True,
                                                  manage_threads=True, read_message_history=True)
    return ow


def apply_card_text(guild_name: str) -> str:
    return (
        f"📝 **Bewerbung bei {guild_name or 'unserer Gilde'}**\n\n"
        "Du möchtest zu uns? Klick unten auf **Bewerben** und beantworte ein paar kurze Fragen "
        "(Charaktername, Klasse, Stufe, Spielzeiten).\n"
        "Danach öffnet sich ein **privater Thread** nur für dich und die Offiziere – dort melden wir uns, meist innerhalb "
        "eines Tages. Wirst du aufgenommen, siehst du sofort den ganzen Gildenbereich.\n\n"
        "Wir sind eine deutschsprachige Gilde – bitte schreib uns auf Deutsch. Für PUG-Raids brauchst du keine "
        "Bewerbung: Schau in 🎲 PUG."
    )


def application_text(user_mention: str, officer_mention: str, answers: dict) -> str:
    def v(k):
        return (answers.get(k) or "–").strip() or "–"
    return (
        f"📝 **Neue Bewerbung** von {user_mention} – {officer_mention}\n\n"
        f"**Charakter:** {v('char')}\n**Klasse:** {v('klasse')}\n**Stufe:** {v('stufe')}\n"
        f"**Spielzeiten / Erfahrung:** {v('zeiten')}\n**Wie gefunden:** {v('quelle')}\n\n"
        "Offiziere: **Aufnehmen** gibt die Rolle Mitglied (Gast wird entfernt), **Ablehnen** schliesst den Thread. "
        "Fragen einfach hier im Thread stellen."
    )


def thread_name(char: str, user_name: str) -> str:
    base = (char or "").strip() or (user_name or "").strip() or "Bewerbung"
    return ("Bewerbung " + base)[:90]
