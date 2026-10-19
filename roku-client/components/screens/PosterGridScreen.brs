sub init()
    m.grid = m.top.FindNode("grid")
    m.count = m.top.FindNode("count")
    m.server = m.top.FindNode("server")
    m.empty = m.top.FindNode("empty")
    m.grid.ObserveField("itemSelected", "onItemSelected")
    m.top.ObserveField("focusedChild", "onFocusedChild")
end sub

sub onContentChanged()
    content = m.top.content
    total = 0
    if content <> invalid then total = content.GetChildCount()
    if total = 1 then m.count.text = "1 movie" else m.count.text = total.ToStr() + " movies"
    m.empty.visible = (total = 0)
    m.grid.visible = (total > 0)
    m.grid.content = content
end sub

sub onServerLabelChanged()
    m.server.text = "Server  " + m.top.serverLabel
end sub

' Forward focus from the screen to the grid whenever the screen is focused.
sub onFocusedChild()
    if m.top.HasFocus() and m.grid.visible then m.grid.SetFocus(true)
end sub

sub onItemSelected()
    m.top.selectedItem = m.grid.content.GetChild(m.grid.itemSelected)
    m.top.action = "select"
end sub

function onKeyEvent(key as string, press as boolean) as boolean
    if not press or not m.top.visible then return false
    if m.grid.visible and not m.grid.HasFocus() and (key = "up" or key = "down" or key = "left" or key = "right" or key = "OK")
        m.grid.SetFocus(true)
        return true
    end if
    if key = "options"
        m.top.action = "settings"
        return true
    else if key = "back"
        m.top.action = "back"
        return true
    end if
    return false
end function
