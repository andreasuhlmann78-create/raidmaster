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
