# Guild Key Invite

Whisper a key word to a guild member running this addon and get invited to the guild automatically. Default key: `!ginvite`.

## Install

Copy the `GuildKeyInvite` folder into `World of Warcraft/_classic_beta_/Interface/AddOns/` (use the folder for the Forever client you play on). Interface 16001.

Download the current build: `releases/GuildKeyInvite-v0.1.0-forever.zip`.

## Commands

`/gki` or `/guildkeyinvite`

| Command | What it does |
|---|---|
| `/gki` | Show status (on/off, keys, cooldown, reply, minimap button, who was invited this session) |
| `/gki on` / `/gki off` | Turn auto invite on or off |
| `/gki key <word> [word2 ...]` | Set the whisper key words (default: `!ginvite`) |
| `/gki cooldown <seconds>` | Wait before inviting the same person again (default 30) |
| `/gki reply <text>` / `/gki reply off` | Whisper this back after a successful invite (default: no reply) |
| `/gki minimap on` / `/gki minimap off` | Show or hide the minimap button |
| `/gki test <text>` | Check whether a message would match, without inviting |

Minimap button (LibDBIcon): left-click turns auto invite on/off, right-click shows status, drag to move.

## How it works

- The whole whisper has to be a key word. Case, a leading `!` and trailing punctuation are ignored, so with the default key `!ginvite`, `!GInvite`, `ginvite` and `!ginvite!!` all work; `please !ginvite me` does not.
- You need to be in a guild and your rank needs permission to invite.
- Whispers are skipped while the game hides chat text from addons (encounters, challenge modes, PvP matches, dungeons and raids).
- Settings are saved per account in `GuildKeyInviteDB`.

## CurseForge description

**Guild Key Invite** invites people to your guild when they whisper you a key word (default `!ginvite`, change it with `/gki key`). It ignores repeats for 30 seconds so nobody gets spammed, can whisper a welcome message back, and has a minimap button to switch it on and off.

Status: tested in a simulated client only (82 checks, 29 mutations caught). Not yet tested in the live Forever client.
