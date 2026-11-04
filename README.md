# Guild Key Invite

Whisper a key word to a guild member running this addon and get invited to the guild automatically. One job, no UI.

## Install

Copy the `GuildKeyInvite` folder into `World of Warcraft/_classic_beta_/Interface/AddOns/` (use the folder for the Forever client you play on). Interface 16001.

Download the current build: `releases/GuildKeyInvite-v0.1.0-forever.zip`.

## Commands

`/gki` or `/guildkeyinvite`

| Command | What it does |
|---|---|
| `/gki` | Show status (on/off, keys, cooldown, who was invited this session) |
| `/gki on` / `/gki off` | Turn auto invite on or off |
| `/gki key <word> [word2 ...]` | Set the whisper key words (default: `invite`) |
| `/gki cooldown <seconds>` | Wait before inviting the same person again (default 30) |
| `/gki test <text>` | Check whether a message would match, without inviting |

## How it works

- The whole whisper has to be a key word. Case, a leading `!` and trailing punctuation are ignored, so `Invite`, `!invite` and `invite!!` all work; `please invite me` does not.
- You need to be in a guild and your rank needs permission to invite.
- Whispers are skipped while the game hides chat text from addons (encounters, challenge modes, PvP matches, dungeons and raids).
- Settings are saved per account in `GuildKeyInviteDB`.

## CurseForge description

**Guild Key Invite** invites people to your guild when they whisper you a key word. Set your own words with `/gki key`, and it ignores repeats for 30 seconds so nobody gets spammed.

Status: tested in a simulated client only (53 checks, 17 mutations caught). Not yet tested in the live Forever client.
