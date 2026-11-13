# Marktanalyse (Prüf-Sitzung) – Wellen und Zyklen

Werkzeuge, mit denen die Prüf-Sitzung Markt-Wellen und Zyklen aus den AHSentinel-SavedVariables (privates Daten-Repo)
nachmisst. Keine Daten im Repo, nur die Programme. Ergebnisse stehen in shared/wissen/markt-strategie.md (8g).

1. `python3 -I verlauf_auspacken.py <AHSentinel.lua> <ausgabe.json>` – Preisverlauf je Item (PD7 hz + Tabellen,
   ohne unbestätigte/Sync-Punkte).
2. `python3 -I wellen_zyklen.py <ausgabe.json>` – Wellen je Stufenband (Staub/Essenz/Splitter als Stellvertreter),
   Tageszyklus (roh), Wochenzyklus.
3. `python3 -I tageszyklus_bereinigt.py <ausgabe.json>` – Tageszyklus ohne Trend (gleitender ±12-Std.-Median) mit
   Bestätigung erste/zweite Hälfte.
Regel: Ein Zyklus gilt erst als belegt, wenn er in mindestens zwei getrennten Zeiträumen in dieselbe Richtung zeigt
(gleiche Richtung ≥ 80 % der Stunden/Tage) und mindestens 3 Wochen Daten vorliegen.
