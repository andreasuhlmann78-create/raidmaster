# Stand AHSentinel (Projekt-Sitzung)

## Stand 27.11.2026 23:42 · Version 0.65.427 (Discord); CurseForge 0.65.423 (Hotfix); 0.65.425 vom Supervisor angenommen (Code)
Repos: ahanalyzerpro (Code, schreiben; tests/ dort direkt pflegen), raidmaster (announce/, berichte/AHSentinel/), goldsentinel-daten (nur
 lesen; Zweig sicherung: aktuell/AUSPLUSLAPTOP/forever/konto-*/AHSentinel.lua.gz; Nachlieferung Rechner B: Zweig nachlieferung-rechner-b-2026-11-27).
Arbeitskopie /home/claude/AHSentinel. Veröffentlichen: /tmp/claude-0/bin/pub.sh <neu> <alt> "<Text>" "<Berichtsdatei>" (nur Discord;
 erwartet in /tmp/claude-0/rel/: AHSentinel-<V>.zip, notes.md, bericht.txt, stand.md). ZIP = gleiche 112 Dateien wie Vorversion (listN.txt).
Nachbau: cd /home/claude/ahanalyzerpro && bash tests/run_offline.sh /home/claude/AHSentinel; FULL=1 nur auf Kopie und ALLEIN (vorher pgrep run_all.sh leer).
 FULL 0.65.427: 357/67, keine neue Rot-Stelle (s326 behoben, AHS-S326). zz_bp1 = Leistung BindOnPickup (TR_TEXT=1 nötig für Ausgaben). Echte Daten im Sim: immer HORDE=1 (sonst leerer Markt), bekannte Items (Sim:AddItem).
 Eigene Szenarien /tmp/claude-0/sim2/wowsim/scenarios_new.lua (zz_api4 KALT/KEEPM/KEEPMC, zz_api5 OUT=<Datei> Wertvergleich, zz_api6 KB je Funktion).

## Gerade in Arbeit
- MASTERPLAN v2 Schritt 2: 2.1 im Nachbau erreicht (0.65.427 kalt 26–45 KB, Korrekturbericht: alte zz_api4-Werte enthielten ~21 KB Messhülle). Weiter 2.2.

## Nächste Schritte (Reihenfolge)
2. KB-Messung "Lohnt bis": zz_api4 immer mit NOTB=1 (sonst +21 KB Messhülle); je Funktion SINGLE=Mod:Fn (A:Fn für A).
3. Schritt 2.2 Vollscan: AHS-I4, VS-121b, AHS-SP1 (d). 2.4 Rest: AHS-S216, AHS-W2E-b, AHS-MK1, AHS-UMG1.
4. Danach R1–R7 (Reiter aktualisieren sich selbst), dann Abnahme-Prüfliste für den Nutzer (berichte/AHSentinel/<Zeit>-pruefliste-abnahme.txt).
5. Schritt 3: Daten Nachlieferung Rechner B im Sim nutzen, Vorschlag-Bericht (kein Bau ohne Freigabe).
6. Regel CF 18:00 / DL-ABN: download/ nur angenommene Version UND Bestätigung des Nutzers im Chat (AskUserQuestion).

## Offen beim Nutzer
- Ingametest AHS-BP1: Blendungspulver/Gift Tooltip "Wird beim Aufheben gebunden"? Markt-Reiter "liegen lassen – Beim Aufheben gebunden".
- Ingametest AHS-API1 (0.65.418+): Zeile API-LANGSAM. W1: Zeile UI-PREBUILD. ST1: Einloggen ohne Testmodus = 1 Zeile.

## Entscheide des Nutzers seit letztem Stand
- keine neuen (21:21 Masterplan v2 frei, 21:00 0.65.423 Hotfix auf CurseForge).

## Wichtig zu wissen
- A:BindOnPickup(id): bindType 1/4 = gebunden, 30 Min. Zwischenspeicher (Zahl, negativ = gebunden), keine Server-Anfrage für ungecachte Items.
- A:PrintError(where, text, reported): ohne Testmodus 1 Zeile je Sitzung; A:PrintOnce(key, msg).
- Laptop-Daten haben db.entwickler = true -> alte volle Einlog-Zeile. Ohne: /tmp/claude-0/tb1/laptop_nodev.lua.
- Letzter Test T1043 (BP1); T1042 CAN1, T1041/T1040 API1. Neue Tests vor "Chk(\"T496\"" einfügen; Index-Eintrag nach AHS-SN-CAN1.
- Nie Blizzard-Globale in Tests ersetzen (Taint) – Nähte A.apiOverride/A:Global, Ch.GameMoney, BK.GameMoney.
- Nie etwas in announce/ löschen. Jede Version: CHANGELOG.de.md-Abschnitt Pflicht (AHS-R1). Neues string.format -> s341 mitlaufen.
