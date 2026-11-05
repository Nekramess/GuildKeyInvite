# Guild Key Invite

Whisper a key word to a guild member running this addon and get invited to the guild. Default key: `!ginvite`. **Off by default**: type `/gki on` to turn it on.

## Install

Copy the `GuildKeyInvite` folder into `World of Warcraft/_classic_beta_/Interface/AddOns/` (use the folder for the Forever client you play on). Interface 16001.

Download the current build: `releases/GuildKeyInvite-v0.1.0-forever.zip`.

## Commands

`/gki` or `/guildkeyinvite`

| Command | What it does |
|---|---|
| `/gki` | Show status (on/off, keys, cooldown, reply, minimap button, waiting invites, who was invited this session) |
| `/gki on` / `/gki off` | Turn auto invite on or off (it starts OFF) |
| `/gki key <word> [word2 ...]` | Set the whisper key words (default: `!ginvite`) |
| `/gki cooldown <seconds>` | Wait before inviting the same person again (default 30) |
| `/gki reply <text>` / `/gki reply off` | Whisper this back after a successful invite (default: no reply) |
| `/gki minimap on` / `/gki minimap off` | Show or hide the minimap button |
| `/gki test <text>` | Check whether a message would match, without inviting |

Minimap button (LibDBIcon): left-click turns auto invite on/off, right-click shows status, drag to move.

## How it works

- The whole whisper has to be a key word. Case, a leading `!` and trailing punctuation are ignored, so with the default key `!ginvite`, `!GInvite`, `ginvite` and `!ginvite!!` all work; `please !ginvite me` does not.
- **The invite is sent on your next key press or click in the game world.** Other Forever addons report that guild invites only work from a real key press or click, so a whisper queues the invite and the input sends it (one per press, at least 1.5 s apart, requests expire after 10 minutes, at most 20 waiting). Turning the addon off drops waiting requests.
- You need to be in a guild and your rank needs permission to invite.
- Whispers are skipped while the game hides chat text from addons (encounters, challenge modes, PvP matches, dungeons and raids).
- If the game blocks an action (the "blocked from an action only available to the Blizzard UI" popup), the addon prints which function was blocked and does not report that invite as sent.
- Settings are saved per account in `GuildKeyInviteDB`.

## CurseForge

Listing text, upload fields and changelog: [`curseforge/LISTING.md`](curseforge/LISTING.md). Release steps: [`docs/RELEASING.md`](docs/RELEASING.md). History: [`CHANGELOG.md`](CHANGELOG.md). License: MIT.

## Tests

`pip install lupa`, then `python3 tests/gki_test.py` (127 checks) and `python3 tests/mutation_check.py` (48 deliberate breaks, all caught). Simulated client only; not yet tested in the live Forever client.
