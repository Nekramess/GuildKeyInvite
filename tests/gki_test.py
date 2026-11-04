#!/usr/bin/env python3
"""Simulated-client tests for Guild Key Invite (python + lupa).

Simulated client only: the mock follows Forever's API docs (secret values in chat
lockdown, C_GuildInfo.Invite, CanGuildInvite), but nothing here runs in the live game.

Usage: python3 tests/gki_test.py            (tests GuildKeyInvite/GuildKeyInvite.lua)
       GKI_LUA=/path/to/file.lua python3 tests/gki_test.py
"""
import os
import sys

import lupa

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LUA_PATH = os.environ.get("GKI_LUA", os.path.join(ROOT, "GuildKeyInvite", "GuildKeyInvite.lua"))
FOREVER_DOCS = "/tmp/claude-0/forever-ui/wow-ui-source/Interface/AddOns/Blizzard_APIDocumentationGenerated"

MOCK = r"""
printed, invited = {}, {}
now = 1000
inGuild = true
canInvite = true
inviteError = nil
frames = {}
secrets = setmetatable({}, {__mode = "k"})

-- A secret value still reports type "string" (like the live client) but errors when used.
local realtype = type
function type(v)
    if secrets[v] then return "string" end
    return realtype(v)
end
function Secret()
    local t = setmetatable({}, {
        __eq = function() error("secret value compared") end,
        __concat = function() error("secret value concatenated") end,
        __lt = function() error("secret value compared") end,
        __len = function() error("secret value measured") end,
    })
    secrets[t] = true
    return t
end
function issecretvalue(v) return secrets[v] == true end
function strlower(s)
    if realtype(s) ~= "string" then error("bad argument to strlower (secret or non-string)") end
    return string.lower(s)
end

function print(...)
    local t = {}
    for i = 1, select("#", ...) do t[#t + 1] = tostring((select(i, ...))) end
    printed[#printed + 1] = table.concat(t, " ")
end
function CreateFrame()
    local f = {scripts = {}, events = {}}
    function f:RegisterEvent(e) self.events[e] = true end
    function f:UnregisterEvent(e) self.events[e] = nil end
    function f:SetScript(n, fn) self.scripts[n] = fn end
    frames[#frames + 1] = f
    return f
end
function GetTime() return now end
function IsInGuild() return inGuild end
function CanGuildInvite() return canInvite end
C_GuildInfo = {Invite = function(name)
    if inviteError then error(inviteError) end
    invited[#invited + 1] = name
end}
SlashCmdList = {}

function Fire(event, ...)
    local f = frames[1]
    if f.events[event] then f.scripts.OnEvent(f, event, ...) end
end
function Whisper(text, sender) Fire("CHAT_MSG_WHISPER", text, sender or "Tester-Realm") end
function Slash(msg) SlashCmdList["GUILDKEYINVITE"](msg) end
function InvitedList() return table.concat(invited, "|") end
function Printed() return table.concat(printed, "\n") end
"""


class Results:
    def __init__(self):
        self.passed = 0
        self.failed = []

    def check(self, name, cond):
        if cond:
            self.passed += 1
            print("PASS", name)
        else:
            self.failed.append(name)
            print("FAIL", name)


def new_env(lua_path, saved=None, setup=None):
    lua = lupa.LuaRuntime()
    lua.execute(MOCK)
    if saved is not None:
        lua.execute("GuildKeyInviteDB = " + saved)  # saved is a Lua table literal
    if setup:
        lua.execute(setup)
    with open(lua_path, encoding="utf-8") as fh:
        src = fh.read()
    chunk = lua.eval("(loadstring or load)")(src, "@GuildKeyInvite.lua")
    chunk("GuildKeyInvite")
    lua.execute('Fire("ADDON_LOADED", "GuildKeyInvite")')
    return lua


def invited(lua):
    return str(lua.eval("InvitedList()"))


def printed(lua):
    return str(lua.eval("Printed()"))


def safe(lua, code):
    """Run code; return (ok, error text)."""
    try:
        lua.execute(code)
        return True, ""
    except Exception as exc:  # noqa: BLE001
        return False, str(exc)


def run(lua_path=LUA_PATH):
    r = Results()

    # --- matching -------------------------------------------------------
    lua = new_env(lua_path)
    ok, err = safe(lua, 'Whisper("invite", "Alice-Realm")')
    r.check("plain key invites the sender", ok and invited(lua) == "Alice-Realm")

    for i, text in enumerate(["Invite", "  INVITE  ", "invite!!", "!invite", "invite."]):
        lua = new_env(lua_path)
        safe(lua, f'Whisper("{text}", "P{i}")')
        r.check(f"normalized match: {text!r}", invited(lua) == f"P{i}")

    for text in ["hello", "please invite me", "invit", "", "   ", "invite me"]:
        lua = new_env(lua_path)
        safe(lua, f'Whisper("{text}", "Bob")')
        r.check(f"non-matching whisper ignored: {text!r}", invited(lua) == "")

    # --- on / off -------------------------------------------------------
    lua = new_env(lua_path)
    safe(lua, 'Slash("off")')
    safe(lua, 'Whisper("invite", "Carol")')
    r.check("/gki off stops invites", invited(lua) == "")
    safe(lua, 'Slash("on")')
    safe(lua, 'Whisper("invite", "Carol")')
    r.check("/gki on resumes invites", invited(lua) == "Carol")

    lua = new_env(lua_path, saved="{enabled = false}")
    safe(lua, 'Whisper("invite", "Dave")')
    r.check("saved enabled=false is kept across loads", invited(lua) == "")

    # --- custom keys ----------------------------------------------------
    lua = new_env(lua_path)
    safe(lua, 'Slash("key inv join")')
    safe(lua, 'Whisper("join", "Eve")')
    safe(lua, 'Whisper("INV", "Frank")')
    safe(lua, 'Whisper("invite", "Grace")')
    r.check("custom keys: join and inv work, old default dropped", invited(lua) == "Eve|Frank")
    safe(lua, 'Slash("key")')
    r.check("/gki key with no word keeps the old keys",
            "usage" in printed(lua) and invited(lua) == "Eve|Frank")
    safe(lua, 'Whisper("join", "Heidi")')
    r.check("keys still work after empty /gki key", invited(lua).endswith("Heidi"))

    lua = new_env(lua_path, saved='{keys = {"recruit"}}')
    safe(lua, 'Whisper("recruit", "Ivan")')
    safe(lua, 'Whisper("invite", "Judy")')
    r.check("saved keys are used and not overwritten by defaults", invited(lua) == "Ivan")

    # --- cooldown -------------------------------------------------------
    lua = new_env(lua_path)
    safe(lua, 'Whisper("invite", "Kim")')
    safe(lua, 'now = now + 10; Whisper("invite", "Kim")')
    r.check("same sender inside cooldown is ignored", invited(lua) == "Kim")
    safe(lua, 'Whisper("invite", "kim")')
    r.check("cooldown is case-insensitive on the name", invited(lua) == "Kim")
    safe(lua, 'Whisper("invite", "Leo")')
    r.check("different sender is not blocked by someone else's cooldown", invited(lua) == "Kim|Leo")
    safe(lua, 'now = now + 25; Whisper("invite", "Kim")')
    r.check("same sender allowed again after cooldown", invited(lua) == "Kim|Leo|Kim")
    safe(lua, 'Slash("cooldown 0"); Whisper("invite", "Mia"); Whisper("invite", "Mia")')
    r.check("/gki cooldown 0 allows repeats", invited(lua).endswith("Mia|Mia"))
    safe(lua, 'Slash("cooldown abc")')
    r.check("bad cooldown value is rejected with usage", "usage" in printed(lua))

    # --- secret values (chat lockdown) ----------------------------------
    lua = new_env(lua_path)
    ok1, e1 = safe(lua, 'Whisper(Secret(), "Nora")')
    ok2, e2 = safe(lua, 'Whisper("invite", Secret())')
    ok3, e3 = safe(lua, 'Whisper(Secret(), Secret())')
    r.check("secret text or sender does not error", ok1 and ok2 and ok3)
    r.check("secret text or sender does not invite", invited(lua) == "")
    safe(lua, 'Whisper("invite", "Oscar")')
    r.check("normal whispers still work after secret ones", invited(lua) == "Oscar")

    # --- guild / permission checks --------------------------------------
    lua = new_env(lua_path)
    safe(lua, 'inGuild = false; Whisper("invite", "Pat"); Whisper("invite", "Quinn")')
    r.check("no invite when not in a guild", invited(lua) == "")
    r.check("not-in-guild warning printed once", printed(lua).count("not in a guild") == 1)

    lua = new_env(lua_path)
    safe(lua, 'canInvite = false; Whisper("invite", "Rita"); Whisper("invite", "Sam")')
    r.check("no invite when rank can't invite", invited(lua) == "")
    r.check("permission warning printed once", printed(lua).count("rank can't invite") == 1)

    lua = new_env(lua_path)
    safe(lua, 'CanGuildInvite = nil; Whisper("invite", "Tina")')
    r.check("still invites when CanGuildInvite does not exist", invited(lua) == "Tina")

    # --- failures and fallbacks -----------------------------------------
    lua = new_env(lua_path)
    ok, err = safe(lua, 'inviteError = "boom"; Whisper("invite", "Uma")')
    r.check("a failing Invite call does not raise", ok)
    r.check("a failing Invite call is reported", "could not invite Uma" in printed(lua))
    safe(lua, 'inviteError = nil; now = now + 31; Whisper("invite", "Uma")')
    r.check("addon keeps working after a failed invite", invited(lua) == "Uma")

    lua = new_env(lua_path, setup='GuildInvite = function(n) invited[#invited + 1] = "old:" .. n end; C_GuildInfo = nil')
    safe(lua, 'Whisper("invite", "Vic")')
    r.check("falls back to GuildInvite when C_GuildInfo is missing", invited(lua) == "old:Vic")

    lua = new_env(lua_path, setup="C_GuildInfo = nil")
    ok, err = safe(lua, 'Whisper("invite", "Wes")')
    r.check("no invite function at all: no error, message printed",
            ok and "no guild invite function" in printed(lua))

    # --- loading / saved variables --------------------------------------
    lua = new_env(lua_path)
    db = lua.eval("GuildKeyInviteDB")
    r.check("defaults are created on first load", db["enabled"] is True and db["cooldown"] == 30 and db["keys"][1] == "invite")

    lua2 = lupa.LuaRuntime()
    lua2.execute(MOCK)
    with open(lua_path, encoding="utf-8") as fh:
        chunk = lua2.eval("(loadstring or load)")(fh.read(), "@GuildKeyInvite.lua")
    chunk("GuildKeyInvite")
    lua2.execute('Fire("ADDON_LOADED", "OtherAddon")')
    r.check("saved variable not created for another addon's ADDON_LOADED", lua2.eval("GuildKeyInviteDB") is None)
    ok, _ = safe(lua2, 'Whisper("invite", "Xena")')
    r.check("whisper before our ADDON_LOADED does not error or invite", ok and invited(lua2) == "")

    lua = new_env(lua_path)
    r.check("registers CHAT_MSG_WHISPER", bool(lua.eval("frames[1].events.CHAT_MSG_WHISPER")))
    r.check("unregisters ADDON_LOADED after loading", not lua.eval("frames[1].events.ADDON_LOADED"))
    r.check("slash /gki registered", str(lua.eval("SLASH_GUILDKEYINVITE1")) == "/gki")
    r.check("slash /guildkeyinvite registered", str(lua.eval("SLASH_GUILDKEYINVITE2")) == "/guildkeyinvite")

    # --- slash output ----------------------------------------------------
    lua = new_env(lua_path)
    safe(lua, 'Slash("")')
    r.check("/gki prints status", "ON" in printed(lua) and "invite" in printed(lua))
    safe(lua, 'printed = {}; Slash("test Invite!")')
    r.check("/gki test says a match would invite", "would trigger" in printed(lua))
    safe(lua, 'printed = {}; Slash("test hello")')
    r.check("/gki test says a non-match would not invite", "would not trigger" in printed(lua))
    r.check("/gki test never invites", invited(lua) == "")
    safe(lua, 'printed = {}; Slash("bogus")')
    r.check("unknown subcommand prints help", "/gki on | off" in printed(lua))
    safe(lua, 'Whisper("invite", "Yan")')
    safe(lua, 'printed = {}; Slash("status")')
    r.check("status lists who was invited this session", "Yan" in printed(lua))

    # --- Forever docs (only when the Forever UI source is present) ------
    guild_docs = os.path.join(FOREVER_DOCS, "GuildInfoDocumentation.lua")
    chat_docs = os.path.join(FOREVER_DOCS, "ChatInfoDocumentation.lua")
    if os.path.exists(guild_docs) and os.path.exists(chat_docs):
        gd = open(guild_docs, encoding="utf-8").read()
        cd = open(chat_docs, encoding="utf-8").read()
        r.check("Forever docs: C_GuildInfo.Invite exists", 'Name = "Invite"' in gd)
        r.check("Forever docs: CHAT_MSG_WHISPER exists", 'LiteralName = "CHAT_MSG_WHISPER"' in cd)
    else:
        print("SKIP Forever docs checks (source not at", FOREVER_DOCS + ")")

    print(f"\n{r.passed} passing, {len(r.failed)} failing")
    return r


if __name__ == "__main__":
    res = run()
    sys.exit(1 if res.failed else 0)
