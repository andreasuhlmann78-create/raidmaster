# Hinweise für Claude-Sitzungen in diesem Repo

Dieses Repo gehört GoldSentinel. Hier veröffentlichen alle GoldSentinel-Addons (`download/`, `announce/`), und hier liegen
das Prüfsystem (`addon-check/`, `shared/`, `testberichte/`) und der Discord-Bot (`RaidMasterBot/`).

## Aufträge der Prüf-Sitzung – vor jeder Arbeit an einem Addon lesen

Ausnahme: Geplante Aufgaben (z. B. «ProfessionSentinel Rezeptdaten-Update», «Raids und Taktiken für WoW Forever») führen nur
ihre eigene Anweisung aus. Sie setzen keine Aufträge aus `auftraege/` um und ändern keinen Programmcode.

Die Prüf-Sitzung verteilt Anweisungen, Korrekturen und Hinweise für die Addon-Projekte über den Ordner `auftraege/`
(Regeln in `auftraege/README.md`). Ein Ordner pro Addon bzw. Projekt: `RaidMaster/`, `ThreatSentinel/`, `AHSentinel/`, `BuffSentinel/`,
`GuildSentinel/`, `ProfessionSentinel/`, `LevelPilot/`, `Discord/` (Discord-Projekt: Gilden-Discord, Server-Bot).

1. `git pull --rebase`
2. Alle Dateien in `auftraege/<dein Addon>/` lesen. Neues zeigt `git log --oneline -- auftraege/<dein Addon>/`.
   `offen-<addon>.txt` ist immer vollständig, mit allem, was noch offen ist.
3. Umsetzen: komplette Dateien, alte Clients nie brechen, Locales und CHANGELOG EN/DE.
4. Vor dem Push: `python3 addon-check/addon_check.py download/<Addon>-<Version>.zip` -> kein FEHLER.
5. Dem Nutzer melden, was umgesetzt wurde, und einen Bericht in `berichte/<dein Addon>/` ablegen (siehe unten).
   Ist ein Befund falsch, begründet zurückmelden (auch im Bericht).

Den Ordner `auftraege/` ändert nur die Prüf-Sitzung. Gemeinsame Dateien (`GoldSentinelGame.lua`, `GoldSentinelTest.lua`,
`GoldSentinelSync.lua`, `GoldSentinelDev.lua`) nur unverändert aus `shared/` kopieren, nie selbst ändern.

## Nur eine Sitzung je Addon (Entscheid des Nutzers, 9. November 2026)

Am 9.11. haben zwei Sitzungen gleichzeitig AHSentinel geändert und veröffentlicht (0.65.18 bis 0.65.20). Das darf
nicht wieder passieren, sonst überschreiben sie sich gegenseitig.

- **AHSentinel ändert und veröffentlicht nur noch EINE Sitzung:** die AHSentinel-Sitzung des Nutzers.
  Alle anderen Sitzungen, die Prüf-Sitzung und geplante Aufgaben ändern AHSentinel nicht und veröffentlichen nichts
  davon (Repo AHAnalyzerPro, `download/AHSentinel-*`, `announce/ahsentinel__*`). Sie melden Befunde nur über
  `auftraege/AHSentinel/` bzw. dem Nutzer.
- Gilt sinngemäss für jedes Addon: je Addon arbeitet nur seine eigene Sitzung daran.
- Vor jeder Veröffentlichung trotzdem `git pull --rebase` und die höchste schon veröffentlichte Version prüfen.

## Ergebnisse von Prüfungen immer über das Repo (Entscheid des Nutzers, 12. November 2026)

Gilt für ALLE Prüf-Sitzungen (Prüf-Sitzung im Chat, geplante Nachprüfung, jede andere Sitzung, die prüft):
Jedes Ergebnis einer Prüfung – erledigt, Befunde, "im Client prüfen", auch "freigegeben, keine Befunde" – kommt
über das Repo zum zuständigen Projekt, in `auftraege/<Projekt>/offen-<projekt>.txt` (bei Bedarf dazu `befund-*.txt`
oder `anweisung-*.txt`). Ein Ergebnis, das nur im Chat oder in einer Nachricht an den Nutzer steht, gilt als nicht
weitergeleitet. Die Nachricht zum Einfügen an den Nutzer ist nur zusätzlich. Betrifft ein Befund ein anderes
Projekt, auch in dessen `offen-*.txt` eintragen. Offene Punkte anderer Prüfungen nie verlieren, sondern übernehmen.
Alles kommt ins Repo (Entscheid des Nutzers, 13. November 2026: "pushe immer alles ins Repo"): auch jede
Nachricht zum Einfügen an eine Projekt-Sitzung liegt zusätzlich als `auftraege/<Projekt>/nachricht-<thema>-<JJJJ-MM-TT>.txt`
im Repo (committen, pushen, dann erst schicken). Nichts bleibt nur im Arbeitsordner oder nur im Chat.
Zuständig: Discord-Bot und Gilden-Discord -> `Discord/`, Uploader -> `RaidMaster/`, jedes Addon -> eigener Ordner.
Keine Überschneidungen: Vor jeder Prüfung, jedem Auftrag und jeder Nachricht zuerst `git pull --rebase` und in
`auftraege/nachrichten-log.txt` und `addon-check/nachpruefung-stand.json` nachsehen, ob dasselbe (Projekt + Version
bzw. Anlass) schon geprüft bzw. die Nachricht schon raus ist. Wenn ja: nichts doppelt schreiben oder schicken. Sonst
sofort eine Zeile ins Log, committen und pushen, erst dann die Nachricht an den Nutzer schicken.

## Regelmässig ins Repo schauen (Entscheid des Nutzers, 12. November 2026)

Gilt für alle Projekt-Sitzungen. Aufträge der Prüf-Sitzung können jederzeit kommen. Deshalb `git pull --rebase` und
`auftraege/<dein Projekt>/` (dazu `git log --oneline -5 -- auftraege/<dein Projekt>/`) prüfen:
- bei jeder neuen Nachricht des Nutzers, bevor du antwortest oder etwas änderst,
- während längerer Arbeit spätestens alle 15 Minuten (zwischen zwei Arbeitsschritten),
- immer direkt vor jedem Push und jeder Veröffentlichung.
Ist etwas Neues da: laufende Arbeit fertig machen, dann den Auftrag lesen und dem Nutzer kurz melden.

## Bericht an die Prüf-Sitzung (Entscheid des Nutzers, 12. November 2026)

Alle Projekt-Sitzungen und alle anderen Prüf-Sitzungen (auch die geplante Nachprüfung) erstatten der Prüf-Sitzung
Bericht über das Repo: eine Datei je Bericht in `berichte/<Projekt>/<JJJJ-MM-TT>-<HHMM>-<thema>.txt` – nach jeder
Veröffentlichung, wenn Aufträge umgesetzt/abgelehnt wurden, wenn ein Befund falsch ist (mit Begründung) und bei
Fragen. Aufbau und Regeln in `berichte/README.md`. `auftraege/` = Prüf-Sitzung -> Projekte, `berichte/` = Projekte ->
Prüf-Sitzung. Die Prüf-Sitzung liest `berichte/` bei jeder Arbeit.

## Neues Addon

Neue GoldSentinel-Addons immer aus der Vorlage erstellen: `python3 shared/vorlage/neues_addon.py <Name> --slash <befehl>
--en "…" --de "…" --zip` (Anleitung in `shared/vorlage/README.md`). Die Vorlage hält alle Regeln der Prüfung schon ein.

## Projekte prüfen sich nicht selbst (Entscheid des Nutzers, 13. November 2026, 22:28)

Projekt-Sitzungen testen ihre Arbeit mit ihren eigenen Testszenarien und Testroutinen und melden gefundene Fehler gerne
im Bericht – mehr nicht. Sie erklären nichts für "erledigt", "freigegeben", "bestanden" oder "geprüft": In Berichten
heisst es nur "umgesetzt, zur Prüfung" mit den Belegen (Tests, Messwerte). Ob ein Auftrag erledigt ist, entscheidet
allein die Prüf-Sitzung nach ihrer eigenen Prüfung (Prüf-Ablauf). Eigene Testergebnisse sind Hinweise, keine Freigabe.

## Prüf-Ablauf (Pflicht für jede Prüfung, Entscheid des Nutzers 13. November 2026)

Die Prüf-Sitzung ist allein für die Prüfungen der Projekte zuständig und arbeitet "sehr genau, akribisch, intelligent
und vorausschauend". Vor JEDER Prüfung (auch die geplante Nachprüfung) `shared/wissen/pruef-ablauf.md` lesen und
Abschnitt A vollständig abarbeiten: Bericht prüfen statt glauben, addon_check, Code-Änderung gegen alle Entscheide des
Nutzers, Zahlen unabhängig nachrechnen, Tempo-/Ruckel-Ziele (PS/RF), Gold-Sicherheit, Zusammenspiel der Addons.
Findet der Nutzer einen Fehler, den die Prüfung hätte finden müssen: Prüfregel in Abschnitt E ergänzen. Fehlen für
ein Thema Informationen, holt die Prüf-Sitzung sie selbst (Repo, Berichte, Diagnosen, Web) statt zu raten.

## Wirtschaft, Preise, Gebühren (Pflicht)

Wer Preise, Gebühren, Gewinne oder Werte berechnet, prüft oder beauftragt, liest vorher
`shared/wissen/wirtschaft-forever.md` und hält dessen Abschnitt 0 (zuerst messen, Zahlen müssen exakt aufgehen) und die
Pflicht-Checkliste (Abschnitt 7) ein. Regeln nur als "belegt" weitergeben, sonst als Messauftrag.

## Buchhaltung (Pflicht)

Wer an Buchhaltung, Gewinn, Kasse oder Lagerwert arbeitet oder Aufträge dazu schreibt, liest vorher
`shared/wissen/buchhaltung.md` (Kostenbasis, realisierter Gewinn, Entzaubern als Umbuchung, Abstimmung mit dem Gold).

## Marktstrategie und Prognosen (Pflicht)

Wer an Preisen, Absatz, Empfehlungen, Sniper, "Heute tun", Markt-Reiter oder Prognosen arbeitet oder Aufträge dazu
schreibt, liest vorher `shared/wissen/markt-strategie.md` (Ziel, Datenlage, Methoden, Erkenntnisse, Messaufträge).

## Addon-Kommunikation (Pflicht)

Wer Sync, Addon-Nachrichten oder Kanäle baut oder beauftragt, liest vorher `shared/wissen/kommunikation-forever.md`.
In WoW Forever kommen Addon-Nachrichten über eigene Chat-Kanäle nicht an.

## Immer

- Das Repo ist öffentlich: nie Tokens, Webhook-URLs, Passwörter oder Spielernamen in Dateien oder Commits.
  `config.json` und `uploader_config.json` nie anfassen.
- Andere Addons als das eigene nicht ändern.
