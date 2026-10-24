"""
Molten-Core-Raidtaktik für Discord.
Jeder Abschnitt ist ein eigener Beitrag (max. 2000 Zeichen).
"""

TACTICS = [
    (
        "Vorbereitung",
        "# 🔥 Molten Core – Raidtaktik\n"
        "## Vorbereitung\n"
        "**Mitbringen**\n"
        "• Feuerschutztränke (große), Heil- und Manatränke, Verbände\n"
        "• Tanks und Nahkämpfer: so viel **Feuerresistenz** wie möglich – vor allem für Ragnaros\n"
        "• **Aqual-Quintessenz** (von Herzog Hydraxis in Azshara): Damit werden die Runen gelöscht. "
        "Jede Quintessenz löscht eine Rune – mehrere Spieler sollten eine dabeihaben.\n"
        "\n"
        "**Feste Aufgaben (vor dem Raid einteilen)**\n"
        "• **Entfluchen:** Magier und Druiden\n"
        "• **Magie bannen:** Priester und Paladine\n"
        "• **Unterbrechen:** Schurken, Krieger, Schamanen\n"
        "• **Einlullender Schuss:** Jäger-Rotation für Magmadar\n"
        "• **Verbannen:** Hexer für Garr\n"
        "• **Furchtschutz:** Zwergenpriester auf die Tanks\n"
        "\n"
        "**Die Runen**\n"
        "Bei 7 Bossen liegt eine Rune am Boden (alle außer Lucifron, Majordomus und Ragnaros). "
        "Nach dem Kill eine Aqual-Quintessenz darauf benutzen. Erst wenn **alle 7 Runen gelöscht** sind, "
        "erscheint **Majordomus Exekutus**.\n"
        "\n"
        "**Übliche Reihenfolge**\n"
        "Lucifron → Magmadar → Gehennas → Garr → Shazzrah → Baron Geddon → Golemagg → Sulfuronherold → "
        "Majordomus → Ragnaros",
    ),
    (
        "Trash",
        "## ⚠️ Wichtiger Trash\n"
        "**Kernhunde (Rudel)**\n"
        "Stehen wieder auf, wenn nicht **alle kurz nacheinander** sterben. Gleichmäßig herunterschlagen, "
        "Flächenschaden am Ende. Kürschner danach häuten lassen (RaidMaster sagt sie an).\n"
        "\n"
        "**Uralte Kernhunde**\n"
        "Jeder hat eine eigene Fähigkeit (z. B. Stampfen, Lavaatem, Debuffs). Einzeln tanken und vom Raid wegdrehen.\n"
        "\n"
        "**Geschmolzene Riesen und Zerstörer**\n"
        "Stampfen und Rückstoß. Mit dem Rücken zur Wand tanken, damit der Tank nicht weggeschleudert wird.\n"
        "\n"
        "**Feuerlords**\n"
        "Beschwören Lavabrut, die sich teilt, wenn sie lange lebt. Lavabrut **sofort** töten.\n"
        "\n"
        "**Lavawogen**\n"
        "Stürmen auf zufällige Spieler. Schnell fokussieren.\n"
        "\n"
        "**Flammenschuppen-Gruppen (vor Bossen)**\n"
        "Heiler und Priester zuerst, Heilzauber unterbrechen.\n"
        "\n"
        "**Allgemein:** Nicht in Lava laufen, Pulls nur durch den Tank, Fernkämpfer warten auf das Signal.",
    ),
    (
        "Lucifron",
        "## 1. Lucifron + 2 Beschützer der Flammenschuppen\n"
        "**Fähigkeiten**\n"
        "• **Fluch des Lucifron:** verdoppelt Kosten für Mana, Wut und Energie → sofort entfluchen\n"
        "• **Drohende Verdammnis:** Magie-Debuff, nach 10 Sek. hoher Schattenschaden → bannen\n"
        "• **Schattenschock:** Schaden in der Nähe\n"
        "• Beschützer: **Gedankenkontrolle** und Spalten\n"
        "\n"
        "**Taktik**\n"
        "• 3 Tanks: Lucifron und je ein Beschützer, Adds vom Boss weg tanken\n"
        "• **Erst die beiden Beschützer töten**, dann Lucifron\n"
        "• Gedankenkontrollierte Spieler kurz verwandeln oder festhalten, nicht töten\n"
        "• Entflucher und Banner arbeiten durchgehend",
    ),
    (
        "Magmadar",
        "## 2. Magmadar\n"
        "**Fähigkeiten**\n"
        "• **Panik:** Furcht auf den ganzen Raid\n"
        "• **Raserei:** stark erhöhter Schaden auf den Tank\n"
        "• **Lavabombe:** Feuerflächen am Boden\n"
        "• **Lavaatem:** Feuerkegel nach vorne\n"
        "\n"
        "**Taktik**\n"
        "• Tank mit **Furchtschutz** (Zwergenpriester), Horde: **Erdbebentotem** (Tremor)\n"
        "• Krieger nutzen **Berserkerwut** gegen die Furcht\n"
        "• **Jäger-Rotation:** Bei Raserei sofort **Einlullender Schuss** – feste Reihenfolge ansagen\n"
        "• Boss vom Raid wegdrehen, niemand steht vor ihm\n"
        "• Sofort aus Lavabomben herauslaufen\n"
        "• Ersatztank in Bereitschaft, falls der Haupttank in Furcht gerät",
    ),
    (
        "Gehennas",
        "## 3. Gehennas + 2 Flammenschuppen\n"
        "**Fähigkeiten**\n"
        "• **Fluch des Gehennas:** stark reduzierte erhaltene Heilung → sofort entfluchen\n"
        "• **Feuerregen:** Feuerflächen → herauslaufen\n"
        "• **Schattenblitz:** Schaden auf zufällige Ziele\n"
        "• Adds: Betäubung und Rüstungsreduktion auf den Tank\n"
        "\n"
        "**Taktik**\n"
        "• 3 Tanks, **Adds zuerst** töten\n"
        "• Entflucher haben höchste Priorität – verfluchte Spieler sind kaum heilbar\n"
        "• Fernkämpfer verteilt stehen, damit der Feuerregen wenige trifft",
    ),
    (
        "Garr",
        "## 4. Garr + 8 Feuerschwörer\n"
        "**Fähigkeiten**\n"
        "• Garr: **Antimagischer Impuls** (entfernt Buffs), **Magmafesseln** (verlangsamt)\n"
        "• Feuerschwörer: **Feuerbrand**, beim Tod **Eruption** (Explosion mit Rückstoß)\n"
        "• Feuerschwörer, die zu weit von Garr weg sind, werden wütend\n"
        "\n"
        "**Taktik**\n"
        "• Jeder Feuerschwörer bekommt ein **Symbol** (RaidMaster-Vorlage „Garr“)\n"
        "• **Hexer verbannen** ihre zugewiesenen Adds (Elementare), Krieger tanken den Rest\n"
        "• Garr wird separat getankt, nicht zu weit von den Adds\n"
        "• Adds **einzeln** nacheinander töten, dann Garr\n"
        "• **Nahkämpfer weg**, wenn ein Add stirbt (Explosion)\n"
        "• Verbannung rechtzeitig erneuern – Hexer achten auf die Laufzeit",
    ),
    (
        "Shazzrah",
        "## 5. Shazzrah\n"
        "**Fähigkeiten**\n"
        "• **Arkane Explosion:** starker Flächenschaden um ihn herum\n"
        "• **Blinzeln:** teleportiert sich und setzt die Bedrohung zurück\n"
        "• **Fluch des Shazzrah:** erhöhter Arkanschaden → entfluchen\n"
        "• **Gegenzauber:** unterbricht Zauberer in der Nähe\n"
        "• **Magiedämpfung:** Schutz auf dem Boss → bannen bzw. reinigen\n"
        "\n"
        "**Taktik**\n"
        "• Mehrere Tanks im Raum verteilen – nach dem Blinzeln übernimmt der nächste\n"
        "• Fernkämpfer und Heiler auf maximale Distanz\n"
        "• Nur Nahkämpfer mit guter Heilung am Boss, nach Arkaner Explosion kurz zurück\n"
        "• Der Kampf ist kurz: voller Schaden, Flüche weg, Buff vom Boss bannen",
    ),
    (
        "Baron Geddon",
        "## 6. Baron Geddon\n"
        "**Fähigkeiten**\n"
        "• **Lebende Bombe:** Spieler explodiert nach kurzer Zeit und trifft alle in der Nähe\n"
        "• **Inferno:** starker Flächenschaden um den Boss\n"
        "• **Mana entzünden:** verbrennt Mana und verursacht Schaden → bannen\n"
        "• Kurz vor dem Tod: große Explosion\n"
        "\n"
        "**Taktik**\n"
        "• **Lebende Bombe → SOFORT aus dem Raid laufen** zu einem vorher festgelegten Platz\n"
        "• **Inferno → Nahkämpfer raus**, danach wieder rein\n"
        "• Raid weit verteilt aufstellen\n"
        "• Mana entzünden bannen\n"
        "• Bei wenig Leben: alle weg vom Boss\n"
        "• Kann **Bindungen des Windsuchers** droppen (legendär)",
    ),
    (
        "Golemagg",
        "## 7. Golemagg der Verbrenner + 2 Kernwüter\n"
        "**Fähigkeiten**\n"
        "• **Magmaspritzer:** stapelnder Debuff auf dem Tank\n"
        "• **Pyroschlag:** Feuerschaden auf zufällige Spieler\n"
        "• **Erdbeben** bei wenig Leben: Schaden für Nahkämpfer\n"
        "• Kernwüter: können nicht sterben, solange Golemagg lebt\n"
        "\n"
        "**Taktik**\n"
        "• Die beiden **Kernwüter abseits tanken und ignorieren** – sie sterben mit Golemagg\n"
        "• Alle Schaden auf **Golemagg**\n"
        "• Bei vielen Stapeln Magmaspritzer Tank wechseln\n"
        "• Gegen Ende Nahkämpfer mit wenig Leben zurückziehen",
    ),
    (
        "Sulfuronherold",
        "## 8. Sulfuronherold + 4 Priester der Flammenschuppen\n"
        "**Fähigkeiten**\n"
        "• Priester: **Dunkle Besserung** (Heilung), Schattenwort: Schmerz, Feuerbrand\n"
        "• Sulfuron: **Inspiration** (stärkt die Adds), **Hand des Ragnaros** (Betäubung und Rückstoß), "
        "Flammenspeer, Demoralisierungsruf\n"
        "\n"
        "**Taktik**\n"
        "• Jeder Priester bekommt ein **Symbol** und einen Tank\n"
        "• Priester **einzeln** töten, Heilungen **konsequent unterbrechen**\n"
        "• Sulfuron separat tanken und zuletzt töten\n"
        "• Schattenwort: Schmerz bannen",
    ),
    (
        "Majordomus",
        "## 9. Majordomus Exekutus + 4 Heiler + 4 Elite\n"
        "**Erscheint erst, wenn alle 7 Runen gelöscht sind.**\n"
        "\n"
        "**Fähigkeiten**\n"
        "• **Magiereflexion:** Zauber werden zurückgeworfen → Zauberer hören auf\n"
        "• **Schadensschild:** Nahkampftreffer schaden dem Angreifer → Nahkämpfer hören auf\n"
        "• **Teleport:** wirft Spieler in die Feuergrube\n"
        "• Heiler: Große Heilung, Schattenblitz · Elite: Feuerschlag, Druckwelle\n"
        "\n"
        "**Taktik**\n"
        "• Majordomus wird nicht angegriffen – der Kampf endet, wenn **alle 8 Adds** tot sind\n"
        "• Symbole: zuerst die Heiler, dann die Elite (RaidMaster-Vorlage „Majordomus“)\n"
        "• **Heiler zuerst**, Heilungen unterbrechen; Magier können Heiler verwandeln\n"
        "• Bei Schild oder Reflexion **sofort aufhören** – der Raidleiter sagt es an\n"
        "• Teleportierte Spieler schnell aus dem Feuer und gegenheilen\n"
        "• Danach: **Truhe des Feuerfürsten** plündern, später Majordomus ansprechen → Ragnaros",
    ),
    (
        "Ragnaros",
        "## 10. Ragnaros\n"
        "**Fähigkeiten**\n"
        "• **Zorn des Ragnaros:** schleudert alle Nahkämpfer weg\n"
        "• **Lavaschlag:** wenn **niemand** in Nahkampfreichweite ist – sehr gefährlich\n"
        "• **Elementarfeuer:** Feuerschaden über Zeit auf dem Tank\n"
        "• **Lavaeruption:** schleudert Spieler hoch\n"
        "• **Waffe schmelzen:** Haltbarkeit der Nahkampfwaffen sinkt\n"
        "• **Abtauchen:** nach einiger Zeit taucht er ab – **Söhne der Flamme** erscheinen\n"
        "\n"
        "**Taktik**\n"
        "• Tanks mit **möglichst viel Feuerresistenz**, Ersatztank steht bereit und spottet nach dem Rückstoß\n"
        "• **Immer jemand in Nahkampfreichweite** – sonst Lavaschlag auf den Raid\n"
        "• Kleine Nahkampfgruppe, vor dem Zorn kurz heraus\n"
        "• Fernkämpfer und Heiler verteilt im Halbkreis\n"
        "• **Söhne der Flamme:** alle Kräfte darauf, schnell töten, Mana-Klassen auf Abstand\n"
        "• Feuerschutztränke trinken, Ersatzwaffe für Nahkämpfer mitnehmen\n"
        "\n"
        "**Viel Erfolg – und denkt an eure DKP!** 🔥",
    ),
]


def as_markdown() -> str:
    return "\n\n---\n\n".join(text for _, text in TACTICS)
