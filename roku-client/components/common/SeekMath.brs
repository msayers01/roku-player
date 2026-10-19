' Pure seek calculations (no node access) so they can be unit tested off-device.

' Clamp position + delta to [0, duration - endMargin].
' Returns invalid when duration is unknown, so callers can show "Seek unavailable".
function SeekCalcTarget(position as dynamic, duration as dynamic, delta as dynamic, endMargin as dynamic) as dynamic
    if duration = invalid or position = invalid or duration <= 0 then return invalid
    safeEnd = duration - endMargin
    if safeEnd < 0 then safeEnd = 0
    target = position + delta
    if target < 0 then target = 0
    if target > safeEnd then target = safeEnd
    return target
end function

' A seek has landed once the reported position is near the target, or once the
' player settles after buffering (keyframe snapping can land a few seconds off).
function SeekHasLanded(position as dynamic, target as dynamic, tolerance as dynamic, settledAfterBuffering as boolean) as boolean
    if settledAfterBuffering then return true
    if position = invalid or target = invalid then return false
    return Abs(position - target) <= tolerance
end function

' Label for the seek toast, e.g. "+15s" / "-30s" for queued taps.
function SeekDeltaLabel(delta as dynamic) as string
    seconds = Int(Abs(delta) + 0.5)
    if delta < 0 then return "-" + seconds.ToStr() + "s"
    return "+" + seconds.ToStr() + "s"
end function
