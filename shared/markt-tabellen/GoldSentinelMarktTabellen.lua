-- GoldSentinelMarktTabellen (Prüf-Sitzung, täglich neu; nur Zahlen, keine Namen). Format: shared/markt-tabellen/README.md
GoldSentinelMarktTabellen = {
  v = 1,
  erstellt = 1794717764,
  datenBis = 1794703697,
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
      zustand = "durch",
      index = 0.22,
      tage = 10,
    },
    ["46-55"] = {
      zustand = "offen",
      index = 0.447,
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
      n = 13,
      quote = 0.333,
    }, {
      bis = 1.03,
      n = 24,
      quote = 0.542,
    }, {
      bis = 1.1,
      n = 3,
      quote = 0.667,
    }, {
      bis = 99,
      n = 30,
      quote = 0.4,
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
      n = 557,
      tabelle = 0.953,
      nKauf = 483,
      gewinn = 0.34,
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
      n = 448,
      tabelle = 1.023,
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
    n = 158,
    gewinn = 0.427,
  }, {
    bis = 0.8,
    n = 236,
    gewinn = 0.331,
  }, {
    bis = 0.9,
    n = 66,
    gewinn = 0.173,
  }, {
    bis = 99,
    n = 14,
    gewinn = -0.042,
  } },
}
