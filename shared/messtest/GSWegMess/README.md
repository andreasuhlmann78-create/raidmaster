# GSWegMess 1.0 – Messwerkzeug Ebenen (Supervisor, 15.11.2026)

Passiv: schreibt nur mit, ändert nichts, sendet nichts. Zweck: belegen, an welchen Zeichen das Spiel eine Ebene erkennen lässt
(LevelPilot-Wegführung, shared/wissen/analysen/levelpilot-wegfuehrung-3d.md).

Installieren: GSWegMess.zip nach Interface/AddOns entpacken (Ordner GSWegMess).
Benutzen: `/wegmess start`, dann laufen; an wichtigen Stellen `/wegmess mark Aufzug oben` usw.; `/wegmess stop`; `/reload`;
Datei WTF/Account/<Konto>/SavedVariables/GSWegMess.lua schicken. Endet von selbst nach 30 Minuten.
Spalten: Zeit | x | y | Karte | Kleinkarte | Zone | Unterzone | Minikarte | drinnen | fällt | schwimmt | Tempo | Ereignis/Notiz.
Eine Zeile bei jeder Änderung, bei Ereignissen und in Bewegung etwa 1× je Sekunde.

Testläufe: (1) Unterstadt Auktionshaus -> Bethor Iceshard (Magieviertel) und zurück; (2) Ruinen von Lordaeron -> Aufzug -> Unterstadt
-> anderer Aufzug hinauf; (3) Donnerfels Aufzug unten -> oben; (4) eine Höhle hinein und hinaus.
Test: test_gswegmess.py (15/15).
