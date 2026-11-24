# GuildSentinel – the guild tool

**GuildSentinel puts everything about your guild into one window:** who is who (with alts), who is where, who is looking for a group, who is offering portals right now, what's coming up, who levels fastest and who has which raid attunement – plus events, a board, polls, recruitment, professions and guild rules.

Everything works with the mouse, in **every WoW client language** (English, German, French, Spanish, Italian, Portuguese, Russian, Korean, Chinese – your client language on start, switchable under Settings > General), for **Classic Era, WoW Forever and Burning Crusade Classic / Anniversary** – and it connects with all GoldSentinel addons.

> Made for WoW Classic: Classic Era, WoW Forever and TBC Classic / Anniversary (level 70, Outland dungeons, attunements and heroic keys). The more members of your guild use GuildSentinel, the more complete everything gets – data syncs automatically between members on login. Nothing is sent outside your guild (except the optional server-wide group search).

---

## What's new

### Version 0.9.61

- Window gets out of the way: if the GuildSentinel window covers another window when it opens (LevelPilot, AHSentinel, ProfessionSentinel, RaidMaster, ThreatSentinel, BuffSentinel, guild, friends or profession window), it docks next to it – right, left, below or above, the shortest way, fully on screen. If it fits nowhere, it shrinks as little as needed (at most to 95 %; at 16:9 (UI 1365 × 768 points) with LevelPilot in its default spot 99.4 %). If such a window opens later, GuildSentinel moves then. Your saved position stays; the next time you open it without the other window, GuildSentinel is back there.
- Group finder: the "Elite quest (LevelPilot)" button is inside the window again (it stuck out on the right); with LevelPilot the note field is narrow enough for both.
- Readability: the Shaman class colour is a little lighter on the dark window (was 3.7:1, now at least 4.6:1) – names in lists, "Where", composition, progress, leadership, rules. All other class colours stay exactly as in the game.
- Board (offers/wants) and crafting requests: an item's tooltip shows quantity and price (or OBO) right in the first line after the name, the game's details follow below.
- Performance: the "Online times" page builds its overview without a new table per measurement (test setup 1,196 KB → 42 KB per build) and only once per display (twice before).
- Shared file GoldSentinelTest 3 (a check returning nil counts as an error; texts are never cut in the middle of a character).
- For the developer: the test routine names the exact place of the longest portions ("in T…" = check running, "nach T…" = between checks) and whether a garbage collection ran in that frame; T21/T22 open the pages in portions of their own; the bank checks can pause in between.

### Version 0.9.60

- Raid readiness without estimates: "raid-ready in n weeks (from x players, y days measured)" instead of "at the current pace in ~n weeks". With fewer than 3 players with a measured pace or less than 7 days of measurement it says "not enough data yet" (no week count in the Discord report either). The pace is now divided by the days actually measured (at most 14; before always by 14).
- Level gain: the level a member joins with no longer counts as a level-up (new members had one level too many – ranking "levels in the last 7 days" and raid readiness).
- "First to max level": if the date only comes from the member list (no event of its own), it says "by <day> at the latest" instead of an exact time.
- Applicant tooltip: "First seen" now sits right under the name (before at the bottom).
- The log entry for merging guild data lists the entries per old key ("before 802 = 479 + 323").
- For the developer: the test routine checks L5 (main number on top in every tooltip with numbers, T317) instead of skipping it.

### Version 0.9.59

- Guild data without realm: on WoW Forever the game reports a different home realm per character – the same guild was stored under several keys (members, log, administration split). Now "faction + guild" is used. Old entries are merged once on login: nothing twice, earlier join time, newer states win; the old data stays as a backup (guildsOld), counts before/after in the log (/gs protokoll, line GILDE). "My week" shows the characters of all home realms.
- Members page: built in a frame of its own after the window opens, the first selection only fills it; the list's numbers are computed once per selection (before up to three times). A slow selection lists its parts in the log (read/filter/sort, rows, numbers, details).
- Recruitment: instead of the white block "Placeholders: {gilde} {fraktion} …" a small "Placeholders (?)" button – its tooltip lists every placeholder with its meaning (ad, automatic reply, welcome, rejection). "Leave empty = default text" is shown in grey in the empty ad field.
- Readability: the selected row of a list now has an accent stripe on the left and a fainter fill (grey and red text on it was too weak); brighter version number in the title bar; every column has a header.
- "Who's free": "Flag as free" and "No longer free" have their own row (they stuck out of the window in 6 of 10 languages); the rejection text has its hint and button below the field.
- Developer commands (sync test, protokoll, clienttest, debug) appear in help and the command list only in developer mode.
- Shared files: GoldSentinelSync 3 and GoldSentinelTakt 3.
- For the developer: the test routine first measures the environment for 10 s (location, ping, frames/s; line "Umgebung" in the report), also compares the shared data (sync address book, sync and market storage) before/after the run (SHARED) and checks readability L1–L8 (T311–T318) and controls inside the window (T319). Found and fixed: T293 created an empty slot in the real market storage.

### Version 0.9.58

- Performance: from 100 members GuildSentinel reads the member list as a task of the shared scheduler – only the reading in one go, the notes in portions, the comparison at the end. Before, everything ran in one frame (16 ms with 500 members in game, every 30 seconds). During the portions the main from the note stays (no flicker).
- Performance: notes like "Alt of X" whose main is no longer in the guild went through the whole list for every alt on every read. The result is now remembered per name (rebuilt with 500 members: 216 ms → 5 ms).
- Title bar on the right in the window's style: flat close X (instead of the Blizzard X), "Support" as a small coin icon with tooltip (instead of a grey button), guild info with spacing – all the same height and on one line.
- For the developer: the test routine checks the shared sync address book for test names (T308), the title bar (T309) and that every player feature is reachable without developer mode (T310); T138 measures the median of 3 runs and the longest frame in portions.

### Version 0.9.57

- New options modelled on AHSentinel (Settings > Options): sections on the left (General, Chat & tooltip, Announcements, Group finder, Recruitment, Data & sync, Features: community, Features: guild & raid, Leadership), only the options of the chosen section on the right in one column, no scrolling. A search box on top searches all sections (e.g. "sound"). Each row: a short label, an "on"/"off" button (or a row of buttons) on the right, the explanation in the tooltip. "Default" per section, rarely used options under "More".
- Every option appears exactly once. Switches that sit next to their own text (automatic reply, welcome, application questions, minimum age, advertising channels, group finder role, promotion, composition) stay there – in the options a link jumps right to them. The advertising reminder and "Delete old applications" moved from the Recruitment page into the options; an "Options" button there opens the Recruitment section (likewise on the Group finder page).
- Clicking a feature that is turned off opens its section in the options.
- All saved settings stay valid (same fields as before).
- For the developer: checklist point "OPT options on screen" (the right-click menu point, already done in game, was removed for it); the test routine checks every option (T307a–e) and reports which old game functions the client has (T306).

*Older versions: see the changelog of each file in the **Files** tab.*

---

## 🏠 Overview

- **Guild health at a glance**: active players vs. last month, joins and departures, who will soon be inactive, open applicants, probations due, weekly goal, next event
- **For you**: events without your reply, open polls, crafting requests you can fulfil, open questions

## 🛡 Leadership (officers only)

- **Guild management window**: button "Management (GuildSentinel)" next to the guild window (J) – invite, promote, demote, remove with confirmation; hand over leadership only as Guild Master and only with a password
- **Probation**: online days, events attended and thanks since joining – then "Promote" or "Talk"
- **Suggest mentor** based on matching online times
- **Departures with reason**, **officer notes with history** (shared only between officers), **rank rights**
- **Guild name**: the guild master can set the name GuildSentinel shows to everyone (ad, chronicle, rules, header) – empty means the name from the game
- **Bulk actions**: remove inactive players by rule or promote several suggestions at once – always with a checklist first, one step per click
- **Import from Guild Roster Manager (GRM)**: alts, join dates and notes, with a preview

## 🗓 My week

- Saved raids and heroics per character with time left, dailies done today
- **Raid prep**: attunements, flasks, elixirs, potions, class reagents, durability, resistances

## 👥 Members

- List with level, class, rank, zone or "last online" – search, filter, show or hide alts
- **Alts** are detected from the public note ("Alt: Testa", "Alt of Testa" – on WoW Forever also with first and last name) or set by hand
- **Who's where**: all online members grouped by zone – for meeting up, summoning and world bosses
- **History**: who joined, left, got promoted or reached level 60
- **Inactive list** (14/30/60/90 days) – only if none of the player's alts were online either
- **Report absence** (`/gs away 14 vacation`): absent players don't show up as inactive and aren't suggested for promotion
- **Online times**: on which days and hours most members are online – perfect for picking raid times
- **Promotion suggestions** based on your own rules (days in guild, level, online days) – promote with one click, always by hand
- **Composition**: classes and roles per level range compared with a 40-player raid target – what's missing?
- **Mentors** for new members
- **Guild chat with main names**: when an alt writes, the main is shown in front – also on "has come online"
- **Write alts into the public note** with one click – visible to everyone, even without the addon
- **Player tooltip**: rank, main or alts, role, professions and attunements of guild members
- Export the member list as text or CSV

## 🔎 Group finder

- Pick a dungeon or activity, tick the roles you need, start the search
- **Guild only or the whole server** – through the whisper network of the GoldSentinel addons your search also reaches players of other guilds
- Players whose level and role fit get a notice in chat (optionally with sound), with the zone of the searcher
- On WoW Forever: all new dungeons and the raids Barrow Deeps, Hyjal Summit and Onyxia's Lair
- "I'll join" – one click, and the searcher invites you with one click; your **item level** goes along
- **Who's free**: flag yourself as free for dungeon, raid, quest group or PvP – inside instances you automatically show as busy

## 📅 Guild events

- PvP night, guild meeting, dungeon night, world boss … – anyone can create events
- Reply **yes / maybe / no** with one click, reminder with sound 15 minutes before
- With RaidMaster installed, the next raid from its sign-up is shown for information

## 📌 Board

- **Services**: mages offer portals and food, warlocks summons and soulstones, rogues lockpicking, enchanters their enchants – detected from your spellbook
- **Offers / wanted between members**: post items with price and note; matching offers and requests notify both players
- Not a guild bank – trading happens directly between players
- **Loot wishes**: who needs what from which dungeon – shown in the group finder
- **Ask the guild**: "Who knows …?" – the most helpful answer earns a thanks point

## 🏁 Progress & goals

- **Leveling race** with guild chat announcements (level 10, 20, 30, 40 – mount!, 50, 60 and the first member to reach 60)
- **Raid attunements and dungeon keys**: Upper Blackrock Spire, Molten Core, Onyxia's Lair, Blackwing Lair, Shadowforge Key, Skeleton Key, Crescent Key, Key to the City
- **Weekly goal**: "150 levels as a guild this week" with progress bar and announcement
- **Guild milestones**: 5 members at 60, 25 players, all tanks attuned, first kills … – each celebrated once
- **Thanks**: say thanks for help, with a ranking of the most helpful members
- **Guild achievements** with progress bars, **chronicle** (export for Discord) and a **weekly recap** in guild chat

## 🗳 Polls

- Officers ask, everyone votes with one click, live results
- One vote per player (alts count for their main), secret polls possible

## 📣 Recruitment

- Ad text with placeholders and preview – each click puts it into the chat input for the next channel, you send it with Enter
- **The ad knows what's missing**: `{wanted}` becomes e.g. "Looking for: Shamans, Tanks, Warlocks.", `{crafters}` lists missing professions
- Collect applicants from whispers, reply automatically and ask **application questions**
- Welcome new members, celebrate anniversaries
- **Guild rules**: everyone sees them on login and accepts with one click
- Only one player announces, even if many have the addon – no double spam

## 🔨 Professions

- Guild-wide directory: who can craft what – search, "ask to craft" with one click
- Skill levels are read automatically – where the game provides the guild profession list, for **every member, even without the addon**
- **Recipes of each member**: click a member to see which recipes they know, with a filter bar by type (Blacksmithing: Head, Chest, Hands, Weapons …; Alchemy: Elixirs, Healing potions, Transmutes …; Enchanting by slot)
- **Fully automatic**: your own professions are sent after logging in, new recipes the moment you learn them, the guild profession list is read with offline members too – no button, never in combat
- Reads the classic profession window (Classic Era, TBC) and the new profession window of **WoW Forever**
- **Requests**: crafters get a notice and take the request with one click
- **Gaps**: important raid recipes nobody in the guild can craft
- **Cooldowns**: transmutes, mooncloth, salt shaker – who is ready right now?

## 🤝 Works with all GoldSentinel addons (all optional)

| Addon | What GuildSentinel uses |
|---|---|
| **RaidMaster** | professions, alts, roles from talent specs, next raid in events, first kills as milestones; optional **bank character**: GuildSentinel reads bank, mail and guild bank stock, and the RaidMaster uploader and bot show it on Discord |
| **AHSentinel** (formerly AH Analyzer Pro) | market value on the board and for profession cooldowns |
| **BuffSentinel** | detects your class services for the board |
| **ThreatSentinel** | your role (tank stance / bear form) for composition and group finder |
| **LevelPilot** | elite quests from your quest log as a group search, players with the same quest |

The **Addons** page shows who in your guild uses which addon and who has an old version.

## ⚙ Usage

- Minimap button: left-click opens the window, right-click posts the guild ad
- **Without a guild** the overview shows a hint – the guild pages appear as soon as you join a guild; My week, Addons and Settings work without one
- Language: always the language of your game client
- **Features** can be turned on and off individually (Settings > Features)
- Commands (optional): `/gs`, `/gs group`, `/gs events`, `/gs board`, `/gs where`, `/gs thanks <name>`, `/gs away <days>`, `/gs poll`, `/gs progress`, `/gs attune`, `/gs rules`, `/gs find <recipe>`, `/gs ad`, `/gs donate`

## 📦 Installation

Install with the CurseForge app, or unzip and copy the folder **GuildSentinel** into `Interface/AddOns`. When updating, your saved data is kept.

---

Questions, bugs or ideas? Please leave a comment – ideally with a short description of what happened.

© GoldSentinel – All rights reserved.
