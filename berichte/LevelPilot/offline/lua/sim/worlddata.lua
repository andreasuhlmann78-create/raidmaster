-- Kartengrenzen für den Nachbau (WORLDHOOK=…/sim/world_hook.lua SIMDIR=…/sim), nur für Tests/Messungen, nicht Teil des Addons.
-- Quelle: UiMapAssignment der Spielversion WoW Forever 1.60.1 (wago.tools, Zweig wowf; dieselbe Datei wie
-- berichte/LevelPilot/strassen/UiMapAssignment-wowf-1.60.1.csv): je uiMap die erste Zeile mit WMOGroupID 0;
-- left = Region_4 (max. Welt-Y), right = Region_1 (min. Y), top = Region_3 (max. X), bottom = Region_0 (min. X).
-- Nachgeprüft 16.11.2026: alle 46 Karten stimmen mit der CSV überein (Abweichung < 0,01).
-- (Die frühere Sitzungsfassung hatte zusätzlich WORLD.xp – vom Welt-Hook nicht benutzt, darum hier weggelassen.)
WORLD = { maps = {}, xp = {} }
WORLD.maps[1411] = { name = "Durotar", inst = 1, parent = 1414, left = -1962.4998779297, right = -7249.9995117188, top = 1808.3332519531, bottom = -1716.6666259766 }
WORLD.maps[1412] = { name = "Mulgore", inst = 1, parent = 1414, left = 2479.1669921875, right = -3675.0, top = 266.666015625, bottom = -3835.416015625 }
WORLD.maps[1413] = { name = "The Barrens", inst = 1, parent = 1414, left = 2622.9165039062, right = -7510.4165039062, top = 1612.4998779297, bottom = -5143.75 }
WORLD.maps[1416] = { name = "Alterac Mountains", inst = 0, parent = 1415, left = 783.33331298828, right = -2016.6666259766, top = 1500.0, bottom = -366.66665649414 }
WORLD.maps[1417] = { name = "Arathi Highlands", inst = 0, parent = 1415, left = -866.66662597656, right = -4466.6665039062, top = -133.33332824707, bottom = -2533.3332519531 }
WORLD.maps[1418] = { name = "Badlands", inst = 0, parent = 1415, left = -2079.1665039062, right = -4566.6665039062, top = -5889.5830078125, bottom = -7547.9165039062 }
WORLD.maps[1419] = { name = "Blasted Lands", inst = 0, parent = 1415, left = -1241.6666259766, right = -4591.6665039062, top = -10566.666015625, bottom = -12800.0 }
WORLD.maps[1420] = { name = "Tirisfal Glades", inst = 0, parent = 1415, left = 3033.3332519531, right = -1485.4166259766, top = 3837.4997558594, bottom = 824.99993896484 }
WORLD.maps[1421] = { name = "Silverpine Forest", inst = 0, parent = 1415, left = 3449.9997558594, right = -750.0, top = 1666.6666259766, bottom = -1133.3332519531 }
WORLD.maps[1422] = { name = "Western Plaguelands", inst = 0, parent = 1415, left = 416.66665649414, right = -3883.3332519531, top = 3366.6665039062, bottom = 499.99996948242 }
WORLD.maps[1423] = { name = "Eastern Plaguelands", inst = 0, parent = 1415, left = -2256.25, right = -6558.333984375, top = 3691.6669921875, bottom = 825.0 }
WORLD.maps[1424] = { name = "Hillsbrad Foothills", inst = 0, parent = 1415, left = 1066.6666259766, right = -2133.3332519531, top = 400.0, bottom = -1733.3332519531 }
WORLD.maps[1425] = { name = "The Hinterlands", inst = 0, parent = 1415, left = -1575.0, right = -5425.0, top = 1466.6666259766, bottom = -1100.0 }
WORLD.maps[1426] = { name = "Dun Morogh", inst = 0, parent = 1415, left = 1802.0832519531, right = -3122.9165039062, top = -3877.0832519531, bottom = -7160.4165039062 }
WORLD.maps[1427] = { name = "Searing Gorge", inst = 0, parent = 1415, left = -322.91665649414, right = -2554.1665039062, top = -6100.0, bottom = -7587.4995117188 }
WORLD.maps[1428] = { name = "Burning Steppes", inst = 0, parent = 1415, left = -266.66665649414, right = -3195.8332519531, top = -7031.2495117188, bottom = -8983.3330078125 }
WORLD.maps[1429] = { name = "Elwynn Forest", inst = 0, parent = 1415, left = 1535.4166259766, right = -1935.4166259766, top = -7939.5830078125, bottom = -10254.166015625 }
WORLD.maps[1430] = { name = "Deadwind Pass", inst = 0, parent = 1415, left = -833.33331298828, right = -3333.3332519531, top = -9866.666015625, bottom = -11533.333007812 }
WORLD.maps[1431] = { name = "Duskwood", inst = 0, parent = 1415, left = 833.33331298828, right = -1866.6666259766, top = -9716.666015625, bottom = -11516.666015625 }
WORLD.maps[1432] = { name = "Loch Modan", inst = 0, parent = 1415, left = -1993.7498779297, right = -4752.0830078125, top = -4487.5, bottom = -6327.0830078125 }
WORLD.maps[1433] = { name = "Redridge Mountains", inst = 0, parent = 1415, left = -1681.25, right = -3852.083984375, top = -8575.0, bottom = -10022.916015625 }
WORLD.maps[1434] = { name = "Stranglethorn Vale", inst = 0, parent = 1415, left = 2220.8332519531, right = -4160.4165039062, top = -11168.75, bottom = -15422.916015625 }
WORLD.maps[1435] = { name = "Swamp of Sorrows", inst = 0, parent = 1415, left = -2222.9165039062, right = -4516.6665039062, top = -9620.8330078125, bottom = -11150.0 }
WORLD.maps[1436] = { name = "Westfall", inst = 0, parent = 1415, left = 3016.6665039062, right = -483.33331298828, top = -9400.0, bottom = -11733.333007812 }
WORLD.maps[1437] = { name = "Wetlands", inst = 0, parent = 1415, left = -389.58331298828, right = -4525.0, top = -2147.9165039062, bottom = -4904.1665039062 }
WORLD.maps[1438] = { name = "Teldrassil", inst = 1, parent = 1414, left = 3814.5832519531, right = -1277.0832519531, top = 11831.25, bottom = 8437.5 }
WORLD.maps[1439] = { name = "Darkshore", inst = 1, parent = 1414, left = 2941.6665039062, right = -3608.3332519531, top = 8333.3330078125, bottom = 3966.6665039062 }
WORLD.maps[1440] = { name = "Ashenvale", inst = 1, parent = 1414, left = 1699.9998779297, right = -4066.6665039062, top = 4672.9165039062, bottom = 829.16662597656 }
WORLD.maps[1441] = { name = "Thousand Needles", inst = 1, parent = 1414, left = -433.33331298828, right = -4833.3330078125, top = -3966.6665039062, bottom = -6899.9995117188 }
WORLD.maps[1442] = { name = "Stonetalon Mountains", inst = 1, parent = 1414, left = 3245.8332519531, right = -1637.4998779297, top = 2916.6665039062, bottom = -339.58331298828 }
WORLD.maps[1443] = { name = "Desolace", inst = 1, parent = 1414, left = 4233.3330078125, right = -262.5, top = 452.08331298828, bottom = -2545.8332519531 }
WORLD.maps[1444] = { name = "Feralas", inst = 1, parent = 1414, left = 5441.6665039062, right = -1508.3332519531, top = -2366.6665039062, bottom = -6999.9995117188 }
WORLD.maps[1445] = { name = "Dustwallow Marsh", inst = 1, parent = 1414, left = -974.99993896484, right = -6225.0, top = -2033.3332519531, bottom = -5533.3330078125 }
WORLD.maps[1446] = { name = "Tanaris", inst = 1, parent = 1414, left = -218.74998474121, right = -7118.7495117188, top = -5875.0, bottom = -10475.0 }
WORLD.maps[1447] = { name = "Azshara", inst = 1, parent = 1414, left = -3277.0832519531, right = -8347.916015625, top = 5341.6665039062, bottom = 1960.4166259766 }
WORLD.maps[1448] = { name = "Felwood", inst = 1, parent = 1414, left = 1641.6666259766, right = -4108.3330078125, top = 7133.3330078125, bottom = 3299.9997558594 }
WORLD.maps[1449] = { name = "Un'Goro Crater", inst = 1, parent = 1414, left = 533.33331298828, right = -3166.6665039062, top = -5966.6665039062, bottom = -8433.3330078125 }
WORLD.maps[1450] = { name = "Moonglade", inst = 1, parent = 1414, left = -1381.25, right = -3689.5832519531, top = 8491.666015625, bottom = 6952.0830078125 }
WORLD.maps[1451] = { name = "Silithus", inst = 1, parent = 1414, left = 2537.5, right = -945.833984375, top = -5958.333984375, bottom = -8281.25 }
WORLD.maps[1452] = { name = "Winterspring", inst = 1, parent = 1414, left = -316.66665649414, right = -7416.6665039062, top = 8533.3330078125, bottom = 3799.9997558594 }
WORLD.maps[1453] = { name = "Stormwind City", inst = 0, parent = 1415, left = 1722.9200439453, right = -14.58399963379, top = -7995.830078125, bottom = -9154.169921875 }
WORLD.maps[1454] = { name = "Orgrimmar", inst = 1, parent = 1414, left = -3680.6010742188, right = -5083.2055664062, top = 2273.8771972656, bottom = 1338.4605712891 }
WORLD.maps[1455] = { name = "Ironforge", inst = 0, parent = 1415, left = -713.59136962891, right = -1504.2164306641, top = -4569.2412109375, bottom = -5096.845703125 }
WORLD.maps[1456] = { name = "Thunder Bluff", inst = 1, parent = 1414, left = 516.66662597656, right = -527.08331298828, top = -849.99993896484, bottom = -1545.8332519531 }
WORLD.maps[1457] = { name = "Darnassus", inst = 1, parent = 1414, left = 2938.3627929688, right = 1880.0295410156, top = 10238.31640625, bottom = 9532.5869140625 }
WORLD.maps[1458] = { name = "Undercity", inst = 0, parent = 1415, left = 873.19262695313, right = -86.18240356445, top = 1877.9453125, bottom = 1237.8411865234 }
