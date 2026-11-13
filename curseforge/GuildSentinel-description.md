# GuildSentinel – the guild tool

**GuildSentinel puts everything about your guild into one window:** who is who (with alts), who is where, who is looking for a group, who is offering portals right now, what's coming up, who levels fastest and who has which raid attunement – plus events, a board, polls, recruitment, professions and guild rules.

Everything works with the mouse, in **every WoW client language** (English, German, French, Spanish, Italian, Portuguese, Russian, Korean, Chinese – your client language on start, switchable under Settings > General), for **Classic Era, WoW Forever and Burning Crusade Classic / Anniversary** – and it connects with all GoldSentinel addons.

> Made for WoW Classic: Classic Era, WoW Forever and TBC Classic / Anniversary (level 70, Outland dungeons, attunements and heroic keys). The more members of your guild use GuildSentinel, the more complete everything gets – data syncs automatically between members on login. Nothing is sent outside your guild (except the optional server-wide group search).

---

## What's new

### Version 0.9.37

- New: market data network (shared file GoldSentinelMarkt.lua, same in all GoldSentinel addons). When any addon or the player runs a full auction house scan, it is read along in small portions (never in combat, never a scan of its own) – lowest unit price, quantity and number of auctions per item, plus measured sales between two scans. No names: owners, bidders and item names are never read. Shared anonymously with the guild and the GoldSentinel network, own faction only. On by default, no question asked; Settings > "Share market data (anonymous, prices only)" turns it off (then nothing is read or sent). Without the auction house interface (Era/TBC) it stays silent.
- Diagnostic log: lines "MARKT-NETZ" (version, on/off, scans read, sent/received, memory) – no names.
- Fix: Guild management > Invite (and the member menu) now also respects the age block – applicants "declined (age)" cannot be invited from there either.
- Developer tests: T291–T293 (MN4), T289f; offline load test with and without the market file.

### Version 0.9.36

- New (GA1): age question "How old are you?" for applicants. With a minimum age set (Recruitment > texts, default 16, 0 = off) it is ALWAYS asked as the last question, also with your own question list. Answer "17", "I'm 17", "17 years" -> continues normally. Below the minimum age: a friendly whisper ("Thanks for your interest in <guild>! Unfortunately we only accept players aged 16 and over. Have fun in Azeroth!" – text adjustable), status "declined (age)", "Invite to guild" blocked. No number or "soon 16" -> no automatic decline, status "age unclear" for an officer.
- Privacy: the exact age and the answer text are never stored, shared or logged – only "16+" / "under 16" / "unclear".
- New (GA2): in recruitment phase Build-up the default ad says so: "<guild> (faction) is being built up and is looking for players of all classes – relaxed, helpful, raid goal …". New placeholder {phase} ("being built up" / "almost raid-ready" / "raid-ready"). An own ad text without {wanted} or {phase} gets a yellow hint with an "Apply" button (takes the phase's default text). The finished chat text is shown right above the "Prepare ad" button.
- Developer tests: T289a–e (T-GA1a–e), T290a–c (T-GA2a–c); offline flow with ages 17 / 15 / "bald 16".

### Version 0.9.35

- The summary for the uploader and the Discord bot (GuildSentinelDB.raidReady, written on logout) now has the field "vorschlag": the recruitment phase GuildSentinel currently suggests ("build" / "trans" / "raid", same words as "phase"); missing when no suggestion is open or it was put off with "Later". No names. The bot can then post "GuildSentinel suggests phase … – confirm in the game".
- Developer test: T288 (T-RP-V).

### Version 0.9.34

- New: command list while typing. Type /gs (or /guildsentinel) in chat and a list of ALL commands with a short description appears above the input box. Every letter filters ("/gs w" = where, away, ad …), German and English command words both work, commands with an argument show it ("thanks <Name>"), the most used are on top. A mouse click or Tab selects an entry, Enter runs it. The chat input is never written to. Developer commands only for the developer. Settings > "Command list while typing /gs" turns it off.
- The command list and the /gs handler use one and the same command table, so the list always has every command.
- Building block taken unchanged from AHSentinel (CmdHint).
- Developer tests: T282–T287 (T-BL1–T-BL6). TU1 situation catalogue extended by group finder, events, polls and sync and by the situations "channel refuses addon messages", "member with an old version" and "guild changed" (11 functions x 9 situations).

### Version 0.9.33

- Fix: the button in the "Guild action" window (promote, demote, remove, leadership) did nothing when the option "Cast action keybinds on key down" (ActionButtonUseKeyDown) was off – the press set "waiting" and the release then blocked the command, so after 6 seconds it always said "Not carried out". GuildSentinel now only reacts in the phase in which the game runs the command (press or release, depending on the option); one click = exactly one command.
- Developer tests: T281 (T-GA1, both settings) in the test routine; offline test client with the setting on and off.

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
