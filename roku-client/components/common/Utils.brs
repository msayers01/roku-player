' Shared helpers and palette. Included by components via <script uri="pkg:/components/common/Utils.brs"/>.

function AppColors() as object
    return {
        bg: "0x0E1116FF"
        panel: "0x171B23FF"
        panelRaised: "0x202633FF"
        text: "0xF2F4F8FF"
        muted: "0x9AA3B2FF"
        accent: "0x4FC3B0FF"
        accentText: "0x0E1116FF"
        warn: "0xF2B544FF"
        error: "0xF26D6DFF"
        disabled: "0x5A6170FF"
    }
end function

' 75 -> "1:15", 6480 -> "1:48:00"
function FormatTime(seconds as dynamic) as string
    if seconds = invalid or seconds < 0 then seconds = 0
    total = Int(seconds)
    hours = Int(total / 3600)
    minutes = Int((total mod 3600) / 60)
    secs = total mod 60
    if hours > 0 then return hours.ToStr() + ":" + Pad2(minutes) + ":" + Pad2(secs)
    return minutes.ToStr() + ":" + Pad2(secs)
end function

function Pad2(value as integer) as string
    if value < 10 then return "0" + value.ToStr()
    return value.ToStr()
end function

' 6480 -> "1h 48m", 150 -> "3m"
function FormatRuntime(seconds as dynamic) as string
    if seconds = invalid or seconds <= 0 then return ""
    minutes = Int((seconds + 30) / 60)
    if minutes < 1 then minutes = 1
    if minutes < 60 then return minutes.ToStr() + "m"
    return Int(minutes / 60).ToStr() + "h " + (minutes mod 60).ToStr() + "m"
end function

function CodecLabel(codec as dynamic) as string
    if codec = invalid or codec = "" then return "?"
    names = { h264: "H.264", hevc: "HEVC", aac: "AAC", ac3: "AC-3", eac3: "E-AC-3", mp4: "MP4", mpeg4: "MPEG-4 Part 2" }
    if names.DoesExist(codec) then return names[codec]
    return UCase(codec)
end function
