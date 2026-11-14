#!/usr/bin/env python3
"""LevelPilot – Offline-Testroutine (TU9) im nachgebauten Spiel.

Start im raidmaster-Repo:
    python3 berichte/LevelPilot/offline/run_offline.py [announce/levelpilot__levelpilot-x.y.z.LevelPilot.zip] [--nur testroutine|regression]
Ohne ZIP: die neueste announce/levelpilot__levelpilot-*.LevelPilot.zip.
Rückgabewert 0 = kein FEHLER, 1 = mindestens ein FEHLER (oder ein Lauf ohne Ergebnis).

Lua 5.1: zuerst die Umgebungsvariable LUA51 (Pfad zu einem lua5.1-Programm), dann lua5.1/lua51 im PATH, sonst lupa
(pip install lupa; jeder Lauf in einem eigenen Prozess).

Teil 1 – Testroutine A–J (/lp testroutine im Nachbau, lua/test40.lua): WoW Forever deDE und enUS (Horde, Durotar L6),
         WoW Forever Allianz (Wald von Elwynn L10), Classic Era deDE, TBC Classic deDE.
Teil 2 – Regressionsläufe (lua/test*.lua): Szenarien seit 2.x, darunter test15 = Wegnetz-Prüfung (Höhlen, Tunnel,
         gelaufene Wege, Wegführung), dazu die Code-Prüfung der Meldungs-Weiche (ML1: keine Chat-, Bildschirm- oder
         Tonausgabe am Schalter "Meldungen" vorbei).
Nicht im Repo (laufen nur in der Arbeitsumgebung der LevelPilot-Sitzung): Läufe mit echten SavedVariables oder
Weltsimulation (test26, test28–test31) und die Entwickler-Erkennung (test34, test37) – sie enthalten Namen.
"""
import concurrent.futures as cf
import glob
import os
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
LUA_DIR = os.path.join(HERE, "lua")
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
TIMEOUT = 1500

# Testroutine A–J: (Name, Umgebung, Volk, Klasse, Fraktion)
ROUTINE = [
    ("Testroutine Forever deDE Horde", {"FOREVER": "1", "LVL": "6", "MAP": "1411", "PX": "43.3", "PY": "68.5", "BRAKE": "1"}, "Orc", "WARRIOR", "Horde"),
    ("Testroutine Forever enUS Horde", {"FOREVER": "1", "LOCALE": "enUS", "LVL": "6", "MAP": "1411", "PX": "43.3", "PY": "68.5", "BRAKE": "1"}, "Orc", "WARRIOR", "Horde"),
    ("Testroutine Forever deDE Allianz", {"FOREVER": "1", "LVL": "10", "MAP": "1429", "PX": "48", "PY": "42", "BRAKE": "1"}, "Human", "WARRIOR", "Alliance"),
    ("Testroutine Classic Era deDE", {"FLAVOR": "era", "LVL": "6", "MAP": "1411", "PX": "43.3", "PY": "68.5", "BRAKE": "1"}, "Orc", "WARRIOR", "Horde"),
    ("Testroutine TBC Classic deDE", {"FLAVOR": "tbc", "LVL": "6", "MAP": "1411", "PX": "43.3", "PY": "68.5", "BRAKE": "1"}, "Orc", "WARRIOR", "Horde"),
]

DUROTAR = {"FOREVER": "1", "LVL": "6", "MAP": "1411", "PX": "43.3", "PY": "68.5"}
# Regressionsläufe: (Skript, Umgebung, Volk, Klasse, Fraktion, ohne Datenpaket)
REGRESSION = [("test2", {}, "Orc", "WARRIOR", "Horde", True)]
REGRESSION += [(t, DUROTAR, "Orc", "WARRIOR", "Horde", False)
               for t in ("test3", "test7", "test9", "test10", "test12", "test16", "test19", "test20", "test21", "test25")]
REGRESSION += [
    ("test13", {"CJKFONTS": "1"}, "Orc", "WARRIOR", "Horde", False),
    ("test22", {"CJKFONTS": "1"}, "Orc", "WARRIOR", "Horde", False),
    ("test6", {}, "Human", "WARRIOR", "Alliance", False),
    ("test11", {"FOREVER": "1", "LVL": "3", "MAP": "1429", "PX": "48", "PY": "42"}, "Human", "WARRIOR", "Alliance", False),
    ("test8", {"FOREVER": "1", "LVL": "22", "MAP": "1436", "PX": "42", "PY": "70"}, "Human", "WARRIOR", "Alliance", False),
    ("test14", {"LVL": "1", "MAP": "1411", "PX": "43.3", "PY": "68.5"}, "Orc", "WARRIOR", "Horde", False),
    ("test15", {}, "Orc", "WARRIOR", "Horde", False),
    ("test17", DUROTAR, "Orc", "HUNTER", "Horde", False),
    ("test18", DUROTAR, "Orc", "WARRIOR", "Horde", False),
    ("test23", {"FOREVER": "1", "LVL": "12", "MAP": "1413", "PX": "51.5", "PY": "30.3"}, "Orc", "WARRIOR", "Horde", False),
    ("test24", {"FOREVER": "1", "LVL": "12", "MAP": "1413", "PX": "51.5", "PY": "30.3"}, "Orc", "WARRIOR", "Horde", False),
    ("test27", {"FOREVER": "1", "LVL": "5", "MAP": "1411", "PX": "43.3", "PY": "68.5"}, "Orc", "WARRIOR", "Horde", False),
    ("test32", {"FOREVER": "1", "LVL": "3", "MAP": "1411", "PX": "43.3", "PY": "68.5"}, "Orc", "HUNTER", "Horde", False),
    ("test33", DUROTAR, "Troll", "HUNTER", "Horde", False),
    ("test35", DUROTAR, "Troll", "HUNTER", "Horde", False),
    ("test36", {"FOREVER": "1", "LVL": "20", "MAP": "1413", "PX": "52", "PY": "30"}, "Troll", "HUNTER", "Horde", False),
    ("test38", DUROTAR, "Troll", "HUNTER", "Horde", False),
]


# 3.12.31 ML1: Meldungs-Weiche – keine Ausgabe am Schalter "Meldungen" vorbei (statische Prüfung des Codes)
DIRECT_OUT = re.compile(r"DEFAULT_CHAT_FRAME:AddMessage|UIErrorsFrame:AddMessage|RaidNotice_AddMessage|(?<![\w.])PlaySound\b|(?<![\w.:])print\s*\(")
SKIP_FILES = re.compile(r"^(GoldSentinel.*|TestRoutine|Locale_.*)\.lua$")


def check_message_gate(root):
    """Liefert (ok, text, befunde): direkte Ausgaben nur in LP.sink (Core.lua), LP.out nur in Core.lua/UI.lua."""
    found = []
    for fn in sorted(os.listdir(root)):
        if not fn.endswith(".lua") or SKIP_FILES.match(fn):
            continue
        lines = open(os.path.join(root, fn), encoding="utf-8", errors="replace").read().split("\n")
        in_sink = False
        for i, line in enumerate(lines, 1):
            code = line.split("--", 1)[0]
            if fn == "Core.lua" and code.strip().startswith("LP.sink = {"):
                in_sink = True
            if DIRECT_OUT.search(code) and not in_sink:
                found.append("%s:%d %s" % (fn, i, line.strip()[:120]))
            if "LP.out." in code and fn not in ("Core.lua", "UI.lua"):
                found.append("%s:%d LP.out direkt: %s" % (fn, i, line.strip()[:100]))
            if in_sink and code.strip() == "}":
                in_sink = False
    ok = not found
    return ok, ("== ALLE TESTS OK" if ok else "== %d FEHLER" % len(found)), found


def version_key(p):
    return [int(x) for x in re.findall(r"\d+", os.path.basename(p))]


def lua_command():
    exe = os.environ.get("LUA51")
    if exe and os.path.exists(exe):
        return [exe]
    for name in ("lua5.1", "lua51"):
        found = shutil.which(name)
        if found:
            return [found]
    try:
        import lupa.lua51  # noqa: F401
    except ImportError:
        try:
            import lupa  # noqa: F401
        except ImportError:
            return None
    return [sys.executable, os.path.abspath(__file__), "--lupa"]


def lupa_main(argv):
    """Ein Lua-Skript mit lupa ausführen (eigener Prozess): argv = [skript, arg1, ...]."""
    try:
        import lupa.lua51 as lupa
    except ImportError:
        import lupa
    rt = lupa.LuaRuntime(unpack_returned_tuples=True)
    rt.globals().arg = rt.table_from({i: a for i, a in enumerate(argv)})
    rt.execute('io.stdout:setvbuf("line")')
    rt.globals().dofile(argv[0])
    sys.stdout.flush()


def run_one(cmd, root, pack, job):
    name, env_add, race, cls, fac, nopack, script = job
    env = dict(os.environ)
    for k in ("FOREVER", "FLAVOR", "LOCALE", "CJKFONTS", "BRAKE", "ASYNC", "SVACC", "SVCHAR", "WORLDHOOK", "SIMDIR"):
        env.pop(k, None)
    env.update(env_add)
    env["PACKDIR"] = "" if nopack else pack
    args = cmd + [os.path.join(LUA_DIR, script + ".lua"), root, "0", race, cls, fac]
    try:
        p = subprocess.run(args, cwd=LUA_DIR, env=env, capture_output=True, text=True, timeout=TIMEOUT)
        out = (p.stdout or "") + (p.stderr or "")
    except subprocess.TimeoutExpired:
        return name, False, "Zeitüberschreitung (%d s)" % TIMEOUT, []
    lines = out.splitlines()
    verdict = [l for l in lines if re.match(r"^== (ALLE|\d+ FEHLER)", l)]
    last = verdict[-1] if verdict else ""
    ok = last.startswith("== ALLE")
    fails = [l.strip() for l in lines if "[FEHLER]" in l or l.startswith("FAIL") or "FEHLER:" in l][:12]
    summary = next((l for l in lines if re.match(r"^OK \d+ · FEHLER", l)), "")
    if not last:
        tail = [l for l in lines if l.strip()][-6:]
        return name, False, "kein Ergebnis", tail
    return name, ok, (summary + " " if summary else "") + last, fails


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--lupa":
        lupa_main(sys.argv[2:])
        return
    args = sys.argv[1:]
    only = None
    if "--nur" in args:
        i = args.index("--nur")
        only = args[i + 1] if i + 1 < len(args) else None
        del args[i:i + 2]
    zips = [a for a in args if a.endswith(".zip")]
    if zips:
        zp = zips[0]
    else:
        found = glob.glob(os.path.join(REPO, "announce", "levelpilot__levelpilot-*.LevelPilot.zip"))
        if not found:
            print("Keine announce/levelpilot__levelpilot-*.LevelPilot.zip gefunden")
            sys.exit(1)
        zp = max(found, key=version_key)
    cmd = lua_command()
    if not cmd:
        print("FEHLER: kein Lua 5.1 gefunden (LUA51=…, lua5.1 im PATH oder pip install lupa)")
        sys.exit(1)
    tmp = tempfile.mkdtemp(prefix="lp_offline_")
    try:
        zipfile.ZipFile(zp).extractall(tmp)
        root, pack = os.path.join(tmp, "LevelPilot"), os.path.join(tmp, "LevelPilot_Data")
        if not os.path.isfile(os.path.join(root, "LevelPilot.toc")):
            print("FEHLER: LevelPilot/LevelPilot.toc fehlt in " + zp)
            sys.exit(1)
        print("LevelPilot Offline-Routine · " + os.path.basename(zp) + " · Lua: " + " ".join(cmd[:1]))
        jobs = []
        if only in (None, "testroutine"):
            jobs += [(n, e, r, c, f, False, "test40") for (n, e, r, c, f) in ROUTINE]
        if only in (None, "regression"):
            jobs += [(t + (" (Wegnetz)" if t == "test15" else ""), e, r, c, f, np, t) for (t, e, r, c, f, np) in REGRESSION]
        results = []
        if only in (None, "regression"):
            ok, text, found = check_message_gate(root)
            results.append(("Meldungs-Weiche (ML1, Code-Prüfung)", ok, text, found))
        with cf.ThreadPoolExecutor(max_workers=max(1, min(8, os.cpu_count() or 2))) as ex:
            futs = [ex.submit(run_one, cmd, root, pack, j) for j in jobs]
            for fu in futs:
                results.append(fu.result())
        bad = 0
        for name, ok, text, fails in results:
            print(("OK      " if ok else "FEHLER  ") + name + ": " + text)
            if not ok:
                bad += 1
                for l in fails:
                    print("        " + l[:300])
        print("")
        print("ERGEBNIS: %d Läufe, %d ohne FEHLER, %d mit FEHLER" % (len(results), len(results) - bad, bad))
        sys.exit(0 if bad == 0 else 1)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
