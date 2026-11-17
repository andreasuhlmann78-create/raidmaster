# LevelPilot – Talent-Builds (Stand 3.12.89, EULA-Austausch)

Entscheid des Nutzers 17.11.2026 06:22 (keine aus Spieldateien abgeleiteten Daten), Supervisor 15:55 (TalentBuilds per Name).

- Entfernt: Talent.csv, TalentSpells.csv, TalentTab-*.csv (Auszüge aus den Spieldatenbanken über wago.tools) sowie builds.py und
  talente_bauen.py (bauten daraus Baum/Reihe/Spalte). Die Historie im Repo bleibt; nichts davon wird mehr benutzt.
- Quelle der Builds ist jetzt nur noch `LevelPilot/Data/TalentBuilds.lua`: eigene Auswahl, eigene Begründungen (de/en), Talent-NAMEN
  (deutsch; englisch als Verdacht aus eigenem Wissen). Die Lage im Talentbaum sucht das Addon zur Laufzeit über GetTalentInfo.
- Namen bestätigen bzw. ergänzen: im Spiel `/lp talente` (Testmodus) auf einem vorhandenen Charakter, dann /reload – die Aufzeichnung
  (LevelPilotDB.talentbaum[Klasse][Sprache]: Name, Reihe, Spalte, Höchstrang) kommt mit dem Upload. Daraus wird die Namensliste ergänzt.
