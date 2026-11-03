# GuildSentinel – the guild tool

**GuildSentinel puts everything about your guild into one window:** who is who (with alts), who is where, who is looking for a group, who is offering portals right now, what's coming up, who levels fastest and who has which raid attunement – plus events, a board, polls, recruitment, professions and guild rules.

Everything works with the mouse, in **every WoW client language** (English, German, French, Spanish, Italian, Portuguese, Russian, Korean, Chinese), for **Classic Era, WoW Forever and Burning Crusade Classic / Anniversary** – and it connects with all GoldSentinel addons.

> Made for WoW Classic: Classic Era, WoW Forever and TBC Classic / Anniversary (level 70, Outland dungeons, attunements and heroic keys). The more members of your guild use GuildSentinel, the more complete everything gets – data syncs automatically between members on login. Nothing is sent outside your guild (except the optional server-wide group search).

---

## What's new

### Version 0.9.11

- **Bank character: stock to Discord** (optional, off by default): tick "Bank character (stock to Discord)" under Settings > General on your guild's bank character. Opening the bank, the mailbox or – where the game has one – the guild bank then reads bags, bank, mail attachments and guild bank tabs (read only, never in combat, in small steps). The RaidMaster uploader sends the stock with its next upload, and the RaidMaster bot shows it in #gildenbank and with /bank. Guilds without the RaidMaster bot notice nothing.
- **Alt notes with first and last names** (WoW Forever) on Korean and Chinese clients, where the name comes before the label ("Rokan Steinwacht의 부캐릭터"), are recognised again.
- **Changing the main** now removes the old alt label completely – with first and last name and in the client language ("Alt: First Last", "Reroll de …") – instead of leaving parts of it in the note.
- **Event sync**: one damaged entry no longer discards the other events of the same sync message.
- All game functions GuildSentinel needs are now chosen in one place (API.lua, modern API first, old one as fallback). Nothing changes for players.
- Developer test routine: real sends now count as an error in the report (T82), every action with consequences is checked to go through one place (T174), new cases for export, event announcements, first/last names and the bank character, and the cases that previously needed a replaced game function now run in the game too.

### Version 0.9.10

- **Alt notes in your client language**: notes that GuildSentinel writes itself ("Reroll de …", "… 的分身" and so on) are recognised again on French, Spanish, Italian, Portuguese, Korean and Chinese clients. Where the label would not fit into the short guild note (Russian), GuildSentinel writes the short form "Alt: Name".
- **AHSentinel** (formerly AH Analyzer Pro) is recognised under its new folder name (Addons page, market values).
- **Applicant whispers in combat** (WoW Forever): more than 30 whispers during one fight are now counted in the notice too instead of being dropped silently.
- More robust against damaged data: malformed event sync messages and broken event or thanks entries no longer cause errors.
- Test mode (developer only): no longer joins or leaves the server channel, sends nothing delayed after "Stop test mode" and leaves the real settings (last ad, free status, My week) untouched.
- New for the developer: `/gs testroutine` (button "Test everything" under Settings > Test mode) checks every feature and saves a report for the GoldSentinel review; the diagnosis shows the error counter. Nothing changes for players.

### Version 0.9.9

Fixes from the review:
- **Officer rights**: players who may only read officer notes no longer count as officers.
- **Applicant whispers in combat** (WoW Forever): if a message stays protected after combat, GuildSentinel reports once how many could not be read instead of losing them silently.
- **Player tooltip**: the combat lock applies to every modern client (WoW Forever, Retail).
- Absence and thanks messages from other players are only accepted when the sender matches exactly.

### Version 0.9.8

- Shared game-version detection (GoldSentinelGame.lua) updated to version 2: it also wins over early, withdrawn copies that other GoldSentinel addons briefly shipped, so loading several GoldSentinel addons together causes no errors. Nothing changes for players.

### Version 0.9.7

- Uses the shared game-version detection of all GoldSentinel addons (GoldSentinelGame.lua): Classic Era, WoW Forever and TBC are detected the same way everywhere, with the shared secret-value guard and first/last name comparison. `/gsgame` shows what was detected. Nothing changes for players.

*Older versions: see the changelog of each file in the **Files** tab.*

---

## 🏠 Overview

- **Guild health at a glance**: active players vs. last month, joins and departures, who will soon be inactive, open applicants, probations due, weekly goal, next event
- **For you**: events without your reply, open polls, crafting requests you can fulfil, open questions

## 🛡 Leadership (officers only)

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
- **Alts** are detected from the public note ("Alt: Rokan", "Alt of Rokan" – on WoW Forever also with first and last name) or set by hand
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
- **Guild only or the whole server** – everyone with GuildSentinel sees your search, other guilds too
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

- Ad text with placeholders and preview – each click posts into the next channel
- **The ad knows what's missing**: `{wanted}` becomes e.g. "Looking for: Shamans, Tanks, Warlocks.", `{crafters}` lists missing professions
- Collect applicants from whispers, reply automatically and ask **application questions**
- Welcome new members, celebrate anniversaries
- **Guild rules**: everyone sees them on login and accepts with one click
- Only one player announces, even if many have the addon – no double spam

## 🔨 Professions

- Guild-wide directory: who can craft what – search, "ask to craft" with one click
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
