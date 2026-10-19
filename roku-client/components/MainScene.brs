' Navigation controller: owns the screen stack, the saved server address and all API calls.

sub init()
    m.top.backgroundColor = AppColors().bg
    m.top.backgroundUri = ""
    m.global.AddFields({ serverBase: "" })

    m.screens = m.top.FindNode("screens")
    m.stack = []
    m.requests = {}
    m.registry = CreateObject("roRegistrySection", "LanMedia")
    ' Re-asserts focus shortly after each screen change, in case a closing dialog or a
    ' grid selection event hands focus back to a screen that is now hidden.
    m.focusGuard = CreateObject("roSGNode", "Timer")
    m.focusGuard.duration = 0.3
    m.focusGuard.ObserveField("fire", "onFocusGuard")

    m.connection = CreateObject("roSGNode", "ConnectionScreen")
    m.connection.ObserveField("action", "onConnectionAction")
    m.connection.host = m.registry.Read("host")
    m.connection.port = m.registry.Read("port")
    if m.connection.port = "" then m.connection.port = "8080"
    PushScreen(m.connection)

    if m.connection.host <> ""
        Connect()
    else
        m.connection.statusKind = "info"
        m.connection.statusText = "Not connected yet."
    end if
end sub

' ---------- screen stack ----------

sub PushScreen(screen as object)
    if m.stack.Count() > 0 then m.stack.Peek().visible = false
    m.screens.AppendChild(screen)
    m.stack.Push(screen)
    screen.visible = true
    screen.SetFocus(true)
    RefocusSoon()
end sub

sub PopScreen()
    if m.stack.Count() <= 1
        m.top.exitApp = true
        return
    end if
    screen = m.stack.Pop()
    screen.visible = false
    if not screen.IsSameNode(m.connection) then m.screens.RemoveChild(screen)
    top = m.stack.Peek()
    top.visible = true
    top.SetFocus(true)
    RefocusSoon()
end sub

sub RefocusSoon()
    m.focusGuard.control = "stop"
    m.focusGuard.control = "start"
end sub

sub onFocusGuard()
    if m.stack.Count() = 0 then return
    top = m.stack.Peek()
    if not top.IsInFocusChain() then top.SetFocus(true)
end sub

' Drop every screen above the connection screen (which is always m.stack[0]).
sub ResetToConnection()
    while m.stack.Count() > 1
        screen = m.stack.Pop()
        if not screen.IsSameNode(m.connection) then m.screens.RemoveChild(screen)
    end while
end sub

sub ShowGrid(items as object)
    ResetToConnection()
    m.grid = CreateObject("roSGNode", "PosterGridScreen")
    m.grid.ObserveField("action", "onGridAction")
    m.grid.serverLabel = m.connection.host + ":" + m.connection.port
    m.grid.content = BuildGridContent(items)
    PushScreen(m.grid)
end sub

' ---------- networking ----------

sub Request(kind as string, path as string, callback as string)
    task = CreateObject("roSGNode", "CatalogTask")
    task.url = m.global.serverBase + path
    task.ObserveField("response", callback)
    m.requests[kind] = task
    task.control = "run"
end sub

' Ignore responses from requests that were superseded (e.g. user re-connected).
function IsCurrent(kind as string, event as object) as boolean
    task = m.requests[kind]
    if task = invalid or not task.IsSameNode(event.GetRoSGNode()) then return false
    m.requests.Delete(kind)
    return true
end function

sub Connect()
    m.global.serverBase = "http://" + m.connection.host + ":" + m.connection.port
    m.connection.statusKind = "busy"
    m.connection.statusText = "Connecting to " + m.connection.host + ":" + m.connection.port + " ..."
    Request("health", "/api/health", "onHealth")
end sub

sub onHealth(event as object)
    if not IsCurrent("health", event) then return
    resp = event.GetData()
    if not resp.ok
        ShowConnectionError("Can't reach the server at " + m.connection.host + ":" + m.connection.port + ". Check that start_server.bat is running, the IP and port are right, and Windows Firewall allows the port. (" + resp.error + ")")
        return
    end if
    if Type(resp.data) <> "roAssociativeArray" or resp.data.service <> "roku-lan-media"
        ShowConnectionError("Something answered at that address, but it isn't a LAN Media server.")
        return
    end if
    m.registry.Write("host", m.connection.host)
    m.registry.Write("port", m.connection.port)
    m.registry.Flush()
    m.connection.statusText = "Loading library ..."
    Request("media", "/api/media", "onMediaList")
end sub

sub onMediaList(event as object)
    if not IsCurrent("media", event) then return
    resp = event.GetData()
    if not resp.ok or Type(resp.data) <> "roAssociativeArray" or Type(resp.data.items) <> "roArray"
        message = "unexpected response"
        if not resp.ok then message = resp.error
        ShowConnectionError("Connected, but the library failed to load (" + message + ").")
        return
    end if
    m.connection.statusKind = "ok"
    m.connection.statusText = "Connected to " + m.connection.host + ":" + m.connection.port
    ShowGrid(resp.data.items)
end sub

sub ShowConnectionError(message as string)
    m.connection.statusKind = "error"
    m.connection.statusText = message
    if not m.stack.Peek().IsSameNode(m.connection)
        ResetToConnection()
        m.connection.visible = true
        m.connection.SetFocus(true)
        RefocusSoon()
    end if
end sub

function BuildGridContent(items as object) as object
    root = CreateObject("roSGNode", "ContentNode")
    for each item in items
        node = root.CreateChild("ContentNode")
        node.AddFields({ mediaId: item.id, playable: item.playable = true, year: 0, durationSeconds: 0 })
        node.title = item.title
        if item.year <> invalid then node.year = item.year
        if item.duration_seconds <> invalid then node.durationSeconds = item.duration_seconds
        node.FHDPosterUrl = m.global.serverBase + item.poster_url
        node.HDPosterUrl = node.FHDPosterUrl
    end for
    return root
end function

' ---------- screen actions ----------

sub onConnectionAction(event as object)
    action = event.GetData()
    if action = "connect"
        Connect()
    else if action = "back"
        ' Back from settings returns to the library when one is loaded, otherwise exits.
        if not m.stack.Peek().IsSameNode(m.connection) then return
        if m.stack.Count() > 1
            m.requests.Delete("health")
            m.requests.Delete("media")
            PopScreen()
        else
            m.top.exitApp = true
        end if
    end if
end sub

sub onGridAction(event as object)
    action = event.GetData()
    if action = "select"
        OpenDetails(m.grid.selectedItem)
    else if action = "settings"
        m.connection.statusKind = "ok"
        m.connection.statusText = "Connected to " + m.connection.host + ":" + m.connection.port
        m.stack.Peek().visible = false
        m.stack.Push(m.connection)
        m.connection.visible = true
        m.connection.SetFocus(true)
        RefocusSoon()
    else if action = "back"
        m.top.exitApp = true
    end if
end sub

sub OpenDetails(item as object)
    m.details = CreateObject("roSGNode", "DetailsScreen")
    m.details.ObserveField("action", "onDetailsAction")
    m.details.item = item
    PushScreen(m.details)
    Request("detail", "/api/media/" + item.mediaId, "onDetail")
end sub

sub onDetail(event as object)
    if not IsCurrent("detail", event) or m.details = invalid then return
    resp = event.GetData()
    if resp.ok
        m.details.detail = resp.data
    else
        m.details.loadError = resp.error
    end if
end sub

sub onDetailsAction(event as object)
    action = event.GetData()
    if action = "play"
        detail = m.details.detail
        content = CreateObject("roSGNode", "ContentNode")
        content.url = m.global.serverBase + detail.stream_url
        content.streamFormat = "mp4"
        content.title = detail.title
        player = CreateObject("roSGNode", "PlaybackScreen")
        player.ObserveField("action", "onPlaybackAction")
        player.content = content
        PushScreen(player)
    else if action = "back"
        m.requests.Delete("detail")
        m.details = invalid
        PopScreen()
    end if
end sub

sub onPlaybackAction(event as object)
    if event.GetData() = "exit" then PopScreen()
end sub

function onKeyEvent(key as string, press as boolean) as boolean
    ' Screens handle their own keys. A key that bubbles here while the top screen is
    ' out of the focus chain means focus was lost (e.g. a dialog restored focus late).
    if press and m.stack.Count() > 0
        top = m.stack.Peek()
        if not top.IsInFocusChain()
            top.SetFocus(true)
            return true
        end if
    end if
    return false
end function
