RaidMaster Uploader – sends the RaidMaster data from the raid leader's PC to the Discord bot
==========================================================================================

1. Install Python 3 (free at python.org; tick "Add Python to PATH" during setup).
2. Put this folder "RaidMasterUploader" somewhere, e.g. into Documents.
3. In Discord, type /uploader (admins only). Put the file uploader_config.json that the bot sends
   you into this folder. NEVER share it – it contains a secret link to your Discord.
4. Double-click uploader.bat and keep the window open.
5. Keep the addons up to date automatically (recommended for officers and everyone using GoldSentinel addons): in this
   folder double-click Addons-automatisch-an.bat, then restart the uploader (close the window, double-click uploader.bat
   again). From then on the uploader installs new versions of the GoldSentinel addons by itself.
6. Start it automatically with Windows: press Windows key + R, type shell:startup and put a
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
  a PRIVATE GitHub repository. It only keeps the latest state and the last state of the last 30 play days (all
  packed, at most 1 GB together); older versions are deleted (no history). If the repository is not private, nothing is delivered.
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

Version 2.3.3 – start after closing, raid readiness, comprehensive tests:
- The uploader no longer wrongly quits with "already running" while GoldSentinel-WoW.bat is syncing or when it is
  restarted within 90 seconds after closing (a lock only counts if its process is still alive and is not the starter).
- GuildSentinel: only the guild bank stock and the raid readiness (raidReady, without names) go to the bot – previously
  the whole file. No members, notes or other guild data anymore.
- At start the uploader checks its saved state ("GRUNDREGEL VERLETZT …" in the window if something is wrong; no names).
- Comprehensive tests (TU1–TU8): situations like no network, missing certificate, wrong token, two computers at once,
  second process; flows; defaults; 1000 random cases with a fixed seed.

Version 2.3.4 – the uploader starts reliably again ("already running" only when true):
- A lock only counts if its process is alive AND really runs uploader.py. Locks without PID, from a finished or a
  different program (reused PID) are taken over – the window then shows "alte Sperre von … entfernt".
- If an old uploader is really still running, the new one asks: "Alte Version … (PID …) beenden und diese starten?
  (J/N)". J stops the old one and starts the new one; without an answer for 60 seconds nothing changes.

Version 2.3.5 – warning for an older version, updating correctly:
- If an OLDER version starts than the one last used on this computer (e.g. because an old ZIP was unpacked over the new
  one), the uploader warns right away in the window and with a Windows notice.

  HOW TO UPDATE (lesson from 13 Nov):
  1. Close ALL uploader windows (also minimized ones) and wait about 10 seconds.
  2. Get the newest version: repository raidmaster download/RaidMasterUploader.zip – or /uploader from the bot, but only
     once the bot has been updated. The window shows the version at the top; if it is older, the uploader warns.
  3. Replace only the program files; keep uploader_config.json, sync_config.json, daten_config.json and
     uploader_state.json.
  4. Double-click uploader.bat. If it says "already running": answer "Alte Version … beenden? (J/N)" with J.

Version 2.3.6 – market data network (MN6):
- The uploader sends the market scans of the GoldSentinel addons ("GSMARKT1|…" from GoldSentinelMarkt) to the bot with
  the package – each scan only once (even if several addons store the same scan), numbers only, no names. Lines in any
  other format are never sent.

Version 2.3.7 – market data: source and notice (MN6b, U3):
- Anonymous source id: the uploader creates a random id once (16 characters, stored in uploader_state.json, never
  derived from names or computer names) and sends it with market scans in the package. The bot can then count PC,
  laptop and different players as separate sources. Old bots ignore the field.
- Market scans larger than 2 MB are skipped and reported once (the bot's limit).
- Market line in an unknown format: not sent, but now reported ONCE in the window, without its content.

Version 2.3.8 – sync no longer gets stuck (UP-S1):
- If the other computer's state arrives empty or broken, the uploader fetches it once more from Discord.
- If it stays unreadable (at least 3 attempts over 30 minutes), it counts as broken: this computer uploads its data
  normally again. Its own version is backed up first. Local files are never overwritten.
- The "not readable" notice appears only once per state instead of every minute.
- New in the status line: "sync blocked since … (reason)" when nothing was uploaded for over an hour despite changes.

Version 2.3.9 – no silent overwrite after a broken state (UP-S1-2):
- If a computer uploads over a broken state of the other computer, it records that in the sync index.
- The other computer then takes nothing over silently: every differing file counts as a conflict. The newer version
  wins, the other one is backed up, and AHSentinel merges both computers' bookkeeping at the next login.
- This happens once per broken state; afterwards sync works as usual.

Version 2.3.10 – "Discord answers 404" (UP-404):
- The uploader now says in words what is missing (the #sync-daten webhook, its index message or the whole channel) and
  what to do: run /uploader in Discord and put the new sync_config.json into the uploader folder on BOTH computers. It is
  picked up immediately, no restart. Your data stays unchanged and is uploaded afterwards.
- On a lasting error it retries every 5 minutes instead of every 5 seconds (network errors: every minute), and the same
  message appears at most every 10 minutes.

Version 2.3.11 – counters after a new sync_config.json (UP-404b):
- If sync_config.json was replaced while an older version was running, the uploader kept counters from the old sync
  location ("rule violated: rev … greater than seq") and would not take over newer states of the other computer for
  that game version. It now adjusts the counters at the first sync and reports it once. Your data stays unchanged.

Version 2.3.12 – same limit as the bot, clearer text on 404:
- A market scan may now be up to 3 MB – exactly what the bot accepts (was 2 MB). GoldSentinelMarkt version 7 keeps all
  scans together below 1.5 MB.
- If the sync webhook is gone (404), the window now says the bot may have been removed from the server or the webhook was
  deleted, and to invite the bot again first if it is gone.

Version 2.3.13 – privacy in the data repo (UP-DS1):
- Applicants (with message) and the ban list (with reasons) from GuildSentinel no longer go to the private data repo. The
  uploader empties them in every guild before uploading GuildSentinel.lua. The file in the game stays unchanged.
- If the file cannot be read safely, it is not delivered at all, with one notice "GuildSentinel-Daten nicht geliefert: …".
- New file svfilter.py – always extract the whole RaidMasterUploader.zip.

Version 2.3.28 – update record and clean exit of the old window (UP-UPD1-c):
- A successful update is now recorded by the new version in the status for the review (the record was lost before).
- After the handover the old window sends nothing more – collected test reports are sent by the new version (no duplicates).

Version 2.3.27 – take over settings files from the Downloads folder (UP-CFG1):
- If you download a new uploader_config.json or sync_config.json from the /uploader Discord message, the uploader window asks:
  "Neue Einstellungsdatei … im Download-Ordner – übernehmen? (j/n)" and shows the channel id old -> new.
  Key j = take over (for uploader_config.json the uploader restarts afterwards). Key n = never offer this file again.
- Protection: only these two file names (also "… (1).json"), only if newer and with different channels, only Discord webhook
  addresses, only from the same bot as before. From uploader_config.json only the channel addresses are taken – SavedVariables
  path, sent pictures and switches stay. The old file is backed up in _update\einstellungen. Nothing is changed in Downloads.
- IMPORTANT: only take over files you just downloaded yourself from YOUR bot's message. If the window asks unexpectedly, press n.
  Switch off: "einstellungen_aus_downloads": false in uploader_config.json. Other downloads folder: "downloads_pfad".
- daten_config.json is never taken over this way.

Version 2.3.26 – old window closes after the update (UP-UPD1-a):
- After "j" the new version starts in a new window; the old window now closes by itself (before it stayed open with "press a
  key"). If the update fails, the old version keeps running in the old window.
- If the new version crashes, ITS window stays open with the message.
- uploader.bat can now be replaced during the update (before: never).
- Note: this applies from the update that 2.3.26 itself performs. Updating from 2.3.24/2.3.25 to 2.3.26 still works the old way
  (the old window stays open once – just close it).

Version 2.3.25 – one line per old lock (UP-MSG2):
- At start after an ended uploader there is only ONE line "alte Sperre von <Version> entfernt" per process.
- Installing by hand: extract the ZIP into the folder ABOVE the uploader folder (the ZIP contains the folder
  RaidMasterUploader). From 2.3.24 on it is easier: press j in the uploader window when asked.

Version 2.3.24 – update at the press of a key (UP-UPD1):
- If a new uploader version is available, the window asks: "Neue Uploader-Version x verfügbar – jetzt installieren? (j/n)".
  Key j = install and restart (new window, close the old one). Key n = do not ask again for this version.
  Without an answer everything keeps running – nothing is installed without j.
- Before installing, the file is checked (only from the GoldSentinel repo, checksum, complete, right version, program files
  only). uploader_config.json, uploader_state.json, sync_config.json, daten_config.json and your data stay untouched. The
  previous version is kept as a backup in _update\alt.
- If the new version does not start within 60 seconds, the old one is restored automatically and keeps running.
- uploader.bat is never replaced during this (it is running); a new uploader.bat comes with the next /uploader.
- This version (2.3.24) has to be installed ONCE by hand (extract the ZIP), afterwards it works with j.

Version 2.3.23 – minimum version instead of "newest" (UP-MIN1):
- Only uploaders BELOW the minimum version are rejected (file RaidMasterUploader/mindestversion.txt in the GoldSentinel repo,
  currently 2.3.20). A newer version without changes to data/format/check/security no longer blocks anyone.
- If your uploader is too old: "Daten nicht angenommen – Uploader x ist zu alt (Mindestversion y), bitte /uploader holen".
- If a newer version exists but you are at or above the minimum: once "neuere Uploader-Version … verfügbar" – your data is
  still accepted.
- IMPORTANT: uploaders 2.3.20 to 2.3.22 still check against "newest" and therefore deliver again only after switching to 2.3.23
  (once; afterwards no longer with every new version).

Version 2.3.22 – clearer messages (UP-MSG1):
- If uploading for the PC/laptop sync fails, the message now names the path: "Abgleich: Hochladen nach Discord #sync-daten
  nicht möglich (…)"; the status line shows "FEHLER Discord #sync-daten: …". When the next attempt works, it says once
  "Abgleich: Discord #sync-daten nachgeholt."
- Notice about other computers with an old uploader in correct singular/plural.

Version 2.3.21 – install new addon versions automatically (UP-AUTO1):
- If you want, the uploader fetches new versions of the GoldSentinel addons (AHSentinel, BuffSentinel, GuildSentinel,
  LevelPilot, ProfessionSentinel, RaidMaster, ThreatSentinel) itself and puts them into the Forever AddOns folder.
- Default: OFF. Switch on: double-click Addons-automatisch-an.bat, then restart the uploader.
  Switch off: Addons-automatisch-aus.bat. Recommended (decision 25.11.): officers and everyone using the GoldSentinel
  addons switch it on – see step 5 above.
- Only addons that are already installed are updated, and only when the new version is higher.
- The only source is the GoldSentinel repo on GitHub; every file is checked before copying (checksum, complete, right
  folder, right version). Your settings and data (WTF/SavedVariables) are never touched, nothing is deleted.
- The window shows e.g. "Addons: AHSentinel 0.65.391 -> 0.65.392 installiert – im Spiel /reload" or
  "– NEUSTART des Spiels nötig" when new files are added.
- Different AddOns folder: add "addons_pfad": "D:\\WoW\\_forever_\\Interface\\AddOns" to uploader_config.json.

Version 2.3.20 – only the newest version delivers (UP-ALT):
- Data from a computer whose uploader is not the newest published version is no longer accepted.
- Newest version = the version of RaidMasterUploader.zip that the bot sends with /uploader. If your uploader is older, it
  delivers nothing and shows "Daten nicht angenommen – Uploader x.y.z ist veraltet (neueste a.b.c), bitte /uploader
  holen". Then get /uploader, extract the whole ZIP and restart the uploader.
- Consequence: after EVERY new uploader version all computers are rejected until they are updated.
- Old uploaders (up to 2.3.19) cannot be changed any more. So they cannot break anything (e.g. cut the daily states to
  7 days), the data repo now uses the branch "sicherung": only a current uploader writes it. What an old uploader puts on
  "main" is never taken over; a current uploader resets "main" within 5 minutes and says so in the window.
- On its first start the current uploader creates the branch "sicherung" (notice in the window).

Version 2.3.19 – everything packed, 30 days (UP-TAGE):
- Every file now goes to the data repo packed as <file>.lua.gz (about a sixth of the size). The same content gives the
  same packed file – without a change there is no new state in the repo.
- The data repo now keeps the last 30 play days (was 7) and may grow up to 1 GB (was 200 MB). If days are dropped, the
  window says which ones and why. stand.json lists the number of days per computer.
- Large files: up to 400 MB unpacked, up to 50 MB packed (was 50 MB unpacked). If a file is too large, its previous
  version stays in the repo.
- If GitHub rejects a file, the uploader retries on its own after 30 minutes (before: only after the next change in game).
- Privacy: packed GuildSentinel files of other computers are filtered too.
- IMPORTANT: update every computer that delivers to the data repo to 2.3.19 – older uploaders cut the daily states back
  to 7 days. The uploader shows a notice if another computer still runs an old uploader.

Version 2.3.18 – deliver files that are too large packed (UP-422b):
- GitHub only accepts a single file through the API up to a certain size ("Sorry, your input was too large to process").
  If a file is too large (e.g. a big AHSentinel.lua), the uploader delivers it packed as <file>.lua.gz (gzip, about a fifth
  of the size); the outdated unpacked version is then removed from the data repo. The uploader remembers this and packs
  the file right away next time; once it is small again, it goes unpacked.
- stand.json marks packed files ("gepackt") with their unpacked size.

Version 2.3.17 – "GitHub antwortet 422" (UP-422):
- If GitHub rejects a delivery, the window now shows WHICH step was rejected (create file, create tree, create commit,
  set branch) and GitHub's text – instead of only "GitHub antwortet 422".
- The uploader recovers by itself: it rebuilds once from the current state of the data repo and sends all its own files
  again. Entries whose file is missing at GitHub are no longer taken over. If GitHub rejects one of its own files, the
  previous version stays there and everything else is delivered. Other computers' files stay unchanged, GuildSentinel stays
  filtered.

Version 2.3.16 – network errors while re-filtering (UP-DS2-a):
- If the connection fails while re-filtering another computer's GuildSentinel.lua, the uploader delivers nothing this time and
  tries again later. The file is no longer dropped permanently; only files that cannot be read safely are left out.

Version 2.3.15 – privacy for older deliveries too (UP-DS2):
- The uploader now filters EVERY GuildSentinel.lua in the data repo, including those of other computers and of earlier days
  (applicants and ban list are emptied). A file that cannot be read safely is dropped. The old state is cleaned after the
  first delivery of a computer with 2.3.15.
- Each computer writes its uploader version to stand.json. If another computer still delivers with an old uploader, a line in
  the window says so: "… still delivers with an old uploader – update the uploader there to 2.3.15."
- Please unpack the new RaidMasterUploader.zip on ALL computers (also the officers').

Version 2.3.14 – even stricter privacy (NP-UP13-1):
- If an entry in GuildSentinel.lua appears twice (e.g. "apps" twice or GuildSentinelDB twice) or the file is nested
  unnaturally deep, the uploader does not deliver it (WoW never writes that). So no applicant and no ban list can slip
  through. Any unexpected error while reading also means: do not deliver.
