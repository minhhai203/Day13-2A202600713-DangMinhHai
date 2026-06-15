"""Minimal compatibility shim for runtimes missing stdlib `zoneinfo`."""
from __future__ import annotations

from datetime import timedelta, tzinfo


class ZoneInfoNotFoundError(KeyError):
    pass


class ZoneInfo(tzinfo):
    """Fallback that behaves like a fixed UTC offset."""

    def __init__(self, key: str):
        self.key = key

    def utcoffset(self, dt):
        return timedelta(0)

    def dst(self, dt):
        return timedelta(0)

    def tzname(self, dt):
        return self.key

    def fromutc(self, dt):
        return dt.replace(tzinfo=self)


__all__ = ["ZoneInfo", "ZoneInfoNotFoundError"]
