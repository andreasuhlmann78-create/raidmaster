#!/usr/bin/env python3
"""BuffSentinel – Offline-Testroutine (TU9) mit lupa (Lua 5.1, sonst eingebautes Lua), alle Versionen und Sprachen.
Start im raidmaster-Repo:  python3 berichte/BuffSentinel/offline/run_offline.py [download/BuffSentinel-x.y.z.zip]
Ohne ZIP: die neueste download/BuffSentinel-*.zip."""
import glob, os, re, sys, tempfile, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
ROOT = None


def runtime():
    try:
        import lupa.lua51 as lua
    except ImportError:
        import lupa as lua
    return lua.LuaRuntime(unpack_returned_tuples=True)


def run(flavor, locale):
    os.environ["BS_FLAVOR"], os.environ["BS_LOCALE"], os.environ["BS_ROOT"] = flavor, locale, ROOT + "/"
    os.environ["BS_TESTS"] = HERE
    rt = runtime()
    out = []
    rt.globals().print = lambda *a: out.append("\t".join(str(x) for x in a))
    rt.execute('arg = nil; os.exit = function() end')
    with open(os.path.join(HERE, "run_offline.lua"), encoding="utf-8") as f:
        rt.execute(f.read())
    print("\n".join(out))
    return any(line == "RESULT PASS" for line in out)


def version_key(p):
    return [int(x) for x in re.findall(r"\d+", os.path.basename(p))]


def main():
    global ROOT
    args = sys.argv[1:]
    zips = [a for a in args if a.endswith(".zip")]
    rest = [a for a in args if not a.endswith(".zip")]
    zp = zips[0] if zips else max(glob.glob(os.path.join(REPO, "download", "BuffSentinel-*.zip")), key=version_key)
    tmp = tempfile.mkdtemp()
    zipfile.ZipFile(zp).extractall(tmp)
    ROOT = os.path.join(tmp, "BuffSentinel")
    combos = [(rest[0], rest[1] if len(rest) > 1 else "deDE")] if rest else \
        [(fl, lo) for fl in ("forever", "era", "tbc") for lo in ("deDE", "enUS")]
    ok = all([run(fl, lo) for fl, lo in combos])
    print("ALLE KOMBINATIONEN: PASS" if ok else "ALLE KOMBINATIONEN: FAIL")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
