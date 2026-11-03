"""Offline-Test (Bot 1.5.100): zwei Updates gleichzeitig (/update und die automatische Prüfung) dürfen sich nicht
gegenseitig den Entpack-Ordner löschen. Früher: "[Errno 2] No such file or directory: …/update/tmp/…/download/…zip".
Start: python3 -I -m unittest discover -s RaidMasterBot/tests"""
import io
import os
import sys
import tempfile
import threading
import time
import unittest
import zipfile
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import updater  # noqa: E402


def repo_zip() -> bytes:
    """Wie die ZIP von GitHub: ein Oberordner, darin download/ mit Addon-ZIPs."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("owner-repo-abc123/RaidMaster/RaidMaster.toc", "## Version: 9.9.9\n")
        for i in range(3):
            z.writestr(f"owner-repo-abc123/download/Addon{i}-1.0.{i}.zip", b"PK" + b"x" * 100)
    return buf.getvalue()


def slow_check(mod, path):
    time.sleep(0.15)          # Prüfung dauert: genau dann kam früher das zweite Update dazwischen
    return []


class Gleichzeitig(unittest.TestCase):
    def test_zwei_updates_parallel(self):
        data = repo_zip()
        with tempfile.TemporaryDirectory() as base, \
                mock.patch.object(updater, "check_addon_zip", slow_check), \
                mock.patch.object(updater, "load_addon_check", lambda tmp, base: object()), \
                mock.patch.object(updater, "build_addon_zip", lambda addon_dir, base: None):
            errors = []

            def run():
                try:
                    updater.install_zip(data, base, "GitHub", "abc123")
                except Exception as e:  # noqa: BLE001
                    errors.append(e)

            threads = [threading.Thread(target=run) for _ in range(2)]
            for t in threads:
                t.start()
                time.sleep(0.05)
            for t in threads:
                t.join()
            self.assertEqual(errors, [])
            self.assertEqual(sorted(os.listdir(os.path.join(base, "addon"))),
                             ["Addon0-1.0.0.zip", "Addon1-1.0.1.zip", "Addon2-1.0.2.zip"])
            # keine Entpack-Ordner übrig
            self.assertEqual([d for d in os.listdir(updater.update_dir(base)) if d.startswith("tmp")], [])


if __name__ == "__main__":
    unittest.main()
