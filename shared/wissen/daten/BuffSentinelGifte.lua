-- BuffSentinel Waffengifte je Spielversion aus den Spieldaten (Supervisor, 16.11.2026 00:05). Quelle: wago.tools ItemSparse (deDE) + Item (ClassID 0 =
-- Verbrauchsgut); Auswahl über den Spieldaten-Namen je Gifttyp (alle Ränge). Zweige: wowf 1.60.1, era 1.15.9, tbc 2.5.6, wrath 3.80.2.
-- 'saison' = Gifte, die in den Daten von wowf/era stehen (Season-Gifte); ob es sie in WoW Forever im Spiel gibt: Verdacht, im Client prüfen.
-- Unverändert übernehmen; neu erzeugen statt von Hand ändern.
BuffSentinelGifte = {
  wowf = {
    sofort = { 6947, 6949, 6950, 8926, 8927, 8928 },
    toedlich = { 2892, 2893, 8984, 8985, 20844 },
    wund = { 10918, 10920, 10921, 10922 },
    verkrueppelnd = { 3775, 3776 },
    gedanken = { 5237, 6951, 9186 },
    saison = { 217345, 217346, 217347, 226374, 234444 },
  },
  era = {
    sofort = { 6947, 6949, 6950, 8926, 8927, 8928 },
    toedlich = { 2892, 2893, 8984, 8985, 20844 },
    wund = { 10918, 10920, 10921, 10922 },
    verkrueppelnd = { 3775, 3776 },
    gedanken = { 5237, 6951, 9186 },
    saison = { 217345, 217346, 217347, 226374, 234444 },
  },
  tbc = {
    sofort = { 6947, 6949, 6950, 8926, 8927, 8928, 21927 },
    toedlich = { 2892, 2893, 8984, 8985, 20844, 22053, 22054 },
    wund = { 10918, 10920, 10921, 10922, 22055 },
    verkrueppelnd = { 3775, 3776 },
    gedanken = { 5237, 6951, 9186 },
    beruhigend = { 21835 },
  },
  wrath = {
    sofort = { 6947, 6949, 6950, 8926, 8927, 8928, 21927, 43230, 43231 },
    toedlich = { 2892, 2893, 8984, 8985, 20844, 22053, 22054, 43232, 43233 },
    wund = { 10918, 10920, 10921, 10922, 22055, 43234, 43235 },
    verkrueppelnd = { 3775 },
    gedanken = { 5237 },
    beruhigend = { 21835, 43237 },
  },
}
