' Off-device unit tests for pure helpers. Run with: npm test
sub Main()
    m.failures = 0
    m.count = 0

    ' SeekCalcTarget: +15 / -15 and clamping (F-07, F-08, F-09)
    AssertEqual(SeekCalcTarget(30, 150, 15, 3), 45, "+15 at 0:30 lands at 0:45")
    AssertEqual(SeekCalcTarget(30, 150, -15, 3), 15, "-15 at 0:30 lands at 0:15")
    AssertEqual(SeekCalcTarget(5, 150, -15, 3), 0, "-15 at 0:05 clamps to 0:00")
    AssertEqual(SeekCalcTarget(140, 150, 15, 3), 147, "+15 near end clamps to duration - margin")
    AssertEqual(SeekCalcTarget(149, 150, 15, 3), 147, "+15 past the end never exceeds safe end")
    AssertEqual(SeekCalcTarget(2, 2, 15, 3), 0, "clip shorter than margin clamps to 0")
    AssertEqual(SeekCalcTarget(30.5, 6480, 15, 3), 45.5, "fractional positions are kept")
    AssertInvalid(SeekCalcTarget(30, 0, 15, 3), "unknown duration means seek unavailable")
    AssertInvalid(SeekCalcTarget(invalid, 100, 15, 3), "unknown position means seek unavailable")

    ' SeekHasLanded
    AssertTrue(SeekHasLanded(44.2, 45, 3, false), "within tolerance has landed")
    AssertTrue(not SeekHasLanded(30, 45, 3, false), "old position has not landed")
    AssertTrue(SeekHasLanded(38, 45, 3, true), "settling after buffering counts as landed")
    AssertTrue(not SeekHasLanded(invalid, 45, 3, false), "invalid position has not landed")

    ' SeekDeltaLabel
    AssertEqual(SeekDeltaLabel(15), "+15s", "positive delta label")
    AssertEqual(SeekDeltaLabel(-30), "-30s", "queued negative delta label")
    AssertEqual(SeekDeltaLabel(14.6), "+15s", "delta label rounds")

    ' Formatting
    AssertEqual(FormatTime(0), "0:00", "zero time")
    AssertEqual(FormatTime(75.9), "1:15", "minutes and seconds")
    AssertEqual(FormatTime(6480), "1:48:00", "hours")
    AssertEqual(FormatTime(-4), "0:00", "negative clamps")
    AssertEqual(FormatTime(invalid), "0:00", "invalid is zero")
    AssertEqual(FormatRuntime(150), "3m", "short runtime")
    AssertEqual(FormatRuntime(6480), "1h 48m", "long runtime")
    AssertEqual(FormatRuntime(invalid), "", "unknown runtime is blank")
    AssertEqual(CodecLabel("h264"), "H.264", "codec label")
    AssertEqual(CodecLabel("vp9"), "VP9", "unknown codec label is upper-cased")

    if m.failures = 0
        print "TESTS PASSED: "; m.count
    else
        print "TESTS FAILED: "; m.failures; " of "; m.count
    end if
end sub

sub AssertEqual(actual as dynamic, expected as dynamic, name as string)
    m.count = m.count + 1
    ok = false
    if Type(actual) <> "Invalid" and Type(expected) <> "Invalid"
        if GetInterface(actual, "ifString") <> invalid or GetInterface(expected, "ifString") <> invalid
            ok = (Type(actual) = Type(expected) or GetInterface(actual, "ifString") <> invalid) and actual = expected
        else
            ok = Abs(actual - expected) < 0.0001
        end if
    end if
    if not ok
        m.failures = m.failures + 1
        print "FAIL: "; name; " (got "; actual; ", expected "; expected; ")"
    end if
end sub

sub AssertInvalid(actual as dynamic, name as string)
    m.count = m.count + 1
    if actual <> invalid
        m.failures = m.failures + 1
        print "FAIL: "; name; " (got "; actual; ")"
    end if
end sub

sub AssertTrue(value as boolean, name as string)
    m.count = m.count + 1
    if not value
        m.failures = m.failures + 1
        print "FAIL: "; name
    end if
end sub
