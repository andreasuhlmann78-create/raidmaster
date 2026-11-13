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

Version 2.3.0 – data for the review (optional) and sync after every /reload:
- PC/laptop sync now uploads after EVERY /reload and logout (10 seconds after WoW finished writing; at most once per
  minute), not only after closing WoW. The other computer still never takes over while WoW runs there (except at a fresh
  start, see 2.2.0).
- Older versions in #sync-daten are really deleted (message and attachment). If deleting fails, it is retried later.
- An AHSentinel merge block (AHSentinelMerge) not yet read stays on its computer and is not uploaded, so the other
  computer never merges the same data twice. If the computer takes over a newer state, its open block is kept.
- Backed-up AHSentinel states from 2.1.x/2.2.0 (also the old backups in WTF\Account\<account>\_sync_backup) are handed
  to AHSentinel one after another for merging – one per login, identical ones only once.
- If the uploader starts while GoldSentinel-WoW.bat is syncing, it waits briefly.

  DATA FOR THE REVIEW (only needed by the addon developer, otherwise just skip it)
  After every /reload and logout the uploader puts the data of the GoldSentinel addons (AHSentinel, GuildSentinel,
  ProfessionSentinel, LevelPilot, ThreatSentinel, BuffSentinel, RaidMaster – account level only, no other addons) into
  a PRIVATE GitHub repository. It only keeps the latest state and the last state of the last 7 play days; older
  versions are deleted (no history). If the repository is not private, nothing is delivered.
  Set up once:
  1. github.com -> "+" top right -> "New repository". Name: goldsentinel-daten. Choose "Private". "Create repository".
  2. Token: your picture top right -> Settings -> "Developer settings" (bottom left) -> "Personal access tokens" ->
     "Fine-grained tokens" -> "Generate new token". Name GoldSentinel-Daten, expiration e.g. 1 year; Repository
     access "Only select repositories" -> goldsentinel-daten; Repository permissions -> "Contents": "Read and write".
     "Generate token" and copy it (shown only once).
  3. Double-click Daten-Repo-einrichten.bat in the uploader folder, enter the repository (e.g.
     yourname/goldsentinel-daten), paste the token (right-click pastes; it is not shown), Enter. The uploader checks
     that the repository is private and reachable and stores both in daten_config.json (secret, never share).
  4. Restart the uploader. The window then shows "Prüfung: zuletzt geliefert 19:36 (3 Dateien) · Repo 12,3 MB".
  Never paste the token into Discord or a chat. When it expires: create a new token and repeat step 3.

Version 2.3.1 – data delivery: setup problems fixed:
- GitHub certificates: if Windows lacked the root certificate ("kein Netz oder GitHub nicht erreichbar"), the uploader
  now installs certifi once by itself and uses it in addition to the Windows certificate store. A manually set
  SSL_CERT_FILE is no longer needed (may stay). No check is switched off.
- Error messages name the real cause: certificate, address not resolvable, timeout, connection refused/aborted, wrong
  token – never the token itself.
- New: Daten-Verbindung-testen.bat – checks repository and token and shows the result.
- Token input in Daten-Repo-einrichten.bat: asterisks instead of nothing; right-click AND Ctrl+V paste. A token with
  invalid characters is never sent ("Token enthält ungültige Zeichen …").
- A hand-made daten_config.json (Windows Notepad, with BOM or typographic quotes) is read; otherwise the uploader names
  the reason ("token fehlt", "repo falsch", "Zeile 2: kein gültiges JSON").
- PC and laptop in the same data repository: each computer has its own folder (aktuell/<computer>/…,
  tage/<date>/<computer>/…) and only replaces that one. The same account has the same id on both computers
  (konto-xxxxxxxx, computed from the account name; the name itself never appears in the repository).
- The start files call "py" first – the confusing line "Python wurde nicht gefunden …" is gone.

Version 2.3.2 – only ONE uploader, no wrong notice "newer state from <own computer>":
- Cause of the notice (13 Nov): two uploaders ran at the same time on the PC (autostart and a second window). The
  second one did not know the first one's latest upload and took it for a newer state – with its own computer name,
  again after every upload.
- Now only ONE uploader runs per computer, even from different folders. A second start writes "Der Uploader läuft
  schon (PID …, Ordner …)" and does nothing.
- What this computer uploaded itself never counts as a "newer state".
- The notice names the right computer, the time and the game version and appears at most once per new state – not
  again after a restart either.
- Every Windows notice is also written to the uploader window (with PID). At start the window shows version, folder
  and PID.
- Autostart-einrichten.bat replaces old or duplicate uploader entries in autostart by exactly one. If the uploader
  finds several entries it says so at start.
- GoldSentinel-WoW.bat never syncs while an uploader runs (also an older version).
- Data for the review: if PC and laptop deliver at exactly the same time, a delivery only counts as done when it is
  really in the repository; otherwise it retries after 1 minute.

  ONCE AFTER THE UPDATE (per computer):
  1. Close all uploader windows (also minimized ones in the taskbar).
  2. Replace the RaidMasterUploader folder with the new version (keep uploader_config.json, sync_config.json,
     daten_config.json and uploader_state.json).
  3. Double-click Autostart-einrichten.bat (cleans up duplicate entries).
  4. Double-click uploader.bat. The window shows "RaidMaster-Uploader 2.3.2 · Ordner … · PID …".
