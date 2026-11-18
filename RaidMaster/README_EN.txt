RaidMaster 3.0.17 – DKP, loot and raid leading tools
====================================================

INSTALLATION
- Copy the folder "RaidMaster" into ...\Interface\AddOns\ of your game version and restart the game.
- Open the window with the minimap button or /rm.
- Works with Classic Era, WoW Forever, TBC, Wrath (incl. Titan Reforged), Cataclysm,
  Mists of Pandaria Classic and Retail. The detected game version is shown in chat at login (/rm version).
- The language follows your game client (English, German, French, Spanish, Italian, Portuguese,
  Russian, Korean, Simplified and Traditional Chinese).

MAIN FEATURES
- DKP per raid (separate point pools), automatic awards for raid start, boss kills and raid end.
- Open bidding with a bid window for everyone; players without the addon bid with /w <looter> !bid 50.
- Loot rules (auction, guild bank, disenchanter, crafter), trade helper, undo log, decay, standby.
- Raid sign-ups imported from Discord: auto invite and automatic group sorting.
- Assignments (healing, decurse, dispel, crowd control per boss) sent to every player.
- Specs of all raid members (own spec is shared automatically, others via inspect).
- PUG raids without DKP (soft reserve via softres.it) and an ad text for public chat channels.
- All raids of every WoW version (Classic to Midnight, 60+ raids, 400+ bosses): the addon shows the raids of
  your game version, with tactics, two raid chat lines and a raid marker template per boss.
  The boss's marker template is selected automatically when the encounter starts.
- Every raid has its own DKP pool; boss kills are detected and booked automatically.
- Raid target icon bar.

WHAT'S NEW IN 3.0.34 – test data stays inside RaidMaster
- Other addons (e.g. GuildSentinel) never see test data during a test any more: RaidMaster.db shows them the real data
  meanwhile. New for other addons: RaidMasterAPI.TestRunning() – true while a test is running.

WHAT'S NEW IN 3.0.33 – even smoother test routine (developer)
- Developer only: the checks that still took more than 5 ms per frame in the game (options, auction rules, damaged data,
  crash test, situation catalogue, data backup) now work in smaller portions. The portions line also shows the total time
  per step and, for the first build, the single page.

WHAT'S NEW IN 3.0.32 – labels always fit
- Buttons and column headers fit their font to the width (smaller, on tall buttons two lines if needed) – in every
  language. Before, e.g. "Golemagg the Incinerator" (Bosses & marks) and the Discord guide steps were cut off.
- Developer only: the test routine always measures window overlap (opens the character window itself if needed and
  closes it again) and reports exact numbers for the test run (loaded, auctioned, awarded).

WHAT'S NEW IN 3.0.31 – no more stutter after AH scans, better test routine (developer)
- Shared market data: no more stutter after a full AH scan (work split across frames). Test entries are never saved or
  shared.
- Tooltips of the marker bar and the main window never cover buttons: beside, above or below the window.
- Developer only: the test routine no longer shows Blizzard's error window (the intentional test errors no longer go
  through the game's error handler). It never waits for you: steps that need a window (professions, bank, mail) are
  done automatically the next time you open it ("Noch offen: …" in the summary). All portions stay below 5 ms; the
  first build of the main window happens before the run and is measured separately.

WHAT'S NEW IN 3.0.30 – raid dates for other addons, test routine "all" (developer)
- New for other addons: RaidMasterAPI.UpcomingRaids() returns the upcoming raid dates from the Discord signup (start
  time and title only, at most 20). AHSentinel can use it e.g. to remind you of potions before a raid.
- Diagnosis: now counts which addon error messages come from (only a count per addon, no text). Shown in the diagnosis
  window and in the test report ("FEHLERQUELLEN").
- Developer only: "/rm testroutine alles" runs all automatic checks one after another – in small portions, without
  stutter, with progress ("3 of 12 …") and one summary at the end. "/rm testroutine stop" aborts; a /reload in the
  middle of a run also leaves everything clean.
- Developer only: the checklist (/rm checklist) describes every manual step exactly: where, step by step, what you
  see, what it costs.

WHAT'S NEW IN 3.0.29 – the diagnosis no longer slows the game down
- Fixed: "Diag.lua: insecure scripts exceeded execution limit for addon RaidMaster" every frame. With the diagnosis
  window open, RaidMaster rebuilt it on EVERY error – also errors of other addons and the execution-limit message itself,
  which escalated. Now an error is only noted briefly (at most 400 characters, only counted during an error flood), and
  the window refreshes at most once per second and only when something changed.
- New test T186 measures this: 5000 errors in one frame and 1000 with the window open.
- Shared file GoldSentinelDev.lua version 2 (character only as a checksum).

WHAT'S NEW IN 3.0.28 – in-game checklist (developer only)
- /rm checklist opens a list of the points that can only be checked in the game, with exact instructions what to do and
  what you should see. The list notices by itself when a point is done. Players without developer mode see nothing.
- New test T185 checks the checklist.

WHAT'S NEW IN 3.0.27 – Chinese fixed, market data network version 7
- Simplified Chinese: the question "Give item to player for DKP?" and the announcement afterwards made the addon fail,
  because the translation had swapped the placeholders. They are now in the right order.
- New test T184: checks in every language that each translation has the same placeholders in the same order.
- GoldSentinelMarkt.lua updated from the shared template (version 7): handing a full scan to the guild now needs at most
  about 2.8 MB of temporary memory instead of up to 7.5 MB – no long stutter, same result.
  The "share market data" switch now also stops a reply to the guild that was already scheduled.

WHAT'S NEW IN 3.0.26 – Market data network version 2
- GoldSentinelMarkt.lua updated from the shared template (version 2): if AHSentinel is loaded, it no longer reads the
  scans a second time (AHSentinel hands them over) – no stutter during full scans and in the sniper. At most 10 queued
  messages, full scan to the guild at most once per hour; sold-out items now count towards measured sales.
- Test routine: T180 checks that the current version is loaded; T181/T182 no longer change the market network counters
  (the diagnosis showed "dropped: off 1" afterwards).

WHAT'S NEW IN 3.0.25 – Market data network (GoldSentinelMarkt)
- RaidMaster ships the shared file GoldSentinelMarkt.lua (like all GoldSentinel addons). It reads auction house scans
  that are made anyway (e.g. by AHSentinel) and shares only prices and quantities – no names, no own queries, no prompt.
  It runs only once per client, however many addons ship it.
- Turn off: Settings -> "Share market data (anonymous, prices only)". Off = read nothing, send nothing.
- Old clients without the needed auction house API: stays silent.
- The test report contains a line "MARKT-NETZ: …" (version, on/off, scans, sent/received, storage).

WHAT'S NEW IN 3.0.24 – Command list while typing, safer defaults
- Type /rm or /raidmaster in chat and a list of ALL commands with a short description appears above the input box
  (in your game language). Keep typing to filter ("/rm be" shows ready, professions, loot …); most used on top.
  Mouse click, Tab or arrow keys select, Enter runs it. The chat box is never changed. Turn off: /rm commandlist.
- New English command words: /rm professions, /rm craft <item>, /rm break <minutes>.
- If a numeric guild setting is missing (e.g. after syncing with an older version), the default applies: auctions start
  again (previously a Lua error), raid start/end award the default DKP. Decay deliberately stays at 0 % then.
- Comprehensive tests (TU1–TU8) in the test routine (area L): situations, flows, defaults, 1000 random cases, real data
  read-only, regressions, report per area.

WHAT'S NEW IN 3.0.23 – Proof for the PC/laptop sync
- For RaidMaster-Uploader 2.2.0: if the uploader takes over a newer state from your other computer while WoW is still on
  the login or character screen, RaidMaster notes at login that this state was read (RaidMasterDB.syncProbe: number,
  computer name, time). That tells the uploader the takeover was in time; after two proofs the notice "please don't log
  in yet" no longer appears. Nothing is sent.

WHAT'S NEW IN 3.0.22 – GoldSentinelSync included
- Brings GoldSentinelSync along so error reports (only with consent, /gstest) can be shared; RaidMaster data
  unchanged (DKP, bids, assignments still only to guild, raid and single players).

WHAT'S NEW IN 3.0.21 – Share error reports (only with your consent)
- GoldSentinelTest 2: share error reports with the developer (only with consent, /gstest). Only short summaries of Lua
  errors and failed test cases are shared, without names. Without consent nothing is shared. Sharing runs over
  GoldSentinelSync 2, which another GoldSentinel addon brings along; RaidMaster itself still sends its raid and DKP data
  only to guild, raid and single players (no channel, no network).

WHAT'S NEW IN 3.0.20 – No real player names in examples and tests
- Examples, comments and the test routine only use made-up names ("Testa Beispiel"); the shared file
  GoldSentinelGame.lua is now version 3 (only comments changed, same behaviour).
- Nothing else changes for you in the game.

WHAT'S NEW IN 3.0.19 – Raid markers in WoW Forever without error messages again
- WoW Forever only lets addons set raid markers through "secure" buttons. Until now clicking the marker bar showed
  "action blocked". Now the marker bar (8 markers, right-click removes, Auto, Clear all) and your RaidMaster keys are
  secure buttons – in combat too. Your key bindings stay as they are.
- "Mark adds" and "Announce + markers" of the boss bar show a suggestion in WoW Forever (which marker on which enemy)
  but set nothing themselves. /rm clear points to "Clear all" on the marker bar.
- In combat the marker bar cannot be shown/hidden or moved (game rule); this is done after combat. In combat Auto
  sets the markers of the template one after another.
- Tooltips at the right height for scaled windows.
- Classic Era, TBC and the other clients: everything as before.

WHAT'S NEW IN 3.0.18 – Tooltips no longer cover buttons, errors counted only once
- Tooltips of RaidMaster windows now appear next to the window (right, otherwise left) instead of on top of other
  buttons of the same window.
- Diagnostics: an error was counted twice when another GoldSentinel addon was loaded as well. Fixed.
- Test tool (developer only): new area K "UI in the client" in the test routine (/rm testroutine K): tooltips cover no
  buttons, no overlap with Blizzard or other GoldSentinel windows, everything on screen, button labels not cut off,
  game values plausible, no error loops. The test run (T43) waits until the loot is loaded from the server; the
  double-name case (T142) no longer depends on your data.

WHAT'S NEW IN 3.0.17 – Discord channel names updated in the texts
- The guild bank inventory is now in #gildenbank on Discord (below the rules) – texts on the guild bank page updated.
- Assignments are in the raid's assignment channel (e.g. #einteilung-mc) – texts of the Discord guide updated.
- No other changes.

WHAT'S NEW IN 3.0.16 – Complete test routine, more protection in combat
- Actions with real effects (chat, raid markers, invites, groups, looting, trade, ready check, countdown,
  screenshot, /reload, profession windows, inspect) now all go through one single place in the addon. Nothing changes
  in the game; in test mode nothing real can go out.
- Group search and invites: protected values (WoW Forever in combat) are no longer evaluated.
- Damaged entries in the saved data no longer cause an error when loading.
- Test tool (developer only): the test routine now checks about 100 cases automatically instead of 46, waits for
  timed flows (auction, invites, timers), stops cleanly when combat starts and has a "Reload and report" button.
- Classic Era, TBC, Wrath, Cata and MoP Classic behave exactly as before.

WHAT'S NEW IN 3.0.15 – Safety before the Forever launch
- Whisper replies (bid accepted, !dkp, raid assignments) now all go through one place. In test mode no real
  whispers are sent to test players any more.
- !dkp in WoW Forever: "!dkp Firstname Lastname" and "!dkp Firstname" (if the first name is unique) find the player.
  Classic Era, TBC etc. unchanged (first name only, exact spelling).
- WoW Forever in combat: protected whispers, senders of addon messages and corpse GUIDs while looting no longer cause
  Lua errors – they are skipped.
- Test tool (developer only): no longer replaces game functions (prevented "action blocked" after a self-test); new
  test routine "Test everything" (/rmtest testroutine) with a report for the review.
- RaidMaster Lua errors are counted and sent to the review via the uploader (error text only, no names).

WHAT'S NEW IN 3.0.14 – Fixes before the Forever launch
- Boss bar: if the target's name is protected in combat (WoW Forever, Retail), changing targets no longer causes a
  Lua error – the bar simply does not detect the boss then.
- Loot database: protected boss GUIDs in combat are skipped; the kill is still assigned via the encounter.
- Inspect: if the reply arrives after the pull, protected GUIDs are no longer compared.
- Names: protected names are never processed.
- Classic Era, TBC and the other old versions use exactly the old path again for the ready check, reagents and
  spell names (UnitAura, GetItemCount, GetSpellInfo) as before 3.0.7 – even where the new functions exist.
- Test tool: the self-test checks the boss bar with a protected target name.

WHAT'S NEW IN 3.0.13 – "Read my professions" button: final version
- Contains the revised button (professions sorted alphabetically; if the profession overview returns nothing,
  RaidMaster opens the windows via spells as before). Anyone who already has a 3.0.12 is offered this update.
- No other changes compared to 3.0.12.

WHAT'S NEW IN 3.0.12 – "Read my professions" button on WoW Forever
- On the modern client (WoW Forever, Retail) the button now opens the profession windows through the profession
  overview (C_TradeSkillUI.OpenTradeSkill) – professions are no longer spells in the spellbook there. Each click opens
  the next profession with recipes; Herbalism, Skinning, Fishing and Archaeology are skipped (their skill is saved).
- A profession is reliably marked as read, so the next click no longer reopens the same one.
- Without the new function RaidMaster opens the window via the spell as before.
- The saved format stays the same. Classic Era, TBC, Wrath, Cata and MoP Classic behave exactly as before.

WHAT'S NEW IN 3.0.11 – Reading professions on WoW Forever
- "Read my professions" now uses the modern profession API (C_TradeSkillUI) on WoW Forever and Retail:
  profession, skill, recipes and special reagents. Linked windows of other players are ignored; if the recipe list
  arrives after opening, RaidMaster reads it then.
- Gathering professions and skill levels come from the profession overview (GetProfessions) there.
- The saved format stays the same – the bot, uploader and ProfessionSentinel read everything as before.
- Classic Era, TBC, Wrath, Cata and MoP Classic behave exactly as before.

WHAT'S NEW IN 3.0.10 – GoldSentinelGame version 2
- The shared version detection is now version 2. It takes precedence over early, withdrawn copies that other
  GoldSentinel addons briefly shipped, so several addons together run without Lua errors. Nothing else changes.

WHAT'S NEW IN 3.0.9 – Shared version detection (GoldSentinelGame)
- New: GoldSentinelGame.lua detects the game version the same way in all GoldSentinel addons and tells the two
  API worlds apart: old (Classic Era, TBC, Wrath, Cata, MoP Classic) and modern (WoW Forever and Retail).
  Forever is detected even if Blizzard raises the interface number at launch.
- WoW Forever no longer counts as "Classic Era". Raids, classes and level 60 stay the same.
- Names with first and last name (Forever) use the shared file.
- /gsgame and the diagnostics window show the detected version and API.
- Nothing changes for Classic Era, TBC, Wrath, Cata and MoP Classic.

WHAT'S NEW IN 3.0.8 – Marking in combat (WoW Forever)
- In combat on WoW Forever (and Retail) RaidMaster no longer marks anything automatically: "Mark adds"
  (button, bar, /rm adds, key binding) and "Markers" on the boss bar stop with the hint
  "In combat, please mark with the mouseover keys." – no Lua error. Before the pull everything works as usual.
- The mouseover keys (marker 1–8, next free marker, clear marker) keep working in combat; locked values
  ("secret values") are skipped.
- Classic Era, TBC, Wrath, Cata and MoP Classic behave exactly as before.

WHAT'S NEW IN 3.0.7 – WoW Forever: modern client
WoW Forever looks like Classic but runs on the modern client: in combat, addons no longer see names, GUIDs
and buffs ("secret values") and the combat log is closed to addons. RaidMaster now handles this:
- Ready check: reads flasks and elixirs via the new aura API (C_UnitAuras), Classic Era keeps the old one.
  If the client does not provide buffs, the check shows "buffs not readable" instead of a false "no flask".
  The check only starts out of combat.
- Core Hounds: on WoW Forever the Raid page has an "Announce skinners" button instead of the automatic
  announcement (which needs the combat log). Classic Era stays automatic.
- Template marking: if the client locks enemy data in combat, RaidMaster now says so clearly.
  Before the pull the template works as usual; in combat, target the enemy and press a marker button.
- Spell names and item counts use the modern APIs (C_Spell, C_Item) with a fallback.

WHAT'S NEW IN 3.0.6
- The test tool is now available to the developer only.

WHAT'S NEW IN 3.0.5
- New "Support" button at the top of the RaidMaster window (also in Settings and /rm donate): opens a small window
  with the PayPal link selected – press Ctrl+C and paste it into your browser. It never pops up on its own.

SUPPORT THE ADDON
RaidMaster is free and made in my spare time. If it helps you, you can support it with a small donation – thank you so much!
Donate with PayPal: https://www.paypal.com/ncp/payment/46R68N2BF7BTY
In-game: the Support button in the addon window (or /rm donate).

COMMANDS
  /rm          open the window
  /rm bar      toggle the raid icon bar
  /rm sync     request a data sync
  /rm minimap  show/hide the minimap button (drag it around the minimap with the left mouse button)
  /rm donate   support the addon (PayPal link to copy; also /rm support)
  /rm clear    remove all raid target icons at once (also the "Clear all" button on the icon bar)
  /rm adds     mark all visible adds at once using the boss marker template (enemy nameplates on)
  /rm version  show addon version, game version and language
  /rm reset    reset window positions

Without a master looter (Retail) won items are put on the trade list and handed over by trade.
