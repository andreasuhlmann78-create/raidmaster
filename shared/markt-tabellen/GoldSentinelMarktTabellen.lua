-- GoldSentinelMarktTabellen (Prüf-Sitzung, täglich neu; nur Zahlen, keine Namen). Format: shared/markt-tabellen/README.md
GoldSentinelMarktTabellen = {
  v = 1,
  erstellt = 1794801439,
  datenBis = 1794766226,
  wellen = {
    ["5-25"] = {
      zustand = "steigt",
      index = 0.649,
      tage = 10,
    },
    ["26-35"] = {
      zustand = "durch",
      index = 0.149,
      tage = 10,
    },
    ["36-45"] = {
      zustand = "offen",
      index = 0.23,
      tage = 10,
    },
    ["46-55"] = {
      zustand = "offen",
      index = 0.453,
      tage = 9,
    },
    ["56-60"] = {
      zustand = "offen",
      index = 0.449,
      tage = 7,
    },
  },
  verkauf = {
    consum = { {
      bis = 1.03,
      n = 1,
      quote = 0,
    } },
    de = { {
      bis = 0.9,
      n = 11,
      quote = 0.298,
    }, {
      bis = 0.97,
      n = 19,
      quote = 0.491,
    }, {
      bis = 1.03,
      n = 48,
      quote = 0.74,
    }, {
      bis = 1.1,
      n = 9,
      quote = 0.6,
    }, {
      bis = 99,
      n = 34,
      quote = 0.353,
    } },
    metal = { {
      bis = 1.03,
      n = 1,
      quote = 1,
    }, {
      bis = 99,
      n = 1,
      quote = 0,
    } },
  },
  entzaubern = {
    ["2:4:a"] = {
      n = 1279,
      tabelle = 0.965,
      nKauf = 1205,
      gewinn = 0.258,
      mindest = 0.2,
    },
    ["2:6:a"] = {
      n = 124,
      tabelle = 0.95,
      nKauf = 62,
      gewinn = 0.199,
      mindest = 0.3,
    },
    ["2:1:a"] = {
      n = 750,
      tabelle = 1.007,
      nKauf = 0,
      gewinn = nil,
      mindest = 0.2,
    },
    ["2:3:a"] = {
      n = 20,
      tabelle = 0.947,
      nKauf = 0,
      gewinn = nil,
      mindest = 0.2,
    },
  },
  kaufen = { {
    bis = 0.6,
    n = 21,
    gewinn = 0.527,
  }, {
    bis = 0.7,
    n = 155,
    gewinn = 0.395,
  }, {
    bis = 0.8,
    n = 425,
    gewinn = 0.307,
  }, {
    bis = 0.9,
    n = 598,
    gewinn = 0.175,
  }, {
    bis = 99,
    n = 15,
    gewinn = -0.065,
  } },
  alle = {
    v = 1,
    tage = 1,
    von = 1794610800,
    bis = 1794697200,
    felder = { "preis", "absatzMin", "absatzMax", "quellen", "tage", "scans" },
    weggelassen = 0,
    ohneAbsatz = 6176,
    eineQuelle = 0,
  },
  kern = {
    markt = {
      ["consum:1"] = {
        p = 0.4963,
        n = 34,
      },
      ["consum:3"] = {
        p = 0,
        n = 944,
      },
      ["consum:5"] = {
        p = 0.0422,
        n = 573,
      },
      ["de:1"] = {
        p = 0.2796,
        n = 137,
      },
      ["de:2"] = {
        p = 0.0638,
        n = 863,
      },
      ["de:3"] = {
        p = 0.0409,
        n = 1503,
      },
      ["de:4"] = {
        p = 0.0771,
        n = 393,
      },
      ["de:5"] = {
        p = 0.0103,
        n = 544,
      },
      ["g:consum"] = {
        p = 0.0307,
        n = 1578,
      },
      ["g:de"] = {
        p = 0.0554,
        n = 3440,
      },
      ["g:gear2"] = {
        p = 0.0272,
        n = 13664,
      },
      ["g:misc"] = {
        p = 0.0569,
        n = 135775,
      },
      ["gear2:2"] = {
        p = 0.1125,
        n = 645,
      },
      ["gear2:3"] = {
        p = 0.0383,
        n = 4718,
      },
      ["gear2:4"] = {
        p = 0.0058,
        n = 1851,
      },
      ["gear2:5"] = {
        p = 0.0167,
        n = 6450,
      },
      ["misc:1"] = {
        p = 0.1108,
        n = 13431,
      },
      ["misc:2"] = {
        p = 0.1421,
        n = 8892,
      },
      ["misc:3"] = {
        p = 0.0398,
        n = 54688,
      },
      ["misc:4"] = {
        p = 0.0822,
        n = 13680,
      },
      ["misc:5"] = {
        p = 0.0372,
        n = 45084,
      },
    },
  },
  kernInfo = {
    quellen = 1,
    zellen = 21,
  },
}
