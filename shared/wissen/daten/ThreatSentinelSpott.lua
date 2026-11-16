-- ThreatSentinel N5 (Ersatz-Spott): Spott-Zauber je Spielversion und Klasse – aus den Spieldaten (wago.tools DB2, 16.11.2026,
-- Supervisor). Quelle je Zeile: SpellEffect Effect 114 (ATTACK_ME) oder EffectAura 11 (MOD_TAUNT) + SkillLineAbility (Klassen-
-- Fähigkeit) + SpellCooldowns (Sekunden). Zweige: forever = wowf 1.60.1, era = wow_classic_era 1.15.9, tbc = wow_anniversary 2.5.6,
-- wrath = wow_classic_titan 3.80.2. Nur Zahlen/IDs; Namen holt das Addon mit GetSpellInfo(id) in der Sprache des Spielers.
-- art: "einzel" = ein Ziel, "flaeche" = alle Gegner in der Nähe. ranks = alle Ränge (höchsten bekannten mit IsSpellKnown wählen).
-- rune = nur mit Rune (Season of Discovery) – in Forever nur nutzen, wenn IsSpellKnown(id) wahr ist (Verdacht, zu messen).
-- trigger = gewirkter Zauber löst den Spott über einen zweiten Zauber aus (im Kampflog kann die Spott-ID erscheinen: beide prüfen).
ThreatSentinelSpott = {
  forever = {
    WARRIOR = { { id = 355, art = "einzel", cd = 8 }, { id = 694, ranks = { 694, 7400, 7402, 20559, 20560 }, art = "einzel", cd = 120 },
                { id = 1161, art = "flaeche", cd = 600 } },
    DRUID   = { { id = 6795, art = "einzel", cd = 8 }, { id = 5209, art = "flaeche", cd = 600 } },
    WARLOCK = { { id = 403828, art = "einzel", cd = 10, rune = true }, { id = 412789, art = "flaeche", cd = 600, rune = true } },
  },
  era = {
    WARRIOR = { { id = 355, art = "einzel", cd = 10 }, { id = 694, ranks = { 694, 7400, 7402, 20559, 20560 }, art = "einzel", cd = 120 },
                { id = 1161, art = "flaeche", cd = 600 } },
    DRUID   = { { id = 6795, art = "einzel", cd = 10 }, { id = 5209, art = "flaeche", cd = 600 } },
    PALADIN = { { id = 407631, art = "einzel", cd = 10, rune = true } },
    WARLOCK = { { id = 403828, art = "einzel", cd = 10, rune = true }, { id = 412789, art = "flaeche", cd = 600, rune = true } },
  },
  tbc = {
    WARRIOR = { { id = 355, art = "einzel", cd = 10 }, { id = 694, ranks = { 694, 7400, 7402, 20559, 20560, 25266 }, art = "einzel", cd = 120 },
                { id = 1161, art = "flaeche", cd = 600 } },
    DRUID   = { { id = 6795, art = "einzel", cd = 10 }, { id = 5209, art = "flaeche", cd = 600 } },
    PALADIN = { { id = 31789, art = "einzel", cd = 15, trigger = 31790 } },   -- 31789 Dummy + Effekt 64 -> Spott in 31790 (beide im Kampflog möglich)
  },
  wrath = {
    WARRIOR     = { { id = 355, art = "einzel", cd = 8 }, { id = 694, art = "einzel", cd = 60 }, { id = 1161, art = "flaeche", cd = 180 } },
    DRUID       = { { id = 6795, art = "einzel", cd = 8 }, { id = 5209, art = "flaeche", cd = 180 } },
    PALADIN     = { { id = 62124, art = "einzel", cd = 8 }, { id = 31789, art = "einzel", cd = 8, trigger = 31790 } },
    DEATHKNIGHT = { { id = 56222, art = "einzel", cd = 8 }, { id = 49576, art = "einzel", cd = 35, trigger = 49560 } },  -- 49576 Dummy-Effekt, Spott in 49560 (per Skript, Verdacht: Kampflog zeigt 49560)
    HUNTER      = { { id = 20736, art = "einzel", cd = 8 } },
    WARLOCK     = { { id = 59671, art = "flaeche", cd = 15, nurIn = 59673 } },   -- Herausforderndes Geheul nur in Metamorphose (59673)
  },
}
