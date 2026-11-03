"""Offline-Tests Gildenbank (Bot 1.5.96): ein Kanal #gildenbank, Bestand von RaidMaster oder GuildSentinel.
Start: python3 -I -m unittest discover -s RaidMasterBot/tests"""
import asyncio
import gzip
import json
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import discord  # noqa: E402
import guildbank  # noqa: E402
import raidmaster_data as rmd  # noqa: E402

BOT_ID = 1
MEMBER_ID = 2


# --- nachgebaute Discord-Objekte -------------------------------------------------------------------------------
class Author:
    def __init__(self, uid):
        self.id = uid


class Msg:
    def __init__(self, ch, mid, content, author_id=BOT_ID):
        self.channel, self.id, self.content, self.author = ch, mid, content, Author(author_id)


class Partial:
    def __init__(self, ch, mid):
        self.ch, self.mid = ch, int(mid)

    def _find(self):
        for m in self.ch.messages:
            if m.id == self.mid:
                return m
        raise discord.NotFound(FakeResp(), "unbekannte Nachricht")

    async def edit(self, content):
        self._find().content = content

    async def delete(self):
        self.ch.messages.remove(self._find())


class FakeResp:
    status = 404
    reason = "Not Found"


class Channel:
    _next = 1000

    def __init__(self, cid, name, guild):
        self.id, self.name, self.guild, self.messages, self.deleted = cid, name, guild, [], False

    async def send(self, text, author_id=BOT_ID):
        Channel._next += 1
        m = Msg(self, Channel._next, text, author_id)
        self.messages.append(m)
        return m

    def get_partial_message(self, mid):
        return Partial(self, mid)

    async def history(self, limit=100):
        for m in list(reversed(self.messages))[:limit]:
            yield m

    async def delete(self, reason=None):
        self.deleted = True
        self.guild.text_channels.remove(self)


class Guild:
    def __init__(self, *names):
        self.text_channels = []
        for i, n in enumerate(names):
            self.text_channels.append(Channel(10 + i, n, self))

    def ch(self, name):
        return guildbank.find_channel(self.text_channels, name)


def run(coro):
    return asyncio.run(coro)


def texts(ch):
    return [m.content for m in ch.messages]


# --- Kanal zusammenlegen ---------------------------------------------------------------------------------------
class OneChannel(unittest.TestCase):
    def setup_server(self, member_message=False):
        g = Guild("gildenbank", "gildenbank-bestand")
        bank, old = g.ch("gildenbank"), g.ch("gildenbank-bestand")
        run(bank.send("REGELN"))
        state = {"bank_messages": [], "bank_t": 5}
        m = run(old.send("BESTAND alt"))
        state["bank_messages"] = [m.id]
        if member_message:
            run(old.send("Danke für die Tränke!", author_id=MEMBER_ID))
        return g, bank, old, state

    def test_beide_kanaele_nur_bot(self):
        g, bank, old, state = self.setup_server()
        rep = run(guildbank.migrate_old_channel(g.text_channels, bank, state, BOT_ID, old))
        self.assertTrue(old.deleted)
        self.assertIsNone(g.ch("gildenbank-bestand"))
        self.assertIn(guildbank.OLD_DELETED, rep)
        self.assertEqual(state["bank_messages"], [])
        self.assertNotIn("bank_t", state)
        run(guildbank.write_bank(bank, ["BESTAND neu"], state))
        self.assertEqual(texts(bank), ["REGELN", "BESTAND neu"])

    def test_mitglieder_nachricht_nicht_loeschen(self):
        g, bank, old, state = self.setup_server(member_message=True)
        rep = run(guildbank.migrate_old_channel(g.text_channels, bank, state, BOT_ID, old))
        self.assertFalse(old.deleted)
        self.assertIn(guildbank.OLD_HAS_MEMBER_MESSAGES, rep)
        self.assertEqual(texts(old), ["Danke für die Tränke!"])      # Bot-Bestand dort entfernt, Mitglied bleibt
        # nur einmal versuchen
        rep2 = run(guildbank.migrate_old_channel(g.text_channels, bank, state, BOT_ID, None))
        self.assertEqual(rep2, [])
        self.assertFalse(old.deleted)

    def test_nur_gildenbank(self):
        g = Guild("gildenbank", "allgemeines")
        bank = g.ch("gildenbank")
        run(bank.send("REGELN"))
        state = {"bank_messages": []}
        rep = run(guildbank.migrate_old_channel(g.text_channels, bank, state, BOT_ID, None))
        self.assertEqual(rep, [])
        self.assertEqual(len(g.text_channels), 2)
        run(guildbank.write_bank(bank, ["BESTAND"], state))
        self.assertEqual(texts(bank), ["REGELN", "BESTAND"])
        # normale Änderung bearbeitet, postet nicht neu
        mid = state["bank_messages"][0]
        run(guildbank.write_bank(bank, ["BESTAND 2"], state))
        self.assertEqual(state["bank_messages"], [mid])
        self.assertEqual(texts(bank), ["REGELN", "BESTAND 2"])

    def test_alter_stand_ohne_vorgemerkten_kanal(self):
        # Stand vor 1.5.96: bank_messages ohne "bank_channel" -> liegen in #gildenbank-bestand
        g, bank, old, state = self.setup_server()
        run(guildbank.migrate_old_channel(g.text_channels, bank, state, BOT_ID, None))
        self.assertTrue(old.deleted)
        self.assertEqual(state["bank_messages"], [])

    def test_regel_geaendert_reihenfolge(self):
        g = Guild("gildenbank")
        bank = g.ch("gildenbank")
        rule = run(bank.send("REGELN 1"))
        state = {}
        run(guildbank.write_bank(bank, ["BESTAND a", "BESTAND b"], state))
        state["bank_t"] = 7
        # Regeltext geändert und länger: zweite Regel-Nachricht kommt dazu (landet zunächst unter dem Bestand)
        run(Partial(bank, rule.id).edit("REGELN 1 neu"))
        run(bank.send("REGELN 2"))
        run(guildbank.reset_bank(bank, state))
        self.assertNotIn("bank_t", state)
        run(guildbank.write_bank(bank, ["BESTAND a", "BESTAND b"], state))
        self.assertEqual(texts(bank), ["REGELN 1 neu", "REGELN 2", "BESTAND a", "BESTAND b"])

    def test_weniger_teile_loescht_ueberzaehlige(self):
        g = Guild("gildenbank")
        bank = g.ch("gildenbank")
        state = {}
        run(guildbank.write_bank(bank, ["A", "B", "C"], state))
        run(guildbank.write_bank(bank, ["A2"], state))
        self.assertEqual(texts(bank), ["A2"])
        self.assertEqual(len(state["bank_messages"]), 1)


# --- Bestand von RaidMaster und GuildSentinel ------------------------------------------------------------------
def lua_db(var, t, char="Bankchar", item="Lavakern"):
    return (f'{var} = {{\n\t["bank"] = {{\n\t\t["c"] = "{char}",\n\t\t["t"] = {t},\n\t\t["g"] = 12345,\n'
            f'\t\t["i"] = {{\n\t\t\t[17011] = {{ ["n"] = "{item}", ["c"] = 3, ["q"] = 3 }},\n\t\t}},\n\t}},\n}}\n')


class Sources(unittest.TestCase):
    def test_nur_raidmaster_alter_uploader(self):
        rm, gs = rmd.pick_upload_files(["RaidMaster.lua.gz"])
        self.assertEqual((rm, gs), (0, None))
        rm_db = rmd.parse_saved_variables(lua_db("RaidMasterDB", 100))["RaidMasterDB"]
        b = rmd.choose_bank(rm_db, None)
        self.assertEqual((b["src"], b["t"], b["items"][0]["c"]), ("raidmaster", 100, 3))

    def test_beide_dateien_neuerer_gewinnt(self):
        rm, gs = rmd.pick_upload_files(["RaidMaster.lua.gz", "GuildSentinel.lua.gz", "shot_1_2.jpg"])
        self.assertEqual((rm, gs), (0, 1))
        rm_db = rmd.parse_saved_variables(lua_db("RaidMasterDB", 100))["RaidMasterDB"]
        text, gs_db = rmd.check_guildsentinel_upload(gzip.compress(lua_db("GuildSentinelDB", 200, item="Feuerkern").encode()),
                                                     "GuildSentinel.lua.gz")
        b = rmd.choose_bank(rm_db, gs_db)
        self.assertEqual((b["src"], b["t"], b["items"][0]["n"]), ("guildsentinel", 200, "Feuerkern"))
        rm_db2 = rmd.parse_saved_variables(lua_db("RaidMasterDB", 300))["RaidMasterDB"]
        self.assertEqual(rmd.choose_bank(rm_db2, gs_db)["src"], "raidmaster")

    def test_reihenfolge_der_anhaenge_egal(self):
        self.assertEqual(rmd.pick_upload_files(["guildsentinel.lua.gz", "RaidMaster.lua.gz"]), (1, 0))
        self.assertEqual(rmd.pick_upload_files(["GuildSentinel.lua"]), (None, 0))

    def test_guildsentinel_ohne_bank(self):
        with self.assertRaises(ValueError):
            rmd.check_guildsentinel_upload(b'GuildSentinelDB = {\n\t["members"] = {},\n}\n', "GuildSentinel.lua")
        with self.assertRaises(ValueError):
            rmd.check_guildsentinel_upload(b"kaputt {{{", "GuildSentinel.lua")
        with self.assertRaises(ValueError):
            rmd.check_guildsentinel_upload(b"kein gzip", "GuildSentinel.lua.gz")

    def test_kein_bestand(self):
        self.assertIsNone(rmd.choose_bank(None, None))
        self.assertIsNone(rmd.choose_bank({"data": {}}, {"members": {}}))


class Rules(unittest.TestCase):
    def test_guild_rules(self):
        path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "guild_rules.json")
        with open(path, encoding="utf-8") as f:
            d = json.load(f)
        keys = [c["key"] for c in d["channels"]]
        self.assertIn("gildenbank", keys)
        self.assertNotIn("gildenbank-bestand", keys)
        gb = next(c for c in d["channels"] if c["key"] == "gildenbank")
        text = "\n".join(gb["posts"])
        self.assertNotIn("{#gildenbank-bestand}", text)
        self.assertIn("RaidMaster oder GuildSentinel", text)
        self.assertLess(len(text), 2000)


if __name__ == "__main__":
    unittest.main()
