"""Offline-Test (Bot 1.5.115): Mitglieder-Bereich und Bewerbung (member_area.py, Discord-Projekt DC2/DC3).
- Nur was @everyone heute sieht und nicht in einer offenen Kategorie liegt, wird dicht gemacht.
- Schon versteckte Kategorien (Offiziere, noch nicht angekündigte Raids) bleiben unverändert.
- Mitglieder-Rollen werden zuerst freigegeben, ein ausdrückliches 'aus' einer Rolle bleibt.
- Mitglieder ohne Rolle (ausser Gast, Bots, Besitzer) bekommen 'Mitglied'.
- Ohne vollständige Mitgliederliste (Intent aus) wird nicht eingerichtet.
- show_raid mit members_only blendet nur für Mitglieder ein.
Start: python3 -I -m unittest discover -s RaidMasterBot/tests"""
import asyncio
import os
import sys
import unittest

import discord

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
import member_area  # noqa: E402
import server_setup  # noqa: E402


class Role:
    def __init__(self, name, rid):
        self.name, self.id = name, rid

    def __hash__(self):
        return self.id

    def __eq__(self, other):
        return isinstance(other, Role) and other.id == self.id


class Item:
    def __init__(self, name, position, kind=discord.ChannelType.text, channels=None, ow=None):
        self.name, self.position, self.type = name, position, kind
        self.id = abs(hash(name)) % 10**9
        self.channels = channels or []
        self.ow = dict(ow or {})
        self.calls = []

    def overwrites_for(self, who):
        o = self.ow.get(who)
        return discord.PermissionOverwrite(**dict(iter(o))) if o else discord.PermissionOverwrite()

    async def set_permissions(self, who, overwrite=None, reason=None):
        self.calls.append((who.name, overwrite))
        if overwrite is None:
            self.ow.pop(who, None)
        else:
            self.ow[who] = overwrite


class Member:
    def __init__(self, mid, roles, bot=False):
        self.id, self.roles, self.bot, self.display_name = mid, roles, bot, f"M{mid}"


class Guild:
    def __init__(self):
        self.default_role = Role("@everyone", 1)
        self.roles = [self.default_role, Role("Offizier", 2), Role("Raidleitung", 3), Role("Raider", 4),
                      Role("Gast", 5), Role("Mitglied", 6)]
        r = {x.name: x for x in self.roles}
        hidden = discord.PermissionOverwrite(view_channel=False)
        self.chat = Item("handwerk-und-handel", 1)
        self.ro = Item("befehle", 2, ow={self.default_role: discord.PermissionOverwrite(send_messages=False)})
        self.voice = Item("AFK", 3, discord.ChannelType.voice)
        self.general = Item("💬 ALLGEMEIN", 3, discord.ChannelType.category, [self.chat, self.ro, self.voice])
        self.info_ch = Item("willkommen", 1)
        self.info = Item("📌 INFO", 0, discord.ChannelType.category, [self.info_ch])
        self.off_ch = Item("offiziere", 1, ow={self.default_role: hidden, r["Raidleitung"]: discord.PermissionOverwrite(view_channel=False)})
        self.off = Item("🔒 OFFIZIERE", 5, discord.ChannelType.category, [self.off_ch],
                        ow={self.default_role: hidden})
        self.bwl_ch = Item("bwl-taktik", 1, ow={self.default_role: hidden})
        self.bwl = Item("🖤 PECHSCHWINGENHORT", 9, discord.ChannelType.category, [self.bwl_ch], ow={self.default_role: hidden})
        self.categories = [self.info, self.general, self.off, self.bwl]
        self.owner_id = 100
        self.members = [Member(100, [self.default_role]), Member(101, [self.default_role]),
                        Member(102, [r["Raider"]]), Member(103, [r["Gast"]]), Member(104, [], bot=True)]
        self.member_count = 5


class Plan(unittest.TestCase):
    def test_nur_sichtbares_ausserhalb_offener_kategorien(self):
        g = Guild()
        names = [i.name for i in member_area.plan_items(g)]
        self.assertEqual(names, ["💬 ALLGEMEIN", "handwerk-und-handel", "befehle", "AFK"])

    def test_gate_rollen_zuerst_und_rest_bleibt(self):
        g = Guild()
        roles = member_area.member_roles(g)
        self.assertTrue(asyncio.run(member_area.gate_item(g.ro, g, roles)))
        self.assertEqual(g.ro.calls[-1][0], "@everyone")                  # @everyone als letztes gesperrt
        e = g.ro.overwrites_for(g.default_role)
        self.assertIs(e.view_channel, False)
        self.assertIs(e.send_messages, False)                             # "nur Bot schreibt" bleibt
        for r in roles:
            self.assertIs(g.ro.overwrites_for(r).view_channel, True)
        self.assertFalse(asyncio.run(member_area.gate_item(g.ro, g, roles)))   # zweites Mal: nichts zu tun

    def test_bot_sieht_weiter(self):
        g = Guild()
        g.me = Role("bot", 99)
        asyncio.run(member_area.gate_item(g.chat, g, member_area.member_roles(g)))
        self.assertIs(g.chat.overwrites_for(g.me).view_channel, True)
        ow = member_area.gate_overwrites({}, g)
        self.assertIs(ow[g.me].view_channel, True)

    def test_ausdrueckliches_aus_bleibt(self):
        g = Guild()
        raidl = next(r for r in g.roles if r.name == "Raidleitung")
        g.chat.ow[raidl] = discord.PermissionOverwrite(view_channel=False)
        asyncio.run(member_area.gate_item(g.chat, g, member_area.member_roles(g)))
        self.assertIs(g.chat.overwrites_for(raidl).view_channel, False)

    def test_wer_bekommt_mitglied(self):
        g = Guild()
        self.assertEqual([m.id for m in member_area.members_without_role(g)], [101])

    def test_ohne_intent_unvollstaendig(self):
        g = Guild()
        self.assertTrue(member_area.members_complete(g))
        g.members = g.members[-1:]
        self.assertFalse(member_area.members_complete(g))
        text = member_area.preview_text(g, [], [], True, True, False)
        self.assertIn("Server Members Intent", text)

    def test_gate_overwrites(self):
        g = Guild()
        ow = member_area.gate_overwrites({g.default_role: discord.PermissionOverwrite(send_messages=False)}, g)
        self.assertIs(ow[g.default_role].view_channel, False)
        self.assertIs(ow[g.default_role].send_messages, False)
        self.assertTrue(all(ow[r].view_channel for r in member_area.member_roles(g)))

    def test_bewerbung_offen_und_threads(self):
        g = Guild()
        me = Role("bot", 99)
        ow = member_area.apply_overwrites(g, me)
        e = ow[g.default_role]
        self.assertTrue(e.view_channel and e.send_messages_in_threads)
        self.assertFalse(e.send_messages or e.create_private_threads or e.create_public_threads)
        self.assertTrue(ow[me].create_private_threads and ow[me].manage_threads)
        self.assertTrue(member_area.is_open_category(member_area.APPLY_CATEGORY))
        self.assertLess(len(member_area.apply_card_text("Alpine Vanguard")), 2000)
        self.assertLessEqual(len(member_area.thread_name("x" * 200, "")), 90)


class OhneKategorie(unittest.TestCase):
    def test_kanal_ohne_kategorie_wird_erfasst(self):
        g = Guild()
        lose = Item("lose", 0)
        lose.category_id = None
        g.chat.category_id = 7
        g.channels = [g.general, g.chat, lose]
        names = [i.name for i in member_area.plan_items(g)]
        self.assertEqual(names.count("lose"), 1)
        self.assertEqual(names.count("handwerk-und-handel"), 1)


class Raids(unittest.TestCase):
    def test_show_raid_nur_fuer_mitglieder(self):
        g = Guild()
        n = asyncio.run(server_setup.show_raid(g, [g.bwl, g.bwl_ch], {}, "t", members_only=True))
        self.assertEqual(n, 2)
        self.assertIs(g.bwl_ch.overwrites_for(g.default_role).view_channel, False)
        raider = next(r for r in g.roles if r.name == "Raider")
        self.assertIs(g.bwl_ch.overwrites_for(raider).view_channel, True)

    def test_hide_raid_nimmt_mitglieder_freigabe_zurueck(self):
        g = Guild()

        class Me(Role):
            pass
        g.me = Me("bot", 99)
        asyncio.run(member_area.gate_item(g.chat, g, member_area.member_roles(g)))
        asyncio.run(server_setup.hide_raid(g, [g.chat], "t"))
        raider = next(r for r in g.roles if r.name == "Raider")
        off = next(r for r in g.roles if r.name == "Offizier")
        self.assertIsNone(g.chat.overwrites_for(raider).view_channel)
        self.assertIs(g.chat.overwrites_for(off).view_channel, True)


class AddonKanaele(unittest.TestCase):
    def test_members_botonly(self):
        g = Guild()
        g.me = Role("bot", 99)
        r = {x.name: x for x in g.roles}
        ow = server_setup._overwrites("members_botonly", g, {k: r[k] for k in ("Offizier", "Raidleitung", "Raider", "Gast")})
        self.assertIs(ow[g.default_role].view_channel, False)
        for n in ("Mitglied", "Raider", "Raidleitung"):
            self.assertIs(ow[r[n]].view_channel, True)
            self.assertIs(ow[r[n]].send_messages, False)
        self.assertTrue(ow[r["Offizier"]].send_messages)
        self.assertNotIn(r["Gast"], ow)
        cat = next(c for c in server_setup.BASE_TOP if c["name"] == server_setup.ADDON_CATEGORY)
        self.assertEqual({cat["mode"]} | {c[3] for c in cat["channels"]}, {"members_botonly"})


class AddonMigration(unittest.TestCase):
    def test_kategorie_und_kanaele_members_botonly(self):
        g = Guild()
        g.me = Role("bot", 99)
        r = {x.name: x for x in g.roles}

        class Ch(Item):
            @property
            def overwrites(self):
                return dict(self.ow)

            async def edit(self, overwrites=None, reason=None):
                self.calls.append(("edit", reason))
                self.ow = dict(overwrites)
        hand = Ch("ahsentinel", 1, ow={g.default_role: discord.PermissionOverwrite(view_channel=False),
                                       r["Offizier"]: discord.PermissionOverwrite(view_channel=True)})
        cat = Ch(server_setup.ADDON_CATEGORY, 6, discord.ChannelType.category, [hand], ow=dict(hand.ow))
        g.categories.append(cat)
        done = asyncio.run(server_setup.open_addon_channels_to_members(g))
        self.assertEqual(sorted(done), sorted([cat.name, "ahsentinel"]))
        for item in (cat, hand):
            self.assertIs(item.ow[g.default_role].view_channel, False)
            self.assertNotIn(r["Gast"], item.ow)
            self.assertIs(item.ow[r["Mitglied"]].view_channel, True)
            self.assertIs(item.ow[r["Mitglied"]].send_messages, False)
            self.assertTrue(item.ow[g.me].view_channel and item.ow[g.me].send_messages)
        self.assertEqual(asyncio.run(server_setup.open_addon_channels_to_members(g)), [])   # zweiter Lauf: nichts


class BotCode(unittest.TestCase):
    def test_raid_erstellen_antwortet_vor_dem_posten(self):
        with open(os.path.join(HERE, "bot.py"), encoding="utf-8") as f:
            src = f.read()
        body = src[src.index("async def raid_create("):]
        body = body[:body.index("\n\n\n")]
        self.assertLess(body.index("inter.response.defer("), body.index("channel_by_id("))
        self.assertLess(body.index("target.send(embed"), body.index("inter.followup.send(f\"Raid erstellt"))
        self.assertNotIn("inter.response.send_message(embed", body)

    def test_raidmaster_pflicht_hinweis(self):
        with open(os.path.join(HERE, "bot.py"), encoding="utf-8") as f:
            src = f.read()
        body = src[src.index("def addon_hint("):src.index("def profile_text(")]
        self.assertIn('"pug"', body)
        self.assertIn("RaidMaster", body)
        self.assertEqual(src.count("addon_hint(raid, actual)"), 2)

    def test_einrichten_nur_mit_bestaetigung(self):
        with open(os.path.join(HERE, "bot.py"), encoding="utf-8") as f:
            src = f.read()
        body = src[src.index("async def member_area_cmd("):]
        body = body[:body.index("\nbot.tree.add_command(mitgliederbereich_group)")]
        self.assertLess(body.index("if not bestaetigen or not complete:"), body.index("gate_item("))
        self.assertNotIn(".delete(", body)


if __name__ == "__main__":
    unittest.main()
