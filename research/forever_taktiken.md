# WoW Forever – Recherche-Stand Raids, Taktiken, Materialien

Gepflegt von der täglichen Recherche-Aufgabe. Nur Bestätigtes aus zuverlässigen Quellen; Unsicheres ist als „noch nicht bestätigt“ markiert.

## (A) Erkannte Raids / Ankündigungen

| Raid (key) | Größe | Öffnet | Ankündigung | Quelle | Stand |
|---|---|---|---|---|---|
| Barrow Deeps (barrow) | 10 | 2026-12-09 | Blizzard Raid-Überblick, 8 Bosse, Eingänge Hyjal/Winterquell/Blackmaw Hold | https://worldofwarcraft.blizzard.com/news/24303009 | schon in forever_raids.json, korrekt |
| Hyjalgipfel (hyjal) | 20 | 2026-12-09 | Blizzard Raid-Überblick, 13 Bosse, neue Bosse, wählbare Wege | https://worldofwarcraft.blizzard.com/news/24303009 | schon in forever_raids.json, korrekt |
| Onyxias Hort (ony) | 40 | 2026-12-09 | Blizzard Raid-Überblick, Einstimmung (Drachenfeueramulett) bleibt | https://worldofwarcraft.blizzard.com/news/24303009 | "opens": "2026-12-09" am 2026-10-27 ergänzt, size 40 korrekt |
| Molten Core (mc) | 40 | – | **nicht** unter den 3 offiziellen Start-Raids; Sommer 2027 „überarbeiteter ikonischer Raid“ ohne Namen | warcraft.wiki.gg/wiki/World_of_Warcraft:_Forever | "forever": true in JSON ist **noch nicht bestätigt** (Hinweis an GoldSentinel) |
| BWL, ZG, AQ20, AQ40, Naxx | – | – | keine offizielle Ankündigung für Forever | – | unverändert |

Roadmap laut Blizzard (über warcraft.wiki.gg): Frühjahr 2027 „2 neue Raids“, Sommer 2027 „überarbeiteter ikonischer Raid + neuer Raid“ – Namen/Daten noch offen.

## (B) Gepostete Taktiken

| Datei | Raid | Version | Datum | Inhalt | Quellen |
|---|---|---|---|---|---|
| announce/barrow-taktik__uebersicht-1.0.md | barrow | 1.0 | 2026-10-27 | Vorschau: Eckdaten + 8 Bossnamen (Reihenfolge unbestätigt), keine Fähigkeiten | Blizzard News 24303009, Blizzard Watch 14.09.2026, warcraft.wiki.gg |
| announce/hyjal-taktik__uebersicht-1.0.md | hyjal | 1.0 | 2026-10-27 | Vorschau: Eckdaten + 13 Bossnamen (Reihenfolge unbestätigt), keine Fähigkeiten | Blizzard News 24303009, Icy Veins 13.09.2026, Blizzard Watch, warcraft.wiki.gg |
| announce/onyxia-taktik__onyxia-video-1.0.md | ony | 1.0 | 2026-10-27 | Taktik-Videos (DE: 5kx6k3A8ytM, EN: BFH1_YGbP3k) + Kurz-Merkliste; auf Wunsch von GoldSentinel; Videoinhalt nicht selbst geprüft (YouTube-Seiten nicht abrufbar), Auswahl nach Titel | YouTube, Warcraft Tavern |
| announce/mc-feuerresi__feuerresi-1.0.md | mc | 1.0 | 2026-10-27 | Neuer Kanal #mc-feuerresi (Wunsch GoldSentinel, Bot 1.5.74 "extra_channels"): FR-Bedarf je Rolle/Boss, Tränke/Buffs (Horde), herstellbare FR-Teile je Beruf; Stand Classic, Forever-Berufe noch prüfen; einige Itemnamen noch englisch | warcraft.wiki.gg Ragnaros (tactics), Icy Veins Ragnaros, Wowhead FR-Tank-Guide, Warcraft Tavern FR-Guide |
| announce/onyxia-feuerresi__feuerresi-1.0.md | ony | 1.0 | 2026-10-28 | Neuer Kanal #onyxia-feuerresi (extra_channels): Blizzard-Vorschau sagt offiziell „Feuerresi vor Onyxia aufbauen“; Bedarf je Rolle (MT/OTs Resi-Teile, Rest Großer Feuerschutztrank), Fähigkeiten mit Classic-Schadenswerten, Tränke/Buffs (Horde); genaue Forever-Werte noch nicht bestätigt | Blizzard News 24303009, warcraft.wiki.gg Onyxia_(Classic), Icy Veins Onyxia Classic, Warcraft Tavern FR-Guide |

### Bosslisten (Namen aus Spiel-Client/Legacy-Challenges laut Blizzard Watch; Reihenfolge laut warcraft.wiki.gg, noch nicht bestätigt)
- **Barrow Deeps (8):** Deepscar Matriarch, Khalith the Dreadspinner, Amethrax, Ravus and Darlissa, Elder Tangleclaw, Well of Sorrow, Del'lynar Songwood, Sonya Darkhallow (Endboss)
- **Hyjalgipfel (13):** Bandalar, Time-Lost Battalion, Old Gloomlurker, Kathris the Haunted, Elder Minderel, Council of Thorns, The Wild King, Ancient of Decay, Sylvestris Dusksong, Gharalis the Abyssal, Anara Chillwind, Tracker Stillwind, Nythus the Dreambound (Endboss)

### Was noch fehlt
- Barrow Deeps: Fähigkeiten/Taktik aller 8 Bosse (ab 09.12.2026 täglich recherchieren), deutsche Namen
- Hyjalgipfel: Fähigkeiten/Taktik aller 13 Bosse, Routen/Wege (ab 09.12.2026), deutsche Namen
- Resistenz-Kanal (wie #mc-feuerresi) für Barrow Deeps, Hyjalgipfel und alle künftigen Forever-Raids: erst anlegen, wenn gesicherte Quellen Resistenzbedarf/Rezepte zeigen (kein Datamining). Stand 2026-10-28: Barrow/Hyjal weiter nichts gesichert (Blizzard-Vorschau nennt keine Resistenz, warcraft.wiki.gg-Bossseiten noch leer), kein Kanal. Onyxia: Kanal #onyxia-feuerresi angelegt (Blizzard bestätigt Feuerresi).
- Hinweis: warcraft.wiki.gg Barrow Deeps nennt im Text 20 Spieler, in der Infobox 10 – Blizzard sagt offiziell 10, size bleibt 10.
- 2026-11-01: method.gg (28.10.2026) nennt „The Wild King“ als Hyjal-Endboss, warcraft.wiki.gg (Stand 20.10.2026) „Nythus the Dreambound“ – widersprüchlich, Endboss **noch nicht bestätigt**; Übersicht 1.0 bleibt (Reihenfolge dort ohnehin als unbestätigt markiert). Icy Veins „mindestens zwei Raids pro Tier“ nennt keine neuen Raidnamen → keine neuen Raids. Weiterhin keine gesicherten Resistenz- oder Materialinfos für Barrow/Hyjal (Malleable Essence of Nature bleibt Datamining).
- 2026-11-02: keine neue offizielle Blizzard-Ankündigung (keine neuen Raids, keine Bossfähigkeiten/Resistenzen/Materialien für Barrow/Hyjal); warcraft.wiki.gg Barrow (Stand 07.10.) und Hyjal (Stand 20.10.) unverändert, nur Bossnamen aus Beta 1.60.1. Endboss Hyjal weiter **noch nicht bestätigt**.
- 2026-11-03: keine neue offizielle Ankündigung. Blizzard „Forever Goes Live Globally November 4“ (Launch 04.11. 15:00 PST = 05.11. 00:00 MEZ) bestätigt nur die 3 Raids ab 09.12. (Barrow, Hyjal, Onyxia) – keine Bossfähigkeiten, Resistenzen oder Materialien. warcraft.wiki.gg Barrow (Stand 07.10.) und Hyjal (Stand 20.10.) unverändert. Wowhead-Interview (18.09.2026) „No Raid Attunements for Launch Raids“ widerspricht scheinbar der Onyxia-Einstimmung aus Blizzard-Raid-Überblick 24303009 → Onyxia-Einstimmung **noch nicht eindeutig**, nach Launch prüfen. Quellen: https://news.blizzard.com/en-us/article/24315820/world-of-warcraft-forever-goes-live-globally-november-4, https://www.wowhead.com/forever/news/no-raid-attunements-for-launch-raids-but-why-tho-interview-on-wow-forever-382964
- 2026-11-15: keine neue offizielle Raid-Ankündigung (keine neuen Raids, keine Termine über 09.12. hinaus). Neu offiziell (Blizzard-Podcast mit Lead Encounter Designer Michael Nuthals, berichtet von Wowhead, ca. 23.10.2026), aber **ohne Bossnamen**, darum noch kein Taktik-Entwurf: Barrow Deeps hat eine Begegnung mit einem Buff, der mehr Schaden bringt, aber etwas kostet, und eine Begegnung mit einem Spinnenpaar (passt vermutlich zu „Ravus and Darlissa“ – **noch nicht bestätigt**); Hyjalgipfel hat einen untoten Krokilisken-Boss, aus dem das besitzende Wesen herauskommt – zwei abwechselnde Phasen. Weltbuffs wirken in Forever-Raids laut Icy-Veins-News/Blizzard-Forum nicht (Seite selbst nicht abrufbar – **noch nicht bestätigt**, nach Öffnung prüfen). Hotfixes bis 13.11.2026: nichts zu Raids/Onyxia, nur Hinweise „bis die Raids öffnen“. Weiterhin keine gesicherten Fähigkeiten, Resistenzen oder Materialien für Barrow/Hyjal; warcraft.wiki.gg Barrow weiter Stand 07.10.2026. Quellen: https://www.wowhead.com/forever/news/blizzard-teases-raid-philosophy-and-encounters-for-wow-forever-383546, https://news.blizzard.com/en-us/article/24315281/wow-forever-hotfixes-november-13-2026, https://www.icy-veins.com/wow-forever/news/world-buffs-just-got-benched-from-raids-in-wow-forever-ending-a-classic-headache/, https://warcraft.wiki.gg/wiki/Barrow_Deeps_(instance)
- 2026-11-16: nichts Neues. Keine neue offizielle Raid-Ankündigung, keine Bossnamen/-fähigkeiten, Resistenzen oder Materialien für Barrow/Hyjal; neueste gefundene Hotfixes weiter 13.11.2026 (Blizzard-Artikel 24315281, Text nicht abrufbar). warcraft.wiki.gg Barrow weiter Stand 07.10.2026, Bossseiten leer. Guided.news (22./23.10.) wiederholt nur die Podcast-Teaser (ohne Bossnamen). Quellen: https://warcraft.wiki.gg/wiki/Barrow_Deeps_(instance), https://guided.news/en/news/wow-forever-barrow-deeps-hyjal-summit-bosses-routes/, https://news.blizzard.com/en-us/article/24315281
- 2026-11-17: nichts Neues. Keine neue offizielle Raid-Ankündigung; gefundene Forever-Hotfixes (5.–11.11.) ohne Änderungen an Onyxia/Barrow/Hyjal. warcraft.wiki.gg Barrow (Stand 07.10.2026) und Hyjal (Stand 20.10.2026) unverändert: nur Bosslisten, keine Fähigkeiten, Resistenzen oder Materialien. Quellen: https://warcraft.wiki.gg/wiki/Barrow_Deeps_(instance), https://warcraft.wiki.gg/wiki/Hyjal_Summit_(instance), https://www.warcrafttavern.com/forever/news/riverglades-mob-nerfs-wow-forever-hotfixes-for-november-11/
- Onyxia-Feuerresi: konkrete Forever-Zahlen/Rezepte nach Öffnung (09.12.2026) prüfen, ggf. Version 1.1.

## (C) Materialien & Rezepte

Eingetragen in raid_materials.json: noch nichts Neues (nichts offiziell bestätigt).

Noch nicht bestätigt (nur Datamining Beta, nicht eintragen):
- **Malleable Essence of Nature** – angeblich nur durch Entzaubern von Items aus Hyjalgipfel und Barrow Deeps; je 3 Stück pro Teil der handwerklich hergestellten Tier-Sets („Artisan set“), Beruf unklar. Quelle: https://www.icy-veins.com/wow-forever/news/wow-forever-crafted-tier-sets-datamined-recipes-costs-and-set-bonuses/ (18.09.2026, Datamining)

## Letzte Wochenprüfung je Raid

| Raid | Letzte Prüfung | Ergebnis |
|---|---|---|
| mc | 2026-11-15 | weiterhin nicht unter den offiziellen Forever-Raids, keine Änderungen gefunden, nichts gepostet |
| ony | 2026-11-15 | keine Forever-Änderungen (Hotfixes bis 13.11. ohne Onyxia) an der Begegnung gefunden, nichts gepostet (Feuerresi-Kanal seit 2026-10-28) |
| barrow | 2026-11-17 | nur Podcast-Teaser ohne Bossnamen (Buff mit Preis, Spinnenpaar), keine offiziellen Bossinfos/Resistenzen/Materialien, nichts gepostet |
| hyjal | 2026-11-17 | nur Podcast-Teaser ohne Bossnamen (untoter Krokilisk, 2 Phasen), keine offiziellen Bossinfos/Resistenzen/Materialien, nichts gepostet |
| bwl, zg, aq20, aq40, naxx | 2026-11-15 | keine Forever-Ankündigung (Launch WoW Forever laut Blizzard Watch 04.11.2026) |
