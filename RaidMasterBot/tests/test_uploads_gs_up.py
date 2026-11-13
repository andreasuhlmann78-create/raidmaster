"""T-D-GS1 und T-D-UP1 (Bot 1.5.128).
T-D-GS1: GuildSentinel.lua nur mit Raidfähigkeit wird angenommen (Bank-Stand bleibt), weder noch -> abgewiesen.
T-D-UP1: Versionsvergleich der verteilten Uploader-ZIP, Warnung bei älterer Fassung.
Start: python3 -I -m unittest discover -s RaidMasterBot/tests"""
import gzip
import io
import os
import sys
import unittest
import zipfile

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
import raid_ready  # noqa: E402
import raidmaster_data as rmd  # noqa: E402
import uploader_version as uv  # noqa: E402

READY = ('GuildSentinelDB = {\n["raidReady"] = {\n["raid"] = "ony",\n["phase"] = "build",\n["aktiv"] = 23,\n'
         '["groesse"] = 40,\n["t"] = 1794470000,\n},\n}\n')
NOTHING = 'GuildSentinelDB = {\n["sonst"] = 1,\n}\n'


class GuildSentinelUpload(unittest.TestCase):
    def test_T_D_GS1_nur_raidfaehigkeit_angenommen(self):
        text, db = rmd.check_guildsentinel_upload(READY.encode(), "GuildSentinel.lua")
        self.assertIsNone(rmd.guild_bank(db))                          # -> getrennte Datei, Bank-Stand bleibt
        rr = raid_ready.parse(db)
        self.assertIn("Phase Aufbau", raid_ready.weekly_text(rr))

    def test_gepackt(self):
        _, db = rmd.check_guildsentinel_upload(gzip.compress(READY.encode()), "GuildSentinel.lua.gz")
        self.assertEqual(raid_ready.parse(db)["aktiv"], 23)

    def test_weder_noch_abgewiesen(self):
        with self.assertRaises(ValueError):
            rmd.check_guildsentinel_upload(NOTHING.encode(), "GuildSentinel.lua")

    def test_neuester_stand(self):
        a, b = {"aktiv": 1, "groesse": 40, "t": 10}, {"aktiv": 2, "groesse": 40, "t": 20}
        self.assertIs(raid_ready.newest([a, None, b]), b)
        self.assertIsNone(raid_ready.newest([None, None]))

    def test_bot_bank_nur_mit_bank(self):
        with open(os.path.join(HERE, "bot.py"), encoding="utf-8") as f:
            src = f.read()
        self.assertIn("gs_path = GS_UPLOAD_PATH if gs_has_bank else GS_READY_PATH", src)
        block = src[src.index("if not att and gs_att is not None:"):][:300]
        self.assertLess(block.index("if gs_has_bank:"), block.index("post_guild_bank()"))


def zip_with(version):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("RaidMasterUploader/uploader.py", f'# Uploader\nVERSION = "{version}"\n')
        zf.writestr("RaidMasterUploader/uploader.bat", "@echo off\n")
    return buf.getvalue()


class UploaderVersion(unittest.TestCase):
    def test_T_D_UP1_vergleich(self):
        self.assertEqual(uv.zip_version(zip_with("2.3.2")), "2.3.2")
        self.assertTrue(uv.is_older("2.3.2", "2.3.5"))
        self.assertTrue(uv.is_older("2.3.9", "2.3.10"))           # Zahlen, nicht Text
        self.assertFalse(uv.is_older("2.3.5", "2.3.5"))
        self.assertFalse(uv.is_older("2.4.0", "2.3.5"))
        self.assertTrue(uv.is_older(None, "2.3.5"))
        self.assertFalse(uv.is_older("2.3.5", None))              # Repo nicht erreichbar: keine Warnung

    def test_hinweis(self):
        self.assertIn("⚠️", uv.note("2.3.2", "2.3.5"))
        self.assertIn("2.3.5", uv.note("2.3.2", "2.3.5"))
        self.assertEqual(uv.note("2.3.5", "2.3.5"), "Uploader-Version **2.3.5**.")

    def test_kaputte_zip_und_repo_datei(self):
        self.assertIsNone(uv.zip_version(b"keine zip"))
        self.assertEqual(uv.parse_version('x = 1\nVERSION = "2.3.5"\n'), "2.3.5")
        repo_zip = os.path.join(os.path.dirname(HERE), "download", "RaidMasterUploader.zip")
        repo_py = os.path.join(os.path.dirname(HERE), "RaidMasterUploader", "uploader.py")
        if os.path.isfile(repo_zip) and os.path.isfile(repo_py):          # ZIP im Repo passt zur Quelle
            with open(repo_py, encoding="utf-8") as f:
                self.assertEqual(uv.file_version(repo_zip), uv.parse_version(f.read()))

    def test_bot_nennt_version(self):
        with open(os.path.join(HERE, "bot.py"), encoding="utf-8") as f:
            src = f.read()
        body = src[src.index("async def uploader_cmd("):]
        self.assertGreaterEqual(body[:6000].count("ensure_fresh_uploader()"), 2)
        self.assertIn("uploader_version.note(have, want)", body[:6000])


if __name__ == "__main__":
    unittest.main()
