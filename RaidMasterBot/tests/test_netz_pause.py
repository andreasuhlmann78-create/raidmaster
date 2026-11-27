"""T-DC-UPL3 (ab Bot 1.5.203): Netz/DNS beim Anmelden -> Code 4, Starter wartet 45 s (nach 60 Versuchen 300 s), danach eine Zeile
in #bot-log "Discord X Min. nicht erreichbar". Andere Abstürze wie bisher."""
import os
import socket
import sys
import tempfile
import types
import unittest
from unittest import mock

HERE = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(HERE, ".."))
sys.path.insert(0, HERE)

import netz_pause as n  # noqa: E402


class ClientConnectorDNSError(OSError):
    pass


class Erkennen(unittest.TestCase):
    def test_netzfehler(self):
        self.assertTrue(n.is_net_error(socket.gaierror(-3, "Temporary failure in name resolution")))
        self.assertTrue(n.is_net_error(ClientConnectorDNSError("Cannot connect to host discord.com:443")))
        try:
            try:
                raise socket.gaierror(-3, "x")
            except socket.gaierror as e:
                raise RuntimeError("aussen") from e
        except RuntimeError as e:
            self.assertTrue(n.is_net_error(e))                       # Ursache in der Kette
        self.assertTrue(n.is_net_error(TimeoutError()))
        self.assertFalse(n.is_net_error(ValueError("Code-Fehler")))
        self.assertFalse(n.is_net_error(KeyError("x")))


class Merker(unittest.TestCase):
    def test_zaehlen_warten_melden(self):
        with tempfile.TemporaryDirectory() as base:
            self.assertIsNone(n.take_down(base))
            self.assertEqual(n.wait_seconds(base), 45)
            n.note_down(base, now=1000)
            for i in range(60):
                n.note_down(base, now=1000 + 45 * (i + 1))
            self.assertEqual(n.wait_seconds(base), 300)              # mehr als 60 Versuche -> nicht drängeln
            self.assertEqual(n.take_down(base, now=1000 + 30 * 60), (30, 61))
            self.assertIsNone(n.take_down(base))                     # nur einmal melden


class Starter(unittest.TestCase):
    def test_code_4_wartet_45_s_ohne_rueckbau(self):
        import launcher
        codes = iter([n.NET_CODE, n.NET_CODE, 0])
        sleeps = []
        with tempfile.TemporaryDirectory() as base, \
                mock.patch.object(launcher, "BASE", base), \
                mock.patch.object(launcher.subprocess, "run", lambda *a, **k: types.SimpleNamespace(returncode=next(codes))), \
                mock.patch.object(launcher.time, "sleep", sleeps.append), \
                mock.patch.object(launcher.updater, "rollback_pending", lambda *a: self.fail("kein Rückbau bei Netzfehler")):
            os.makedirs(launcher.updater.update_dir(base))
            with open(launcher.updater.pending_path(base), "w") as f:      # frisches Update: trotzdem kein Rückbau
                f.write("{}")
            self.assertEqual(launcher.main(), 0)
        self.assertEqual(sleeps, [45, 45])

    def test_bot_meldet_und_beendet_mit_code_4(self):
        with open(os.path.join(HERE, "..", "bot.py"), encoding="utf-8") as f:
            src = f.read()
        self.assertIn("sys.exit(netz_pause.NET_CODE)", src)
        self.assertIn("netz_pause.take_down(BASE)", src)
        self.assertIn("nicht erreichbar (Netz/DNS", src)


if __name__ == "__main__":
    unittest.main()
