sub init()
    m.top.functionName = "fetchJson"
end sub

sub fetchJson()
    m.top.response = HttpGetJson(m.top.url, m.top.timeoutMs)
end sub

' Returns { ok, status, data } on success or { ok: false, status, error } on failure.
function HttpGetJson(url as string, timeoutMs as integer) as object
    port = CreateObject("roMessagePort")
    xfer = CreateObject("roUrlTransfer")
    xfer.SetMessagePort(port)
    xfer.SetUrl(url)
    xfer.AddHeader("Accept", "application/json")
    xfer.RetainBodyOnError(true)
    if not xfer.AsyncGetToString() then return { ok: false, status: 0, error: "Could not start the request" }

    msg = Wait(timeoutMs, port)
    if msg = invalid
        xfer.AsyncCancel()
        return { ok: false, status: 0, error: "No response after " + Int(timeoutMs / 1000).ToStr() + " seconds" }
    end if
    if Type(msg) <> "roUrlEvent" then return { ok: false, status: 0, error: "Unexpected network event" }

    code = msg.GetResponseCode()
    if code <= 0
        reason = msg.GetFailureReason()
        if reason = invalid or reason = "" then reason = "no response"
        return { ok: false, status: code, error: reason }
    end if

    body = msg.GetString()
    data = invalid
    if body <> invalid and body <> "" then data = ParseJson(body)
    if code <> 200
        message = "Server returned HTTP " + code.ToStr()
        if Type(data) = "roAssociativeArray" and Type(data.error) = "roAssociativeArray" and data.error.message <> invalid
            message = data.error.message
        end if
        return { ok: false, status: code, error: message }
    end if
    if data = invalid then return { ok: false, status: code, error: "The server sent a response this app can't read" }
    return { ok: true, status: code, data: data }
end function
