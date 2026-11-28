# Stand AHSentinel (Projekt-Sitzung)

## Stand 28.11.2026 11:23 · Version 0.65.437 (Discord, angenommen Code); 0.65.438 in Arbeit (nicht veröffentlicht); CurseForge 0.65.423
Repos: ahanalyzerpro (Code, schreiben; tests/ dort direkt pflegen), raidmaster (announce/, berichte/AHSentinel/), goldsentinel-daten (nur
 lesen; Zweig sicherung: aktuell/<RECHNER>/forever/konto-*/AHSentinel.lua.gz; PC = DESKTOP-NVITMSE; Nachlieferung Rechner B: eigener Zweig).
Arbeitskopie /home/claude/AHSentinel. Veröffentlichen: /tmp/claude-0/bin/pub.sh <neu> <alt> "<Text>" "<Berichtsdatei>" (nur Discord;
 erwartet in /tmp/claude-0/rel/: AHSentinel-<V>.zip, notes.md, bericht.txt, stand.md – stand.md VORHER aus dem Repo übernehmen!).
Nachbau: FULL=1 nur auf Kopie und ALLEIN (pgrep run_all.sh leer). FULL 0.65.436: 361/67, keine neue Rot-Stelle (fail436.txt). Eigene Prüfliste: bei Act:Business-Änderungen s54/s55 mitlaufen.
 Echte Daten im Sim: HORDE=1, Ausgaben eigener Szenarien nur mit TR_TEXT=1. KB-Messung "Lohnt bis": zz_api4 NOTB=1 (sonst +21 KB Messhülle),
 je Funktion SINGLE=Mod:Fn. PC-Daten entpackt: /tmp/claude-0/tb1/pc_cur.lua (27.11. 23:17).

## Gerade in Arbeit
- 0.65.438 (Arbeitskopie, NICHT veröffentlicht, Version noch 0.65.437 im Code): AHS-SN-UX1 (3)(4) + AHS-SN-ROT1. Schon gebaut:
  (3) Sn:Alert: Chat "Treffer:" EINMAL je Ziel+Angebot (Sn.printedAt[Ziel]=Item:Menge:Preis), Merker leer, wenn die Suche des Ziels
      keinen Treffer hat / ForgetTarget; PRINT_REPEAT entfernt. Ursache belegt: 0.65.437 wiederholte nach 30 s (s351: alt 2, neu 1 in 60 s).
  (4) "Insgesamt:" ist Sn:PlanTotal = was die nächste Raste mit Restbudget kaufen KANN, nicht gekauft -> Text "Kaufbar jetzt: …"
      und "– %d Angebote auf einmal" (10 Locales). 0/1000 ist richtig (Supervisor las "Insgesamt" als gekauft).
  ROT1: Ursache aus Spieldaten 11:02 (db.sniper.takt, 300 Suchen): mit Treffer-Halt Ø 3,36 s je Suche (Halt Ø 2,99 s), ohne 1,63 s,
      Antwort Ø 0,29 s -> je Ziel ~7,6 s. Entscheid Nutzer: "Halt nur 1× je Treffer" -> Sn.holdSeen/holdUntil (FinishSearch), Takt prüft
      holdUntil. s351: Treffer-Ziel Ø 4,7 s -> 2,2 s. Sniper-Satz 33: 31 PASS (s1/s4 alt rot) – vor ROT1-Änderung; nach ROT1 neu laufen lassen.
- NEU 62e33c44 AHS-SN-BUD1: "Nichts bis zu deinem Max-Preis (13s25). Günstigstes: 13s20" + Knopf "Kaufen 13s20" + Chat 3× bei
  leerem Budget. Prüfen: wurde wirklich gekauft (t.bought 0/1000?) – Supervisor liest "Insgesamt 37" wieder als gekauft; Spieldaten
  nach 11:16 abwarten/holen. Bei Budget-Rest < günstigstes: Grund "Budget aufgebraucht", Knopf grau, keine Chatzeile.
- Danach: Changelog/Version 0.65.438, Sniper-Satz + s350/s351, Zip, addon_check, Bericht (UX1 3/4, ROT1 mit "seltener gesucht"-Frage), FULL.

## Nächste Schritte (Reihenfolge = Masterplan Supervisor 28.11. 10:20, verbindlich)
1. 0.65.438 fertig (oben). (FULL 0.65.437: 362/67, fail437.txt.) Danach Schritt 2 Rest.
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
- 28.11. ~11:20: Sniper-Suchtakt: Treffer-Halt 3 s nur 1× je NEUEM Treffer (AHS-SN-ROT1).
- 28.11. 10:36: Sniper mit 2 Zielen mit Treffer: weiter alle 3 s wechseln (SN-Z4 bleibt, nicht stehen lassen).
- 28.11. 04:55: Anzeige-Befunde = Schritt 2b (nach 2, vor R1–R7), keiner darf verloren gehen, jeder mit Test + Abnahme-Bild.
- 28.11. 05:03: Eine Raste kauft ALLE Angebote des Treffers (Massenkauf) – gewollt, nicht ändern.

## Wichtig zu wissen
- Sn:ForgetTarget(key) räumt beim Löschen alles des Ziels. Sn:SetTarget 5. Wert f.zweck/f.quelle. A:VendorDealsChatText(n).
- A:BindOnPickup(id): 30 Min. Zwischenspeicher (Zahl, negativ = gebunden). VS:Ladder savedLad je Text (max 400).
- Sniper-Anzeige: UI_Sniper self.shownR = rechts gezeigtes Ergebnis; Sn.printedAt[Ziel|Angebot]. Letzte Tests T1043–T1049; neue Tests vor "Chk(\"T1043\"" o. ä. einfügen; Index-Einträge vor "AHS-BP1".
- Nie Blizzard-Globale in Tests ersetzen (Taint). Nie etwas in announce/ löschen. CHANGELOG.de.md je Version Pflicht.
