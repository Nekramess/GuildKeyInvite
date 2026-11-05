# Changelog

## 0.1.0 - first release

- Whisper a key word to get invited to the guild. Default key word: `!ginvite`; change it with `/gki key <word> [word2 ...]`.
- **OFF by default.** Turn it on with `/gki on` or by left-clicking the minimap button. A one-time chat hint explains this on the first login.
- Guild invites need a real key press or click, so a whisper queues the invite and it is sent on your next key press or world click (one per press, at least 1.5 s apart, requests expire after 10 minutes, at most 20 waiting).
- Optional welcome whisper after an invite: `/gki reply <text>`, `/gki reply off`.
- 30 second cooldown per person (`/gki cooldown <seconds>`).
- Minimap button through LibDBIcon-1.0: left-click on/off, right-click status, drag to move, `/gki minimap on|off`.
- `/gki test <text>` shows whether a message would match, without inviting anyone.
- If the game blocks a call, the addon says which function it was and no longer reports that invite as sent.
- Whispers are ignored while the game hides chat text from addons (encounters, challenge modes, PvP matches, dungeons and raids).

Not yet tested in the live Forever client (simulated client only).
