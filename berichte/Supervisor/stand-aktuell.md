# Stand Supervisor – 27.11.2026 13:20

## Gerade in Arbeit
- Warte auf: LP-DL1 (3.13.28 nach download/, freigegeben 13:15), AHS-API1 (Speicheranlage im Entzauber-Teil belegen), PS-P2/PS-SK1 (Merken, "Skill ?"),
  GS-CF3 (GuildSentinel 0.9.66 um 18:00 auf CurseForge; Nachprüfung als Erinnerung 18:20 gestellt).

## Nächste Schritte (Reihenfolge)
1. Bei jedem "repo": pull, Berichte prüfen, addon_check, annehmen/ablehnen, push + nachprüfen, Workflow "Addon-Prüfung" ansehen (E-Regel 27.11.!).
2. LP-DL1: download/LevelPilot-3.13.28.zip = announce-md5 3fcede98…, Workflow grün.
3. AHS-API1: Zeit ~ angelegter Speicher (25–30 µs/KB im Spiel); Auftrag: was legt 200–900 KB an, GC trennen, Ziel ≤ 2 ms/≤ 50 KB.
4. PS: PS-P2 (nil merken, Lauf 3 vergisst alles, Neuaufbau 18,8 ms), PS-SK1 HOCH (Lehrer-Lernstufen, kein "Skill ?"); 0.9.94 nach download/ erst nach Ingametest PS-P2.
5. 18:20: CF GS 0.9.66 prüfen + CF-Kommentare lesen (eingebauter Browser, Slugs ah-analyzer-pro / guildsentinel).
6. Offiziere: Uploader 2.3.30 (A: j; B: Handinstallation + Nachtrag daten_config.json, DM 08:18/08:20). stand.json "uploader" beobachten; danach BS-M1-b Messdaten Offizier A.

## Offen beim Nutzer
- PC (abends): einmal j für 2.3.30, dann Addons-Testversionen-an.bat + Neustart.
- Entscheid SH-M1 (A jetzt / B gebündelt, empfohlen B).
- 09.12. 07:00 Erinnerung: Aufgabe "Raids und Taktiken" wieder einschalten.

## Entscheide des Nutzers seit letztem Stand (alle in entscheide.md 27.11.)
- 08:27–09:23 Spieler-Texte (ST1, alle 7 angenommen 10:30). 08:44 Tooltips nie anfassen. 11:21 GS 0.9.66 um 18:00 auf CF, Marktdaten-Schalter bleibt.

## Wichtig zu wissen
- DL-ABN: download/ nur angenommene Versionen (Uploader installiert automatisch bei allen); addon_check erlaubt download/ < announce/ (WARNUNG).
- RM: Uploader-Versionen nur über Zweig pruefung/uploader-<V>, erst nach Annahme auf main.
- GS-REK1 erledigt (0.9.66): fremde Gilden-Einladungen werden nicht mehr beantwortet (unabhängig im Nachbau geprüft).
- LP T215–T217 erledigt (nur Testroutine: Jobs.sync am Stück). AHS 0.65.420 angenommen (Messversion). PS 0.9.93 in download/.
- Prüfwerkzeug Spieler-Texte: /home/claude/chatprobe.py (Mock, Chat beim Einloggen/Zeitgeber/Slash, Testmodus aus) – nicht im Repo.
