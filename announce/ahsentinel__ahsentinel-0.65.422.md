## AHSentinel 0.65.422

**Deutsch**
- **Schnellere "Lohnt bis"-Antworten (z. B. für ProfessionSentinel):** die Sicherheitsmarge beim Entzaubern hat für jeden einzelnen früheren Entzauber-Kauf die Item-Daten neu abgefragt (rund 1000-mal) – jetzt nur einmal je Item. Eine erste Abfrage dauert etwa 1–2 ms statt bis zu 40 ms, mit denselben Werten.
- Materialpreise und Entzauber-Startwerte werden je Abfrage nur noch einmal gerechnet.

**English**
- **Faster "worth up to" answers (e.g. for ProfessionSentinel):** the disenchanting safety margin looked up the item data of every single past disenchant purchase again (about 1000 times) – now only once per item. A cold question takes about 1–2 ms instead of up to 40 ms, with the same values.
- Material prices and disenchanting start values are now worked out only once per question.
