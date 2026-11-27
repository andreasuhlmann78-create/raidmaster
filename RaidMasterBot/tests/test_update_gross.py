"""T-DC-UPL1 (ab Bot 1.5.202): Das Repo ist ~900 MB gross (announce/*.zip). Bis 1.5.201 lud der Bot die ganze Repo-ZIP in den
Speicher und entpackte alles -> am 27.11. 1,7 GB (85 %) -> Server hing. Jetzt: Download auf die Platte, Berichte/Geschichte nicht
entpacken, schon vorhandene gleich grosse Anhänge in announce/ nur als Platzhalter (Name bleibt für die Liste, kein Kopieren,
kein Löschen)."""
import asyncio
import io
import os
import sys
import tempfile
import unittest
import zipfile
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import updater  # noqa: E402

TOP = "owner-repo-abc123/"


def repo_zip_file(path, big=b"PK" + b"z" * 5000):
    with zipfile.ZipFile(path, "w") as z:
        z.writestr(TOP + "RaidMaster/RaidMaster.toc", "## Version: 9.9.9\n")
        z.writestr(TOP + "testberichte/AHSentinel/bericht.txt", "x" * 1000)
        z.writestr(TOP + "berichte/Discord/b.txt", "y")
        z.writestr(TOP + "auftraege/Discord/offen-discord.txt", "z")
        z.writestr(TOP + "announce/ahs__ahs-0.65.1.md", "alt")
        z.writestr(TOP + "announce/ahs__ahs-0.65.1.AHSentinel.zip", big)      # liegt schon auf dem Server
        z.writestr(TOP + "announce/ahs__ahs-0.65.2.md", "neu")
        z.writestr(TOP + "announce/ahs__ahs-0.65.2.AHSentinel.zip", big)      # neu


class Entpacken(unittest.TestCase):
    def test_nur_noetiges_und_platzhalter(self):
        with tempfile.TemporaryDirectory() as d:
            base, tmp, zpath = os.path.join(d, "base"), os.path.join(d, "tmp"), os.path.join(d, "repo.zip")
            os.makedirs(os.path.join(base, "announce"))
            with open(os.path.join(base, "announce", "ahs__ahs-0.65.1.AHSentinel.zip"), "wb") as f:
                f.write(b"PK" + b"z" * 5000)
            repo_zip_file(zpath)
            with zipfile.ZipFile(zpath) as zf:
                ph = updater._safe_extract(zf, tmp, base)
            self.assertEqual(ph, {"ahs__ahs-0.65.1.AHSentinel.zip"})
            for top in ("testberichte", "berichte", "auftraege"):
                self.assertFalse(os.path.exists(os.path.join(tmp, TOP, top)), top)
            ann = os.path.join(tmp, TOP, "announce")
            self.assertEqual(os.path.getsize(os.path.join(ann, "ahs__ahs-0.65.1.AHSentinel.zip")), 0)      # Platzhalter
            self.assertEqual(os.path.getsize(os.path.join(ann, "ahs__ahs-0.65.2.AHSentinel.zip")), 5002)   # neu: ganz
            self.assertTrue(os.path.isfile(os.path.join(ann, "ahs__ahs-0.65.1.md")))                     # .md immer

    def test_gegenprobe_andere_groesse_wird_entpackt(self):
        with tempfile.TemporaryDirectory() as d:
            base, tmp, zpath = os.path.join(d, "base"), os.path.join(d, "tmp"), os.path.join(d, "repo.zip")
            os.makedirs(os.path.join(base, "announce"))
            with open(os.path.join(base, "announce", "ahs__ahs-0.65.1.AHSentinel.zip"), "wb") as f:
                f.write(b"anders")
            repo_zip_file(zpath)
            with zipfile.ZipFile(zpath) as zf:
                self.assertEqual(updater._safe_extract(zf, tmp, base), set())

    def test_install_aus_datei_kopiert_platzhalter_nicht_und_loescht_nichts(self):
        with tempfile.TemporaryDirectory() as d:
            base, zpath = os.path.join(d, "base"), os.path.join(d, "repo.zip")
            os.makedirs(os.path.join(base, "announce"))
            old = os.path.join(base, "announce", "ahs__ahs-0.65.1.AHSentinel.zip")
            with open(old, "wb") as f:
                f.write(b"PK" + b"z" * 5000)
            repo_zip_file(zpath)
            with mock.patch.object(updater, "load_addon_check", lambda tmp, base: None), \
                    mock.patch.object(updater, "build_addon_zip", lambda addon_dir, base: None):
                res = updater.install_zip(zpath, base, "GitHub", "abc123")      # Pfad statt Bytes
            self.assertEqual(os.path.getsize(old), 5002)                         # Platzhalter hat nichts überschrieben
            self.assertTrue(os.path.isfile(os.path.join(base, "announce", "ahs__ahs-0.65.2.AHSentinel.zip")))
            self.assertEqual(res["announce_removed"], [])                       # Name in der Liste -> nichts "gelöscht"
            self.assertFalse(os.listdir(os.path.join(base, "update")) and
                             any(n.startswith("tmp-") for n in os.listdir(os.path.join(base, "update"))))

    def test_bytes_gehen_weiter(self):
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as z:
            z.writestr(TOP + "RaidMaster/RaidMaster.toc", "## Version: 9.9.9\n")
        with tempfile.TemporaryDirectory() as base, \
                mock.patch.object(updater, "load_addon_check", lambda tmp, base: None), \
                mock.patch.object(updater, "build_addon_zip", lambda addon_dir, base: None):
            updater.install_zip(buf.getvalue(), base, "Upload", "")


class Download(unittest.TestCase):
    def test_in_stuecken_auf_die_platte(self):
        chunks = [b"a" * (1 << 20), b"b" * 10]

        class Content:
            async def iter_chunked(self, n):
                for c in chunks:
                    yield c

        class Resp:
            status = 200
            content = Content()

            async def __aenter__(self):
                return self

            async def __aexit__(self, *a):
                return False

        class Session:
            def get(self, url, headers=None):
                self.url = url
                return Resp()
        with tempfile.TemporaryDirectory() as base:
            s = Session()
            path = asyncio.run(updater.github_zip_to_file(s, "o/r", "abc", None, base))
            self.assertTrue(s.url.endswith("/repos/o/r/zipball/abc"))
            self.assertEqual(os.path.getsize(path), (1 << 20) + 10)
            Resp.status = 500
            with self.assertRaises(updater.UpdateError):
                asyncio.run(updater.github_zip_to_file(s, "o/r", "abc", None, base))
            self.assertEqual(sorted(os.listdir(updater.update_dir(base))), [os.path.basename(path)])   # keine Reste


if __name__ == "__main__":
    unittest.main()
