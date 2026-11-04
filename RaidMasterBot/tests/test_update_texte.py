"""Offline-Test (Bot 1.5.104): in den Addon-Kanälen bleibt von den Update-Texten nur der neueste je Addon.
Nachrichten mit Datei, Vorstellungen/Übersichten/Hilfen, geschützte Beiträge und Nachrichten anderer bleiben.
Start: python3 -I -m unittest discover -s RaidMasterBot/tests"""
import os
import sys
import unittest
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server_setup  # noqa: E402

BOT, USER = 1, 2
T0 = datetime(2026, 11, 1, 12, 0, tzinfo=timezone.utc)


class M:
    def __init__(self, mid, content, minutes=0, seconds=0, author=BOT, files=False):
        self.id, self.content, self.author_id, self.has_files = mid, content, author, files
        self.created_at = T0 + timedelta(minutes=minutes, seconds=seconds)


def plan(msgs, protected=()):
    return sorted(server_setup.plan_update_cleanup(msgs, BOT, protected))


class Kopfzeile(unittest.TestCase):
    def test_update_texte(self):
        self.assertEqual(server_setup.update_head("📦 **ThreatSentinel 2.4.4** – Ladefehler behoben"),
                         ("threatsentinel", (2, 4, 4, 0)))
        self.assertEqual(server_setup.update_head("📢 **LevelPilot 3.12.5** – Reparieren"), ("levelpilot", (3, 12, 5, 0)))
        self.assertEqual(server_setup.update_head("🆕 **AHSentinel 0.65.7** ist da!\nDownload …"), ("ahsentinel", (0, 65, 7, 0)))
        self.assertEqual(server_setup.update_head("📦 **AH Analyzer Pro 0.60.1** – alt"), ("ahsentinel", (0, 60, 1, 0)))

    def test_keine_update_texte(self):
        for text in ("📘 **LevelPilot – was das Addon kann** (Stand 3.12.5)",
                     "🛡️ **ThreatSentinel – was das Addon kann** (Version 2.2)",
                     "# ❓ AHSentinel – Hilfe",
                     "💰 **AHSentinel – das Auktionshaus-Addon**",
                     "Ich habe Version 2.4.4 installiert und es geht nicht",
                     ""):
            self.assertIsNone(server_setup.update_head(text), text)

    def test_2_0_gleich_2_0_0(self):
        self.assertEqual(server_setup.update_head("📦 **ThreatSentinel 2.0** – x")[1],
                         server_setup.update_head("📦 **ThreatSentinel 2.0.0** – x")[1])


class Aufraeumen(unittest.TestCase):
    def test_nur_neuester_text_bleibt(self):
        msgs = [M(1, "📦 **ThreatSentinel 2.4.3** – letzte Vorbereitung", 0),
                M(2, "Teil 2 vom Text 2.4.3", 0, 1),                                  # Fortsetzung
                M(3, "📦 **ThreatSentinel 2.4.4** – Ladefehler behoben", 60),
                M(4, "📦 **ThreatSentinel 2.4.5** – bitte aktualisieren", 120)]
        self.assertEqual(plan(msgs), [1, 2, 3])

    def test_dateien_bleiben(self):
        msgs = [M(1, "📦 **ThreatSentinel 2.4.3** – mit ZIP", 0, files=True),
                M(2, "🆕 **ThreatSentinel 2.4.4** ist da!", 30, files=True),
                M(3, "📦 **ThreatSentinel 2.4.4** – Text", 31),
                M(4, "📦 **ThreatSentinel 2.4.5** – Text", 60)]
        self.assertEqual(plan(msgs), [3])

    def test_vorstellung_und_andere_bleiben(self):
        msgs = [M(1, "📘 **LevelPilot – was das Addon kann** (Stand 3.4.0)", 0),
                M(2, "📢 **LevelPilot 3.4.0** – alt", 1),
                M(3, "Danke, läuft super!", 1, 5, author=USER),                      # Mitglied: nie
                M(4, "📢 **LevelPilot 3.12.5** – neu", 100)]
        self.assertEqual(plan(msgs), [2])

    def test_fortsetzung_endet_an_anderer_nachricht(self):
        msgs = [M(1, "📦 **BuffSentinel 0.9.6** – alt", 0),
                M(2, "Fortsetzung", 0, 2),
                M(3, "🛡️ **BuffSentinel – was das Addon kann**", 0, 10),               # geschützte Vorstellung
                M(4, "noch ein Teil der Vorstellung", 0, 11),
                M(5, "📦 **BuffSentinel 0.9.7** – neu", 50)]
        self.assertEqual(plan(msgs, protected={3, 4}), [1, 2])

    def test_fortsetzung_nur_20_sekunden(self):
        msgs = [M(1, "📦 **GuildSentinel 0.9.11** – alt", 0),
                M(2, "spätere Bot-Nachricht", 1),                                   # 60 s später: keine Fortsetzung
                M(3, "📦 **GuildSentinel 0.9.13** – neu", 5)]
        self.assertEqual(plan(msgs), [1])

    def test_geschuetzt_und_einzeln(self):
        msgs = [M(1, "📦 **ProfessionSentinel 0.9.12** – alt", 0), M(2, "📦 **ProfessionSentinel 0.9.13** – neu", 9)]
        self.assertEqual(plan(msgs, protected={1}), [])
        self.assertEqual(plan([M(1, "📦 **ProfessionSentinel 0.9.13** – einziger", 0)]), [])

    def test_mehrere_addons_im_kanal_getrennt(self):
        msgs = [M(1, "📦 **AH Analyzer Pro 0.60.1** – alt", 0),
                M(2, "📦 **AHSentinel 0.65.8** – neu", 10),
                M(3, "📦 **LevelPilot 3.12.5** – anderes Addon", 20)]
        self.assertEqual(plan(msgs), [1])

    def test_reihenfolge_egal(self):
        msgs = [M(4, "📦 **ThreatSentinel 2.4.5** – neu", 120), M(1, "📦 **ThreatSentinel 2.4.3** – alt", 0)]
        self.assertEqual(plan(msgs), [1])


if __name__ == "__main__":
    unittest.main()
