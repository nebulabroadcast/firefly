"""Timecode and duration formatting.

Positions are stored as float seconds, so a frame start such as 29 / 25
(1.16) may come out as 1.15999... Everything is nudged by EPSILON (far less
than a frame) before truncating, so frames are never shown one too early.
"""

import math

EPSILON = 1e-6


def _clean(secs: float) -> float:
    """Clamp to >= 0 and nudge by EPSILON. ValueError for non-numbers/NaN/inf."""
    secs = float(secs)
    if not math.isfinite(secs):
        raise ValueError(secs)
    return max(0.0, secs) + EPSILON


def s2tc(secs: float, base: float = 25) -> str:
    """Convert seconds to an SMPTE timecode (HH:MM:SS:FF).

    Frames are counted within each wall-clock second, as the Nebula web
    frontend does, so fractional frame rates (29.97) match the web.
    """
    try:
        secs = _clean(secs)
    except ValueError:
        return "--:--:--:--"
    whole = int(secs)
    ff = int((secs - whole) * base)
    hh, rem = divmod(whole, 3600)
    mm, ss = divmod(rem, 60)
    return f"{hh % 24:02d}:{mm:02d}:{ss:02d}:{ff:02d}"


def tc2s(tc: str, base: float = 25) -> float:
    """Convert an SMPTE timecode (HH:MM:SS:FF, ';' also accepted) to seconds."""
    hh, mm, ss, ff = (int(e) for e in tc.replace(";", ":").split(":"))
    return hh * 3600 + mm * 60 + ss + ff / float(base)


def s2time(secs: float, show_secs: bool = True, show_fracs: bool = True) -> str:
    """Convert seconds to HH:MM, HH:MM:SS or HH:MM:SS.CS"""
    try:
        secs = _clean(secs)
    except ValueError:
        placeholder = "--:--"
        if show_secs:
            placeholder += ":--"
            if show_fracs:
                placeholder += ".--"
        return placeholder
    whole = int(secs)
    centisecs = int((secs - whole) * 100)
    hh, rem = divmod(whole, 3600)
    mm, ss = divmod(rem, 60)
    result = f"{hh % 24:02d}:{mm:02d}"
    if show_secs:
        result += f":{ss:02d}"
        if show_fracs:
            result += f".{centisecs:02d}"
    return result
