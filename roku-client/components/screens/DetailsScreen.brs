sub init()
    m.colors = AppColors()
    m.backdrop = m.top.FindNode("backdrop")
    m.poster = m.top.FindNode("poster")
    m.title = m.top.FindNode("title")
    m.meta = m.top.FindNode("meta")
    m.tech = m.top.FindNode("tech")
    m.status = m.top.FindNode("status")
    m.buttonGroup = m.top.FindNode("buttons")
    m.note = m.top.FindNode("note")
    m.buttons = [m.top.FindNode("playButton"), m.top.FindNode("backButton")]
    m.canPlay = false
    m.focusIndex = 1
    UpdateFocus()
end sub

sub onItemChanged()
    item = m.top.item
    m.title.text = item.title
    m.poster.uri = item.FHDPosterUrl
    m.backdrop.uri = item.FHDPosterUrl
    SetMeta(item.year, item.durationSeconds, invalid, invalid)
    m.tech.text = ""
    SetStatus("Loading details ...", m.colors.muted)
    SetCanPlay(false)
    Layout()
end sub

sub onDetailChanged()
    d = m.top.detail
    if d = invalid then return
    m.title.text = d.title
    SetMeta(d.year, d.duration_seconds, d.width, d.height)

    if d.codecs_verified = true
        m.tech.text = CodecLabel(d.stream_format) + "   " + CodecLabel(d.video_codec) + "   " + CodecLabel(d.audio_codec)
    else
        m.tech.text = "MP4   codecs not verified"
    end if

    if d.playable = true and d.codecs_verified = true
        SetStatus("Ready for direct play", m.colors.accent)
    else if d.playable = true
        SetStatus("Playable, but the server couldn't verify the codecs (install FFmpeg on the PC).", m.colors.warn)
    else
        note = d.compatibility_note
        if note = invalid then note = "Not direct-play compatible"
        SetStatus(note + ". Convert it to MP4 (H.264 video, AAC audio) to play it on Roku.", m.colors.warn)
    end if
    SetCanPlay(d.playable = true)
    Layout()
end sub

sub onLoadError()
    SetStatus("Couldn't load details: " + m.top.loadError, m.colors.error)
    SetCanPlay(false)
    Layout()
end sub

sub SetMeta(year as dynamic, duration as dynamic, width as dynamic, height as dynamic)
    parts = []
    if year <> invalid and year > 0 then parts.Push(year.ToStr())
    runtime = FormatRuntime(duration)
    if runtime <> "" then parts.Push(runtime)
    if width <> invalid and height <> invalid then parts.Push(width.ToStr() + " x " + height.ToStr())
    m.meta.text = parts.Join("     ")
end sub

sub SetStatus(text as string, color as string)
    m.status.text = text
    m.status.color = color
end sub

sub SetCanPlay(canPlay as boolean)
    m.canPlay = canPlay
    if canPlay then m.focusIndex = 0 else m.focusIndex = 1
    UpdateFocus()
end sub

' Stack the right-hand column under a title that may wrap to two lines.
sub Layout()
    y = m.title.BoundingRect().height + 16
    m.meta.translation = [0, y]
    y = y + 56
    m.tech.translation = [0, y]
    y = y + 70
    m.status.translation = [0, y]
    y = y + m.status.BoundingRect().height + 50
    m.buttonGroup.translation = [0, y]
    m.note.translation = [0, y + 150]
end sub

sub UpdateFocus()
    for i = 0 to 1
        button = m.buttons[i]
        focused = (i = m.focusIndex)
        bg = button.FindNode("bg")
        label = button.FindNode("label")
        button.FindNode("focusRing").visible = focused
        if i = 0 and not m.canPlay
            bg.color = m.colors.panel
            label.color = m.colors.disabled
        else if focused
            bg.color = m.colors.accent
            label.color = m.colors.accentText
        else
            bg.color = m.colors.panelRaised
            label.color = m.colors.text
        end if
    end for
end sub

function onKeyEvent(key as string, press as boolean) as boolean
    if not press or not m.top.visible then return false
    if key = "left" and m.canPlay
        m.focusIndex = 0
        UpdateFocus()
        return true
    else if key = "right"
        m.focusIndex = 1
        UpdateFocus()
        return true
    else if key = "OK" or key = "play"
        if key = "play" and m.canPlay then m.focusIndex = 0
        if m.focusIndex = 0 and m.canPlay
            m.top.action = "play"
        else if m.focusIndex = 1 and key = "OK"
            m.top.action = "back"
        end if
        return true
    else if key = "back"
        m.top.action = "back"
        return true
    end if
    return false
end function
