# Messwerkzeuge der Prüf-Sitzung

Kleine Addons, mit denen der Nutzer im Spiel etwas misst, das die Prüf-Sitzung nicht offline prüfen kann. Sie werden
**nicht veröffentlicht** (nicht in `download/`, nicht auf CurseForge) und nach der Messung wieder gelöscht.

## GSMesstest (9. Nov. 2026) – Grundlage für das Flüster-Netz von GoldSentinelSync

Misst in WoW Forever:

| Test | Frage |
|---|---|
| T1 Grundweg | Kommen Addon-Flüsternachrichten an, in beide Richtungen? |
| T2 Drossel | 10/s, 20/s und 30 im selben Frame: geht etwas verloren oder kommt verspätet? |
| T3 Offline | Welche Meldung kommt beim Flüstern an Offline- und unbekannte Spieler, lässt sie sich ausblenden? |
| T4 Realm | Ist der Partner auf demselben internen Realm (gemeinsamer Kanal)? Mit T1: Flüstern zwischen den Realms? |

Ablauf: Beide Spieler installieren `GSMesstest.zip` (Ordner `GSMesstest` nach `Interface/AddOns`). Einer tippt
`/gsmess partner <Name>` und `/gsmess alle` (ca. 1 Minute). Danach `/reload`: der RaidMasterUploader bringt das Ergebnis
als `GSDIAG1` nach `testberichte/diagnose/GSMesstest/`. Ohne Uploader: Ergebnis aus dem Chat kopieren.

Für T4 braucht es einen freien Kanalplatz (max. 10); der Kanal `GSMessRealm` wird danach wieder verlassen.
Am aussagekräftigsten: einmal mit einem Gildenmitglied, einmal mit einem Spieler, der dich in gemeinsamen Kanälen nicht
sieht (anderer interner Realm).

Keine Namen im Ergebnis (`<Ich>`, `<Partner>`, `<Offline>`, `<Unbekannt>`). Offline-Test: `shared/tests/test_gsmesstest.py`.
