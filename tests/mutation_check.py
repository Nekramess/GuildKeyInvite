#!/usr/bin/env python3
"""Mutation check: break GuildKeyInvite.lua on purpose and confirm a test fails.

Every mutation is applied to a temp copy; the real file is never touched.
Exit code 1 if any mutation survives (no test noticed it).
"""
import contextlib
import io
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gki_test  # noqa: E402

SRC = os.path.join(gki_test.ROOT, "GuildKeyInvite", "GuildKeyInvite.lua")

MUTATIONS = [
    ("secret check removed",
     "if IsSecret(text) or IsSecret(sender) then return end", ""),
    ("cooldown removed",
     "if last and (now - last) < db.cooldown then return end", ""),
    ("enabled flag ignored",
     "if not db or not db.enabled then return end", "if not db then return end"),
    ("in-guild check removed",
     "if not IsInGuild() then", "if false then"),
    ("invite-permission check removed",
     "if CanGuildInvite and not CanGuildInvite() then", "if false then"),
    ("exact match turned into contains",
     "if t == Normalize(key) then", "if t:find(Normalize(key), 1, true) then"),
    ("pcall around Invite removed",
     "return pcall(invite, name)", "return true, invite(name)"),
    ("trailing punctuation no longer stripped",
     's = s:gsub("[%p%s]+$", "")', ""),
    ("lowercasing removed",
     "s = strlower(s)", "s = s"),
    ("leading ! no longer stripped",
     's = s:gsub("^!+", "")', ""),
    ("saved settings overwritten by defaults",
     "if dst[k] == nil then", "if true then"),
    ("GuildInvite fallback removed",
     "(C_GuildInfo and C_GuildInfo.Invite) or GuildInvite", "(C_GuildInfo and C_GuildInfo.Invite)"),
    ("not-in-guild warning repeats",
     "warnedNoGuild = true", "warnedNoGuild = false"),
    ("permission warning repeats",
     "warnedPermission = true", "warnedPermission = false"),
    ("cooldown keyed on exact-case name",
     "local id = strlower(sender)", "local id = sender"),
    ("invite sent to wrong name",
     "local ok, err = DoInvite(sender)", 'local ok, err = DoInvite("Nobody")'),
    ("cooldown set before checks (never invites twice)",
     "lastInvite[id] = now", "lastInvite[id] = now + 100000"),
    ("default key changed back to invite",
     'keys = { "!ginvite" }', 'keys = { "invite" }'),
    ("reply never sent",
     "        SendReply(sender)\n    else", "    else"),
    ("reply sent to /say instead of a whisper",
     'pcall(send, db.reply, "WHISPER", nil, sender)', 'pcall(send, db.reply, "SAY", nil, sender)'),
    ("pcall around the reply removed",
     'local ok, err = pcall(send, db.reply, "WHISPER", nil, sender)',
     'local ok, err = true, send(db.reply, "WHISPER", nil, sender)'),
    ("SendChatMessage fallback removed",
     "(C_ChatInfo and C_ChatInfo.SendChatMessage) or SendChatMessage",
     "(C_ChatInfo and C_ChatInfo.SendChatMessage)"),
    ("minimap button never registered",
     "icon:Register(LDB_NAME, launcher, db.minimap)", ""),
    ("minimap command does not refresh the button",
     "if LDBIcon then LDBIcon:Refresh(LDB_NAME, db.minimap) end", ""),
    ("minimap on/off inverted",
     'db.minimap.hide = (arg == "off")', 'db.minimap.hide = (arg == "on")'),
    ("left-click no longer toggles",
     "db.enabled = not db.enabled", "db.enabled = true"),
    ("broken minimap setting not repaired",
     'if type(db.minimap) ~= "table" then db.minimap = { hide = false } end', ""),
    ("missing libraries not tolerated",
     "if not LDB or not icon then return end", ""),
    ("default tables copied without their named fields",
     "for key, item in pairs(v) do copy[key] = item end",
     "for key, item in ipairs(v) do copy[key] = item end"),
]


def main():
    with open(SRC, encoding="utf-8") as fh:
        original = fh.read()
    survived = []
    for name, old, new in MUTATIONS:
        if original.count(old) != 1:
            print(f"INVALID  {name}: pattern found {original.count(old)} times")
            survived.append(name + " (invalid pattern)")
            continue
        mutated = original.replace(old, new)
        with tempfile.NamedTemporaryFile("w", suffix=".lua", delete=False, encoding="utf-8") as tmp:
            tmp.write(mutated)
            path = tmp.name
        try:
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                try:
                    res = gki_test.run(path)
                    failed = bool(res.failed)
                except Exception:  # noqa: BLE001  (a crash also means the mutation was noticed)
                    failed = True
        finally:
            os.unlink(path)
        print(("KILLED   " if failed else "SURVIVED ") + name)
        if not failed:
            survived.append(name)
    print(f"\n{len(MUTATIONS) - len(survived)} of {len(MUTATIONS)} mutations caught, {len(survived)} survived")
    return 1 if survived else 0


if __name__ == "__main__":
    sys.exit(main())
