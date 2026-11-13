# ProfessionSentinel – genaue Durchsicht (Prüf-Sitzung, 13.11.2026 22:30) – "für später aufheben" (Nutzer)

Grundlage: Code 0.9.44 (Repo ProfessionSentinel, Commit 5940493), Kopfkommentare aller Module, API in Today.lua,
Nutzung in AHSentinel (Comfort.lua). Noch NICHT mit dem Nutzer besprochen – bei Gelegenheit vorlegen.

## Was es heute schon kann (wichtig, damit nichts doppelt gebaut wird)
- Rezept-Bibliothek Forever/Era/Retail (alle Lehrer-, Händler-, Drop-Rezepte), gelernt/fehlend je Beruf und Figur,
  "Lebenslinie" bis Grau (Fertigkeits-Chance je Herstellung).
- Advisor: Ranglisten "Leveln" (Gold je Fertigkeitspunkt), "Gold verdienen" (Nettogewinn je Herstellung, auch grau),
  "Herstellen & Entzaubern" (für Verzauberer).
- Plan: Leveling-Plan mit Ziel, Schritten und Einkaufsliste; fehlende Händler-Reagenzien direkt kaufen, AH-Reagenzien
  an den Sniper von AHSentinel übergeben.
- **"Heute herstellen" (Today.lua) = die Herstellungs-Kette existiert bereits:** die lohnendsten Herstellungen aller
  Berufe, je Zeile der nächste Schritt mit einem Klick (Händler kaufen -> AH kaufen über AHSentinel -> Berufsfenster
  -> herstellen -> im Verkaufen-Reiter von AHSentinel einstellen), Kapitalschutz 20 % des Golds, max. 5 je Rezept.
  Öffentliche API ProfessionSentinelAPI.TodayCrafts(max) (itemID, Rezept, Anzahl, Gewinn gesamt/je Herstellung,
  Kosten, Kapital, nächster Schritt, run()). AHSentinel nutzt sie schon in "Heute tun" (Comfort.lua).
- Market (PM1–PM7): Herstellen ODER Rohstoff verkaufen; echte Preise über die Leiter für die benötigte Menge;
  Abklingzeit-Rezepte je Abklingzeit; KEINE Schein-Gewinne (Preise > 6 Std., Aufkauf, dünner Markt -> keine Zahl);
  eine Zahl mit AHSentinel (Werte nur über AHSentinel.API); Leveling-Wellen-Hinweis (PM5 – entspricht Idee I6!);
  Trefferquote der Empfehlungen je Beruf (PM6).
- Preis-Makler (PriceSource): AHSentinel zuerst, dann auxForever, Auctionator, Auctioneer, TSM, sonst eigene Regeln.
- Forever-Händlergunst (Favor): Kosten der Gunst-Rezepte, Planer, Kisten-Rechner (Gold je Gunstpunkt), Gilde.
- Gilde: wer kann was, welche Rezepte niemand kennt, Abklingzeiten (liest GuildSentinel/RaidMaster).
- Rezept-Alarm: fehlendes Rezept liegt im AH (nach jedem AHSentinel-Scan).
- Händler-Mengenfenster (Shift+Klick), Wegpunkte zu NPCs, Diagnose, UICheck, grosse Testroutine (7'847 Zeilen).

## Folge für den Auftrag HK (Herstellungs-Kette, Entscheid 22:23)
- NICHT neu bauen. HK = die bestehende Kette (TodayCrafts) in AHSentinel als EINE schlichte Zeile/ein Vorschlag
  zeigen, nur wenn alle Schritte nach PM3 gesichert sind, mit der Zahl aus der einen Funktion "bester Weg"
  (SN2115b) und den Preisen "Jetzt im AH" (TP). Aufträge HK/HK-P entsprechend berichtigt (22:32).

## Ideen und Prüfpunkte für später
1. Optik-Regel OR auch für ProfessionSentinel: Ranglisten und Lebenslinie zeigen viele Zahlen/Erklärungen –
   prüfen, was davon Rechenweg ist (z. B. "Gold je Fertigkeitspunkt", Chancen) und was Ergebnis.
2. Tempo/RF/PS auch hier: UI.lua 2'969 Zeilen mit portioniertem Neuaufbau; Speicher nahe an der Grenze (T145);
   gleiche Leistungsziele wie AHSentinel ansetzen (Reiter ≤ 50 ms, kein Bild > 16 ms).
3. Rezept-Alarm über das Marktdaten-Netz (GoldSentinelMarkt): fehlendes Rezept auch aus den Scans der Gilde melden
   (nur gesichert, ≤ 60 s wie SA) – passt zu Idee I5.
4. Leveling-Wellen (PM5) mit dem Netz verbinden: Stufenverteilung aus GuildSentinel/Netz + Marktzustand.
5. Trefferquote PM6 mit der unabhängigen Nachrechnung (ZN) koppeln: Empfehlung "lohnt" vs. echter Verkauf.
6. Abklingzeiten der Gilde (Transmutation, Mondstoff, Salz) als Geldquelle: "wer kann heute was herstellen".
7. Händlergunst: Kisten-Rechner (Gold je Gunstpunkt) in "Heute tun" einbinden, wenn eine Kiste lohnt.
8. Doppelte Arbeit vermeiden: PriceSource-Regeln (Gebühr, Einzahlung) müssen mit AHSentinel identisch bleiben –
   bei jeder Gebühren-Änderung (z. B. 1c Mindest-Einzahlung ab 17./18.11.) beide prüfen.
