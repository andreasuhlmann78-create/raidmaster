RaidMaster Uploader – sends the RaidMaster data from the raid leader's PC to the Discord bot
==========================================================================================

1. Install Python 3 (free at python.org; tick "Add Python to PATH" during setup).
2. Put this folder "RaidMasterUploader" somewhere, e.g. into Documents.
3. In Discord, type /uploader (admins only). Put the file uploader_config.json that the bot sends
   you into this folder. NEVER share it – it contains a secret link to your Discord.
4. Double-click uploader.bat and keep the window open.
5. Start it automatically with Windows: press Windows key + R, type shell:startup and put a
   shortcut to uploader.bat into the folder that opens.

After every /reload or logout, DKP, loot, assignments and specs show up in Discord within a few
seconds. In the game, the page "Discord" (or /rm discord) shows the full step-by-step guide.

UPDATING TO A NEW VERSION
- First back up uploader_config.json from the old folder (e.g. copy it to the desktop).
- REPLACE the old "RaidMasterUploader" folder with the new one – do not unpack into the old folder.
  Otherwise you get RaidMasterUploader\RaidMasterUploader and uploader.bat keeps starting the old version.
- Put uploader_config.json back into the new folder and start uploader.bat.
- On start the window shows the version (e.g. "RaidMaster-Uploader 1.7.0").

New in 1.7.0:
- WoW Forever: on every start and then every 5 minutes the uploader looks for a newer RaidMaster.lua. If you used
  RaidMaster in the Anniversary client or another client before, it switches to the Forever folder automatically and
  says so in the window ("Wechsle zu: …").
- Guild bank with GuildSentinel too: if the bank character is set up in GuildSentinel, the uploader also sends
  GuildSentinel.lua from the same SavedVariables folder – only if it contains a guild bank inventory. It shows up in
  #gildenbank. If the file is somewhere else, set "guildsentinel_path" in uploader_config.json.

New in 1.8.0 – test reports (#testberichte):
- GoldSentinel addons (RaidMaster, ThreatSentinel, BuffSentinel …) store test reports and error messages in their
  SavedVariables. The uploader finds them in the same folder and sends new ones to the channel #testberichte, where the
  addon check reads them so bugs get fixed quickly.
- Only these reports are sent (class, level, game version, language, result) – no names, no DKP, nothing else from
  other addons' SavedVariables.
- This needs a second link: run /uploader in Discord again and put the new uploader_config.json into the folder.
  Without it, the data upload works as before and you only see a hint.

New in 1.9.0 – diagnostic logs and route data (#testberichte):
- AHSentinel and ProfessionSentinel store a diagnostic log on logout ("GSDIAG1"), LevelPilot its route data
  ("GSWEGE1"). After /reload or logout the uploader sends them to #testberichte the same way as the test reports –
  only when they are new.
- Only these strings are sent, nothing else from the SavedVariables. The addons write no names into them.
- No new uploader_config.json needed (the link from 1.8.0 is enough). Replace the whole folder as usual (back up
  uploader_config.json first).

Version 1.9.1:
- Diagnostic logs or route data that are too large (over 512 KB) are reported only once and no longer retried again
  and again.

New in 2.0.0 – fewer messages in #testberichte:
- Only new things: every test report once (also after /reload, relog or restarting the uploader), diagnostic logs
  only when new entries were added, route data once. An error that was already reported only comes as a counter
  ("now 12×").
- Everything new goes into ONE message with ONE attachment (paket-<time>.json.gz).
- At most every 15 minutes: after a /reload the uploader waits and collects; several /reloads in a row give one
  package. When you close the uploader window the rest is sent right away.
- What was already sent is remembered in uploader_state.json (next to the uploader). uploader_config.json stays
  unchanged. Replace the whole folder as usual (back up uploader_config.json first); uploader_state.json may stay.

Version 2.0.1:
- Diagnostic logs or route data that are too large are reported only once again (also after a restart).
- Very large packages in several parts: each part that was sent is remembered right away; if a later part fails, the
  earlier one is not sent again on the next try.

New in 2.1.0 – sync addon data between PC and laptop:
- If you play on two computers, each one has the latest state of ALL addon data (all SavedVariables of your account
  and characters). Nothing to copy by hand.
- Setup (once): run /uploader in Discord. You also get sync_config.json (secret like uploader_config.json). Put both
  files into the uploader folder – on BOTH computers.
- From now on start WoW with GoldSentinel-WoW.bat (in the uploader folder) instead of the WoW shortcut: it fetches the
  latest state from the other computer first and then starts WoW.
- Keep uploader.bat running as usual: after WoW is closed (and 2 minutes of quiet) it uploads the state.
- If WoW is running and the other computer has newer data: nothing is overwritten, you get a notice.
- Played on both without syncing in between: per file the newer one wins, the other stays as a backup in
  _sync_backup in the uploader folder and is reported. AHSentinel additionally gets the older version to merge.
- Before taking over anything the uploader backs up your files in _sync_backup (last 5 backups kept).
- Stored only in your private Discord channel #sync-daten (only you and the bot see it), at most 10 versions.

Version 2.1.1:
- Sync now covers ALL game versions and accounts on the computer (e.g. _forever_ and _anniversary_), not only the
  folder with RaidMaster.lua. What does not exist on the other computer is not created there, but not dropped either.
- Backups (_sync_backup) are now kept in the uploader folder, no longer in the WoW folder.
- GoldSentinel-WoW.bat starts WoW Forever (_forever_) if present.
- New: Autostart-einrichten.bat – double-click once and the uploader starts with every login (minimised).

Version 2.2.0 – sync right away, no clicks:
- The ONLY step per computer: double-click Autostart-einrichten.bat once (plus uploader_config.json and
  sync_config.json from /uploader in the folder, as before). After that everything runs by itself while the uploader
  runs. GoldSentinel-WoW.bat is no longer needed (may stay; if the uploader runs, it only starts WoW).
- Upload at most 15 seconds after WoW is closed. After logging out to the character screen (WoW still open), after
  1 minute of quiet as well.
- The other computer checks every 30 seconds and fetches a new state right away when WoW is not running there.
- Just start WoW normally: if the uploader sees a fresh WoW start and the other computer has a newer state, it takes it
  over while you are still on the login/character screen (WoW reads addon data only when you enter the world).
  Until this is proven you get a notice "please don't log in yet, taking over …" and then "done – you can log in".
  RaidMaster 3.0.23+ provides the proof; after 2 proofs there is no notice anymore.
- Only what changed is uploaded (one package per game version and account). Game versions unchanged for 14 days are
  uploaded once; Retail only if you play there.
- Who wins if you played on both: no longer only by file time. Both computers' clocks are compared with Discord; if both
  changes are less than 10 minutes apart it counts as a conflict. Same for the very first sync. The other version stays
  in _sync_backup for 30 days; AHSentinel ALWAYS gets it to merge.
  Merge block in AHSentinel.lua: AHSentinelMerge = { v = 1, von = <computer>, zeit = <unix time>, grund = "konflikt",
  db = <other AHSentinelDB> }. AHSentinelDB itself is never changed.
- Once: if _sync_backup holds an AHSentinel state from 2.1.x that was never merged, AHSentinel gets it to merge at the
  next login.
- The uploader and GoldSentinel-WoW.bat no longer overwrite each other's state (only one syncs).
- Less load: files are only read again when they changed. If Discord says "too many requests", the uploader waits as
  long as asked.
- Diagnostic logs that are too large are reported only once, even when written again with a new time.
