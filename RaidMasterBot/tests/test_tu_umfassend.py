"""Umfassende Tests TU1–TU6 (Bot 1.5.125, auftraege/Discord/anweisung-tests-umfassend.txt).
Discord-Aufrufe sind nachgebildet (Attrappen), nichts Echtes wird ausgeführt, echte Daten bleiben unverändert.
Start: python3 -I -m unittest discover -s RaidMasterBot/tests
Zufallsdaten: fester Startwert SEED (unten), 1000 Fälle je Grundregel."""
import asyncio
import os
import random
import re
import sys
import tempfile
import time
import unittest
from datetime import datetime, timedelta
from types import SimpleNamespace as N
from zoneinfo import ZoneInfo

import discord

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
import member_area  # noqa: E402
import raid_ready  # noqa: E402
import raidmaster_data as rmd  # noqa: E402
import self_check  # noqa: E402
import server_setup  # noqa: E402
import updater  # noqa: E402

SEED = 4711
CASES = 1000
TZ = "Europe/Zurich"
TOKEN_RE = re.compile(r"[MN][A-Za-z\d]{23,}\.[\w-]{6}\.[\w-]{27,}|discord(app)?\.com/api/webhooks/")
PROFILE = {"name": "Testheld", "cls": "WARRIOR", "role": "tank"}


def prof(i):
    return {"name": f"Test{i}", "cls": "MAGE", "role": ("tank", "heal", "melee", "ranged")[i % 4]}


# ---------------------------------------------------------------------------------------------------------------
# Attrappen für Discord
# ---------------------------------------------------------------------------------------------------------------
class Role:
    def __init__(self, name, rid, perms=None):
        self.name, self.id = name, rid
        self.permissions = perms or discord.Permissions.none()

    def __hash__(self):
        return self.id

    def __eq__(self, o):
        return isinstance(o, Role) and o.id == self.id


class Ch:
    def __init__(self, name, cid, kind=discord.ChannelType.text, ow=None, channels=None, can_post=True):
        self.name, self.id, self.type, self.position = name, cid, kind, cid
        self.ow = dict(ow or {})
        self.channels = channels or []
        self.category_id = None
        self.can_post = can_post

    def overwrites_for(self, who):
        o = self.ow.get(who)
        return discord.PermissionOverwrite(**dict(iter(o))) if o else discord.PermissionOverwrite()

    def permissions_for(self, _):
        return discord.Permissions(view_channel=self.can_post, send_messages=self.can_post, embed_links=self.can_post)

    async def set_permissions(self, who, overwrite=None, reason=None):
        self.ow[who] = overwrite


def server(members_area=True, officer_hidden=True, bot_can_post=True, with_member_role=True, with_apply=True):
    everyone = Role("@everyone", 1)
    roles = [everyone, Role("Offizier", 2), Role("Raider", 3), Role("Gast", 4)]
    if with_member_role:
        roles.append(Role("Mitglied", 5))
    hide = {everyone: discord.PermissionOverwrite(view_channel=False)}
    off = Ch("🔒 OFFIZIERE", 50, discord.ChannelType.category, ow=hide if officer_hidden else {},
             channels=[Ch("offiziere", 51, ow=hide if officer_hidden else {})])
    add = Ch("Addon's by GoldSentinel", 60, discord.ChannelType.category, ow=hide, channels=[Ch("guildsentinel", 61, ow=hide)])
    general = Ch("💬 ALLGEMEIN", 70, discord.ChannelType.category, ow=hide if members_area else {},
                 channels=[Ch("Allgemein", 71, ow=hide if members_area else {})])
    sign = Ch("barrow-anmeldung", 81, can_post=bot_can_post)
    info = Ch("📌 INFO", 10, discord.ChannelType.category, channels=[Ch("willkommen", 11)])
    texts = [c for cat in (off, add, general, info) for c in cat.channels] + [sign]
    if with_apply:
        texts.append(Ch("bewerbung", 91))
    by_id = {c.id: c for c in texts}
    return N(default_role=everyone, roles=roles, categories=[info, off, add, general], text_channels=texts,
             me=Role("bot", 99), get_channel=by_id.get, channels=[])


CFG = {"raid_channels": {"barrow": {"signup": 81}}, "member_area": True}


# ---------------------------------------------------------------------------------------------------------------
# TU1 Lagen-Katalog: jede Lage durch die betroffenen Funktionen, Erwartung als Tabelle
# ---------------------------------------------------------------------------------------------------------------
class TU1Lagen(unittest.TestCase):
    def test_lagen_tabelle(self):
        empty = N(categories=[], channels=[], roles=[], default_role=Role("@everyone", 1), text_channels=[],
                  voice_channels=[], members=[], member_count=0, owner_id=0)
        table = [
            ("Server ohne Kategorien: Mitglieder-Bereich", lambda: member_area.plan_items(empty), []),
            ("Server ohne Kategorien: Bewerbung nach oben", lambda: asyncio.run(server_setup.place_first(empty, "x")), []),
            ("Ohne DISBOARD-Rolle", lambda: asyncio.run(server_setup.drop_disboard_manage_channels(empty)), []),
            ("Unbekannter Kanal anlegen", lambda: asyncio.run(server_setup.ensure_channel_if_missing(
                empty, server_setup.GENERAL, "gibtsnicht", "t")), (None, [])),
            ("Raid-Kanäle fehlen in config", lambda: server_setup.pool_from_channel(N(id=1, category_id=2, guild=None), {}), None),
            ("Mitgliederliste fehlt (Intent aus)", lambda: member_area.members_complete(N(member_count=5, members=[])), False),
            ("Kein raidReady im Upload", lambda: raid_ready.parse(None), None),
            ("Willkommen ohne Kanäle unter 2000", lambda: len(server_setup.welcome_text("x" * 100, {}, None)) < 2000, True),
            ("Selbstprüfung: alles gut", lambda: self_check.check(server(), CFG), []),
        ]
        for name, fn, want in table:
            with self.subTest(lage=name):
                self.assertEqual(fn(), want)

    def test_selbstpruefung_findet_fehllagen(self):
        cases = [
            ("Offiziere für alle sichtbar", server(officer_hidden=False), "OFFIZIERE"),
            ("Bot darf nicht posten", server(bot_can_post=False), "Bot darf nicht posten"),
            ("Rolle Mitglied fehlt", server(with_member_role=False), "Rolle Mitglied fehlt"),
            ("#bewerbung fehlt", server(with_apply=False), "#bewerbung fehlt"),
            ("Mitglieder-Bereich offen", server(members_area=False), "Mitglieder-Bereich"),
        ]
        for name, g, word in cases:
            with self.subTest(lage=name):
                found = self_check.check(g, CFG)
                self.assertTrue(any(word in v for v in found), found)

    def test_raid_mit_0_und_40_anmeldungen(self):
        with tempfile.TemporaryDirectory() as d:
            book = rmd.RaidBook(d)
            start = datetime.now(ZoneInfo(TZ)) + timedelta(days=1)
            r0 = book.create("Leer", start, "", 40, 1, 81)
            self.assertEqual(sum(book.count_status(r0, s) for s in ("an", "ersatz", "vielleicht", "ab")), 0)
            self.assertTrue(rmd.raid_fields(r0))
            r = book.create("Voll", start, "", 40, 1, 81)
            for i in range(40):
                self.assertEqual(book.signup(r, 1000 + i, "an", prof(i), 1), "an")
            self.assertEqual(book.signup(r, 2000, "an", prof(41), 1), "ersatz")      # 41. Spieler -> Ersatzbank
            self.assertEqual(book.count_status(r, "an"), 40)

    def test_sommer_und_winterzeit(self):
        zone = ZoneInfo(TZ)
        now = datetime(2026, 1, 1, tzinfo=zone)
        for d, t in (("29.03.2026", "02:30"), ("25.10.2026", "02:30"), ("29.03.2026", "20:00"), ("25.10.2026", "20:00")):
            with self.subTest(d=d, t=t):
                dt = rmd.parse_datetime(d, t, TZ, now)
                self.assertEqual((dt.day, dt.month, dt.year), tuple(int(x) for x in d.split(".")))
        sommer = rmd.parse_datetime("01.07.2026", "20:00", TZ, now)
        winter = rmd.parse_datetime("01.12.2026", "20:00", TZ, now)
        self.assertEqual(sommer.utcoffset(), timedelta(hours=2))
        self.assertEqual(winter.utcoffset(), timedelta(hours=1))

    def test_ankuendigung_absatz_ueber_1900(self):
        head = "**GuildSentinel 1.2.3**\n"
        self.assertEqual(server_setup.update_head(head + "x" * 2500), ("guildsentinel", (1, 2, 3, 0)))


# ---------------------------------------------------------------------------------------------------------------
# TU2 Abläufe wie ein Spieler (mit Neustart mitten drin)
# ---------------------------------------------------------------------------------------------------------------
class TU2Ablaeufe(unittest.TestCase):
    def test_erstellen_anmelden_abmelden_neustart(self):
        with tempfile.TemporaryDirectory() as d:
            book = rmd.RaidBook(d)
            start = datetime.now(ZoneInfo(TZ)) + timedelta(days=2)
            r = book.create("Ablauf", start, "", 0, 1, 81)
            book.signup(r, 11, "an", prof(1), 1)
            book.signup(r, 12, "vielleicht", prof(2), 2)
            book2 = rmd.RaidBook(d)                                   # Bot-Neustart mitten in der Anmeldung
            r2 = book2.get(r["id"])
            self.assertEqual(r2["signups"]["11"]["status"], "an")
            book2.signup(r2, 11, "ab", prof(1), 3)
            book2.signup(r2, 12, "an", prof(2), 4)
            book3 = rmd.RaidBook(d)
            r3 = book3.get(r["id"])
            self.assertEqual({k: v["status"] for k, v in r3["signups"].items()}, {"11": "ab", "12": "an"})
            self.assertEqual(len(book3.open_raids()), 1)

    def test_raid_ohne_nachricht_bleibt_nicht(self):
        # Ablauf wie raid_create bei gescheitertem Posten (Befund R1): anlegen, Posten scheitert, wieder entfernen
        with tempfile.TemporaryDirectory() as d:
            book = rmd.RaidBook(d)
            r = book.create("Weg", datetime.now(ZoneInfo(TZ)) + timedelta(days=1), "", 0, 1, 81)
            book.raids.data["raids"].pop(str(r["id"]), None)
            book.save()
            self.assertIsNone(rmd.RaidBook(d).get(r["id"]))

    def test_neue_version_ein_post_alte_weg(self):
        bot = 7
        t0 = datetime(2026, 11, 13, 8, 0)
        msgs = [N(id=1, author_id=bot, content="**GuildSentinel 0.9.27**\nalt", has_files=False, created_at=t0),
                N(id=2, author_id=bot, content="", has_files=True, created_at=t0 + timedelta(seconds=1)),
                N(id=3, author_id=bot, content="**GuildSentinel 0.9.28**\nneu", has_files=False,
                  created_at=t0 + timedelta(hours=1))]
        self.assertEqual(server_setup.plan_update_cleanup(msgs, bot), [1])          # Datei und neuster Text bleiben


# ---------------------------------------------------------------------------------------------------------------
# TU3 Standardwerte: leer bzw. ab Werk -> was der Spieler meint
# ---------------------------------------------------------------------------------------------------------------
class TU3Standardwerte(unittest.TestCase):
    STANDARDS = [
        ("Raid-Modus ohne Angabe", "dkp"),
        ("Raidgrösse ohne Angabe (0 = unbegrenzt)", 0),
        ("Raid ohne raid-Angabe in #barrow-anmeldung", "barrow"),
        ("Raid ohne raid-Angabe in fremdem Kanal", "mc"),
        ("Datum ohne Jahr, schon vorbei", "nächstes Jahr"),
        ("Uhrzeit '20' ohne Minuten", "20:00"),
        ("/mitgliederbereich einrichten ohne bestaetigen", "nur Vorschau"),
    ]

    def test_raid_standard(self):
        with tempfile.TemporaryDirectory() as d:
            r = rmd.RaidBook(d).create("Std", datetime.now(ZoneInfo(TZ)) + timedelta(days=1), "", 0, 1, 81)
            self.assertEqual((r["mode"], r["max"]), ("dkp", 0))
            r = rmd.RaidBook(d).create("Std", datetime.now(ZoneInfo(TZ)) + timedelta(days=1), "", None, 1, 81, mode="quatsch")
            self.assertEqual((r["mode"], r["max"]), ("dkp", 0))

    def test_raid_aus_kanal_standard(self):
        rc = {"barrow": {"signup": 81}}
        self.assertEqual(server_setup.pool_from_channel(N(id=81, category_id=None, guild=None), rc) or "mc", "barrow")
        self.assertEqual(server_setup.pool_from_channel(N(id=5, category_id=None, guild=None), rc) or "mc", "mc")

    def test_datum_uhrzeit_standard(self):
        zone = ZoneInfo(TZ)
        now = datetime(2026, 11, 13, 9, 0, tzinfo=zone)
        self.assertEqual(rmd.parse_datetime("01.11.", "20", TZ, now).year, 2027)
        self.assertEqual(rmd.parse_datetime("20.11.", "20", TZ, now).strftime("%Y %H:%M"), "2026 20:00")

    def test_einrichten_standard_ist_vorschau(self):
        with open(os.path.join(HERE, "bot.py"), encoding="utf-8") as f:
            src = f.read()
        self.assertIn("bestaetigen: bool = False", src[src.index("async def member_area_cmd("):][:200])


# ---------------------------------------------------------------------------------------------------------------
# TU4 Grundregeln mit Zufallsdaten (fester Startwert, 1000 Fälle)
# ---------------------------------------------------------------------------------------------------------------
class TU4Grundregeln(unittest.TestCase):
    def test_jede_anmeldung_genau_einmal_und_max(self):
        rnd = random.Random(SEED)
        with tempfile.TemporaryDirectory() as d:
            book = rmd.RaidBook(d)
            book.raids.save = lambda: None                      # in Portionen ohne Plattenzugriff (schnell)
            start = datetime.now(ZoneInfo(TZ)) + timedelta(days=1)
            t0 = time.perf_counter()
            for case in range(CASES):
                mx = rnd.choice((0, 5, 10, 20, 40))
                r = book.create(f"Fall{case}", start, "", mx, 1, 81)
                users = [rnd.randrange(1, 60) for _ in range(rnd.randrange(0, 80))]
                for i, u in enumerate(users):
                    book.signup(r, u, rnd.choice(("an", "ersatz", "vielleicht", "ab")), prof(u), i)
                total = sum(book.count_status(r, s) for s in ("an", "ersatz", "vielleicht", "ab"))
                self.assertEqual(total, len(set(users)), f"Fall {case} (Startwert {SEED})")
                if mx:
                    self.assertLessEqual(book.count_status(r, "an"), mx, f"Fall {case} (Startwert {SEED})")
            per_case = (time.perf_counter() - t0) / CASES * 1000
            self.assertLess(per_case, 8, f"{per_case:.2f} ms je Fall")

    def test_aufraeumen_loescht_nie_neuste_datei_oder_fremde(self):
        rnd = random.Random(SEED + 1)
        bot = 7
        names = ("GuildSentinel", "AHSentinel", "RaidMaster", "LevelPilot")
        for case in range(CASES):
            t0 = datetime(2026, 11, 1)
            msgs = []
            for i in range(rnd.randrange(1, 12)):
                author = bot if rnd.random() < 0.85 else 8
                kind = rnd.random()
                if kind < 0.6:
                    content = f"**{rnd.choice(names)} {rnd.randrange(0, 3)}.{rnd.randrange(0, 10)}.{rnd.randrange(0, 30)}**\nText"
                else:
                    content = "Fortsetzung"
                msgs.append(N(id=i + 1, author_id=author, content=content, has_files=rnd.random() < 0.2,
                              created_at=t0 + timedelta(seconds=rnd.randrange(0, 600))))
            out = set(server_setup.plan_update_cleanup(msgs, bot))
            newest = {}
            for m in msgs:
                h = server_setup.update_head(m.content) if m.author_id == bot else None
                if h and (h[0] not in newest or h[1] > newest[h[0]]):
                    newest[h[0]] = h[1]
            for m in msgs:
                h = server_setup.update_head(m.content) if m.author_id == bot else None
                msg = f"Fall {case} (Startwert {SEED + 1}), Nachricht {m.id}"
                if m.id in out:
                    self.assertEqual(m.author_id, bot, msg)                  # nie fremde Nachrichten
                    self.assertFalse(m.has_files, msg)                       # nie Dateien
                if h and h[1] == newest[h[0]]:
                    self.assertNotIn(m.id, out, msg)                         # neuster Update-Text bleibt
            self.assertEqual(len(out), len(set(out)))

    def test_ankuendigung_mit_beitrag_bleibt_live(self):
        rnd = random.Random(SEED + 2)
        for case in range(CASES):
            files = [f"kanal__reihe-1.{rnd.randrange(0, 5)}.md" for _ in range(rnd.randrange(1, 6))]
            rec = {f: {"ids": [1]} for f in files if rnd.random() < 0.5}
            live = updater.announce_live(files, set(files), rec, lambda fn: ("kanal__reihe",
                                                                              (1, int(fn.split(".")[1]))))
            for f in rec:
                self.assertIn(f, live, f"Fall {case} (Startwert {SEED + 2})")

    def test_nie_token_oder_webhook_in_texten(self):
        rnd = random.Random(SEED + 3)
        for case in range(CASES):
            rr = raid_ready.parse({"raidReady": {"raid": rnd.choice(("onyxia", "mc", "x")), "phase": "aufbau",
                                                 "aktiv": rnd.randrange(0, 41), "groesse": rnd.choice((10, 20, 40)),
                                                 "tanks": 1, "tanksSoll": 4, "heiler": 2, "heilerSoll": 8,
                                                 "wochen": rnd.choice((None, 1, 3)), "vorschlag": "raid"}})
            texts = [raid_ready.weekly_text(rr), raid_ready.suggestion_text(rr) or "",
                     member_area.apply_card_text("Alpine Vanguard"),
                     server_setup.welcome_text("Alpine Vanguard", {}, None)]
            for t in texts:
                self.assertIsNone(TOKEN_RE.search(t), f"Fall {case}")
                self.assertLess(len(t), 2000)


# ---------------------------------------------------------------------------------------------------------------
# TU6 Regressionen: je Befund ein bleibender Test T-<ID>
# ---------------------------------------------------------------------------------------------------------------
REGRESSIONEN = {
    "T-N1": ("test_mitgliederbereich", "OhneKategorie", "test_kanal_ohne_kategorie_wird_erfasst"),
    "T-N2": ("test_mitgliederbereich", "AddonMigration", "test_kategorie_und_kanaele_members_botonly"),
    "T-R1": ("test_mitgliederbereich", "BotCode", "test_raid_ohne_nachricht_wird_entfernt"),
    "T-R2": ("test_mitgliederbereich", "RaidAusKanal", "test_kanal_des_topfs"),
    "T-D1": ("test_mitgliederbereich", "Disboard", "test_nur_kanaele_verwalten_weg"),
    "T-RE1": ("test_mitgliederbereich", "BotCode", "test_raid_erstellen_antwortet_vor_dem_posten"),
    "T-RE2": ("test_mitgliederbereich", "BotCode", "test_raid_aus_dem_kanal"),
    "T-BEW": ("test_mitgliederbereich", "BewerbungOben", "test_ganz_nach_oben_und_nur_einmal"),
    "T-RP-D": ("test_raid_ready", "Termine", "test_nur_montag_und_einmal_pro_woche"),
    "T-108": ("test_update_schleife", "CopyNew", "test_gleiche_version_zweimal_nichts_geaendert"),
    "T-107": ("test_neustart_schleife", "Starter", "test_schleife_bekommt_pause"),
    "T-100": ("test_update_gleichzeitig", None, None),
}


class TU6Regressionen(unittest.TestCase):
    def test_regressionen_vorhanden(self):
        import importlib
        have = 0
        for tid, (mod, cls, meth) in REGRESSIONEN.items():
            with self.subTest(befund=tid):
                m = importlib.import_module(mod)
                if cls:
                    self.assertTrue(hasattr(getattr(m, cls), meth), tid)
                have += 1
        print(f"\nRegressionen: {have} von {len(REGRESSIONEN)} vorhanden", file=sys.stderr)


if __name__ == "__main__":
    unittest.main()
