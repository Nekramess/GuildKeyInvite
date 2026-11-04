# CurseForge listing: Guild Key Invite

Everything needed to create the project and upload the first file. Copy each block as written.
Prepared 4 Nov 2026 for addon version 0.1.0 (Interface 16001).

## 1. Name check (done 4 Nov 2026)

- Searched CurseForge (via web search, 4 queries) for "Guild Key Invite", "GuildKeyInvite", "ginvite", guild auto-invite and whisper-keyword addons: **no addon with this exact name or slug turned up.** I could not open `curseforge.com/wow/addons/guild-key-invite` directly (the session's fetch allowlist blocked it), so the final check is CurseForge itself: it refuses a taken name/slug when you create the project.
- Similar names that exist (all different names): Fast Guild Invite - Revived, Ultimate Guild Invite, Auto Guild Invite, Lazy Guild Invite, Guild Quick Invite, EasyGuildInvite, Simple Guild Invite, Guild Invite Repair, Invite On Whisper (by Numy), ForeverRecruiter (by iAmDerpDiggler).
- Same job, different name: **Invite On Whisper** lists a Forever version, invites on whispered words (guild defaults `ginv`, `guildinv`, `ginvite`) and asks you to confirm guild invites in a popup. ForeverRecruiter scans for unguilded players and also invites people who reply. Guild Key Invite is a small single-purpose alternative: one key word, off by default, no popup (the invite goes out on your next key press or click), optional welcome whisper.
- Folder / `.toc` / zip name: `GuildKeyInvite` (display name "Guild Key Invite").

## 2. Project settings

| Field | Value |
|---|---|
| Game / type | World of Warcraft, Addons |
| Project name | `Guild Key Invite` |
| Slug (URL) | `guild-key-invite` (CurseForge fills it from the name) |
| Categories | Guild; Chat & Communication; Miscellaneous (the same ones ForeverRecruiter uses; pick from the list CurseForge shows) |
| License | MIT (a `LICENSE` file is in the repo; choose "All Rights Reserved" instead if you prefer) |
| Logo | `docs/logo.png` (400x400) |
| Source URL | `https://github.com/Nekramess/GuildKeyInvite` (after you create the repo) |
| Issues URL | `https://github.com/Nekramess/GuildKeyInvite/issues` |
| Donations | none |

## 3. Summary (one line, 175 characters)

```
Whisper a key word (default !ginvite) and get invited to the guild on your next key press or click. Off by default. Custom key words, optional welcome whisper, minimap button.
```

## 4. Description (paste into the description box)

```
# Guild Key Invite

Whisper a key word to a guild member and get invited to the guild. One job, nothing else.

**Off by default.** Type `/gki on` (or left-click the minimap button) to turn it on.

## How it works

1. A player whispers you the key word. The default is `!ginvite`.
2. The addon queues the invite and tells you in chat.
3. On your next key press or click in the game world, the invite is sent. If you set a welcome message, it is whispered to them right after.

Guild invites only work from a real key press or click, so the invite cannot go out while you are completely idle. Requests wait up to 10 minutes, and invites go out one per press, at least 1.5 seconds apart.

## Features

- Your own key words: `/gki key <word> [word2 ...]`
- Off by default, with a one-time hint on first login
- Optional welcome whisper after each invite: `/gki reply <text>`
- Cooldown so nobody is invited twice in a row (30 seconds, change with `/gki cooldown <seconds>`)
- Minimap button: left-click on/off, right-click status, drag to move
- `/gki test <text>` shows whether a message would match, without inviting anyone
- Does nothing if you are not in a guild or your rank cannot invite (you get one message)
- Ignores whispers while the game hides chat text from addons (encounters, challenge modes, PvP matches, dungeons and raids)

The whole whisper has to be a key word. Case, a leading `!` and trailing punctuation are ignored, so `!GInvite`, `ginvite` and `!ginvite!!` all work, but `please !ginvite me` does not.

## Commands

`/gki` or `/guildkeyinvite`

| Command | What it does |
|---|---|
| `/gki` | Status |
| `/gki on` / `/gki off` | Turn auto invite on or off |
| `/gki key <word> [word2 ...]` | Set the key words (default `!ginvite`) |
| `/gki cooldown <seconds>` | Wait before inviting the same person again |
| `/gki reply <text>` / `/gki reply off` | Welcome whisper after an invite |
| `/gki minimap on` / `/gki minimap off` | Show or hide the minimap button |
| `/gki test <text>` | Check a message without inviting |

## Notes

- Made for World of Warcraft: Forever (Interface 16001).
- Status: tested in a simulated client only. Not yet confirmed in the live Forever client, so please report anything odd.
- Source and issue tracker: https://github.com/Nekramess/GuildKeyInvite
```

## 5. File upload (Files tab, after the project exists)

| Field | Value |
|---|---|
| File | `releases/GuildKeyInvite-v0.1.0-forever.zip` exactly as built (never rezip or rename; never retype the name) |
| Display name | leave CurseForge's default (the file name) |
| Release type | **Beta** until you have tried it in game (switch to Release for 0.1.1 or later once confirmed) |
| Game version | the World of Warcraft: Forever version in CurseForge's dropdown (Interface 16001) |
| Relations / dependencies | none (LibStub, CallbackHandler, LibDataBroker and LibDBIcon are embedded in the zip) |
| Changelog | paste the text below |

Changelog (Markdown):

```
First release.

- Whisper a key word (default !ginvite, changeable) to get invited to the guild.
- Off by default: /gki on, or left-click the minimap button.
- Guild invites need a real key press or click, so the invite is queued and sent on your next key press or world click (one per press, 1.5 s apart, requests expire after 10 minutes).
- Optional welcome whisper: /gki reply <text>.
- 30 second cooldown per person.
- Minimap button (LibDBIcon): left-click on/off, right-click status, drag to move.
- /gki test <text> checks a message without inviting.

Not yet tested in the live Forever client.
```

## 6. Before you upload

1. Install the test zip, then try in game (see the list below). Upload only the file that ends up in `releases/` after any fixes, and bump `## Version` for every new upload.
2. Create the GitHub repo, say "push", merge the PR, then download the zip from `https://github.com/Nekramess/GuildKeyInvite/raw/main/releases/GuildKeyInvite-v0.1.0-forever.zip` and upload that.
3. Add 1 or 2 screenshots (the minimap button and the chat lines after an invite) once you have them; none are included yet.

Things to try in game:

- `/gki on`, have an alt or friend whisper `!ginvite`: you should see "asked for a guild invite", then the invite after you press any key.
- Click the world instead of pressing a key: it should also send.
- `/gki reply Welcome!`: the whisper should go out right after the invite (unconfirmed that Forever allows it from a key press).
- Check that every key still works normally and typing in chat is not affected while a request is waiting.
- `/gki minimap off` and `on`; drag the button; confirm the icon shows (a green question mark means the icon guess `INV_Misc_GroupNeedMore` is wrong).
