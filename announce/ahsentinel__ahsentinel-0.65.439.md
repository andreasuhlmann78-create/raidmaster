## AHSentinel 0.65.439

**Deutsch**
- **Lohnt bis bei Preissprung:** Steigt das günstigste Angebot frisch über 150 % des Medians (jünger als 24 Std.), rechnet der Wiederverkauf höchstens mit dem Median. Beispiel Braune Leinenhose: die Angebote zu 2s25 waren weg, übrig 5 × 50s – "Lohnt bis" war 37s99, jetzt 1s80.
- **Entzauber-Rechnung im Berufsfenster:** Wer ein Item im Berufsfenster ansieht, stellt es her – die Rechnung vergleicht dort mit den Herstellkosten aus dem Rezept ("Herstellkosten (Rezept)") statt mit dem günstigsten AH-Angebot. Ohne bekanntes Rezept kein Gewinn, nur der Entzauberwert. Ausserhalb heisst die Zeile "Kaufpreis im AH (Scan)".
- **Rechnung:** Titel "Rechnung je Entzauberung – Anteile aus 767 eigenen Entzauberungen" (statt doppelter Klammer), deckender Hintergrund.
- **Schnittstelle:** WorthUpTo liefert als 6. Wert einen Hinweis, wenn der AH-Weg fehlt, weil es keine Angebotsliste gibt ("AH-Weg: keine Angebotsliste – im AH suchen oder Vollscan").

**English**
- **Worth up to on a price jump:** if the cheapest offer jumped above 150 % of the median recently (less than 24 h), resale is calculated with at most the median. Example Brown Linen Pants: the offers at 2s25 were gone, 5 × 50s were left – "worth up to" was 37s99, now 1s80.
- **Disenchant calculation in the profession window:** whoever looks at an item in the profession window crafts it – there the calculation compares with the crafting cost from the recipe ("Crafting cost (recipe)") instead of the cheapest AH offer. Without a known recipe no profit, only the disenchant value. Elsewhere the line reads "Buy price in AH (scan)".
- **Calculation:** title "Calculation per disenchant – shares from 767 of your disenchants" (instead of double brackets), opaque background.
- **API:** WorthUpTo returns a hint as 6th value when the AH route is missing because there is no offer list.
