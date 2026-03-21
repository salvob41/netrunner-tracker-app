"""
Game event log for the Netrunner Tracker.

Separated from GameState because the log is presentational — it
captures what happened for the player's benefit but doesn't affect
any game rule or win condition.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class LogEntry:
    """Immutable record of a single game event."""
    round: int
    player: str   # "corp", "runner", or "game"
    symbol: str   # unicode glyph matching the event type
    message: str  # e.g. "Click spent (2/3)", "+3 credits → 8¢"


class GameLog:
    """
    Append-only ring buffer of game events.

    Entries are stored newest-first so the ListView shows recent events
    at the top without reversing.  MAX_ENTRIES caps memory; the oldest
    entry is silently dropped when full.
    """

    MAX_ENTRIES = 80

    def __init__(self) -> None:
        self.entries: list[LogEntry] = []

    def record(
        self,
        round: int,
        player: str,
        symbol: str,
        message: str,
    ) -> None:
        self.entries.insert(0, LogEntry(round, player, symbol, message))
        if len(self.entries) > self.MAX_ENTRIES:
            self.entries.pop()

    def clear(self) -> None:
        self.entries.clear()
