-- Guild Key Invite
-- One job: when someone whispers you a key word, invite them to your guild.
--
-- Forever API notes (Forever UI source, `forever` branch, build 1.60.1.70755, 4 Nov 2026):
--   * Event CHAT_MSG_WHISPER (ChatInfoDocumentation.lua): text and playerName carry
--     SecretInChatMessagingLockdown, so they are secret values during encounters,
--     challenge modes, PvP matches and on restricted maps (dungeons/raids). We skip
--     those whispers (issecretvalue) instead of erroring.
--   * C_GuildInfo.Invite(name) (GuildInfoDocumentation.lua): SecretArguments =
--     "AllowedWhenUntainted", so it must never be given a secret value. The docs show
--     no hardware-event flag; Blizzard's own /ginvite calls it directly.
--   * CanGuildInvite() is used by Blizzard's UI but is not in the generated API docs;
--     we only call it when it exists.
--   * C_GuildInfo.Invite was `GuildInvite` in old clients; the global is only a
--     deprecated shim in Forever, so we use it only as a fallback.

local ADDON_NAME = ...

local PREFIX = "|cff9370dbGuild Key Invite|r: "

local DEFAULTS = {
    enabled = true,
    keys = { "invite" },
    cooldown = 30, -- seconds before the same person can be invited again
}

local db
local lastInvite = {}   -- lowercase sender -> GetTime() of last invite attempt
local recent = {}       -- last few invites, newest last (this session only)
local warnedPermission = false
local warnedNoGuild = false

local function Print(msg)
    print(PREFIX .. msg)
end

-- Lowercase, trim, drop a leading "!" and trailing punctuation ("Invite!!" -> "invite").
local function Normalize(s)
    s = strlower(s)
    s = s:gsub("^%s+", "")
    s = s:gsub("%s+$", "")
    s = s:gsub("^!+", "")
    s = s:gsub("[%p%s]+$", "")
    return s
end

local function MatchesKey(text)
    local t = Normalize(text)
    if t == "" then return false end
    for _, key in ipairs(db.keys) do
        if t == Normalize(key) then
            return true
        end
    end
    return false
end

local function IsSecret(v)
    return issecretvalue ~= nil and issecretvalue(v)
end

local function DoInvite(name)
    local invite = (C_GuildInfo and C_GuildInfo.Invite) or GuildInvite
    if not invite then
        return false, "no guild invite function found"
    end
    return pcall(invite, name)
end

local function HandleWhisper(text, sender)
    if not db or not db.enabled then return end

    -- Secret values (chat lockdown) can't be compared or passed to Invite.
    if IsSecret(text) or IsSecret(sender) then return end
    if type(text) ~= "string" or type(sender) ~= "string" or sender == "" then return end

    if not MatchesKey(text) then return end

    if not IsInGuild() then
        if not warnedNoGuild then
            warnedNoGuild = true
            Print("someone whispered the key, but you are not in a guild.")
        end
        return
    end

    if CanGuildInvite and not CanGuildInvite() then
        if not warnedPermission then
            warnedPermission = true
            Print("someone whispered the key, but your guild rank can't invite.")
        end
        return
    end

    local id = strlower(sender)
    local now = GetTime()
    local last = lastInvite[id]
    if last and (now - last) < db.cooldown then return end
    lastInvite[id] = now

    local ok, err = DoInvite(sender)
    if ok then
        Print("invited " .. sender .. ".")
        recent[#recent + 1] = sender
        if #recent > 5 then table.remove(recent, 1) end
    else
        Print("could not invite " .. sender .. ": " .. tostring(err))
    end
end

local function ShowStatus()
    Print((db.enabled and "ON" or "OFF") .. " | keys: " .. table.concat(db.keys, ", ")
        .. " | cooldown: " .. db.cooldown .. "s")
    if #recent > 0 then
        Print("invited this session: " .. table.concat(recent, ", "))
    end
end

local HELP = {
    "/gki - show status",
    "/gki on | off - turn auto invite on or off",
    "/gki key <word> [word2 ...] - whisper keys that trigger an invite (default: invite)",
    "/gki cooldown <seconds> - wait before inviting the same person again (default 30)",
    "/gki test <text> - check whether a message would match (does not invite)",
}

local function HandleSlash(msg)
    msg = msg or ""
    local cmd, rest = msg:match("^%s*(%S*)%s*(.-)%s*$")
    cmd = strlower(cmd or "")

    if cmd == "" or cmd == "status" then
        ShowStatus()
    elseif cmd == "on" then
        db.enabled = true
        Print("ON")
    elseif cmd == "off" then
        db.enabled = false
        Print("OFF")
    elseif cmd == "key" or cmd == "keys" then
        local keys = {}
        for word in rest:gmatch("%S+") do
            keys[#keys + 1] = word
        end
        if #keys == 0 then
            Print("usage: /gki key <word> [word2 ...]")
        else
            db.keys = keys
            Print("keys: " .. table.concat(keys, ", "))
        end
    elseif cmd == "cooldown" then
        local n = tonumber(rest)
        if n and n >= 0 then
            db.cooldown = n
            Print("cooldown: " .. n .. "s")
        else
            Print("usage: /gki cooldown <seconds>")
        end
    elseif cmd == "test" then
        if rest == "" then
            Print("usage: /gki test <text>")
        else
            Print(MatchesKey(rest) and ('"' .. rest .. '" would trigger an invite.')
                or ('"' .. rest .. '" would not trigger an invite.'))
        end
    else
        for _, line in ipairs(HELP) do Print(line) end
    end
end

-- Fill in only the settings that are missing; a saved key list is never merged with the default.
local function CopyDefaults(src, dst)
    for k, v in pairs(src) do
        if dst[k] == nil then
            if type(v) == "table" then
                local copy = {}
                for i, item in ipairs(v) do copy[i] = item end
                dst[k] = copy
            else
                dst[k] = v
            end
        end
    end
end

local frame = CreateFrame("Frame")
frame:RegisterEvent("ADDON_LOADED")
frame:RegisterEvent("CHAT_MSG_WHISPER")
frame:SetScript("OnEvent", function(_, event, ...)
    if event == "ADDON_LOADED" then
        if (...) == ADDON_NAME then
            GuildKeyInviteDB = GuildKeyInviteDB or {}
            db = GuildKeyInviteDB
            CopyDefaults(DEFAULTS, db)
            frame:UnregisterEvent("ADDON_LOADED")
        end
    elseif event == "CHAT_MSG_WHISPER" then
        local text, sender = ...
        HandleWhisper(text, sender)
    end
end)

SLASH_GUILDKEYINVITE1 = "/gki"
SLASH_GUILDKEYINVITE2 = "/guildkeyinvite"
SlashCmdList["GUILDKEYINVITE"] = HandleSlash
