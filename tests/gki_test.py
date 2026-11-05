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
    function f:EnableKeyboard(v) self.keyboard = v and true or false end
    function f:SetPropagateKeyboardInput(v) self.propagate = v and true or false end
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
UIParent = {}
WorldFrame = {hooks = {}}
function WorldFrame:HookScript(name, fn)
    self.hooks[name] = self.hooks[name] or {}
    table.insert(self.hooks[name], fn)
end

sent, registered, refreshes = {}, {}, {}
C_ChatInfo = {SendChatMessage = function(msg, chatType, lang, target)
    if sendError then error(sendError) end
    sent[#sent + 1] = tostring(chatType) .. ":" .. tostring(target) .. ":" .. msg
end}
local ldb = {}
function ldb:NewDataObject(name, obj) return obj end
local icon = {}
function icon:Register(name, obj, d) registered[name] = {obj = obj, db = d} end
function icon:Refresh(name, d) refreshes[#refreshes + 1] = tostring(d.hide) end
function LibStub(name, silent)
    if name == "LibDataBroker-1.1" then return ldb end
    if name == "LibDBIcon-1.0" then return icon end
end
function Tooltip()
    local t = {lines = {}}
    function t:AddLine(text) self.lines[#self.lines + 1] = text end
    return t
end

function Fire(event, ...)
    local f = frames[1]
    if f.events[event] then f.scripts.OnEvent(f, event, ...) end
end
function Whisper(text, sender) Fire("CHAT_MSG_WHISPER", text, sender or "Tester-Realm") end
function Press()
    local f = frames[2]
    if f and f.keyboard and f.scripts.OnKeyDown then f.scripts.OnKeyDown(f, "A") end
end
function Click()
    for _, fn in ipairs(WorldFrame.hooks.OnMouseDown or {}) do fn(WorldFrame, "LeftButton") end
end
-- A whisper followed, 2 s later, by a key press (the way an invite really goes out).
function Ask(text, sender) Whisper(text, sender); now = now + 2; Press() end
function Slash(msg) SlashCmdList["GUILDKEYINVITE"](msg) end
function InvitedList() return table.concat(invited, "|") end
function Printed() return table.concat(printed, "\n") end
function SentList() return table.concat(sent, "|") end
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


def new_env(lua_path, saved=None, setup=None, on=True):
    lua = lupa.LuaRuntime()
    lua.execute(MOCK)
    if on:
        if saved is None:
            saved = "{enabled = true}"
        elif "enabled" not in saved:
            saved = saved.replace("{", "{enabled = true, ", 1)
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
    ok, err = safe(lua, 'Ask("!ginvite", "Alice-Realm")')
    r.check("plain key invites the sender", ok and invited(lua) == "Alice-Realm")

    for i, text in enumerate(["!Ginvite", "  !GINVITE  ", "!ginvite!!", "ginvite", "!ginvite."]):
        lua = new_env(lua_path)
        safe(lua, f'Ask("{text}", "P{i}")')
        r.check(f"normalized match: {text!r}", invited(lua) == f"P{i}")

    for text in ["hello", "invite", "!invite", "please !ginvite me", "!ginvit", "", "   ", "!ginvite me"]:
        lua = new_env(lua_path)
        safe(lua, f'Ask("{text}", "Bob")')
        r.check(f"non-matching whisper ignored: {text!r}", invited(lua) == "")

    # --- on / off -------------------------------------------------------
    lua = new_env(lua_path)
    safe(lua, 'Slash("off")')
    safe(lua, 'Ask("!ginvite", "Carol")')
    r.check("/gki off stops invites", invited(lua) == "")
    safe(lua, 'Slash("on")')
    safe(lua, 'Ask("!ginvite", "Carol")')
    r.check("/gki on resumes invites", invited(lua) == "Carol")

    lua = new_env(lua_path, saved="{enabled = false}")
    safe(lua, 'Ask("!ginvite", "Dave")')
    r.check("saved enabled=false is kept across loads", invited(lua) == "")

    # --- custom keys ----------------------------------------------------
    lua = new_env(lua_path)
    safe(lua, 'Slash("key inv join")')
    safe(lua, 'Ask("join", "Eve")')
    safe(lua, 'Ask("INV", "Frank")')
    safe(lua, 'Ask("!ginvite", "Grace")')
    r.check("custom keys: join and inv work, old default dropped", invited(lua) == "Eve|Frank")
    safe(lua, 'Slash("key")')
    r.check("/gki key with no word keeps the old keys",
            "usage" in printed(lua) and invited(lua) == "Eve|Frank")
    safe(lua, 'Ask("join", "Heidi")')
    r.check("keys still work after empty /gki key", invited(lua).endswith("Heidi"))

    lua = new_env(lua_path, saved='{keys = {"recruit"}}')
    safe(lua, 'Ask("recruit", "Ivan")')
    safe(lua, 'Ask("!ginvite", "Judy")')
    r.check("saved keys are used and not overwritten by defaults", invited(lua) == "Ivan")

    # --- cooldown -------------------------------------------------------
    lua = new_env(lua_path)
    safe(lua, 'Ask("!ginvite", "Kim")')
    safe(lua, 'now = now + 10; Ask("!ginvite", "Kim")')
    r.check("same sender inside cooldown is ignored", invited(lua) == "Kim")
    safe(lua, 'Ask("!ginvite", "kim")')
    r.check("cooldown is case-insensitive on the name", invited(lua) == "Kim")
    safe(lua, 'Ask("!ginvite", "Leo")')
    r.check("different sender is not blocked by someone else's cooldown", invited(lua) == "Kim|Leo")
    safe(lua, 'now = now + 25; Ask("!ginvite", "Kim")')
    r.check("same sender allowed again after cooldown", invited(lua) == "Kim|Leo|Kim")
    safe(lua, 'Slash("cooldown 0"); Ask("!ginvite", "Mia"); Ask("!ginvite", "Mia")')
    r.check("/gki cooldown 0 allows repeats", invited(lua).endswith("Mia|Mia"))
    safe(lua, 'Slash("cooldown abc")')
    r.check("bad cooldown value is rejected with usage", "usage" in printed(lua))

    # --- secret values (chat lockdown) ----------------------------------
    lua = new_env(lua_path)
    ok1, e1 = safe(lua, 'Ask(Secret(), "Nora")')
    ok2, e2 = safe(lua, 'Ask("!ginvite", Secret())')
    ok3, e3 = safe(lua, 'Ask(Secret(), Secret())')
    r.check("secret text or sender does not error", ok1 and ok2 and ok3)
    r.check("secret text or sender does not invite", invited(lua) == "")
    safe(lua, 'Ask("!ginvite", "Oscar")')
    r.check("normal whispers still work after secret ones", invited(lua) == "Oscar")

    # --- guild / permission checks --------------------------------------
    lua = new_env(lua_path)
    safe(lua, 'inGuild = false; Ask("!ginvite", "Pat"); Ask("!ginvite", "Quinn")')
    r.check("no invite when not in a guild", invited(lua) == "")
    r.check("not-in-guild warning printed once", printed(lua).count("not in a guild") == 1)

    lua = new_env(lua_path)
    safe(lua, 'canInvite = false; Ask("!ginvite", "Rita"); Ask("!ginvite", "Sam")')
    r.check("no invite when rank can't invite", invited(lua) == "")
    r.check("permission warning printed once", printed(lua).count("rank can't invite") == 1)

    lua = new_env(lua_path)
    safe(lua, 'CanGuildInvite = nil; Ask("!ginvite", "Tina")')
    r.check("still invites when CanGuildInvite does not exist", invited(lua) == "Tina")

    # --- failures and fallbacks -----------------------------------------
    lua = new_env(lua_path)
    ok, err = safe(lua, 'inviteError = "boom"; Ask("!ginvite", "Uma")')
    r.check("a failing Invite call does not raise", ok)
    r.check("a failing Invite call is reported", "could not invite Uma" in printed(lua))
    safe(lua, 'inviteError = nil; now = now + 31; Ask("!ginvite", "Uma")')
    r.check("addon keeps working after a failed invite", invited(lua) == "Uma")

    lua = new_env(lua_path, setup='GuildInvite = function(n) invited[#invited + 1] = "old:" .. n end; C_GuildInfo = nil')
    safe(lua, 'Ask("!ginvite", "Vic")')
    r.check("falls back to GuildInvite when C_GuildInfo is missing", invited(lua) == "old:Vic")

    lua = new_env(lua_path, setup="C_GuildInfo = nil")
    ok, err = safe(lua, 'Ask("!ginvite", "Wes")')
    r.check("no invite function at all: no error, message printed",
            ok and "no guild invite function" in printed(lua))

    # --- loading / saved variables --------------------------------------
    lua = new_env(lua_path, on=False)
    db = lua.eval("GuildKeyInviteDB")
    r.check("defaults are created on first load", db["enabled"] is False and db["cooldown"] == 30 and db["keys"][1] == "!ginvite")

    lua2 = lupa.LuaRuntime()
    lua2.execute(MOCK)
    with open(lua_path, encoding="utf-8") as fh:
        chunk = lua2.eval("(loadstring or load)")(fh.read(), "@GuildKeyInvite.lua")
    chunk("GuildKeyInvite")
    lua2.execute('Fire("ADDON_LOADED", "OtherAddon")')
    r.check("saved variable not created for another addon's ADDON_LOADED", lua2.eval("GuildKeyInviteDB") is None)
    ok, _ = safe(lua2, 'Ask("!ginvite", "Xena")')
    r.check("whisper before our ADDON_LOADED does not error or invite", ok and invited(lua2) == "")

    lua = new_env(lua_path)
    r.check("registers CHAT_MSG_WHISPER", bool(lua.eval("frames[1].events.CHAT_MSG_WHISPER")))
    r.check("unregisters ADDON_LOADED after loading", not lua.eval("frames[1].events.ADDON_LOADED"))
    r.check("slash /gki registered", str(lua.eval("SLASH_GUILDKEYINVITE1")) == "/gki")
    r.check("slash /guildkeyinvite registered", str(lua.eval("SLASH_GUILDKEYINVITE2")) == "/guildkeyinvite")

    # --- slash output ----------------------------------------------------
    lua = new_env(lua_path)
    safe(lua, 'Slash("")')
    r.check("/gki prints status", "ON" in printed(lua) and "!ginvite" in printed(lua))
    safe(lua, 'printed = {}; Slash("test !GInvite!")')
    r.check("/gki test says a match would invite", "would trigger" in printed(lua))
    safe(lua, 'printed = {}; Slash("test hello")')
    r.check("/gki test says a non-match would not invite", "would not trigger" in printed(lua))
    r.check("/gki test never invites", invited(lua) == "")
    safe(lua, 'printed = {}; Slash("bogus")')
    r.check("unknown subcommand prints help", "/gki on | off" in printed(lua))
    safe(lua, 'Ask("!ginvite", "Yan")')
    safe(lua, 'printed = {}; Slash("status")')
    r.check("status lists who was invited this session", "Yan" in printed(lua))

    # --- reply -----------------------------------------------------------
    lua = new_env(lua_path)
    safe(lua, 'Ask("!ginvite", "Zed-Realm")')
    r.check("no reply is sent by default", str(lua.eval("SentList()")) == "")

    safe(lua, 'Slash("reply Welcome! Check Discord")')
    safe(lua, 'now = now + 31; Ask("!ginvite", "Zed-Realm")')
    r.check("reply is whispered to the sender after an invite",
            str(lua.eval("SentList()")) == "WHISPER:Zed-Realm:Welcome! Check Discord")
    safe(lua, 'Ask("!ginvite", "Zed-Realm")')
    r.check("no second reply inside the cooldown", str(lua.eval("SentList()")).count("|") == 0)
    safe(lua, 'printed = {}; Slash("reply")')
    r.check("/gki reply with no text shows the current reply", "Welcome! Check Discord" in printed(lua))
    safe(lua, 'Slash("reply off"); now = now + 31; Ask("!ginvite", "Zed-Realm")')
    r.check("/gki reply off stops replies", str(lua.eval("SentList()")).count("|") == 0)

    lua = new_env(lua_path, saved='{reply = "Hi!"}')
    safe(lua, 'Ask("!ginvite", "Amy")')
    r.check("saved reply is used", str(lua.eval("SentList()")) == "WHISPER:Amy:Hi!")

    lua = new_env(lua_path, saved='{reply = "Hi!"}')
    safe(lua, 'inviteError = "boom"; Ask("!ginvite", "Ben")')
    r.check("no reply when the invite itself failed", str(lua.eval("SentList()")) == "")

    lua = new_env(lua_path, saved='{reply = "Hi!"}')
    ok, _ = safe(lua, 'sendError = "nope"; Ask("!ginvite", "Cat")')
    r.check("a failing reply does not raise and the invite still happened", ok and invited(lua) == "Cat")
    r.check("a failing reply is reported", "could not send the reply to Cat" in printed(lua))

    lua = new_env(lua_path, saved='{reply = "Hi!"}',
                  setup="C_ChatInfo = nil; function SendChatMessage(msg, chatType, lang, target) "
                        "sent[#sent + 1] = 'old:' .. target .. ':' .. msg end")
    safe(lua, 'Ask("!ginvite", "Dan")')
    r.check("falls back to SendChatMessage when C_ChatInfo is missing", str(lua.eval("SentList()")) == "old:Dan:Hi!")

    lua = new_env(lua_path, saved='{reply = "Hi!"}')
    safe(lua, 'Ask(Secret(), "Eli")')
    r.check("no reply for a secret whisper", str(lua.eval("SentList()")) == "")

    # --- minimap button (LibDBIcon) ---------------------------------------
    lua = new_env(lua_path)
    reg = lua.eval('registered["GuildKeyInvite"]')
    r.check("registers with LibDBIcon under the addon name", reg is not None)
    r.check("launcher object has type launcher and an icon",
            reg["obj"]["type"] == "launcher" and bool(reg["obj"]["icon"]))
    r.check("minimap setting defaults to shown", reg["db"]["hide"] is False)
    r.check("LibDBIcon is given the saved minimap table",
            bool(lua.eval('registered["GuildKeyInvite"].db == GuildKeyInviteDB.minimap')))

    lua = new_env(lua_path, saved="{minimap = {hide = true, minimapPos = 123}}")
    r.check("saved hidden flag and position are passed through",
            bool(lua.eval('registered["GuildKeyInvite"].db.hide == true and registered["GuildKeyInvite"].db.minimapPos == 123')))

    lua = new_env(lua_path, saved="{minimap = true}")
    r.check("a broken minimap setting is replaced with a table",
            bool(lua.eval('type(registered["GuildKeyInvite"].db) == "table"')))

    lua = new_env(lua_path)
    safe(lua, 'Slash("minimap off")')
    r.check("/gki minimap off hides and refreshes the button",
            bool(lua.eval('GuildKeyInviteDB.minimap.hide == true and refreshes[#refreshes] == "true"')))
    safe(lua, 'Slash("minimap on")')
    r.check("/gki minimap on shows and refreshes the button",
            bool(lua.eval('GuildKeyInviteDB.minimap.hide == false and refreshes[#refreshes] == "false"')))
    safe(lua, 'printed = {}; Slash("minimap maybe")')
    r.check("/gki minimap with a bad argument prints usage", "usage" in printed(lua))

    lua = new_env(lua_path)
    safe(lua, 'registered["GuildKeyInvite"].obj.OnClick(nil, "LeftButton")')
    r.check("left-click turns auto invite off", bool(lua.eval("GuildKeyInviteDB.enabled == false")))
    safe(lua, 'registered["GuildKeyInvite"].obj.OnClick(nil, "LeftButton")')
    r.check("left-click again turns it back on", bool(lua.eval("GuildKeyInviteDB.enabled == true")))
    safe(lua, 'printed = {}; registered["GuildKeyInvite"].obj.OnClick(nil, "RightButton")')
    r.check("right-click prints status and leaves the setting alone",
            "keys:" in printed(lua) and bool(lua.eval("GuildKeyInviteDB.enabled == true")))
    safe(lua, 'tip = Tooltip(); registered["GuildKeyInvite"].obj.OnTooltipShow(tip)')
    r.check("tooltip shows the title and the key words",
            bool(lua.eval('tip.lines[1] == "Guild Key Invite" and tip.lines[2]:find("!ginvite", 1, true) ~= nil')))

    lua = new_env(lua_path, setup="LibStub = nil")
    ok, _ = safe(lua, 'Slash("minimap off")')
    r.check("works without the libraries: no error from minimap command", ok)
    safe(lua, 'Ask("!ginvite", "Fay")')
    r.check("works without the libraries: invites still go out", invited(lua) == "Fay")

    # --- OFF by default ---------------------------------------------------
    lua = new_env(lua_path, on=False)
    r.check("addon starts OFF on a fresh install", bool(lua.eval("GuildKeyInviteDB.enabled == false")))
    safe(lua, 'Ask("!ginvite", "Pia")')
    r.check("nothing is invited while it is OFF", invited(lua) == "")
    safe(lua, 'printed = {}; Slash("")')
    r.check("nothing is queued while it is OFF", "waiting for" not in printed(lua))
    safe(lua, 'Slash("on"); Ask("!ginvite", "Pia")')
    r.check("after /gki on it invites", invited(lua) == "Pia")

    lua = new_env(lua_path, on=False)
    safe(lua, 'Fire("PLAYER_LOGIN")')
    r.check("first login shows a hint that it is OFF", "OFF" in printed(lua) and "/gki on" in printed(lua))
    safe(lua, 'printed = {}; Fire("PLAYER_LOGIN")')
    r.check("the OFF hint is shown only once", printed(lua) == "")
    lua = new_env(lua_path, saved="{introShown = true}", on=False)
    safe(lua, 'Fire("PLAYER_LOGIN")')
    r.check("no hint when it was already shown in an earlier session", printed(lua) == "")
    lua = new_env(lua_path)
    safe(lua, 'Fire("PLAYER_LOGIN")')
    r.check("no hint when it is already ON", printed(lua) == "")

    # --- guild invites need a real key press or click ---------------------
    lua = new_env(lua_path)
    r.check("key events are propagated so every key keeps working", bool(lua.eval("frames[2].propagate == true")))
    r.check("world clicks are hooked", bool(lua.eval("#WorldFrame.hooks.OnMouseDown == 1")))
    r.check("keyboard listening is off while nothing waits", bool(lua.eval("frames[2].keyboard == false")))
    safe(lua, 'Whisper("!ginvite", "Ann-Realm")')
    r.check("a whisper alone does not call Invite", invited(lua) == "")
    r.check("the request is announced", "asked for a guild invite" in printed(lua))
    r.check("keyboard listening is on while a request waits", bool(lua.eval("frames[2].keyboard == true")))
    safe(lua, "now = now + 2; Press()")
    r.check("a key press sends the queued invite", invited(lua) == "Ann-Realm")
    safe(lua, "now = now + 2; Press()")
    r.check("a second key press does nothing", invited(lua) == "Ann-Realm")
    r.check("keyboard listening is off again once nothing waits", bool(lua.eval("frames[2].keyboard == false")))

    lua = new_env(lua_path)
    safe(lua, 'Whisper("!ginvite", "Bo"); now = now + 2; Click()')
    r.check("a world click sends the queued invite", invited(lua) == "Bo")

    lua = new_env(lua_path)
    safe(lua, 'Whisper("!ginvite", "A1"); Whisper("!ginvite", "B1")')
    safe(lua, "now = now + 2; Press(); Press()")
    r.check("one invite per key press", invited(lua) == "A1")
    safe(lua, "now = now + 1; Press()")
    r.check("invites are at least 1.5 s apart", invited(lua) == "A1")
    safe(lua, "now = now + 1; Press()")
    r.check("the next request goes out once the spacing has passed", invited(lua) == "A1|B1")

    lua = new_env(lua_path)
    safe(lua, 'Whisper("!ginvite", "Old"); now = now + 601; Press()')
    r.check("a request older than 10 minutes is dropped", invited(lua) == "")
    safe(lua, 'now = now + 1; Whisper("!ginvite", "Fresh"); now = now + 2; Press()')
    r.check("a fresh request after an expired one still works", invited(lua) == "Fresh")

    lua = new_env(lua_path)
    safe(lua, 'Slash("cooldown 0"); Whisper("!ginvite", "Dup"); Whisper("!ginvite", "dup")')
    safe(lua, "now = now + 2; Press(); now = now + 2; Press()")
    r.check("the same person waiting twice is queued once", invited(lua) == "Dup")

    lua = new_env(lua_path)
    safe(lua, 'for i = 1, 25 do Whisper("!ginvite", "P" .. i) end')
    safe(lua, "for i = 1, 30 do now = now + 2; Press() end")
    r.check("at most 20 requests wait; the oldest are dropped",
            invited(lua).split("|") == [f"P{i}" for i in range(6, 26)])

    lua = new_env(lua_path)
    safe(lua, 'Whisper("!ginvite", "Zoe"); Slash("off"); Slash("on"); now = now + 2; Press()')
    r.check("turning it off drops waiting requests", invited(lua) == "")
    safe(lua, 'Whisper("!ginvite", "Yul"); registered["GuildKeyInvite"].obj.OnClick(nil, "LeftButton"); '
              'registered["GuildKeyInvite"].obj.OnClick(nil, "LeftButton"); now = now + 2; Press()')
    r.check("turning it off with the minimap button drops waiting requests", invited(lua) == "")

    lua = new_env(lua_path)
    safe(lua, 'Whisper("!ginvite", "Bad"); Whisper("!ginvite", "Good"); inviteError = "boom"; now = now + 2; Press()')
    r.check("a failed invite is reported", "could not invite Bad" in printed(lua))
    safe(lua, 'inviteError = nil; now = now + 2; Press()')
    r.check("the next waiting request still goes out after a failure", invited(lua) == "Good")

    lua = new_env(lua_path, saved='{reply = "Hi!"}')
    safe(lua, 'Whisper("!ginvite", "Rex")')
    r.check("reply is not sent before the invite goes out", str(lua.eval("SentList()")) == "")
    safe(lua, "now = now + 2; Press()")
    r.check("reply goes out together with the invite", str(lua.eval("SentList()")) == "WHISPER:Rex:Hi!")

    lua = new_env(lua_path)
    safe(lua, 'Whisper("!ginvite", "Sky"); printed = {}; Slash("")')
    r.check("status shows how many invites are waiting", "waiting for a key press or click: 1" in printed(lua))

    # --- calls the game blocks ---------------------------------------------
    lua = new_env(lua_path)
    r.check("listens for ADDON_ACTION_BLOCKED and ADDON_ACTION_FORBIDDEN",
            bool(lua.eval("frames[1].events.ADDON_ACTION_BLOCKED and frames[1].events.ADDON_ACTION_FORBIDDEN")))

    BLOCK_INVITE = ('C_GuildInfo.Invite = function(name) '
                    'Fire("ADDON_ACTION_FORBIDDEN", "GuildKeyInvite", "GuildInvite()") end')
    lua = new_env(lua_path, saved='{reply = "Hi!"}')
    safe(lua, BLOCK_INVITE)
    safe(lua, 'Ask("!ginvite", "Blk")')
    r.check("a blocked invite is not reported as invited", "invited Blk" not in printed(lua))
    r.check("a blocked invite is reported as blocked, with the function name",
            "could not invite Blk: blocked by the game (GuildInvite())" in printed(lua))
    r.check("the blocked function name is printed for the player", "the game blocked GuildInvite()" in printed(lua))
    r.check("no reply is sent after a blocked invite", str(lua.eval("SentList()")) == "")
    safe(lua, 'printed = {}; Slash("")')
    r.check("a blocked invite is not listed as invited this session", "Blk" not in printed(lua))

    lua = new_env(lua_path)
    safe(lua, BLOCK_INVITE)
    safe(lua, 'Slash("cooldown 0"); Ask("!ginvite", "B1"); Ask("!ginvite", "B2")')
    r.check("the blocked function name is announced only once", printed(lua).count("the game blocked GuildInvite()") == 1)
    r.check("every blocked invite still gets its own failure line",
            "could not invite B1" in printed(lua) and "could not invite B2" in printed(lua))

    lua = new_env(lua_path)
    safe(lua, 'Fire("ADDON_ACTION_BLOCKED", "OtherAddon", "Foo()")')
    r.check("another addon's blocked action is ignored", "the game blocked" not in printed(lua))
    safe(lua, 'C_GuildInfo.Invite = function(n) invited[#invited + 1] = n; '
              'Fire("ADDON_ACTION_BLOCKED", "OtherAddon", "Foo()") end')
    safe(lua, 'Ask("!ginvite", "Ok1")')
    r.check("another addon's blocked action during an invite does not fail it",
            invited(lua) == "Ok1" and "invited Ok1." in printed(lua))

    lua = new_env(lua_path)
    safe(lua, 'Fire("ADDON_ACTION_FORBIDDEN", "GuildKeyInvite", "Old()")')
    safe(lua, 'Ask("!ginvite", "Ok2")')
    r.check("an earlier block does not make a later invite fail",
            invited(lua) == "Ok2" and "invited Ok2." in printed(lua))

    lua = new_env(lua_path, saved='{reply = "Hi!"}')
    safe(lua, 'C_ChatInfo.SendChatMessage = function() '
              'Fire("ADDON_ACTION_BLOCKED", "GuildKeyInvite", "SendChatMessage()") end')
    safe(lua, 'Ask("!ginvite", "Ok3")')
    r.check("a blocked reply is reported with the function name",
            "could not send the reply to Ok3: blocked by the game (SendChatMessage())" in printed(lua))
    r.check("the invite still counts when only the reply is blocked",
            invited(lua) == "Ok3" and "invited Ok3." in printed(lua))

    # --- Forever docs (only when the Forever UI source is present) ------
    guild_docs = os.path.join(FOREVER_DOCS, "GuildInfoDocumentation.lua")
    chat_docs = os.path.join(FOREVER_DOCS, "ChatInfoDocumentation.lua")
    if os.path.exists(guild_docs) and os.path.exists(chat_docs):
        gd = open(guild_docs, encoding="utf-8").read()
        cd = open(chat_docs, encoding="utf-8").read()
        r.check("Forever docs: C_GuildInfo.Invite exists", 'Name = "Invite"' in gd)
        r.check("Forever docs: CHAT_MSG_WHISPER exists", 'LiteralName = "CHAT_MSG_WHISPER"' in cd)
        r.check("Forever docs: C_ChatInfo.SendChatMessage exists", 'Name = "SendChatMessage"' in cd)
    else:
        print("SKIP Forever docs checks (source not at", FOREVER_DOCS + ")")

    print(f"\n{r.passed} passing, {len(r.failed)} failing")
    return r


if __name__ == "__main__":
    res = run()
    sys.exit(1 if res.failed else 0)
