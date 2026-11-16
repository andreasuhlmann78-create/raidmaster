# Prüfliste im Spiel (GoldSentinelPruefliste.lua)

Entscheid des Nutzers 16.11.2026 06:47: "Für AHS und alle anderen Addons, wenn etwas getestet werden muss, eine Checkliste im Spiel,
die merkt, wenn ein Punkt bearbeitet ist – nur im Entwicklermodus aufrufbar – inkl. Anweisungen im Spiel, damit ich immer genau weiss,
was zu tun ist."

## Was der Nutzer sieht
`/<addon> prüfliste` (nur im Entwicklermodus, GoldSentinelDev) öffnet ein Fenster:
- Kopf: "Prüfliste AHSentinel 0.65.259 – 3 von 9 erledigt".
- Liste der Punkte mit Zustand (offen · erledigt (erkannt) · OK · nicht OK · Fehler (erkannt)).
- Unten immer die Anweisung zum **nächsten offenen Punkt**: "Schritt 4 von 9: … · Das tust du: … · Das musst du sehen: …".
  Ist ein Punkt erledigt, springt die Anzeige von selbst weiter. Ein angeklickter Punkt bleibt gewählt.
- Knöpfe: OK · Nicht OK · Zurücksetzen · Jetzt prüfen. Am Ende: "Alle Punkte erledigt – jetzt /reload".

## Wie ein Punkt "merkt", dass er erledigt ist
1. `PL:Hit("ID", "Messwert")` an der Stelle im Code, wo die Funktion wirklich benutzt wurde (z. B. nach einem echten Kauf über den
   Kauf-Knopf). Das ist der Normalfall – der Nutzer tut einfach, was dasteht.
2. `auto = function() return true/false/nil, "Info" end` – wird bei offenem Fenster alle 2 s geprüft (nie im Kampf).
   false = "Fehler (erkannt)" mit Info; ein Lua-Fehler darin trifft nur diesen Punkt.
3. Wo nichts messbar ist (nur Hinschauen): der Nutzer drückt OK oder Nicht OK.

## Einbau (je Addon, Datei UNVERÄNDERT kopieren)
- `GoldSentinelPruefliste.lua` aus `shared/` ins Addon, `.toc` nach `GoldSentinelDev.lua`, vor den eigenen Dateien.
- Eigene Datei (z. B. `Pruefliste.lua`) mit `GoldSentinelPruefliste:Register("<Addon>", { db = …, version = …, points = { … } })`.
- Punkte = die offenen "IM CLIENT PRÜFEN"-Punkte des Addons (aus offen-*.txt / eigenen Berichten), je Punkt:
  `id` (Kürzel des Auftrags), `title` (≤ 8 Wörter), `since` (Version), `todo` (1–2 Sätze, genau: welcher Knopf, welcher Befehl),
  `expect` (was zu sehen ist, mit Zahl wo möglich), dazu `Hit()`-Stellen im Code bzw. `auto`.
- Erledigte Punkte nach der Prüfung der Prüf-Sitzung aus der Liste nehmen (neue Version), neue dazu. Höchstens 14 Punkte je Liste.
- Testbericht: `PL:ReportLines()` (eine Kopfzeile + eine Zeile je Punkt) in den Testbericht/Diagnose-Bericht.
- Ohne Entwicklermodus ist alles wirkungslos (Spieler sehen nichts, keine Kosten). Nichts senden, nichts im Kampf.

Test: `python3 -I shared/pruefliste/test_pruefliste.py` (26/26).
