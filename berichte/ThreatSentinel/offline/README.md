# ThreatSentinel – Testroutine offline (TU9)

Dieselbe Testroutine wie `/ts testroutine` im Spiel, im nachgebauten Spiel der Addon-Prüfung (`addon-check/ladetest.py`).
Die Kämpfe sind simuliert: Lagen als Zeitreihe von Bedrohungswerten (Bereich U, TU1/TU2), 1000 Zufallsfälle mit festem
Startwert (TU4).

```
mkdir -p /tmp/ts && unzip -o -q download/ThreatSentinel-<Version>.zip -d /tmp/ts
python3 -I berichte/ThreatSentinel/offline/routine_offline.py /tmp/ts/ThreatSentinel Forever
python3 -I berichte/ThreatSentinel/offline/routine_offline.py /tmp/ts/ThreatSentinel Era
python3 -I berichte/ThreatSentinel/offline/routine_offline.py /tmp/ts/ThreatSentinel Forever u   # nur Bereich U
```

Ausgabe: der Bericht der Routine (mit den TU-Zeilen), am Ende
`Offline: FEHLER ausserhalb der Nachbildungs-Liste: n` (Rückgabewert 1, wenn n > 0).
Die Nachbildungs-Liste im Skript nennt die wenigen Fälle, die nur in der Nachbildung FEHLER sind, mit Grund.
Braucht Python 3 mit `lupa`.
