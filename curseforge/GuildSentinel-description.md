# GuildSentinel – the guild tool

**GuildSentinel puts everything about your guild into one window:** who is who (with alts), who is where, who is looking for a group, who is offering portals right now, what's coming up, who levels fastest and who has which raid attunement – plus events, a board, polls, recruitment, professions and guild rules.

Everything works with the mouse, in **every WoW client language** (English, German, French, Spanish, Italian, Portuguese, Russian, Korean, Chinese – your client language on start, switchable under Settings > General), for **Classic Era, WoW Forever and Burning Crusade Classic / Anniversary** – and it connects with all GoldSentinel addons.

> Made for WoW Classic: Classic Era, WoW Forever and TBC Classic / Anniversary (level 70, Outland dungeons, attunements and heroic keys). The more members of your guild use GuildSentinel, the more complete everything gets – data syncs automatically between members on login. Nothing is sent outside your guild (except the optional server-wide group search).

---

## What's new

### Version 0.9.31

- New: recruitment in phases (Members > Line-up). Build-up (default for every guild): {wanted} in the ad becomes "players of all classes" – the line-up is not used. Transition: "players of all classes, especially <up to 3 gaps>". Raid: the gaps of the line-up, as before. Your own ad texts stay; {wanted} follows the phase.
- The line-up targets are never deleted, converted or overwritten; the page says "the targets above apply from phase Raid". Only the Guild Master and officers can change them, every change is logged with name and time (last 50, in the game only).
- Raid readiness for a target raid (Onyxia's Lair 40, Molten Core 40, Barrow Deeps 10, Hyjal Summit 20 and more; TBC: Karazhan 10, Gruul 25 …): active mains (level ≥ line-up minimum and online in the last 14 days; alts only with "count alts") against raid size, plus tanks and healers (from the line-up, scaled to the raid size; otherwise size/10 and size/5). Shown on Line-up, Recruitment and Overview: "Raid-ready (Onyxia's Lair): 23 of 40 active at level 55+ · Tanks 2/4 · Healers 5/10 · Phase Build-up", with an estimate from the levelling race ("at the current pace in ~x weeks", or "still measuring" with less than 7 days of data).
- From 60 % officers get the suggestion "Transition", from 100 % "Raid" (in the window and once in officer chat, said by one only) with "Confirm" / "Later". Nothing switches automatically. Back only after 7 days below the threshold of the current phase.
- Chronicle milestone "Guild is raid-ready (<raid>)", optional guild chat announcement (Settings, on by default, said by one only).
- On logout a summary without names is stored for the uploader and the Discord bot (GuildSentinelDB.raidReady).
- Developer test routine: T261–T269 (T-RP1–T-RP9) new; T244/T246 now run in phase Raid.

### Version 0.9.30

- New: right-click menu on members (Members list, inactive list, Who is where, Applicants, Leadership lists): Whisper, Invite to group, Promote, Demote, Set rank …, Assign alt …, Edit note, Edit officer note, Enter absence, Say thanks, Assign mentor …, Remove from guild (with confirmation), Transfer guild leadership (Guild Master only, password protected). Entries your rank may not use are shown in grey with the reason; in combat "not in combat".
- Protected guild actions are never called directly any more (lesson from the invite fix in 0.9.29): promote, demote, remove and leadership transfer – from the menu, the Guild Management window, the promotion suggestions and the bulk actions – open the new "Guild action" window. You click its button and Blizzard's own command (/gpromote, /gdemote, /gremove, /gleader) carries it out. Names with spaces work.
- Set rank: every step is its own click ("Promote – 2 steps left to Officer"), never above your own rank and never to Guild Master.
- A step counts as done only when the game confirms it (system message or new rank in the roster); without confirmation after 6 seconds: "Not carried out" and the step can be repeated. Each confirmed rank change is kept in the rank history (who, whom, from -> to, time).
- Multi-select: Shift/Ctrl-click in the member list, then right-click: promote or demote all of them – one click per member ("3 of 5 done").
- Promotion: new option "Suggest the main's rank for alts" (only a suggestion, carried out step by step).
- Leadership > Rank rights: button "Edit ranks in the game" opens Blizzard's rank window.
- Developer test routine: T254–T260 (menu by rights, no protected call, name with spaces, rank steps, confirmation, alt suggestion, multi-select) new; T64, T174, T194, T195, T213 adapted. The offline test client now rejects protected guild functions like WoW Forever.

### Version 0.9.29

- Fix (WoW Forever): "Invite to guild" (Recruitment > Applicants and Guild management) no longer triggers "GuildSentinel has been blocked from an action only available to the Blizzard UI". The game forbids addons to invite into the guild directly, even on a mouse click. Now "/ginvite <name>" is put into the chat input and you press Enter – Blizzard's own command sends the invite. Names with spaces work as they are.
- The applicant only shows as "invited" once the game confirms the invite ("You have invited X to join your guild."), no longer right after the click.
- Your own ad texts with {tag} but without a dash: without a tag or Discord link, "(Tag {tag})" is removed with its brackets and a sentence of its own with {tag} is removed completely; otherwise only {tag} is emptied.
- Developer test routine: T253 (invite only via the chat input, status only after the confirmation) new; T174, T194 and T251 extended.

### Version 0.9.28

- Recruitment page: new "Suggestion 2" button – a second ad text that names your Discord server tag ("… Discord: <link> – you'll know us by the tag XY."). The default ad text is unchanged.
- New field "Server tag" next to the Discord link and new placeholder {tag}. Without a tag or without a Discord link the tag part is left out completely.
- Tip below the Discord link: use a permanent invite (never expires, unlimited uses); whoever clicks it sees the guild's server profile before joining.
- Developer test routine: T251 (suggestion 2 with/without link and tag, DE/EN/RU) and T252 (invite tip) new.

### Version 0.9.27

- Russian recruitment ad: "Пишите мне" now starts with a capital letter, also when the Discord part is left out.
- Developer test routine: T250 also checks the old default text in the client's language.

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
