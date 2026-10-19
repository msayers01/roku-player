' Playback + HUD. The SeekController described in the design lives here as the
' m.seek state machine; the clamping math is in common/SeekMath.brs.

sub init()
    m.colors = AppColors()
    m.SKIP_SECONDS = 15
    m.END_MARGIN = 3        ' never seek closer than this to EOF
    m.SEEK_TOLERANCE = 3    ' keyframe snapping can land a little off target
    m.TRACK_WIDTH = 1680

    m.video = m.top.FindNode("video")
    m.video.notificationInterval = 0.5
    m.video.ObserveField("state", "onVideoState")
    m.video.ObserveField("position", "onVideoPosition")
    m.video.ObserveField("duration", "onVideoDuration")
    m.video.ObserveField("bufferingStatus", "onBufferingStatus")

    m.hud = m.top.FindNode("hud")
    m.title = m.top.FindNode("title")
    m.track = m.top.FindNode("track")
    m.fill = m.top.FindNode("fill")
    m.marker = m.top.FindNode("marker")
    m.positionLabel = m.top.FindNode("position")
    m.durationLabel = m.top.FindNode("duration")
    m.buffering = m.top.FindNode("buffering")
    m.buffering.text = "Loading ..."
    m.buttons = [m.top.FindNode("back15"), m.top.FindNode("playPause"), m.top.FindNode("fwd15"), m.top.FindNode("audio")]
    m.playPauseLabel = m.buttons[1].FindNode("label")

    m.toast = m.top.FindNode("toast")
    m.toastMain = m.top.FindNode("toastMain")
    m.toastSub = m.top.FindNode("toastSub")
    m.panel = m.top.FindNode("panel")
    m.panelBar = m.top.FindNode("panelBar")
    m.panelTitle = m.top.FindNode("panelTitle")
    m.panelBody = m.top.FindNode("panelBody")
    m.panelHint = m.top.FindNode("panelHint")

    m.hudTimer = m.top.FindNode("hudTimer")
    m.hudTimer.ObserveField("fire", "onHudTimer")
    m.toastTimer = m.top.FindNode("toastTimer")
    m.toastTimer.ObserveField("fire", "onToastTimer")
    m.seekTimer = m.top.FindNode("seekTimer")
    m.seekTimer.ObserveField("fire", "onSeekTimeout")

    m.seek = { inFlight: false, target: 0, queued: invalid, sawBuffering: false, toastDelta: 0 }
    ' The user's own pause intent. Seeking while paused stays paused, even if the
    ' player resumes by itself once the seek lands.
    m.userPaused = false
    m.pausedPosition = invalid
    m.focusIndex = 1
    m.timelineFocused = false
    m.scrubTarget = invalid
    m.overlay = ""
    m.exiting = false
    UpdateButtons()
end sub

sub onContentChanged()
    m.title.text = m.top.content.title
    m.video.content = m.top.content
    m.video.control = "play"
    ShowHud()
end sub

' ---------- video events ----------

sub onVideoState()
    state = m.video.state
    m.buffering.visible = (state = "buffering" or state = "none")
    if state = "buffering"
        m.buffering.text = "Loading ..."
        if m.seek.inFlight then m.seek.sawBuffering = true
    else if state = "playing" or state = "paused"
        if state = "playing" and m.userPaused then m.video.control = "pause"
        UpdatePlayPause()
        if m.seek.inFlight and m.seek.sawBuffering then CompleteSeek()
        if m.video.state = "paused" then ShowHud() else RestartHudTimer()
    else if state = "finished"
        ExitPlayback()
    else if state = "error"
        ShowError()
    end if
end sub

sub onVideoPosition()
    ' Some players resume on their own after a seek; hold the user's pause.
    if m.userPaused and not m.seek.inFlight and m.pausedPosition <> invalid
        if m.video.position - m.pausedPosition > 1
            m.video.control = "pause"
            m.pausedPosition = m.video.position
        end if
    end if
    if m.seek.inFlight and SeekHasLanded(m.video.position, m.seek.target, m.SEEK_TOLERANCE, false)
        CompleteSeek()
    end if
    UpdateProgress()
end sub

sub onVideoDuration()
    UpdateProgress()
end sub

sub onBufferingStatus()
    status = m.video.bufferingStatus
    if status <> invalid and status.percentage <> invalid
        m.buffering.text = "Loading ... " + status.percentage.ToStr() + "%"
    end if
end sub

' ---------- seek controller ----------

function CanSeek() as boolean
    state = m.video.state
    return m.video.duration > 0 and (state = "playing" or state = "paused" or state = "buffering")
end function

sub SeekBy(delta as dynamic)
    if not CanSeek()
        ShowToast("Seek unavailable", "Wait for the video to load")
        return
    end if

    ' Repeated taps build on the newest pending target rather than a stale position.
    base = m.video.position
    if m.seek.inFlight
        base = m.seek.target
        if m.seek.queued <> invalid then base = m.seek.queued
    end if

    target = SeekCalcTarget(base, m.video.duration, delta, m.END_MARGIN)
    if target = invalid
        ShowToast("Seek unavailable", "")
        return
    end if
    if Abs(target - base) < 0.5
        if delta < 0 then ShowToast("Start", "Already at the beginning") else ShowToast("End", "Can't skip past the end")
        return
    end if

    if m.seek.inFlight
        m.seek.queued = target
        m.seek.toastDelta = m.seek.toastDelta + (target - base)
    else
        m.seek.toastDelta = target - base
        IssueSeek(target)
    end if
    ShowToast(SeekDeltaLabel(m.seek.toastDelta), "to " + FormatTime(target))
    UpdateProgress()
end sub

sub IssueSeek(target as dynamic)
    m.seek.inFlight = true
    m.seek.target = target
    m.seek.sawBuffering = false
    m.video.seek = target
    m.seekTimer.control = "stop"
    m.seekTimer.control = "start"
end sub

sub CompleteSeek()
    m.seekTimer.control = "stop"
    m.seek.inFlight = false
    if m.seek.queued <> invalid
        nextTarget = m.seek.queued
        m.seek.queued = invalid
        IssueSeek(nextTarget)
        return
    end if
    m.pausedPosition = m.video.position
    UpdateProgress()
end sub

sub onSeekTimeout()
    if not m.seek.inFlight then return
    m.seek.inFlight = false
    m.seek.queued = invalid
    ShowToast("Seek failed", "Try again")
    UpdateProgress()
end sub

' Timeline scrubbing (HUD timeline row, or FF/RW keys): move a marker, OK commits.
sub Scrub(direction as integer)
    duration = m.video.duration
    if not CanSeek()
        ShowToast("Seek unavailable", "Wait for the video to load")
        return
    end if
    stepSeconds = 10
    if duration >= 600 then stepSeconds = 30
    if duration >= 3600 then stepSeconds = 60
    if m.scrubTarget = invalid then m.scrubTarget = m.video.position
    m.scrubTarget = SeekCalcTarget(m.scrubTarget, duration, direction * stepSeconds, m.END_MARGIN)
    ShowHud()
    m.timelineFocused = true
    UpdateButtons()
    UpdateProgress()
end sub

sub CommitScrub()
    if m.scrubTarget = invalid then return
    target = m.scrubTarget
    m.scrubTarget = invalid
    delta = target - m.video.position
    if m.seek.inFlight
        m.seek.queued = target
    else
        IssueSeek(target)
    end if
    m.seek.toastDelta = delta
    ShowToast(SeekDeltaLabel(delta), "to " + FormatTime(target))
    RestartHudTimer()
    UpdateProgress()
end sub

sub CancelScrub()
    m.scrubTarget = invalid
    UpdateProgress()
end sub

' ---------- HUD ----------

sub TogglePause()
    state = m.video.state
    if state = "playing" or state = "buffering"
        m.userPaused = true
        m.pausedPosition = m.video.position
        m.video.control = "pause"
    else if state = "paused"
        m.userPaused = false
        m.video.control = "resume"
    end if
end sub

sub UpdatePlayPause()
    if m.userPaused or m.video.state = "paused" then m.playPauseLabel.text = "Play" else m.playPauseLabel.text = "Pause"
end sub

sub UpdateProgress()
    duration = m.video.duration
    shown = m.video.position
    if m.scrubTarget <> invalid
        shown = m.scrubTarget
    else if m.seek.inFlight
        shown = m.seek.target
        if m.seek.queued <> invalid then shown = m.seek.queued
    end if

    fraction = 0
    if duration > 0 then fraction = shown / duration
    if fraction < 0 then fraction = 0
    if fraction > 1 then fraction = 1
    m.fill.width = m.TRACK_WIDTH * fraction
    m.marker.translation = [m.TRACK_WIDTH * fraction - 4, -12]
    m.positionLabel.text = FormatTime(shown)
    if duration > 0 then m.durationLabel.text = FormatTime(duration) else m.durationLabel.text = "--:--"
end sub

sub UpdateButtons()
    for i = 0 to m.buttons.Count() - 1
        button = m.buttons[i]
        focused = (i = m.focusIndex) and not m.timelineFocused
        button.FindNode("focusRing").visible = focused
        if focused
            button.FindNode("bg").color = m.colors.accent
            button.FindNode("label").color = m.colors.accentText
        else
            button.FindNode("bg").color = m.colors.panelRaised
            button.FindNode("label").color = m.colors.text
        end if
    end for
    m.marker.visible = m.timelineFocused
    if m.timelineFocused
        m.track.height = 16
        m.fill.height = 16
        m.track.translation = [0, -3]
        m.fill.translation = [0, -3]
    else
        m.track.height = 10
        m.fill.height = 10
        m.track.translation = [0, 0]
        m.fill.translation = [0, 0]
    end if
end sub

sub ShowHud()
    m.hud.visible = true
    UpdatePlayPause()
    UpdateProgress()
    RestartHudTimer()
end sub

sub HideHud()
    m.hud.visible = false
    m.timelineFocused = false
    m.scrubTarget = invalid
    m.focusIndex = 1
    UpdateButtons()
end sub

sub RestartHudTimer()
    m.hudTimer.control = "stop"
    m.hudTimer.control = "start"
end sub

sub onHudTimer()
    ' Stay up while paused, scrubbing or showing a panel.
    if m.userPaused or m.video.state = "paused" or m.scrubTarget <> invalid or m.overlay <> "" then return
    HideHud()
end sub

sub ShowToast(main as string, detail as string)
    m.toastMain.text = main
    m.toastSub.text = detail
    m.toast.visible = true
    m.toastTimer.control = "stop"
    m.toastTimer.control = "start"
end sub

sub onToastTimer()
    m.toast.visible = false
end sub

sub ActivateButton(index as integer)
    if index = 0
        SeekBy(-m.SKIP_SECONDS)
    else if index = 1
        TogglePause()
    else if index = 2
        SeekBy(m.SKIP_SECONDS)
    else if index = 3
        ShowAudioInfo()
    end if
end sub

' ---------- panels ----------

' F-12: EQ is designed but not available, so say so plainly instead of offering fake presets.
sub ShowAudioInfo()
    ShowPanel("audio", "Audio EQ isn't available", "Roku's built-in video player doesn't give apps an equalizer, so this app can't change how movies sound. Presets like Dialogue, Movie or Night are planned only if a real way to apply them is found. For now, use your TV or soundbar's sound settings.", "OK  close", m.colors.accent)
end sub

sub ShowError()
    m.seekTimer.control = "stop"
    message = m.video.errorMsg
    if message = invalid or message = "" then message = "unknown error"
    ShowPanel("error", "Playback failed", "The video stopped with: " + message + ". The PC server may have stopped, gone to sleep or lost the network, or the file may not be direct-play compatible.", "OK  back to details", m.colors.error)
end sub

sub ShowPanel(kind as string, title as string, body as string, hint as string, accent as string)
    m.overlay = kind
    m.panelTitle.text = title
    m.panelBody.text = body
    m.panelHint.text = hint
    m.panelBar.color = accent
    m.panel.visible = true
    m.toast.visible = false
end sub

sub ClosePanel()
    m.overlay = ""
    m.panel.visible = false
    RestartHudTimer()
end sub

sub ExitPlayback()
    if m.exiting then return
    m.exiting = true
    m.hudTimer.control = "stop"
    m.toastTimer.control = "stop"
    m.seekTimer.control = "stop"
    m.video.control = "stop"
    m.top.action = "exit"
end sub

' ---------- keys ----------

function onKeyEvent(key as string, press as boolean) as boolean
    if not press or not m.top.visible then return false

    if m.overlay <> ""
        if key = "OK" or key = "back"
            if m.overlay = "error" then ExitPlayback() else ClosePanel()
        end if
        return true
    end if

    if key = "back"
        if m.scrubTarget <> invalid
            CancelScrub()
        else if m.hud.visible
            HideHud()
        else
            ExitPlayback()
        end if
        return true
    else if key = "play"
        TogglePause()
        ShowHud()
        return true
    else if key = "replay"
        ' Optional shortcut from the design: Replay jumps back 15 seconds.
        SeekBy(-m.SKIP_SECONDS)
        return true
    else if key = "fwd"
        Scrub(1)
        return true
    else if key = "rev"
        Scrub(-1)
        return true
    end if

    if not m.hud.visible
        ShowHud()
        return true
    end if
    RestartHudTimer()

    if m.timelineFocused
        if key = "left"
            Scrub(-1)
        else if key = "right"
            Scrub(1)
        else if key = "OK"
            CommitScrub()
        else if key = "down"
            CancelScrub()
            m.timelineFocused = false
            UpdateButtons()
        end if
        return true
    end if

    if key = "left" and m.focusIndex > 0
        m.focusIndex = m.focusIndex - 1
    else if key = "right" and m.focusIndex < m.buttons.Count() - 1
        m.focusIndex = m.focusIndex + 1
    else if key = "up"
        m.timelineFocused = true
    else if key = "OK"
        ActivateButton(m.focusIndex)
    end if
    UpdateButtons()
    return true
end function
