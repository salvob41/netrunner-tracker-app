"""
Pure game-state model for Android: Netrunner.

No Flet imports — state is entirely decoupled from the UI layer so it
stays testable and can gain save/load or undo history without touching
any widget.

Turn structure (standard Netrunner):
  1. Corp takes their full turn (3 clicks + mandatory draw)
  2. Runner takes their full turn (4 clicks)
  = 1 complete round

active_player tracks whose half-turn it is so the UI can highlight the
right panel and label the End Turn button correctly.
"""


class GameState:
    """
    Tracks all mutable values for one Corp vs Runner match.

    Class constants encode the rules; instance attributes encode the
    current game state.  Nothing here knows about widgets or rendering.
    """

    CORP_CLICKS_PER_TURN   = 3
    RUNNER_CLICKS_PER_TURN = 4
    STARTING_CREDITS       = 5
    BASE_HAND_SIZE         = 5
    AGENDA_WIN_THRESHOLD   = 7

    def __init__(self) -> None:
        self.round          = 1
        self.active_player  = "corp"       # whose half-turn it currently is

        # Corp
        self.corp_clicks    = self.CORP_CLICKS_PER_TURN
        self.corp_credits   = self.STARTING_CREDITS
        self.corp_agenda    = 0
        self.corp_drew      = False        # mandatory draw taken this turn?
        self.corp_bad_pub   = 0            # bad publicity tokens on the Corp

        # Runner
        self.runner_clicks  = self.RUNNER_CLICKS_PER_TURN
        self.runner_credits = self.STARTING_CREDITS
        self.runner_agenda  = 0
        self.runner_tags    = 0            # each tag lets Corp retaliate (SYNC, etc.)
        self.runner_brain   = 0            # permanent -1 hand size per token
        self.runner_net     = 0            # net damage dealt this game

    # ── Computed properties ───────────────────────────────────────────────────

    @property
    def runner_hand_size(self) -> int:
        # Brain damage is the only permanent card-disadvantage effect in
        # standard Netrunner — clamped at 0 so the display never goes negative.
        return max(0, self.BASE_HAND_SIZE - self.runner_brain)

    @property
    def winner(self) -> str | None:
        """'corp', 'runner', or None.  Checked after every agenda change."""
        if self.corp_agenda   >= self.AGENDA_WIN_THRESHOLD:
            return "corp"
        if self.runner_agenda >= self.AGENDA_WIN_THRESHOLD:
            return "runner"
        return None

    @property
    def agenda_bar_ratio(self) -> float:
        """
        Corp's share of scored agendas (0.0–1.0) for the pip display.
        Returns 0.5 when nobody has scored so the UI starts in a neutral state.
        """
        total = self.corp_agenda + self.runner_agenda
        return self.corp_agenda / total if total > 0 else 0.5

    # ── Mutations ─────────────────────────────────────────────────────────────

    def end_turn(self) -> None:
        """
        Advance the active_player.

        Corp → Runner: give Runner their clicks (they start fresh).
        Runner → Corp: new round begins; refill Corp's clicks, reset draw.
        Clicks are refilled HERE (not in the button handler) so the rule
        "clicks restore at turn start" is enforced by the model, not the UI.
        """
        if self.active_player == "corp":
            self.active_player  = "runner"
            self.runner_clicks  = self.RUNNER_CLICKS_PER_TURN
        else:
            self.round         += 1
            self.active_player  = "corp"
            self.corp_clicks    = self.CORP_CLICKS_PER_TURN
            self.corp_drew      = False

    def toggle_mandatory_draw(self) -> None:
        # Corp must draw once per turn before other actions.
        # A boolean toggle is simpler than a separate phase system.
        self.corp_drew = not self.corp_drew

    def adjust(self, attr: str, delta: int,
               min_val: int = 0, max_val: int = 99) -> None:
        """
        Bounded increment for any numeric attribute.
        Central clamp keeps min/max logic out of individual button handlers
        so limits can't drift out of sync.
        """
        current = getattr(self, attr)
        setattr(self, attr, max(min_val, min(max_val, current + delta)))

    def spend_click(self, player: str) -> None:
        """Spend one click for the given player (tapping a filled token)."""
        attr = f"{player}_clicks"
        self.adjust(attr, -1, 0, self.CORP_CLICKS_PER_TURN if player == "corp"
                    else self.RUNNER_CLICKS_PER_TURN)

    def restore_click(self, player: str) -> None:
        """Restore one click for the given player (tapping a spent token)."""
        max_clicks = (self.CORP_CLICKS_PER_TURN if player == "corp"
                      else self.RUNNER_CLICKS_PER_TURN)
        attr = f"{player}_clicks"
        self.adjust(attr, +1, 0, max_clicks)

    def reset(self) -> None:
        # Reinitialise own __dict__ — guaranteed to stay in sync when
        # new fields are added later.
        self.__init__()
