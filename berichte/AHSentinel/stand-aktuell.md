# Stand AHSentinel (Projekt-Sitzung)

## Stand 28.11.2026 06:00 · Version 0.65.430 (Discord); CurseForge 0.65.423; 0.65.429 vom Supervisor angenommen (Code)
Repos: ahanalyzerpro (Code, schreiben; tests/ dort direkt pflegen), raidmaster (announce/, berichte/AHSentinel/), goldsentinel-daten (nur
 lesen; Zweig sicherung: aktuell/<RECHNER>/forever/konto-*/AHSentinel.lua.gz; PC = DESKTOP-NVITMSE; Nachlieferung Rechner B: eigener Zweig).
Arbeitskopie /home/claude/AHSentinel. Veröffentlichen: /tmp/claude-0/bin/pub.sh <neu> <alt> "<Text>" "<Berichtsdatei>" (nur Discord;
 erwartet in /tmp/claude-0/rel/: AHSentinel-<V>.zip, notes.md, bericht.txt, stand.md – stand.md VORHER aus dem Repo übernehmen!).
Nachbau: FULL=1 nur auf Kopie und ALLEIN (pgrep run_all.sh leer). FULL 0.65.429: 357/67, keine neue Rot-Stelle (fail429.txt).
 Echte Daten im Sim: HORDE=1, Ausgaben eigener Szenarien nur mit TR_TEXT=1. KB-Messung "Lohnt bis": zz_api4 NOTB=1 (sonst +21 KB Messhülle),
 je Funktion SINGLE=Mod:Fn. PC-Daten entpackt: /tmp/claude-0/tb1/pc_cur.lua (27.11. 23:17).

## Gerade in Arbeit
- 0.65.430 = AHS-SN-FIND1 HOCH (Namenssuche-Rückfall bei Schlüssel mit Itemstufe + alle Varianten-Schlüssel, s346). Danach AHS-BH-REN2 HOCH.

## Nächste Schritte (Reihenfolge, Entscheid 04:55)
1. FULL 0.65.430 allein (gegen fail429.txt). Dann AHS-BH-REN2 HOCH (Rendite-Reiter Entzaubern Einsatz 0) + BH-REN.
2. Schritt 2.2: I4 erreicht, VS-121b geschlossen (Supervisor 05:50). Rest: T459 Nachlauf-Speicher (89 976 KB) je Schritt, dann AHS-SP1 (d).
3. Rest Schritt 2b: AHS-MR4-T zuerst (ma4log der PC-Daten LEER = nie ein Band belegt; Verdacht: W:LevelBands rechnet nach dem Login mit
   W:ReqLevel ohne Item-Cache -> zu wenige Items, Ergebnis gilt den ganzen Tag (W.ma4.day); im Sim mit PC-Daten messen), Gebote leer
   (Restzeit bei Ausrüstung nur Stufe), AHS-SP-MENGE, AHS-TT-WEG (3 Fälle), AHS-MW-AUSR, AHS-BH-REN, Einsatz neben "Gewinn gesamt", AHS-SN-LB1.
4. Danach R1–R7, dann Abnahme-Prüfliste (berichte/AHSentinel/<Zeit>-pruefliste-abnahme.txt), dann Schritt 3 (Daten Rechner B).
5. Regel CF 18:00 / DL-ABN: download/ nur angenommene Version UND Bestätigung des Nutzers im Chat (AskUserQuestion).

## Offen beim Nutzer
- Ingametest: API-LANGSAM-Zeilen (≤ 2 ms, ≤ 50 KB), Blendungspulver/Gift-Tooltip + "ruht · gebunden", Einkauf > Seltenheit (ganz sichtbar,
  Klick daneben schliesst, Restzeit gefüllt), Protokollzeile UI-DD1.
- PS muss f.zweck = "eigenbedarf" senden (über Supervisor an PS).

## Entscheide des Nutzers seit letztem Stand
- 28.11. 04:55: Anzeige-Befunde = Schritt 2b (nach 2, vor R1–R7), keiner darf verloren gehen, jeder mit Test + Abnahme-Bild.
- 28.11. 05:03: Eine Raste kauft ALLE Angebote des Treffers (Massenkauf) – gewollt, nicht ändern.

## Wichtig zu wissen
- Sn:ForgetTarget(key) räumt beim Löschen alles des Ziels. Sn:SetTarget 5. Wert f.zweck/f.quelle. A:VendorDealsChatText(n).
- A:BindOnPickup(id): 30 Min. Zwischenspeicher (Zahl, negativ = gebunden). VS:Ladder savedLad je Text (max 400).
- Letzte Tests T1044–T1047; neue Tests vor "Chk(\"T1043\"" o. ä. einfügen; Index-Einträge vor "AHS-BP1".
- Nie Blizzard-Globale in Tests ersetzen (Taint). Nie etwas in announce/ löschen. CHANGELOG.de.md je Version Pflicht.
