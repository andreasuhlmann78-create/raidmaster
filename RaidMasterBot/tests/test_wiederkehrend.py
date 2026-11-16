"""T-D-N1-W3: Wiederkehrende Raids (D-N1 Wunsch 3, ab Bot 1.5.186) – ohne Netz.

wiederkehrend.py: Uhrzeit lesen; fällige Termine (nur Wochentag, nur Zukunft, höchstens N Wochen voraus, nicht vor
dem Öffnungsdatum); Sommer-/Winterzeit (20:00 Schweizer Zeit = 19:00 UTC im Winter, 18:00 UTC im Sommer, an beiden
Umstellungen); "schon da" (gemerkt, im Buch auch abgesagt, nur gleicher Raid); Merken mit Aufräumen.
wiederkehrend_bot.py mit echtem RaidBook (Temp-Ordner des Test-Bots): Anlegen erstellt und postet die Raids mit
Plätzen je Rolle; kein Doppel beim zweiten Lauf und nach Neustart (gemerkt verloren -> Buch; Raid gelöscht ->
gemerkt); Pausieren/wieder starten; Löschen lässt Raids stehen; Öffnungsdatum; ohne Kanal nichts gemerkt;
Rechte, unbekannter Raid, falsche Uhrzeit, doppelte Vorlage.
"""
import asyncio
import os
import sys
import types
import unittest
from datetime import date, datetime, timezone
from zoneinfo import ZoneInfo

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.dirname(__file__))

import wiederkehrend as wk  # noqa: E402

N = types.SimpleNamespace
Z = ZoneInfo("Europe/Zurich")
JETZT = datetime(2026, 11, 16, 10, 0, tzinfo=Z)                 # Montag


def tpl(**kw):
    return dict({"id": 1, "pool": "mc", "title": "MC Mittwoch", "weekday": 2, "time": "20:00", "weeks": 2,
                 "description": "", "max": 0, "limits": {}, "paused": False, "creator": 1, "done": []}, **kw)


class Rein(unittest.TestCase):
    def test_uhrzeit(self):
        self.assertEqual([wk.parse_time(t) for t in ("20:00", "8:5", " 19.30 ")], ["20:00", "08:05", "19:30"])
        for t in ("24:00", "20:60", "20", "abc", ""):
            with self.assertRaises(ValueError):
                wk.parse_time(t)

    def test_plan(self):
        self.assertEqual([d.date() for d in wk.plan(tpl(), JETZT)], [date(2026, 11, 18), date(2026, 11, 25)])
        self.assertEqual(len(wk.plan(tpl(weeks=1), JETZT)), 1)
        self.assertEqual(len(wk.plan(tpl(weeks=4), JETZT)), 4)
        self.assertEqual(len(wk.plan(tpl(weeks=9), JETZT)), 4)                      # höchstens 4 Wochen
        heute = tpl(weekday=0)
        self.assertEqual(wk.plan(heute, JETZT)[0].date(), date(2026, 11, 16))        # heute 20:00 noch offen
        spaet = datetime(2026, 11, 16, 20, 0, tzinfo=Z)
        self.assertEqual(wk.plan(heute, spaet)[0].date(), date(2026, 11, 23))        # genau jetzt: nicht mehr
        self.assertEqual([d.date() for d in wk.plan(tpl(weeks=4), JETZT, date(2026, 12, 9))], [date(2026, 12, 9)])
        self.assertEqual(wk.plan(tpl(), JETZT, date(2026, 12, 9)), [])

    def test_sommer_winterzeit(self):
        utc = lambda dts: [d.astimezone(timezone.utc).strftime("%d.%m. %H:%M") for d in dts]   # noqa: E731
        self.assertEqual(utc(wk.plan(tpl(), datetime(2027, 3, 22, 12, tzinfo=Z))), ["24.03. 19:00", "31.03. 18:00"])
        self.assertEqual(utc(wk.plan(tpl(), datetime(2026, 10, 19, 12, tzinfo=Z))), ["21.10. 18:00", "28.10. 19:00"])
        sonntag = tpl(weekday=6, time="02:30")                                      # Umstellungstag selbst
        d = wk.plan(sonntag, datetime(2026, 10, 24, 12, tzinfo=Z))[0]
        self.assertEqual((d.date(), d.strftime("%H:%M")), (date(2026, 10, 25), "02:30"))

    def test_schon_da_und_merken(self):
        dt = datetime(2026, 11, 18, 20, tzinfo=Z)
        self.assertFalse(wk.already(tpl(), dt, []))
        self.assertTrue(wk.already(tpl(done=["2026-11-18"]), dt, []))
        mc = {"pool": "mc", "start": int(datetime(2026, 11, 18, 21, tzinfo=Z).timestamp()), "cancelled": True}
        self.assertTrue(wk.already(tpl(), dt, [mc]))                                   # auch abgesagt
        self.assertFalse(wk.already(tpl(), dt, [dict(mc, pool="ony")]))                # anderer Raid
        nachts = {"pool": "mc", "start": int(datetime(2026, 11, 18, 0, 30, tzinfo=Z).timestamp())}
        self.assertTrue(wk.already(tpl(), dt, [nachts]))                               # Schweizer Tag, nicht UTC
        t = tpl(done=["2026-10-01", "2026-11-04"])
        wk.mark_done(t, dt, date(2026, 11, 16))
        wk.mark_done(t, dt, date(2026, 11, 16))
        self.assertEqual(t["done"], ["2026-11-04", "2026-11-18"])
        self.assertEqual(wk.describe(tpl(weeks=1), "Molten Core"), "Molten Core – jeden Mittwoch 20:00, 1 Woche im Voraus")


class Kanal:
    def __init__(self):
        self.id, self.name, self.mention, self.sent, self.fail = 77, "mc-anmeldung", "#mc-anmeldung", [], False

    async def send(self, embed=None, view=None, **kw):
        if self.fail:
            import discord
            raise discord.HTTPException(N(status=403, reason="x"), "verboten")
        self.sent.append(embed)
        return N(id=900 + len(self.sent))


class Antwort:
    def __init__(self):
        self.messages = []

    async def send_message(self, text, **kw):
        assert kw.get("ephemeral")
        self.messages.append(text)

    async def defer(self, **kw):
        pass

    async def send(self, text, **kw):                                  # followup.send
        await self.send_message(text, **kw)


class Bot(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from bot_harness import load_bot
        cls.bot, _ = load_bot()
        cls.m = sys.modules["wiederkehrend_bot"]

    def setUp(self):
        m = self.m
        self.saved = {k: getattr(m, k) for k in ("now_local", "channel_by_id", "raid_channel", "create_raid_event",
                                                 "is_creator", "post_bot_log")}
        self.saved_state = {k: m.state.data.get(k) for k in ("recurring", "recurring_next")}
        self.saved_save = m.state.save
        self.saved_raids = dict(m.book.raids.data["raids"])
        m.state.data["recurring"], m.state.data["recurring_next"] = [], 1
        m.state.save = lambda: None
        m.book.raids.data["raids"].clear()
        self.ch, self.logs = Kanal(), []
        m.now_local = lambda: JETZT
        m.raid_channel = lambda pool, kind: 5

        async def by_id(cid):
            return self.ch if cid == 5 else None

        async def noop(*a):
            return None

        async def blog(t):
            self.logs.append(t)
        m.channel_by_id, m.create_raid_event, m.is_creator, m.post_bot_log = by_id, noop, (lambda u: True), blog

    def tearDown(self):
        m = self.m
        for k, v in self.saved.items():
            setattr(m, k, v)
        for k, v in self.saved_state.items():
            m.state.data[k] = v if v is not None else ([] if k == "recurring" else 1)
        m.state.save = self.saved_save
        m.book.raids.data["raids"].clear()
        m.book.raids.data["raids"].update(self.saved_raids)
        m.book.save()

    def anlegen(self, raid="mc", tag=2, zeit="20:00", **kw):
        i = N(user=N(id=1), response=Antwort(), followup=Antwort())
        args = dict(wochen_voraus=2, titel=None, beschreibung=None, max_spieler=0, tanks=None, heiler=None,
                    nahkampf=None, fernkampf=None)
        args.update(kw)
        asyncio.run(self.m.recurring_add.callback(i, raid, N(value=tag, name=wk.WEEKDAYS[tag]), zeit, **args))
        return (i.response.messages + i.followup.messages)[0]

    def befehl(self, cmd, *a):
        i = N(user=N(id=1), response=Antwort(), followup=Antwort())
        asyncio.run(cmd.callback(i, *a))
        return (i.response.messages + i.followup.messages)[0]

    def raids(self):
        return sorted(self.m.book.all(), key=lambda r: r["start"])

    def test_angemeldet(self):
        g = self.bot.bot.tree.get_command("raid").get_command("wiederkehrend")
        self.assertIs(g, self.m.recurring_group)
        self.assertEqual(sorted(c.name for c in g.commands), ["anlegen", "liste", "loeschen", "pausieren"])

    def test_anlegen_erstellt_und_postet(self):
        text = self.anlegen(heiler=8, max_spieler=40)
        self.assertIn("Wochentermin **#1** eingetragen: Molten Core – jeden Mittwoch 20:00, 2 Wochen im Voraus", text)
        self.assertIn("Jetzt angelegt: 2 Raids", text)
        rs = self.raids()
        self.assertEqual([datetime.fromtimestamp(r["start"], Z).strftime("%d.%m. %H:%M") for r in rs],
                         ["18.11. 20:00", "25.11. 20:00"])
        self.assertEqual({(r["pool"], r["title"], r["max"], r["recurring"], r["message_id"] is not None) for r in rs},
                         {("mc", "Molten Core Mittwoch", 40, 1, True)})
        self.assertEqual(rs[0]["limits"], {"heal": 8})
        self.assertEqual(len(self.ch.sent), 2)
        self.assertEqual(self.m.state.data["recurring"][0]["done"], ["2026-11-18", "2026-11-25"])

    def test_kein_doppel_auch_nach_neustart(self):
        self.anlegen()
        self.assertEqual(asyncio.run(self.m.run_recurring()), 0)
        t = self.m.state.data["recurring"][0]
        t["done"] = []                                                  # gemerkt verloren: Buch verhindert Doppel
        self.assertEqual(asyncio.run(self.m.run_recurring()), 0)
        self.m.book.raids.data["raids"].clear()                         # Raids gelöscht, aber gemerkt
        wk.mark_done(t, datetime(2026, 11, 18, 20, tzinfo=Z), JETZT.date())
        wk.mark_done(t, datetime(2026, 11, 25, 20, tzinfo=Z), JETZT.date())
        self.assertEqual(asyncio.run(self.m.run_recurring()), 0)
        self.m.now_local = lambda: datetime(2026, 11, 19, 9, tzinfo=Z)  # eine Woche weiter: nur der neue Termin
        self.assertEqual(asyncio.run(self.m.run_recurring()), 1)
        self.assertEqual(datetime.fromtimestamp(self.raids()[-1]["start"], Z).date(), date(2026, 12, 2))

    def test_pausieren_und_loeschen(self):
        self.anlegen(wochen_voraus=1)
        self.assertIn("pausiert", self.befehl(self.m.recurring_pause, 1))
        self.m.now_local = lambda: datetime(2026, 11, 19, 9, tzinfo=Z)
        self.assertEqual(asyncio.run(self.m.run_recurring()), 0)
        self.assertIn("⏸️ pausiert", self.befehl(self.m.recurring_list))
        self.assertIn("läuft wieder. Jetzt angelegt: 1", self.befehl(self.m.recurring_pause, 1))
        self.assertIn("gelöscht", self.befehl(self.m.recurring_delete, 1))
        self.assertEqual(self.m.state.data["recurring"], [])
        self.assertEqual(len(self.raids()), 2)                          # angelegte Raids bleiben
        self.assertIn("gibt es nicht", self.befehl(self.m.recurring_delete, 1))
        self.assertIn("Keine festen Wochentermine", self.befehl(self.m.recurring_list))

    def test_oeffnungsdatum(self):
        text = self.anlegen(raid="ony", wochen_voraus=4)
        self.assertIn("Erste Termine ab Öffnung am 09.12.2026", text)
        self.assertEqual([datetime.fromtimestamp(r["start"], Z).date() for r in self.raids()], [date(2026, 12, 9)])

    def test_ohne_kanal_und_discord_fehler(self):
        self.m.raid_channel = lambda pool, kind: 0
        self.assertIn("Jetzt angelegt: 0 Raids", self.anlegen())
        self.assertEqual(self.m.state.data["recurring"][0]["done"], [])         # nichts gemerkt: nächster Lauf
        self.m.raid_channel = lambda pool, kind: 5
        self.ch.fail = True
        self.assertEqual(asyncio.run(self.m.run_recurring()), 0)
        self.assertEqual(self.raids(), [])                                       # kein Raid ohne Nachricht
        self.assertIn("Wiederkehrender Raid", self.logs[0])
        self.ch.fail = False
        self.assertEqual(asyncio.run(self.m.run_recurring()), 2)

    def test_rechte_und_eingaben(self):
        self.m.is_creator = lambda u: False
        for cmd, args in ((self.m.recurring_list, ()), (self.m.recurring_pause, (1,)), (self.m.recurring_delete, (1,))):
            self.assertIn("nur der Gildenchef", self.befehl(cmd, *args))
        self.assertIn("nur der Gildenchef", self.anlegen())
        self.m.is_creator = lambda u: True
        self.assertIn("kenne ich nicht", self.anlegen(raid="gibtsnicht"))
        self.assertIn("HH:MM", self.anlegen(zeit="25:00"))
        self.assertEqual(self.m.state.data["recurring"], [])
        self.anlegen(zeit="20.00")
        self.assertIn("gibt es schon", self.anlegen(zeit="20:00"))
        self.assertEqual(len(self.m.state.data["recurring"]), 1)


if __name__ == "__main__":
    unittest.main()
