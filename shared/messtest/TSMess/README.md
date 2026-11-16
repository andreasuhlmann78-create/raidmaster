# TSMess – Messwerkzeug für ThreatSentinel (N4-MESS, 16.11.2026)

**Frage:** Liefert WoW Forever im Kampf lesbare Bedrohungswerte? Nur dann kann ThreatSentinel einem Schaden- oder
Heiler-Spieler sagen, *wie bald* er Aggro zieht (Abstand zum Tank, Bedrohung je Sekunde, „Zeit bis Pull“ – Wunsch N4).

**Was es misst:** im Kampf je Sekunde, für das aktuelle Ziel, für die Einheiten `player`, `pet`, `party1`–`party4`:
`UnitDetailedThreatSituation(Einheit, "target")` (isTanking, status, Prozent, Roh-Prozent, Rohwert),
`UnitThreatSituation(Einheit, "target")` und `UnitThreatSituation(Einheit)`. Dazu Kampfbeginn/-ende und Zielwechsel.
Gespeichert wird nur die Art jedes Werts: `-` nil · `G` geschützt · `1`/`0` wahr/falsch · Zahl mit 2 Nachkommastellen ·
`F` Funktion warf einen Fehler. **Keine Namen** (nur Kennungen), nichts wird gesendet oder verändert.

**Benutzen**
1. `TSMess.zip` entpacken, Ordner `TSMess` nach `Interface/AddOns` (nur für den Test; ThreatSentinel bleibt installiert).
2. Im Spiel `/tsmess start`.
3. Am besten **als DD oder Heiler in einer Gruppe mit Tank** ein paar Kämpfe machen, Ziel angewählt (ein Kampf als Tank
   ist auch nützlich). Die Messung endet von selbst nach 60 Minuten.
4. `/tsmess stop`, dann `/reload` (oder ausloggen).
5. Datei `WTF/Account/<Konto>/SavedVariables/TSMess.lua` schicken (enthält keine Namen).

Befehle: `/tsmess start` · `/tsmess stop` · `/tsmess` (Stand).

**Auswerten:** `python3 -I shared/messtest/TSMess/auswerten.py <TSMess.lua>` – zeigt je Einheit und Feld, wie oft nil /
geschützt / Zahl, und das Urteil zu N4 (MÖGLICH · NUR PROZENT · NICHT MÖGLICH · NICHT ENTSCHIEDEN).
Tests: `python3 -I test_tsmess.py` (Addon im Nachbau) und `python3 -I test_auswerten.py` (Auswertung).

Nicht veröffentlichen (nicht in `download/`), nach der Messung wieder löschen.
