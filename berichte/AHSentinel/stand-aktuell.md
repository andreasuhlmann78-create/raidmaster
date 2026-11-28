# Stand AHSentinel (Projekt-Sitzung)

## Stand 28.11.2026 12:16 · Version 0.65.439 (Discord); 0.65.437 angenommen (Code); CurseForge 0.65.423
Repos: ahanalyzerpro (Code, schreiben; tests/ dort direkt pflegen), raidmaster (announce/, berichte/AHSentinel/), goldsentinel-daten (nur
 lesen; Zweig sicherung: aktuell/<RECHNER>/forever/konto-*/AHSentinel.lua.gz; PC = DESKTOP-NVITMSE; Nachlieferung Rechner B: eigener Zweig).
Arbeitskopie /home/claude/AHSentinel. Veröffentlichen: /tmp/claude-0/bin/pub.sh <neu> <alt> "<Text>" "<Berichtsdatei>" (nur Discord;
 erwartet in /tmp/claude-0/rel/: AHSentinel-<V>.zip, notes.md, bericht.txt, stand.md – stand.md VORHER aus dem Repo übernehmen!).
Nachbau: FULL=1 nur auf Kopie und ALLEIN (pgrep run_all.sh leer). FULL 0.65.436: 361/67, keine neue Rot-Stelle (fail436.txt). Eigene Prüfliste: bei Act:Business-Änderungen s54/s55 mitlaufen.
 Echte Daten im Sim: HORDE=1, Ausgaben eigener Szenarien nur mit TR_TEXT=1. KB-Messung "Lohnt bis": zz_api4 NOTB=1 (sonst +21 KB Messhülle),
 je Funktion SINGLE=Mod:Fn. PC-Daten entpackt: /tmp/claude-0/tb1/pc_cur.lua (27.11. 23:17).

## Gerade in Arbeit
- 0.65.439 = AHS-TT-DE2 (Berufsfenster: Herstellkosten statt AH-Kaufpreis, TT:InCraftWindow/TT:CraftCost, Titel, Hintergrund) +
  AHS-LB-AH1 (Preissprung -> Wiederverkauf höchstens Median in A:ResalePrice; ohne Leiter Grund als 6. Wert von API.WorthUpTo).
  Tests T1050/T1051. Messszenario zz_lb1 in /tmp/claude-0/sim2 (SVIN=pc_1156.lua). FULL 0.65.439 allein (sim_full439.txt).
- 0.65.438 (SN-UX1 3/4, SN-ROT1, SN-BUD1) beim Supervisor; FULL 438: 364/67, keine neue Rot-Stelle (fail438.txt).

## Nächste Schritte (Reihenfolge = Masterplan Supervisor 28.11. 10:20, verbindlich)
1. FULL 0.65.439 gegen fail438.txt. Danach Schritt 2 Rest (T459, SN-LAG2, SP1 d), dann 2b-Rest (DE-MSG1 u. a.).
2. Schritt 2 Rest: T459 Nachlauf-Speicher + AHS-SN-LAG2 (SEARCH_RESULTS 16–35 ms, Tabellen wiederverwenden) + AHS-SP1 (d).
3. Schritt 2b Rest in Masterplan-Reihenfolge: MR4-T (ma4log leer; Verdacht ReqLevel ohne Item-Cache), SP-MENGE, TT-WEG, MW-AUSR, BH-QUOTE,
   BH-LEER, DE-WID1, MKT-WID2, PROF-SP1 (+ CHAT-PROFIT Zahl 14/22), VEN-GW1 (8 Fälle), SN-LB1, Einkauf-Zeilen beschriften, Eigenbedarf-Buchung,
   Lager-Anteil "de".
4. R1–R7, dann Abnahme-Prüfliste, dann 0.66.0. Neue Befunde nur vor den Plan, wenn HOCH (Gold, Absturz, Ruckeln > 40 ms, Kauf falsch).
5. Regel CF 18:00 / DL-ABN: download/ nur angenommene Version UND Bestätigung des Nutzers im Chat (AskUserQuestion).

## Offen beim Nutzer
- Ingametest: API-LANGSAM-Zeilen (≤ 2 ms, ≤ 50 KB), Blendungspulver/Gift-Tooltip + "ruht · gebunden", Einkauf > Seltenheit (ganz sichtbar,
  Klick daneben schliesst, Restzeit gefüllt), Protokollzeile UI-DD1.
- CurseForge-Antwort AHS-CF-1 (EN, Bericht 09:07) wartet auf OK des Nutzers – nicht selbst posten.

## Entscheide des Nutzers seit letztem Stand
- 28.11. ~12:05: Preissprung (> 150 % Median, < 24 Std.) -> Wiederverkauf höchstens Median. Ohne Angebotsliste: Regel F1 bleibt, Grund anzeigen.
- 28.11. 11:39 (über Supervisor): unrealistische Zahl in einer Anzeige = HOCH.
- 28.11. ~11:20/11:45: Sniper-Suchtakt: neuer Treffer 3 s Halt, Wiederholung desselben Treffers 1,5 s (2. Frage mit Messreihe; 1. Wahl "Halt nur 1×" ohne Risiko-Angabe gefragt).
- 28.11. 10:36: Sniper mit 2 Zielen mit Treffer: weiter alle 3 s wechseln (SN-Z4 bleibt, nicht stehen lassen).
- 28.11. 04:55: Anzeige-Befunde = Schritt 2b (nach 2, vor R1–R7), keiner darf verloren gehen, jeder mit Test + Abnahme-Bild.
- 28.11. 05:03: Eine Raste kauft ALLE Angebote des Treffers (Massenkauf) – gewollt, nicht ändern.

## Wichtig zu wissen
- Sn:ForgetTarget(key) räumt beim Löschen alles des Ziels. Sn:SetTarget 5. Wert f.zweck/f.quelle. A:VendorDealsChatText(n).
- A:BindOnPickup(id): 30 Min. Zwischenspeicher (Zahl, negativ = gebunden). VS:Ladder savedLad je Text (max 400).
- Sniper-Anzeige: UI_Sniper self.shownR = rechts gezeigtes Ergebnis; Sn.printedAt[Ziel|Angebot]. Letzte Tests T1043–T1049; neue Tests vor "Chk(\"T1043\"" o. ä. einfügen; Index-Einträge vor "AHS-BP1".
- Nie Blizzard-Globale in Tests ersetzen (Taint). Nie etwas in announce/ löschen. CHANGELOG.de.md je Version Pflicht.
