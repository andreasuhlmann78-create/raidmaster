# Stand AHSentinel (Projekt-Sitzung)

## Stand 23.11.2026 16:11 · Version 0.65.386
Repos: ahanalyzerpro (Code, schreiben; tests/run_offline.sh = Nachbau mit Testroutine), raidmaster (announce/, berichte/AHSentinel/), goldsentinel-daten (nur lesen).
Arbeitskopie /home/claude/AHSentinel; Veröffentlichen mit /tmp/claude-0/bin/pub.sh (nur Discord, löscht NICHTS in announce/).
Nachbau: cd /home/claude/ahanalyzerpro && TR_ROWS=1 bash tests/run_offline.sh /home/claude/AHSentinel (~70 s). Bisektion: /tmp/claude-0/bis/run1.sh <commit> <ver>.

## Gerade in Arbeit
- AHS-I2: veraltete Tests umschreiben (V1/P8: T509 T514–T519 T521 T522 T525 T545 T788 T290 T875 T891; TT: T215 T228 T248 T273 T467–T470 T743 T789 T888 T287;
  T225 T255), Echtdaten-Isolation (T285 T289 T291 T292, T875), T397/T579 belegen, T750/T191 UI.

## Nächste Schritte (Reihenfolge Supervisor)
1. AHS-I2 Rest (oben). 2. AHS-I4 712-ms-Lücke beim Vollscan belegen. 3. AHS-I3 (T126 8,5 ms, T459 Speicher).

## Offen beim Nutzer
- Neuer Testlauf nach den Test-Anpassungen; CurseForge gesperrt (E5).
- Messung RecipeList-Fehler mit nur AHS aktiv.

## Entscheide des Nutzers seit letztem Stand
- keine neuen.

## Wichtig zu wissen
- Nachbau zeigt 41 der 49 Ingame-FEHLER ohne Spielerdaten -> Sandbox-Verdacht widerlegt; Bisektion: V1 0.65.358/359, TT 0.65.360, P5/P8 0.65.361.
- Letzter Test T1002. Neue Tests vor "-- CF-AHS-5 (CurseForge 17.11. …"; Index vor { "BEFUND-S5", .
