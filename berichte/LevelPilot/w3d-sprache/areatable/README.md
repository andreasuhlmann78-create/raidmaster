# AreaTable + WMOAreaTable für den sprachfreien Ebenen-Schlüssel (Supervisor, 15.11.2026 22:03)

Quelle: wago.tools db2, Zweig **wowf**, Build **1.60.1.70938**, abgerufen 15.11.2026 22:03, je Sprache (deDE enUS esES esMX frFR
itIT koKR ptBR ruRU zhCN zhTW). Gekürzt auf die nötigen Spalten:
- AreaTable-<locale>.csv: ID, AreaName_lang, ParentAreaID, ContinentID (1404 Zeilen je Sprache)
- WMOAreaTable-<locale>.csv: ID, AreaName_lang, WMOID, WMOGroupID, AreaTableID (52 737 Zeilen mit Namen je Sprache)

WICHTIGER BEFUND (belegt aus diesen Daten): Die Viertel von Unterstadt (und die Räume von Orgrimmar/Eisenschmiede) stehen NICHT in
AreaTable (Unterstadt 1497 hat dort keine Unterzonen), sondern in **WMOAreaTable** (AreaTableID = 1497). Genau diese Namen liefert
GetSubZoneText drinnen. Das Werkzeug areanames_bauen.py muss darum WMOAreaTable mitlesen.
Zweiter Befund: Unterstadt gibt es mit ZWEI Gebäuden (WMOID 1150 und 20736) mit leicht verschiedenen Namen, z. B. deDE
"Magieviertel" (1150) und "Das Magieviertel" (20736). Welches Forever benutzt, zeigt erst GSWegMess – beide Namen auf denselben
Schlüssel abbilden (gleicher enUS-Name + gleiche AreaTableID = gleiche Ebene).
