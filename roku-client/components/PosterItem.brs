sub init()
    m.ring = m.top.FindNode("focusRing")
    m.poster = m.top.FindNode("poster")
    m.badge = m.top.FindNode("badge")
    m.title = m.top.FindNode("title")
end sub

sub onContentChanged()
    item = m.top.itemContent
    if item = invalid then return
    m.poster.uri = item.FHDPosterUrl
    m.title.text = item.title
    m.badge.visible = (item.playable = false)
end sub

sub onFocusChanged()
    focus = m.top.focusPercent
    if not m.top.gridHasFocus then focus = 0
    m.ring.opacity = focus
    if focus > 0.5 then m.title.color = "0xF2F4F8FF" else m.title.color = "0x9AA3B2FF"
end sub
