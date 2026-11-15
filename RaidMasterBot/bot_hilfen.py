"""Hilfsfunktionen des Bots ohne gemeinsamen Zustand (D-3 Schritt 1, ab Bot 1.5.146).

Aus bot.py hierher verschoben, UNVERÄNDERT: Funktionen, die weder Konfiguration noch Zustand, Datenbanken, Logger oder
das Bot-Objekt brauchen (per ast und pyflakes geprüft). bot.py importiert sie mit Namen, darum funktionieren Aufrufe
und Attrappen in bot.py wie vorher. Weg A "kern.py + Module" (Antwort der Prüf-Sitzung 15.11. 20:48), Bereich für
Bereich.
"""
from __future__ import annotations

import gzip
import io
import os
import re
import time
import zipfile

import discord

import member_area
import raidmaster_data as rmd

__all__ = ['_Msg', '_config_ids', '_norm_category', 'apply_card_view', 'check_upload', 'clean_softres', 'ensure_member_role', 'fetch_invite_uses', 'name_key', 'player_class', 'profile_text', 'proposer_text', 'raid_view', 'status_text', 'sub_candidates', 'table_file', 'test_info', 'tip_view', 'version_tuple', 'vote_word', 'zip_addon_info']


def raid_view(raid: dict) -> discord.ui.View:
    v = discord.ui.View(timeout=None)
    closed = bool(raid.get("closed"))
    rid = raid["id"]
    v.add_item(discord.ui.Button(label="Anmelden", emoji="✅", style=discord.ButtonStyle.success, custom_id=f"rm:an:{rid}", disabled=closed, row=0))
    v.add_item(discord.ui.Button(label="Ersatzbank", emoji="🪑", style=discord.ButtonStyle.secondary, custom_id=f"rm:ersatz:{rid}", disabled=closed, row=0))
    v.add_item(discord.ui.Button(label="Vielleicht", emoji="❔", style=discord.ButtonStyle.secondary, custom_id=f"rm:vielleicht:{rid}", disabled=closed, row=0))
    v.add_item(discord.ui.Button(label="Abmelden", emoji="❌", style=discord.ButtonStyle.danger, custom_id=f"rm:ab:{rid}", disabled=closed, row=0))
    v.add_item(discord.ui.Button(label="Charakter ändern", emoji="👤", style=discord.ButtonStyle.secondary, custom_id=f"rm:char:{rid}", row=1))
    v.add_item(discord.ui.Button(label="Für RaidMaster (Offiziere)", emoji="📋", style=discord.ButtonStyle.primary, custom_id=f"rm:export:{rid}", row=1))
    return v


def status_text(actual: str, wanted: str, raid: dict | None = None, role: str | None = None) -> str:
    if actual != wanted and actual == "ersatz":
        # ab 1.5.185: voll nur für die eigene Rolle (D-N1 Wunsch 4) – der ganze Raid hat noch Platz
        if raid is not None and role and not (raid.get("max") and sum(
                1 for s in raid["signups"].values() if s["status"] == "an") >= raid["max"]):
            return (f"Für **{rmd.ROLES.get(role, role)}** sind alle Plätze belegt – du stehst auf der **Ersatzbank**. "
                    "Wird ein Platz frei, kann dich der Bot fragen.")
        return "Der Raid ist voll – du stehst auf der **Ersatzbank**."
    return {
        "an": "Du bist **angemeldet**. ✅",
        "ersatz": "Du stehst auf der **Ersatzbank**. 🪑",
        "vielleicht": "Du bist als **vielleicht** eingetragen. ❔",
        "ab": "Du bist **abgemeldet**. ❌",
    }.get(actual, "")


def profile_text(p: dict) -> str:
    text = f"**{p['name']}** ({rmd.CLASSES.get(p['cls'], p['cls'])}, {rmd.ROLES.get(p['role'], p['role'])})"
    spec = p.get("spec")
    if spec:
        text += f" · Skillung **{spec['label']}**" + (f" ({spec['points']})" if spec.get("points") else "")
    return text


def clean_softres(link: str | None) -> str:
    """Nur echte softres.it-Links zulassen."""
    link = (link or "").strip().strip("<>")
    if not link:
        return ""
    if not link.startswith("http"):
        link = "https://" + link
    if not re.match(r"^https://(www\.)?softres\.it/[\w\-/?=&#.]+$", link):
        return ""
    return link


def table_file(png: bytes | None, name: str):
    return discord.File(io.BytesIO(png), filename=name) if png else None


def player_class(db: dict | None, name: str) -> str | None:
    p_ = (((db or {}).get("data") or {}).get("players") or {}).get(name)
    return p_.get("c") if isinstance(p_, dict) else None


def tip_view(items: list[dict], db: dict | None = None) -> discord.ui.View | None:
    """Auswahlmenü "Tooltip anzeigen" unter der Loot-Liste (je Menü 25 Items, höchstens 5 Menüs)."""
    opts = []
    for e in items:
        iid = rmd.item_id(e.get("link"))
        if not iid:
            continue
        p_ = (((db or {}).get("data") or {}).get("players") or {}).get(e["name"])
        cls = (p_.get("c") if isinstance(p_, dict) else "") or ""
        value = f"{iid}|{e['name']}|{e['amount']}|{int(e['t'])}|{cls}"[:100]
        opts.append(discord.SelectOption(label=str(e["item"])[:100], description=f"{e['name']} · {e['amount']} DKP"[:100],
                                         value=value))
    if not opts:
        return None
    view = discord.ui.View(timeout=None)
    for n, i in enumerate(range(0, min(len(opts), 125), 25)):
        part = opts[i:i + 25]
        # Werte müssen je Menü eindeutig sein
        seen, uniq = set(), []
        for o in part:
            if o.value in seen:
                continue
            seen.add(o.value)
            uniq.append(o)
        view.add_item(discord.ui.Select(custom_id=f"rmtip:{n}:{int(time.time() * 1000) % 10**9}",
                                        placeholder="🔍 Tooltip anzeigen …" + (f" ({n + 1})" if len(opts) > 25 else ""),
                                        options=uniq, min_values=1, max_values=1))
    return view


def sub_candidates(raid: dict, leaver: dict) -> list[tuple[str, dict]]:
    asked = set(raid.get("subs_asked") or [])
    cands = [(uid, s) for uid, s in raid["signups"].items() if s["status"] == "ersatz" and uid not in asked and not uid.startswith("9000")]
    def score(item):
        _, s = item
        return (0 if s.get("role") == leaver.get("role") else 1, 0 if s.get("cls") == leaver.get("cls") else 1, 1 if s.get("main") else 0, s.get("t", 0))
    return sorted(cands, key=score)


def version_tuple(v: str) -> tuple:
    return tuple(int(x) for x in re.findall(r"\d+", v or "0"))


def zip_addon_info(path: str) -> tuple[str, str, str] | None:
    """(Schlüssel, Ordnername, Version) aus einer Addon-ZIP oder None."""
    try:
        with zipfile.ZipFile(path) as z:
            tocs = [n for n in z.namelist() if n.lower().endswith(".toc") and "/" in n.strip("/")]
            tocs = tocs or [n for n in z.namelist() if n.lower().endswith(".toc")]
            if not tocs:
                return None
            tocs.sort(key=lambda n: ("_" in os.path.basename(n), len(n)))
            toc = tocs[0]
            text = z.read(toc).decode("utf-8-sig", "replace")
    except (zipfile.BadZipFile, OSError, KeyError):
        return None
    m = re.search(r"##\s*Version:\s*v?([\d.]+)", text)
    if not m:
        return None
    base = os.path.basename(toc)[:-4]
    key = base.split("_")[0].lower()
    folder = toc.split("/")[0] if "/" in toc else base.split("_")[0]
    return key, folder, m.group(1)


def _norm_category(name: str) -> str:
    return re.sub(r"[^a-z0-9]", "", (name or "").lower())


def _config_ids(value) -> set:
    """Alle Zahlen/IDs aus der config.json (verschachtelt), um eingetragene Kanäle zu erkennen."""
    out = set()
    if isinstance(value, dict):
        for v in value.values():
            out |= _config_ids(v)
    elif isinstance(value, (list, tuple)):
        for v in value:
            out |= _config_ids(v)
    elif isinstance(value, int) and not isinstance(value, bool):
        out.add(value)
    elif isinstance(value, str) and value.isdigit():
        out.add(int(value))
    return out


class _Msg:
    """Kurzform einer Discord-Nachricht für server_setup.plan_update_cleanup."""
    __slots__ = ("id", "author_id", "content", "has_files", "created_at")

    def __init__(self, m):
        self.id, self.author_id, self.content = m.id, m.author.id, m.content or ""
        self.has_files, self.created_at = bool(m.attachments), m.created_at


def check_upload(raw: bytes, filename: str) -> tuple[str, dict]:
    """Entpackt und prüft einen Upload. Liefert (Text, RaidMasterDB) oder wirft ValueError."""
    if filename.lower().endswith(".gz"):
        try:
            raw = gzip.decompress(raw)
        except OSError:
            raise ValueError("Datei ist nicht richtig gepackt")
    text = raw.decode("utf-8", errors="replace")
    try:
        db = rmd.parse_saved_variables(text).get("RaidMasterDB")
    except Exception as e:  # noqa: BLE001
        raise ValueError(f"Datei nicht lesbar: {e}")
    if not isinstance(db, dict) or not isinstance(db.get("data"), dict):
        raise ValueError("keine RaidMaster-Daten enthalten")
    return text, db


def test_info(db: dict | None) -> dict | None:
    t = (db or {}).get("testMode")
    return t if isinstance(t, dict) and t.get("active") else None


async def fetch_invite_uses(guild) -> dict[str, int] | None:
    if guild is None or not guild.me.guild_permissions.manage_guild:
        return None
    try:
        return {i.code: int(i.uses or 0) for i in await guild.invites()}
    except discord.HTTPException:
        return None


def name_key(name: str) -> str:
    s = name.casefold()
    for a, b in (("ä", "ae"), ("ö", "oe"), ("ü", "ue"), ("ß", "ss")):
        s = s.replace(a, b)
    return re.sub(r"[^a-z]", "", s)


def vote_word(n: int) -> str:
    return "1 Stimme" if n == 1 else f"{n} Stimmen"


def proposer_text(prop: dict) -> str:
    return f"<@{prop['by']}>" if prop.get("by") else (prop.get("by_name") or "Gildenleitung")


async def ensure_member_role(guild) -> discord.Role:
    role = discord.utils.get(guild.roles, name=member_area.MEMBER_ROLE)
    if role is None:
        role = await guild.create_role(name=member_area.MEMBER_ROLE, permissions=discord.Permissions.none(),
                                       colour=discord.Colour(0x3498DB), hoist=False, mentionable=False,
                                       reason=member_area.REASON)
    return role


def apply_card_view() -> discord.ui.View:
    v = discord.ui.View(timeout=None)
    v.add_item(discord.ui.Button(label="Bewerben", emoji="📝", style=discord.ButtonStyle.success, custom_id="rmapply:start:0"))
    return v
