📦 **AHSentinel 0.65.376** – Stückpreise und Post-Mengen richtig

• **Zusammengefasste Angebote:** der Server fasst gleiche Einzel-Angebote nicht stapelbarer Items in eine Zeile („9 Stück“). AHSentinel teilte den Preis durch 9 (z. B. „1s16“ statt 10s44 je Seite → „kaufen −98 %“). Jetzt Preis je Angebot, ein Kauf = 1 Stück; falsche gespeicherte Werte werden bereinigt.
• **Post:** „Gekauft: 36× …“ las die Lieferzeit statt der Menge – behoben, alte Mengen bereinigt.
• **Eine Rundung** für den Stückpreis (unter 1s mit Bruchteil, „6,9c“).
• **Woher der Vorschlag kommt:** „Vorschlag 53c = günstigstes fremdes Angebot 54c (33 Stück) − 1c“.
• **Händler zahlt mehr:** immer roter Hinweis mit beiden Zahlen; Einstellen bleibt möglich.

**Installation:** ZIP unten herunterladen, entpacken und den Ordner `AHSentinel` in `Interface/AddOns` ersetzen. Deine Daten und Einstellungen bleiben erhalten.
