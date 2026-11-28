# Stand Supervisor (Prüf-Sitzung)

## Stand 28.11.2026 11:10 · AHS 0.65.437 · PS 0.9.101 · LP 3.13.35 (Pause)

## Gerade in Arbeit
- Nichts offen in Arbeit; warte auf neue Berichte (AHS, PS) und Spieltests des Nutzers.

## Nächste Schritte (Reihenfolge)
1. AHS 0.65.437 Spieltest SN-UX1 (Nutzer, Sniper AN mit 2–3 Zielen): Anzeige = Kauf, kein Ziel ohne Treffer rechts, Wechsel >= 3 s,
   Chat <= 1 Zeile/Ziel/30 s, keine rote Zeile bei Enter. Dann SN-UX1 schliessen.
2. PS: Bericht zu PS-SK3 (Magiestoffballen "Skill ?" im Plan – Rückschritt seit 04:47?). Wenn nicht neu: PS-DL 0.9.101 frei.
   Weitere PS-Punkte: PS-PERF-NB1 (22 ms), PS-P4, PS-REZ-ZAHL (362/369), PS-PLAN-KOST, PS-VAL-VK1, PS-VAL-LB2, PS-VAL-HV1.
3. AHS nach Masterplan (Nachtrag 10:20): Schritt 2 Rest (T459 + SN-LAG2 + SP1), dann 2b Rest (inkl. AHS-DE-MSG1 neu 11:08).
4. LP ab Montag 30.11./Dienstag 1.12.: Ingametest 3.13.35 kalt (T261 < 1000 ms), LP-T261-REST, LP-TAKT-16.

## Offen beim Nutzer
- CurseForge: englische Antwort an Spieler CF-1 posten? (wartet auf OK)
- Preisverlauf-Graph im Tooltip als Option (Standard aus)?
- Homezugriff: Uploader-Zip 2.3.30 nochmals an Offizier B?
- Spieltests: AHS 0.65.437 Sniper; PS Flut-Tooltip erst, wenn ein Rezept Flut hat (blockiert nicht).
- Idee für später: Homepage für die Gilde.

## Entscheide des Nutzers seit letztem Stand (in entscheide.md eingetragen)
- 10:36 AHS Sniper: zwei Ziele mit Treffer wechseln weiter alle 3 s (SN-Z4 bleibt).
- 11:07 LevelPilot pausiert bis Montag/Dienstag.
- 10:12 Max-Preise im Sniper hat der Nutzer selbst geändert (Klärung, kein Entscheid).

## Wichtig zu wissen
- Heute geprüft: PS 0.9.101 im Spiel (Rezepte, Plan Skillen, Gold) – OVL1/REZ1 bestanden; LP 3.13.34 im Spiel (FRZ1, T155 erledigt;
  T261 1143 ms) -> 3.13.35 angenommen, 3.13.34 in download/ (md5 geprüft).
- "Lohnt bis" beim Weg Händler = Händlerpreis / 1,2 (Kern.lua K:LohntBis, VENDOR_MIN_GAIN) – kein Fehler.
- addon_check auf download/-Zips kann > 120 s dauern: einzeln mit timeout 110 oder md5 gegen announce vergleichen.
