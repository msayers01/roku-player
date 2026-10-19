sub init()
    m.colors = AppColors()
    m.rows = [m.top.FindNode("hostRow"), m.top.FindNode("portRow"), m.top.FindNode("connectRow")]
    m.hostValue = m.rows[0].FindNode("value")
    m.portValue = m.rows[1].FindNode("value")
    m.connectLabel = m.rows[2].FindNode("name")
    m.status = m.top.FindNode("status")
    m.focusIndex = 2
    m.dialog = invalid
    onAddressChanged()
    onStatusChanged()
end sub

sub onAddressChanged()
    SetValueLabel(m.hostValue, m.top.host, "Not set")
    SetValueLabel(m.portValue, m.top.port, "8080")
    if m.top.host = "" then m.focusIndex = 0
    UpdateFocus()
end sub

sub SetValueLabel(label as object, value as string, placeholder as string)
    if value = ""
        label.text = placeholder
        label.color = m.colors.disabled
    else
        label.text = value
        label.color = m.colors.text
    end if
end sub

sub onStatusChanged()
    kind = m.top.statusKind
    m.status.text = m.top.statusText
    if kind = "error"
        m.status.color = m.colors.error
        m.connectLabel.text = "Retry"
    else if kind = "busy" or kind = "ok"
        m.status.color = m.colors.accent
        m.connectLabel.text = "Connect"
    else
        m.status.color = m.colors.muted
        m.connectLabel.text = "Connect"
    end if
end sub

sub UpdateFocus()
    for i = 0 to m.rows.Count() - 1
        row = m.rows[i]
        focused = (i = m.focusIndex)
        row.FindNode("focusRing").visible = focused
        bg = row.FindNode("bg")
        if i = 2
            ' The Connect button fills with the accent colour when focused.
            if focused then bg.color = m.colors.accent else bg.color = m.colors.panelRaised
            if focused then m.connectLabel.color = m.colors.accentText else m.connectLabel.color = m.colors.text
        end if
    end for
end sub

' ---------- editing ----------

sub OpenKeyboard(field as string)
    dialog = CreateObject("roSGNode", "StandardKeyboardDialog")
    if field = "host"
        dialog.title = "Server IP address"
        dialog.message = ["Type the IP address shown by start_server.bat, for example 192.168.1.50."]
        dialog.text = m.top.host
    else
        dialog.title = "Server port"
        dialog.message = ["The port shown by start_server.bat. The default is 8080."]
        dialog.text = m.top.port
        dialog.keyboardDomain = "numeric"
    end if
    dialog.buttons = ["Save", "Cancel"]
    dialog.ObserveField("buttonSelected", "onKeyboardButton")
    dialog.ObserveField("wasClosed", "onKeyboardClosed")
    m.editing = field
    m.dialog = dialog
    m.top.GetScene().dialog = dialog
end sub

sub onKeyboardButton(event as object)
    if m.dialog = invalid then return
    if event.GetData() = 0
        value = m.dialog.text.Trim()
        if m.editing = "host"
            if IsValidHost(value)
                m.top.host = value
                m.focusIndex = 1
            else
                ShowValidationError("'" + value + "' isn't a valid IP address. Use the address printed by start_server.bat.")
            end if
        else
            if IsValidPort(value)
                m.top.port = Int(Val(value)).ToStr()
                m.focusIndex = 2
            else
                ShowValidationError("The port must be a number between 1 and 65535.")
            end if
        end if
    end if
    m.dialog.close = true
    ' Take focus back now; wasClosed can arrive noticeably later.
    UpdateFocus()
    m.top.SetFocus(true)
end sub

sub onKeyboardClosed()
    m.dialog = invalid
    UpdateFocus()
    ' wasClosed can arrive after another screen was pushed; never steal focus back while hidden.
    if m.top.visible then m.top.SetFocus(true)
end sub

sub ShowValidationError(message as string)
    m.top.statusKind = "error"
    m.top.statusText = message
end sub

function IsValidHost(value as string) as boolean
    ipv4 = CreateObject("roRegex", "^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$", "")
    parts = ipv4.Match(value)
    if parts.Count() = 5
        for i = 1 to 4
            if Val(parts[i]) > 255 then return false
        end for
        return true
    end if
    hostname = CreateObject("roRegex", "^[A-Za-z0-9]([A-Za-z0-9-]*[A-Za-z0-9])?(\.[A-Za-z0-9]([A-Za-z0-9-]*[A-Za-z0-9])?)*$", "")
    return hostname.IsMatch(value)
end function

function IsValidPort(value as string) as boolean
    digits = CreateObject("roRegex", "^\d{1,5}$", "")
    if not digits.IsMatch(value) then return false
    port = Val(value)
    return port >= 1 and port <= 65535
end function

' ---------- keys ----------

function onKeyEvent(key as string, press as boolean) as boolean
    if not press or not m.top.visible then return false
    if key = "up"
        if m.focusIndex > 0 then m.focusIndex = m.focusIndex - 1
        UpdateFocus()
        return true
    else if key = "down"
        if m.focusIndex < m.rows.Count() - 1 then m.focusIndex = m.focusIndex + 1
        UpdateFocus()
        return true
    else if key = "OK"
        if m.focusIndex = 0
            OpenKeyboard("host")
        else if m.focusIndex = 1
            OpenKeyboard("port")
        else if m.top.host = ""
            ShowValidationError("Enter the server IP address first.")
            m.focusIndex = 0
            UpdateFocus()
        else
            m.top.action = "connect"
        end if
        return true
    else if key = "back"
        m.top.action = "back"
        return true
    end if
    return false
end function
