"""MN8 – Messauftrag Blizzard-Schnittstelle (ab Bot 1.5.129, nur lesen, ändert nichts).

Prüft, ob die Blizzard Game Data API für WoW Forever Auktionsdaten liefert:
  1. Zugangstoken holen (Client-Credentials, oauth.battle.net)
  2. je Namespace-Kandidat: connected-realm/index (Antwortcode, Anzahl Realms) und Realm-Namen
  3. für passende Realms: auctions/index (Auktionshäuser je Fraktion) und auctions/<haus> (Code, Grösse, Anzahl,
     Last-Modified)
Ausgabe: Bericht als Text (stdout) – OHNE Client-ID, Geheimnis oder Token. Für berichte/Discord/ geeignet.

Zugang (nie ins Repo, nie in Logs): in /opt/raidmaster/config.json die Felder "blizzard_client_id" und
"blizzard_client_secret" (eintragen mit RaidMasterBot/blizzard_zugang.sh) oder Umgebungsvariablen
BLIZZARD_CLIENT_ID / BLIZZARD_CLIENT_SECRET.

Aufruf auf dem Server:  sudo /opt/raidmaster/.venv/bin/python /opt/raidmaster/blizzard_api_check.py [--realm Name] [--region eu]
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

NAMESPACES = ("dynamic-classic1x", "dynamic-classic", "dynamic-classicann", "dynamic-classic-anniversary",
              "dynamic-forever", "dynamic-classicforever", "dynamic-classic-forever", "dynamic-classic1x-forever",
              "dynamic")
CFG = "/opt/raidmaster/config.json"
UA = "RaidMaster-MN8-Messung"


def credentials(cfg_path: str = CFG) -> tuple[str | None, str | None]:
    cid, sec = os.environ.get("BLIZZARD_CLIENT_ID"), os.environ.get("BLIZZARD_CLIENT_SECRET")
    if cid and sec:
        return cid, sec
    try:
        with open(cfg_path, encoding="utf-8") as f:
            cfg = json.load(f)
        return cfg.get("blizzard_client_id"), cfg.get("blizzard_client_secret")
    except (OSError, ValueError):
        return None, None


def redact(text: str, *secrets: str | None) -> str:
    """Geheimnisse nie ausgeben (auch nicht in Fehlermeldungen)."""
    for s in secrets:
        if s:
            text = text.replace(s, "***")
    return text


def http(url: str, headers: dict, data: bytes | None = None, timeout: int = 60) -> tuple[int, bytes, dict]:
    req = urllib.request.Request(url, data=data, headers=dict(headers, **{"User-Agent": UA}))
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.read(), dict(r.headers)
    except urllib.error.HTTPError as e:
        return e.code, e.read() or b"", dict(e.headers or {})
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        return 0, str(e).encode(), {}


def token(region: str, cid: str, sec: str) -> tuple[str | None, int]:
    auth = base64.b64encode(f"{cid}:{sec}".encode()).decode()
    code, body, _ = http(f"https://oauth.battle.net/token", {"Authorization": "Basic " + auth,
                                                              "Content-Type": "application/x-www-form-urlencoded"},
                         b"grant_type=client_credentials")
    if code != 200:
        return None, code
    try:
        return json.loads(body).get("access_token"), code
    except ValueError:
        return None, code


def api(region: str, tok: str, path: str, namespace: str) -> tuple[int, bytes, dict]:
    q = urllib.parse.urlencode({"namespace": f"{namespace}-{region}", "locale": "de_DE"})
    return http(f"https://{region}.api.blizzard.com{path}?{q}", {"Authorization": "Bearer " + tok})


def realm_names(region, tok, ns, href) -> list[str]:
    path = urllib.parse.urlparse(href).path
    code, body, _ = api(region, tok, path, ns)
    if code != 200:
        return []
    try:
        return [r.get("name") if isinstance(r.get("name"), str) else (r.get("name") or {}).get("de_DE", "?")
                for r in json.loads(body).get("realms", [])]
    except ValueError:
        return []


def list_realms(region: str, cid: str, sec: str, out, namespaces=NAMESPACES) -> dict:
    """Alle Realm-Namen je Namespace ausgeben (ab 1.5.130) – um zu sehen, wo WoW Forever auftaucht."""
    def say(line=""):
        print(redact(line, cid, sec), file=out)
    tok, code = token(region, cid, sec)
    say(f"Zugangstoken: Antwortcode {code}")
    found = {}
    if not tok:
        return found
    for ns in namespaces:
        code, body, _ = api(region, tok, "/data/wow/connected-realm/index", ns)
        if code != 200:
            continue
        try:
            items = json.loads(body).get("connected_realms", [])
        except ValueError:
            items = []
        names = []
        for it in items:
            href = it.get("href", "")
            cr = urllib.parse.urlparse(href).path.rstrip("/").split("/")[-1]
            for n in realm_names(region, tok, ns, href):
                names.append(f"{n} ({cr})")
                if n and "forever" in n.casefold():
                    found.setdefault(ns, []).append(cr)
        say(f"- {ns}-{region}: {len(items)} Gruppen: " + ", ".join(sorted(names)))
    say("")
    say("FOREVER gefunden in: " + (", ".join(f"{k} (Gruppen {v})" for k, v in found.items()) if found else "keinem Namespace"))
    return found


def measure(region: str, realm_filter: str | None, cid: str, sec: str, out, namespaces=NAMESPACES) -> int:
    def say(line=""):
        print(redact(line, cid, sec), file=out)

    say(f"MN8 – Blizzard Game Data API, Region {region}, Messung {time.strftime('%d.%m.%Y %H:%M')}")
    tok, code = token(region, cid, sec)
    say(f"Zugangstoken: Antwortcode {code} – {'OK' if tok else 'FEHLER (Client-ID/Geheimnis prüfen)'}")
    if not tok:
        return 2
    found_any = False
    for ns in namespaces:
        code, body, _ = api(region, tok, "/data/wow/connected-realm/index", ns)
        if code != 200:
            say(f"- {ns}-{region}: connected-realm/index -> {code}")
            continue
        try:
            items = json.loads(body).get("connected_realms", [])
        except ValueError:
            items = []
        say(f"- {ns}-{region}: connected-realm/index -> 200, {len(items)} Realm-Gruppen")
        for it in items[:60]:
            href = it.get("href", "")
            names = realm_names(region, tok, ns, href)
            if realm_filter and not any(realm_filter.casefold() in (n or "").casefold() for n in names):
                continue
            cr = urllib.parse.urlparse(href).path.rstrip("/").split("/")[-1]
            say(f"  · Gruppe {cr}: {', '.join(n for n in names if n)[:120]}")
            c2, b2, _ = api(region, tok, f"/data/wow/connected-realm/{cr}/auctions/index", ns)
            houses = []
            if c2 == 200:
                try:
                    houses = [(h.get("id"), h.get("name")) for h in json.loads(b2).get("auctions", [])]
                except ValueError:
                    pass
            say(f"    auctions/index -> {c2}" + (f", Häuser: {houses}" if houses else ""))
            for hid, hname in houses or [(None, None)]:
                path = f"/data/wow/connected-realm/{cr}/auctions" + (f"/{hid}" if hid is not None else "")
                t0 = time.time()
                c3, b3, h3 = api(region, tok, path, ns)
                n = None
                if c3 == 200:
                    try:
                        n = len(json.loads(b3).get("auctions", []))
                    except ValueError:
                        pass
                    found_any = True
                say(f"    {path.split('/auctions')[1] or '/'} ({hname or 'alle'}) -> {c3}, {len(b3) // 1024} KB, "
                    f"{n if n is not None else '-'} Auktionen, Last-Modified {h3.get('Last-Modified', '-')}, "
                    f"{time.time() - t0:.1f} s")
            if not realm_filter:
                break
    say("")
    say("ERGEBNIS: " + ("Auktionsdaten verfügbar (siehe oben) – Folgeauftrag möglich."
                        if found_any else "keine Auktionsdaten gefunden (nur Fehlercodes oder leere Antworten)."))
    return 0 if found_any else 1


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="MN8: Blizzard-Auktionsdaten für WoW Forever messen (nur lesen)")
    ap.add_argument("--region", default="eu")
    ap.add_argument("--realm", default=None, help="Teil des Realm-Namens, z. B. Forever-Realm der Gilde")
    ap.add_argument("--list", action="store_true", help="alle Realm-Namen je Namespace auflisten (wo ist Forever?)")
    args = ap.parse_args(argv)
    cid, sec = credentials()
    if not cid or not sec:
        print("Kein Blizzard-Zugang: zuerst mit blizzard_zugang.sh Client-ID und Geheimnis eintragen.")
        return 3
    if args.list:
        found = list_realms(args.region, cid, sec, sys.stdout)
        for ns, groups in found.items():                     # dort gleich die Auktionen messen
            measure(args.region, "forever", cid, sec, sys.stdout, namespaces=(ns,))
        return 0 if found else 1
    return measure(args.region, args.realm, cid, sec, sys.stdout)


if __name__ == "__main__":
    sys.exit(main())
