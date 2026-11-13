"""T-RP-D (Bot 1.5.125): Raidfähigkeit im Offizierskanal (raid_ready.py).
Start: python3 -I -m unittest discover -s RaidMasterBot/tests"""
import os
import sys
import unittest
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import raid_ready  # noqa: E402

RR = {"raid": "onyxia", "phase": "aufbau", "aktiv": 23, "groesse": 40, "tanks": 2, "tanksSoll": 4, "heiler": 5,
      "heilerSoll": 10, "pct": 58, "wochen": 3, "t": 1794470000}


class Parse(unittest.TestCase):
    def test_beispiel_aus_dem_auftrag(self):
        rr = raid_ready.parse({"raidReady": RR})
        self.assertEqual(raid_ready.weekly_text(rr),
                         "📊 **Raidfähig (Onyxia):** 23/40 aktiv · Tanks 2/4 · Heiler 5/10 · Phase Aufbau · "
                         "Schätzung ~3 Wochen")

    def test_keine_namen_nur_bekannte_felder(self):
        rr = raid_ready.parse({"raidReady": dict(RR, namen=["Spieler1"], spieler={"x": 1})})
        self.assertNotIn("namen", rr)
        self.assertNotIn("spieler", rr)
        self.assertNotIn("Spieler1", raid_ready.weekly_text(rr))

    def test_unbrauchbar(self):
        for db in (None, {}, {"raidReady": None}, {"raidReady": "x"}, {"raidReady": {"aktiv": 3}},
                   {"raidReady": {"aktiv": 3, "groesse": 0}}, {"raidReady": {"aktiv": -1, "groesse": 40}}):
            self.assertIsNone(raid_ready.parse(db), db)

    def test_ohne_wochen_messe_noch_und_eine_woche(self):
        rr = raid_ready.parse({"raidReady": dict(RR, wochen=None)})
        self.assertIn("messe noch", raid_ready.weekly_text(rr))
        rr = raid_ready.parse({"raidReady": dict(RR, wochen=1)})
        self.assertIn("~1 Woche ", raid_ready.weekly_text(rr) + " ")


class Termine(unittest.TestCase):
    def test_nur_montag_und_einmal_pro_woche(self):
        mon = datetime(2026, 11, 16, 9, 0)
        self.assertTrue(raid_ready.weekly_due(mon, None))
        self.assertFalse(raid_ready.weekly_due(mon, raid_ready.week_key(mon)))          # nie doppelt
        for d in range(1, 7):
            self.assertFalse(raid_ready.weekly_due(mon + timedelta(days=d), None))
        self.assertTrue(raid_ready.weekly_due(mon + timedelta(days=7), raid_ready.week_key(mon)))

    def test_jahreswechsel(self):
        self.assertNotEqual(raid_ready.week_key(datetime(2026, 12, 28)), raid_ready.week_key(datetime(2027, 1, 4)))


class Vorschlag(unittest.TestCase):
    def test_vorschlag_einmal(self):
        rr = raid_ready.parse({"raidReady": dict(RR, vorschlag="uebergang")})
        self.assertIn("Phase Übergang", raid_ready.suggestion_text(rr))
        self.assertEqual(raid_ready.suggestion_key(rr), "Aufbau->Übergang")

    def test_kein_vorschlag_bei_gleicher_phase(self):
        rr = raid_ready.parse({"raidReady": dict(RR, vorschlag="Aufbau")})
        self.assertIsNone(raid_ready.suggestion_text(rr))
        self.assertIsNone(raid_ready.suggestion_key(rr))


class BotCode(unittest.TestCase):
    def test_nur_offizierskanal_und_merker(self):
        here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        with open(os.path.join(here, "bot.py"), encoding="utf-8") as f:
            src = f.read()
        body = src[src.index("async def post_raid_ready("):src.index("@tasks.loop(hours=1)\nasync def monthly_loop")]
        self.assertIn('find_channel(guild.text_channels, "offiziere")', body)
        self.assertEqual(body.count("ch.send("), 2)
        self.assertIn('state.data["raidready_week"]', body)
        self.assertIn('state.data["raidready_suggestion"]', body)


if __name__ == "__main__":
    unittest.main()
