# GuildSentinel – the guild tool

**GuildSentinel puts everything about your guild into one window:** who is who (with alts), who is where, who is looking for a group, who is offering portals right now, what's coming up, who levels fastest and who has which raid attunement – plus events, a board, polls, recruitment, professions and guild rules.

Everything works with the mouse, in **every WoW client language** (English, German, French, Spanish, Italian, Portuguese, Russian, Korean, Chinese – your client language on start, switchable under Settings > General), for **Classic Era, WoW Forever and Burning Crusade Classic / Anniversary** – and it connects with all GoldSentinel addons.

> Made for WoW Classic: Classic Era, WoW Forever and TBC Classic / Anniversary (level 70, Outland dungeons, attunements and heroic keys). The more members of your guild use GuildSentinel, the more complete everything gets – data syncs automatically between members on login. Nothing is sent outside your guild (except the optional server-wide group search).

---

## What's new

### Version 0.9.24

- Recruitment ad: a long ad no longer gets cut off by the chat input and then never counts as posted. The ad text is limited to 251 characters (room for "/<channel> "), the counter shows "(n/251)", and the text in the chat input is exactly the one that counts once it appears in the channel. Umlauts and other special characters are never cut in half.
- Developer test routine: T242–T243 new.

### Version 0.9.23

- **Recruitment ad no longer blocked**: WoW Forever blocks addons from writing into chat channels ("action blocked"), even from a click. The button is now "Prepare ad": it puts "/<channel> <text>" into the chat input and you send it with Enter (all game versions). The ad only counts as posted (wait times, "last posted", reminder) once your text appears in the channel.
- Group finder: a guild search can only be closed by the searcher; for "whole server" searches the searcher's name in the data is enough (they arrive passed on through the network).
- Guild profession list: the diagnostic line now says why offline members were or were not shown (already on, no function, combat, guild window open, 5-minute lock …); if the list can no longer be read on the second read, the settings are still put back.
- Developer test routine: T239–T241 new.

### Version 0.9.22

- **Recipes of each member**: on the Professions page, click a member to see WHICH recipes they know for that profession – with a back button, item links and tooltips, and "Request craft" for the selected recipe.
  - **Filter bar by type**, only types that occur, with counts and "All" first: Blacksmithing, Leatherworking, Tailoring by slot (Head, Chest, Hands, Weapons …), Alchemy by Healing/Mana/Rejuvenation/Protection potions, Elixirs, Flasks, Oils, Transmutes, Reagents, Engineering by Explosives, Devices, Scopes, Enchanting by target slot, Cooking/First Aid by Food and Bandages. The bar wraps when space runs out.
  - The type is worked out on your own PC from the item (slot, class) or the recipe name – nothing new has to be sent, so data from older versions works too ("Other" if unknown).
  - On WoW Forever, Blizzard's recipe category is sent along as a new optional field; older versions simply ignore it.
  - The search box also filters a member's recipes; filter and search can be combined.
- Group finder "whole server": group changes and replies to questions now go to the group only; the whisper network gets a search only when it starts and when it ends.
- Developer test routine: T231–T238 new.

### Version 0.9.21

- **GoldSentinelSync 2 (whisper network)**: the shared sync file now also reaches players with GoldSentinel addons outside your guild and group, by whispering through other players who have it (throttled, no chat spam; "no player named … is online" is hidden).
  - **What goes into the network**: only the group finder for the whole server (new search and closing it). Everything else stays inside the guild (professions, events, board, polls, thanks, attunements …), in the group or in a whisper to one player.
  - Group finder: "whole server" is back – your search goes to the guild, your group and the network.
  - Known players of the network are kept across /reload (GuildSentinelDB.gsSync: names, times, version only; stays on your PC).
- **GoldSentinelTest 2**: share error reports with the developer (only with your consent, /gstest).
- Diagnostic log: new line "NETZ …" (no names).
- Developer test routine: T225–T230 new.

### Version 0.9.20

- **Addon messages for all game versions**: GuildSentinel now uses the shared GoldSentinel sync file. It sends only through the guild, your group/raid and whispers – never through a custom chat channel (WoW Forever does not deliver addon messages there). Messages from older GuildSentinel versions of other players are still understood. Players using 0.9.19 or older will no longer receive messages from 0.9.20 – please update.
  - The custom channel "GuildSentinelLFG" is no longer joined (it is left once if you are in it) – one chat channel slot is freed.
  - Group finder: "Guild and group" replaces "whole server" – your search goes to the guild and to your current group or raid. The setting "Searches from the whole server" is gone.
  - Recruitment ads: only Blizzard channels (General, Trade, LocalDefense, LookingForGroup …) can be selected; addon and player channels are hidden.
  - "/gs sync test" shows who answers ("N replies (guild a, group b)"); the settings show the number of players with GuildSentinel in the last hour.
- **Professions**: levelling up a profession with the window open no longer sends to the guild at every skill-up (at most every 5 minutes, and when you close the window); new recipes are still sent right away. The diagnostic log is no longer filled by it.
- Guild profession list with offline members: GuildSentinel now always waits for the game before reading and switching the setting back.
- Blizzard's guild recipes: opening the guild view restarts the queries at most every 10 minutes per profession, and no recipe is asked twice a day.
- Profession data received from other players is checked in depth; broken data can no longer cause an error in tooltips or craft requests.
- Diagnostic log: lines for addon messages (ways, players, sent/received/dropped, channel refused).
- Developer test routine: T214–T224 new; test names are placeholders only.

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
