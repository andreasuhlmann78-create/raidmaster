# Spott-Zauber je Spielversion (für ThreatSentinel)

Erstellt von der Prüf-Sitzung am 16.11.2026 aus den Spieldaten (wago.tools DB2: SpellEffect, SkillLineAbility, SpellCooldowns, SpellName
enUS/deDE). Datei: `ThreatSentinelSpott.lua`.

Auswahl: Klassen-Fähigkeit (SkillLineAbility) mit Effekt 114 ATTACK_ME oder Aura 11 MOD_TAUNT. Dazu Zauber, die den Spott über einen zweiten
Zauber auslösen (Paladin Rechtschaffene Verteidigung 31789 -> 31790; Todesritter Todesgriff 49576 -> 49560; beide per Dummy/Skript, nicht über
EffectTriggerSpell – darum von Hand, im Kampflog können beide IDs vorkommen).

Auffällig: Forever (wowf 1.60.1) hat für Spott 355 und Knurren 6795 eine Abklingzeit von **8 s**, Era 1.15.9 **10 s**. ThreatSentinel liest
die Abklingzeit im Spiel (GetSpellCooldown) – die Zahl in der Datei ist nur Hinweis.
Rune-Zauber (Season of Discovery: 403828, 412789, 407631) stehen in den Daten von Forever/Era; ob sie in Forever lernbar sind, ist offen
(Verdacht, zu messen: IsSpellKnown).

Prüfung gegen ThreatSentinel Core.lua:529–533 (ns.CLASS_SPELLS backup): Krieger 694/1161, Druide 5209 – stimmen mit den Daten überein;
Spöttischer Schlag hat in Era/Forever 5 Ränge (694, 7400, 7402, 20559, 20560), in TBC 6 (+25266).
