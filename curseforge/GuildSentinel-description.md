# GuildSentinel – the guild tool

**GuildSentinel puts everything about your guild into one window:** who is who (with alts), who is where, who is looking for a group, who is offering portals right now, what's coming up, who levels fastest and who has which raid attunement – plus events, a board, polls, recruitment, professions and guild rules.

Everything works with the mouse, in **every WoW client language** (English, German, French, Spanish, Italian, Portuguese, Russian, Korean, Chinese – your client language on start, switchable under Settings > General), for **Classic Era, WoW Forever and Burning Crusade Classic / Anniversary** – and it connects with all GoldSentinel addons.

> Made for WoW Classic: Classic Era, WoW Forever and TBC Classic / Anniversary (level 70, Outland dungeons, attunements and heroic keys). The more members of your guild use GuildSentinel, the more complete everything gets – data syncs automatically between members on login. Nothing is sent outside your guild (except the optional server-wide group search).

---

## What's new

### Version 0.9.16

- **Professions of all members, automatically**: where the game itself knows the guild's professions (guild profession list), GuildSentinel now reads the skill levels of every member – also of members without GuildSentinel. Recipes still come only from players with GuildSentinel (or RaidMaster) who have opened their profession window once; their own data always wins over the guild list.
- **New members**: whoever joins the guild while online now shares their professions right away instead of at the next login.

### Version 0.9.15

- **Diagnostic log**: GuildSentinel now records problems that only happen in the real game (slow pages, blocked actions with the calling place, error loops – never player, guild or realm names). Open it with `/gs protokoll` to copy it; after a logout or /reload it is also stored for the RaidMaster uploader, which sends it to the developer.
- Developer test routine: T188 (diagnostic log) and T189 (in the game).

### Version 0.9.14

Fixes from the in-game test run on WoW Forever launch night:
- **Big guilds**: the Overview and Leadership pages no longer stutter with hundreds of members (main/alt lookups are now done once per page build – about 25× faster with 500 members).
- **Professions button (WoW Forever)**: no more "action blocked" message. If the profession window does not open, GuildSentinel now asks you to open it yourself once instead of calling a protected function.
- **Achievements/Chronicle**: damaged profession data no longer breaks the page.
- **Event announcement** in test mode also works for characters without a guild (only "[Test]" in your chat, nothing is sent).
- Developer test routine: new area K checks the interface in the real client (tooltips covering buttons, overlapping windows, windows off screen, cut-off texts, plausible game values, error loops); clearer results for first/last names and slow pages.

### Version 0.9.13

- **Language selectable for everyone**: Settings > General > "Language". On start GuildSentinel still uses the language of your game client; you can switch to German, English, French, Spanish (Spain/Mexico), Italian or Portuguese on any client (Russian, Korean and Chinese on a client in that language). GuildSentinel reloads after the change; "Same as the game client" goes back. Replaces the developer-only switch from 0.9.12.

### Version 0.9.12

- Developer only: under Settings > Test mode the language can be switched between German, English and the game client's language (for screenshots); GuildSentinel reloads after the change. Nothing changes for players – GuildSentinel always uses the language of the game client.

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
- Skill levels are read automatically – where the game provides the guild profession list, for **every member, even without the addon**
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
