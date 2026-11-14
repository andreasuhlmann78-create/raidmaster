-- GoldSentinelMarktTabellen (Prüf-Sitzung, täglich neu; nur Zahlen, keine Namen). Format: shared/markt-tabellen/README.md
GoldSentinelMarktTabellen = {
  v = 1,
  erstellt = 1794643547,
  datenBis = 1794640965,
  wellen = {
    ["5-25"] = {
      zustand = "offen",
      index = 0.586,
      tage = 9,
    },
    ["26-35"] = {
      zustand = "durch",
      index = 0.138,
      tage = 9,
    },
    ["36-45"] = {
      zustand = "offen",
      index = 0.26,
      tage = 9,
    },
    ["46-55"] = {
      zustand = "offen",
      index = 0.377,
      tage = 8,
    },
    ["56-60"] = {
      zustand = "offen",
      index = 0.274,
      tage = 6,
    },
  },
  verkauf = {
    de = { {
      bis = 0.9,
      n = 11,
      quote = 0.298,
    }, {
      bis = 0.97,
      n = 10,
      quote = 0.333,
    }, {
      bis = 1.03,
      n = 20,
      quote = 0.55,
    }, {
      bis = 1.1,
      n = 2,
      quote = 1,
    }, {
      bis = 99,
      n = 19,
      quote = 0.217,
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
      n = 524,
      tabelle = 0.956,
      nKauf = 450,
      gewinn = 0.354,
      mindest = 0.2,
    },
    ["2:6:a"] = {
      n = 124,
      tabelle = 0.95,
      nKauf = 62,
      gewinn = 0.199,
      mindest = 0.3,
    },
  },
  kaufen = { {
    bis = 0.6,
    n = 21,
    gewinn = 0.527,
  }, {
    bis = 0.7,
    n = 154,
    gewinn = 0.432,
  }, {
    bis = 0.8,
    n = 234,
    gewinn = 0.331,
  }, {
    bis = 0.9,
    n = 42,
    gewinn = 0.182,
  }, {
    bis = 99,
    n = 11,
    gewinn = -0.021,
  } },
}
