# UX Overhaul Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a game log, credit debouncing with delta badge, and improved click token UX to the Netrunner Tracker.

**Architecture:** The game log is a new pure-Python data model (`game_log.py`) wired into `tracker.py` via handler factories. Credit debounce uses `threading.Timer` to batch rapid taps into one log entry. Click tokens get bigger touch targets, a count display, and a refill button. All new UI primitives live in `components.py`.

**Tech Stack:** Python 3.13, Flet 0.82, threading.Timer for debounce

**Spec:** `docs/superpowers/specs/2026-03-21-ux-overhaul-design.md`

---

## File Structure

| File | Responsibility | Change type |
|---|---|---|
| `game_log.py` | `LogEntry` dataclass + `GameLog` ring buffer | **New** |
| `theme.py` | Add 6 `SYM_*` unicode constants for log symbols | Modify |
| `components.py` | Update `click_token`/`click_tokens_row`, add `refill_button`, `credit_row`, `log_entry_row` | Modify |
| `tracker.py` | Add log, debounce, `_stat_adjuster`, `_credit_adjuster`, log panel, improved click sections | Modify |
| `state.py` | No changes | — |
| `main.py` | No changes | — |

---

## Chunk 1: Data Model + Theme

### Task 1: Create game_log.py

**Files:**
- Create: `game_log.py`

- [ ] **Step 1: Create game_log.py with LogEntry and GameLog**

```python
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
```

- [ ] **Step 2: Verify import works**

Run: `python3 -c "from game_log import GameLog, LogEntry; g = GameLog(); g.record(1, 'corp', '◆', 'test'); print(len(g.entries), g.entries[0])"`
Expected: `1 LogEntry(round=1, player='corp', symbol='◆', message='test')`

- [ ] **Step 3: Commit**

```bash
git add game_log.py
git commit -m "feat: add GameLog data model for event tracking"
```

### Task 2: Add log symbols to theme.py

**Files:**
- Modify: `theme.py:52-57` (after existing `SYM_*` constants)

- [ ] **Step 1: Add the 6 new symbol constants**

Append after line 57 (`SYM_HAND = "⎇"`):

```python
SYM_CLICK   = "◆"   # click spent
SYM_CREDIT  = "¢"   # credit change
SYM_TAG     = "⊕"   # tag added/removed
SYM_BRAIN   = "⊗"   # brain damage
SYM_NET     = "⚡"   # net damage
SYM_BAD_PUB = "☢"   # bad publicity
```

- [ ] **Step 2: Verify import**

Run: `python3 -c "import theme; print(theme.SYM_CLICK, theme.SYM_CREDIT, theme.SYM_TAG, theme.SYM_BRAIN, theme.SYM_NET, theme.SYM_BAD_PUB)"`
Expected: `◆ ¢ ⊕ ⊗ ⚡ ☢`

- [ ] **Step 3: Commit**

```bash
git add theme.py
git commit -m "feat: add unicode symbols for game log events"
```

---

## Chunk 2: Component Updates

### Task 3: Update click_token and click_tokens_row

**Files:**
- Modify: `components.py:39-91`

The two key changes:
1. `click_token` — accept `on_tap=None`; when `None`, return plain Container (no GestureDetector)
2. `click_tokens_row` — accept `on_token_tap=None`; use null guard before calling factory
3. Token container size: 44→48px

- [ ] **Step 1: Update click_token**

Replace the `click_token` function (lines 39-70):

```python
def click_token(filled: bool, color: str, on_tap=None) -> ft.Control:
    """
    One click token using the official NSG click symbol.

    When on_tap is provided, the token is wrapped in a GestureDetector
    for tap interaction.  When None (inactive player), it returns a
    plain Container — no tap handler, used as display-only.
    """
    asset = theme.ASSET_CLICK if filled else theme.ASSET_CLICK_SPENT
    icon_color = color if filled else ft.Colors.with_opacity(0.30, color)
    bg = ft.Colors.with_opacity(0.15, color) if filled else "transparent"
    border_color = ft.Colors.with_opacity(0.7, color) if filled else ft.Colors.with_opacity(0.22, color)

    token_container = ft.Container(
        width=48,
        height=48,
        border_radius=6,
        bgcolor=bg,
        border=ft.Border.all(2, border_color),
        alignment=ft.Alignment.CENTER,
        content=ft.Image(
            src=asset,
            width=26,
            height=26,
            fit=ft.BoxFit.CONTAIN,
            color=icon_color,
            color_blend_mode=ft.BlendMode.SRC_IN,
        ),
    )
    if on_tap is not None:
        return ft.GestureDetector(content=token_container, on_tap=on_tap)
    return token_container
```

- [ ] **Step 2: Update click_tokens_row**

Replace the `click_tokens_row` function (lines 73-91):

```python
def click_tokens_row(
    current: int,
    maximum: int,
    color: str,
    on_token_tap=None,
) -> list:
    """
    Builds the list of click tokens for a player's clicks section.

    When on_token_tap is None (inactive player), tokens are display-only
    with no tap handler.  The null guard skips the factory call entirely.
    """
    return [
        click_token(
            filled=(i < current),
            color=color,
            on_tap=on_token_tap(i, i < current) if on_token_tap else None,
        )
        for i in range(maximum)
    ]
```

- [ ] **Step 3: Verify import**

Run: `python3 -c "import components; print('OK')"`
Expected: `OK`

- [ ] **Step 4: Commit**

```bash
git add components.py
git commit -m "feat: click tokens support optional tap handler + 48px size"
```

### Task 4: Add refill_button, credit_row, log_entry_row to components.py

**Files:**
- Modify: `components.py` (append after existing functions, before `action_button`)

- [ ] **Step 1: Add refill_button**

Add before the `action_button` function:

```python
# ── Refill button ─────────────────────────────────────────────────────────

def refill_button(color: str, on_click) -> ft.Container:
    """
    Small correction button to restore all clicks to maximum.
    Muted styling communicates this is a correction, not a primary action.
    """
    return ft.Container(
        content=ft.Text(
            "↺ refill",
            size=10,
            color=ft.Colors.with_opacity(0.5, color),
        ),
        border=ft.Border.all(1, ft.Colors.with_opacity(0.2, color)),
        border_radius=4,
        padding=ft.Padding.symmetric(horizontal=8, vertical=3),
        on_click=on_click,
    )
```

- [ ] **Step 2: Add credit_row**

Add after `refill_button`:

```python
# ── Credit row (with debounce delta badge) ────────────────────────────────

def credit_row(
    color: str,
    value_ref: ft.Text,
    delta_ref: ft.Text,
    timer_bar_ref: ft.Container,
    on_decrement,
    on_increment,
) -> ft.Container:
    """
    Credits stat row with a pending delta badge and timer bar for
    debounce feedback.  The delta_ref and timer_bar_ref are owned by
    the tracker — this component just places them in the layout.
    """
    return ft.Container(
        content=ft.Column(
            [
                ft.Row(
                    [
                        nsg_icon(theme.ASSET_CREDIT, 22, color),
                        ft.Text("Credits", size=11, color=theme.TEXT_SECONDARY, width=62),
                        ft.Row(
                            [value_ref, delta_ref],
                            spacing=6,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                        ft.Row(
                            [
                                stepper("−", on_decrement, color),
                                stepper("+", on_increment, color),
                            ],
                            spacing=4,
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                timer_bar_ref,
            ],
            spacing=2,
        ),
        padding=ft.Padding.symmetric(horizontal=8, vertical=5),
    )
```

- [ ] **Step 3: Add log_entry_row**

Add after `credit_row`:

```python
# ── Log entry row ─────────────────────────────────────────────────────────

def log_entry_row(entry) -> ft.Container:
    """
    One line in the game log.  `entry` is a LogEntry from game_log.py.

    Player label is faction-colored; message uses primary text.
    Import is avoided — we duck-type LogEntry's attributes instead.
    """
    player_colors = {
        "corp":   theme.CORP_ACCENT,
        "runner": theme.RUNNER_ACCENT,
        "game":   theme.AGENDA_GOLD,
    }
    color = player_colors.get(entry.player, theme.TEXT_SECONDARY)

    return ft.Container(
        content=ft.Row(
            [
                ft.Text(
                    f"R{entry.round}·{entry.player.upper()}",
                    size=9,
                    color=ft.Colors.with_opacity(0.6, color),
                    width=64,
                ),
                ft.Text(
                    entry.symbol,
                    size=12,
                    color=color,
                    width=20,
                    text_align=ft.TextAlign.CENTER,
                ),
                ft.Text(
                    entry.message,
                    size=10,
                    color=theme.TEXT_PRIMARY,
                    expand=True,
                ),
            ],
            spacing=6,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        padding=ft.Padding.symmetric(horizontal=10, vertical=4),
        border=ft.Border(
            bottom=ft.BorderSide(1, ft.Colors.with_opacity(0.10, theme.TEXT_SECONDARY)),
        ),
    )
```

- [ ] **Step 4: Verify all imports**

Run: `python3 -c "import components; print('OK')"`
Expected: `OK`

- [ ] **Step 5: Commit**

```bash
git add components.py
git commit -m "feat: add refill_button, credit_row, log_entry_row components"
```

---

## Chunk 3: Tracker — Game Log + Stat Logging

### Task 5: Add GameLog, _stat_adjuster, _refresh_log, and log panel to tracker.py

This is the largest task. It touches `__init__`, `_create_widget_refs`, `refresh`, event handlers, panel builders, and `_build_layout`.

**Files:**
- Modify: `tracker.py`

- [ ] **Step 1: Add imports**

At the top of `tracker.py`, add after the existing imports:

```python
import threading
from game_log import GameLog
```

- [ ] **Step 2: Add log + debounce state to __init__**

In `__init__`, after `self.state = GameState()`, add:

```python
        self.log = GameLog()

        # Credit debounce state (spec §2)
        self._pending_credit = {"corp": 0, "runner": 0}
        self._credit_timer: dict = {"corp": None, "runner": None}

        # Log panel starts expanded
        self._log_expanded = True
```

- [ ] **Step 3: Add log widget refs to _create_widget_refs**

Add at the end of `_create_widget_refs`, before the closing of the method:

```python
        # ── Credit delta badges (spec §2) ────────────────────────────────
        self._corp_credits_delta = ft.Text(
            "", size=13, weight=ft.FontWeight.BOLD,
            color=theme.NEON_GREEN, visible=False,
        )
        self._corp_credits_timer_bar = ft.Container(
            height=2, bgcolor=theme.NEON_GREEN,
            border_radius=1, visible=False,
        )
        self._runner_credits_delta = ft.Text(
            "", size=13, weight=ft.FontWeight.BOLD,
            color=theme.NEON_GREEN, visible=False,
        )
        self._runner_credits_timer_bar = ft.Container(
            height=2, bgcolor=theme.NEON_GREEN,
            border_radius=1, visible=False,
        )

        # ── Click count displays (spec §3) ───────────────────────────────
        self._corp_clicks_count = ft.Text(
            "3 / 3 remaining", size=11, color=theme.TEXT_SECONDARY,
        )
        self._runner_clicks_count = ft.Text(
            "4 / 4 remaining", size=11, color=theme.TEXT_SECONDARY,
        )

        # ── Log panel (spec §1) ─────────────────────────────────────────
        self._log_list = ft.ListView(spacing=0, height=160, padding=0)
        self._log_count_text = ft.Text(
            "0 events", size=10, color=theme.AGENDA_GOLD,
        )
        self._log_toggle_icon = ft.Text(
            "▼", size=12, color=theme.TEXT_SECONDARY,
        )
        self._log_body = ft.Container(
            content=self._log_list,
            bgcolor=ft.Colors.with_opacity(0.3, theme.BG_DARK),
            border_radius=ft.BorderRadius.only(bottom_left=8, bottom_right=8),
            visible=True,
        )
```

- [ ] **Step 4: Add _refresh_log method**

Add after the `refresh` method:

```python
    def _refresh_log(self) -> None:
        """Update just the log panel — called after debounce timer fires."""
        self._log_list.controls = [
            ui.log_entry_row(e) for e in self.log.entries
        ]
        self._log_count_text.value = f"{len(self.log.entries)} events"
        self.page.update()
```

- [ ] **Step 5: Update refresh() to include click counts**

In the `refresh` method, after the click tokens section (after line ~199 where `self._runner_clicks_row.controls = ...`), add:

```python
        # ── Click counts ─────────────────────────────────────────────────
        self._corp_clicks_count.value = (
            f"{s.corp_clicks} / {GameState.CORP_CLICKS_PER_TURN} remaining"
        )
        self._runner_clicks_count.value = (
            f"{s.runner_clicks} / {GameState.RUNNER_CLICKS_PER_TURN} remaining"
        )
```

Also add at the end of `refresh()`, just before `self.page.update()`:

```python
        # ── Log panel ────────────────────────────────────────────────────
        self._refresh_log_inline()
```

And add the inline helper (avoids double `page.update()`):

```python
    def _refresh_log_inline(self) -> None:
        """Update log controls without calling page.update() — used inside refresh()."""
        self._log_list.controls = [
            ui.log_entry_row(e) for e in self.log.entries
        ]
        self._log_count_text.value = f"{len(self.log.entries)} events"
```

- [ ] **Step 6: Add _stat_adjuster handler factory**

Add after the existing `_adjuster` method:

```python
    def _stat_adjuster(self, attr: str, delta: int,
                       min_val: int = 0, max_val: int = 99,
                       symbol: str = "·", label: str = "",
                       suffix_fn=None):
        """
        Like _adjuster but writes an immediate log entry.
        Player is inferred from the attr prefix (corp_ or runner_).
        suffix_fn: optional callable(state) -> str for extra context
        (e.g. brain damage appends "(hand=N)").
        """
        def handle(e):
            self.state.adjust(attr, delta, min_val, max_val)
            val = getattr(self.state, attr)
            player = "corp" if attr.startswith("corp_") else "runner"
            sign = "+" if delta > 0 else ""
            msg = f"{sign}{delta} {label} → {val}"
            if suffix_fn:
                msg += f" {suffix_fn(self.state)}"
            self.log.record(
                self.state.round, player, symbol, msg,
            )
            self.refresh()
        return handle
```

- [ ] **Step 7: Add _on_toggle_log handler**

Add after `_on_reset`:

```python
    def _on_toggle_log(self, e) -> None:
        self._log_expanded = not self._log_expanded
        self._log_body.visible = self._log_expanded
        # ▼ when expanded (content below), ▲ when collapsed (tap to expand)
        self._log_toggle_icon.value = "▼" if self._log_expanded else "▲"
        # Round bottom corners when collapsed (no body below)
        bl = 0 if self._log_expanded else 8
        self._log_header.border_radius = ft.BorderRadius.only(
            top_left=8, top_right=8,
            bottom_left=bl, bottom_right=bl,
        )
        self.page.update()
```

- [ ] **Step 8: Add logging to _on_end_turn**

Replace `_on_end_turn`:

```python
    def _on_end_turn(self, e) -> None:
        # State mutation first — log reads the post-mutation round (spec §1)
        was_corp = self.state.active_player == "corp"
        prev_round = self.state.round
        self.state.end_turn()

        if was_corp:
            self.log.record(
                self.state.round, "game", "→",
                "Corp turn ended · Runner begins",
            )
        else:
            self.log.record(
                self.state.round, "game", theme.SYM_TURN,
                f"Round {prev_round} complete · Round {self.state.round} begins",
            )

        # Check for win after turn change
        winner = self.state.winner
        if winner:
            label = "Corporation" if winner == "corp" else "Runner"
            self.log.record(
                self.state.round, "game", theme.SYM_AGENDA,
                f"{label} wins!",
            )

        self.refresh()
```

- [ ] **Step 9: Add logging to _on_reset**

Replace `_on_reset`:

```python
    def _on_reset(self, e) -> None:
        self.state.reset()
        self._pending_credit = {"corp": 0, "runner": 0}
        # Cancel any running credit timers
        for player in ("corp", "runner"):
            if self._credit_timer[player]:
                self._credit_timer[player].cancel()
                self._credit_timer[player] = None
        self.log.clear()
        self.log.record(0, "game", theme.SYM_TURN, "Game reset")
        self.refresh()
```

- [ ] **Step 10: Add logging to click token taps**

Replace `_corp_token_tap`:

```python
    def _corp_token_tap(self, index: int, filled: bool):
        def handle(e):
            if filled:
                self.state.spend_click("corp")
                remaining = self.state.corp_clicks
                self.log.record(
                    self.state.round, "corp", theme.SYM_CLICK,
                    f"Click spent ({remaining}/{GameState.CORP_CLICKS_PER_TURN})",
                )
            else:
                self.state.restore_click("corp")
            self.refresh()
        return handle
```

Replace `_runner_token_tap`:

```python
    def _runner_token_tap(self, index: int, filled: bool):
        def handle(e):
            if filled:
                self.state.spend_click("runner")
                remaining = self.state.runner_clicks
                self.log.record(
                    self.state.round, "runner", theme.SYM_CLICK,
                    f"Click spent ({remaining}/{GameState.RUNNER_CLICKS_PER_TURN})",
                )
            else:
                self.state.restore_click("runner")
            self.refresh()
        return handle
```

- [ ] **Step 11: Update panel builders to use _stat_adjuster for all non-credit stats**

In `_build_corp_panel`, replace the bad pub `stat_row` call:

```python
            ui.stat_row(
                theme.ASSET_BAD_PUB, theme.BAD_PUB_COLOR,
                "Bad Pub", self._corp_bad_pub_text, theme.BAD_PUB_COLOR,
                self._stat_adjuster("corp_bad_pub", -1, symbol=theme.SYM_BAD_PUB, label="bad pub"),
                self._stat_adjuster("corp_bad_pub",  1, symbol=theme.SYM_BAD_PUB, label="bad pub"),
            ),
```

In `_build_runner_panel`, replace ALL stat_row calls for tags/brain/net:

```python
            ui.stat_row(
                theme.ASSET_TAG, theme.AGENDA_GOLD,
                "Tags", self._runner_tags_text, theme.AGENDA_GOLD,
                self._stat_adjuster("runner_tags", -1, symbol=theme.SYM_TAG, label="tag"),
                self._stat_adjuster("runner_tags",  1, symbol=theme.SYM_TAG, label="tag"),
            ),
            ui.stat_row(
                theme.ASSET_CORE_DAMAGE, theme.PURPLE_ACCENT,
                "Brain", self._runner_brain_text, theme.PURPLE_ACCENT,
                self._stat_adjuster("runner_brain", -1, symbol=theme.SYM_BRAIN, label="brain",
                                    suffix_fn=lambda s: f"(hand={s.runner_hand_size})"),
                self._stat_adjuster("runner_brain",  1, symbol=theme.SYM_BRAIN, label="brain",
                                    suffix_fn=lambda s: f"(hand={s.runner_hand_size})"),
            ),
            ui.stat_row(
                theme.ASSET_CORE_DAMAGE, theme.DANGER_RED,
                "Net Dmg", self._runner_net_text, theme.DANGER_RED,
                self._stat_adjuster("runner_net", -1, symbol=theme.SYM_NET, label="net dmg"),
                self._stat_adjuster("runner_net",  1, symbol=theme.SYM_NET, label="net dmg"),
            ),
```

In `_build_agenda_section`, replace both agenda stepper calls:

```python
                            ui.stepper("−", self._stat_adjuster("corp_agenda", -1, 0, 7, symbol=theme.SYM_AGENDA, label="agenda", suffix_fn=lambda s: "pts"), theme.CORP_ACCENT),
                            ui.stepper("+", self._stat_adjuster("corp_agenda",  1, 0, 7, symbol=theme.SYM_AGENDA, label="agenda", suffix_fn=lambda s: "pts"), theme.CORP_ACCENT),
```

```python
                            ui.stepper("−", self._stat_adjuster("runner_agenda", -1, 0, 7, symbol=theme.SYM_AGENDA, label="agenda", suffix_fn=lambda s: "pts"), theme.RUNNER_ACCENT),
                            ui.stepper("+", self._stat_adjuster("runner_agenda",  1, 0, 7, symbol=theme.SYM_AGENDA, label="agenda", suffix_fn=lambda s: "pts"), theme.RUNNER_ACCENT),
```

- [ ] **Step 12: Build the log panel and add to layout**

In `_build_layout`, create the log panel and add it to the page Column.

Add before `self.page.add(...)`:

```python
        self._log_header = ft.Container(
            content=ft.Row(
                [
                    ft.Text("◎", size=14, color=theme.TEXT_SECONDARY),
                    ft.Text(
                        "GAME LOG",
                        size=11,
                        color=theme.TEXT_SECONDARY,
                        style=ft.TextStyle(
                            weight=ft.FontWeight.BOLD,
                            letter_spacing=1.5,
                        ),
                    ),
                    ft.Container(expand=True),
                    ft.Text("●", size=8, color=theme.AGENDA_GOLD),
                    self._log_count_text,
                    self._log_toggle_icon,
                ],
                spacing=6,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            bgcolor=theme.PANEL_BG,
            border=ft.Border.all(1, theme.PANEL_BORDER),
            border_radius=ft.BorderRadius.only(
                top_left=8, top_right=8,
                bottom_left=0, bottom_right=0,
            ),
            padding=ft.Padding.symmetric(horizontal=12, vertical=8),
            on_click=self._on_toggle_log,
        )

        log_header = self._log_header

        log_panel = ft.Column(
            [log_header, self._log_body],
            spacing=0,
        )
```

Then in `self.page.add(...)`, add `log_panel` after `actions_row`:

```python
        self.page.add(
            ft.Column(
                [
                    title_bar,
                    self._turn_banner,
                    self._winner_banner,
                    self._build_agenda_section(),
                    self._panels_row,
                    actions_row,
                    log_panel,
                ],
                spacing=10,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                scroll=ft.ScrollMode.AUTO,
                expand=True,
            )
        )
```

Note: `scroll=ft.ScrollMode.AUTO` is added to make the page scrollable now that the log takes extra space.

- [ ] **Step 13: Log the initial game start**

In `__init__`, after `self.log = GameLog()`:

```python
        self.log.record(0, "game", theme.SYM_TURN, "Game started")
```

- [ ] **Step 14: Verify app launches**

Run: `python3 main.py &; sleep 5; kill $!`
Expected: App launches without errors, log panel visible at bottom

- [ ] **Step 15: Commit**

```bash
git add tracker.py
git commit -m "feat: add game log panel with stat change logging"
```

---

## Chunk 4: Credit Debounce + Click UX

### Task 6: Add credit debounce with delta badge

**Files:**
- Modify: `tracker.py`

- [ ] **Step 1: Add _credit_adjuster handler factory**

Add after `_stat_adjuster`:

```python
    def _credit_adjuster(self, player: str, delta: int):
        """
        Adjusts credits immediately but debounces the log entry.
        Rapid taps accumulate into one entry like "+5 credits → 8¢".
        A delta badge shows the pending change while the timer runs.
        """
        field = f"{player}_credits"
        delta_ref = (self._corp_credits_delta if player == "corp"
                     else self._runner_credits_delta)
        timer_bar = (self._corp_credits_timer_bar if player == "corp"
                     else self._runner_credits_timer_bar)

        def handle(e):
            # Immediate state update
            self.state.adjust(field, delta, 0, 99)
            self._pending_credit[player] += delta

            # Update delta badge
            p = self._pending_credit[player]
            if p == 0:
                delta_ref.visible = False
            else:
                delta_ref.value = f"+{p}" if p > 0 else str(p)
                delta_ref.color = theme.NEON_GREEN if p > 0 else theme.DANGER_RED
                delta_ref.visible = True

            # Show timer bar
            timer_bar.visible = True

            # Cancel existing timer
            if self._credit_timer[player]:
                self._credit_timer[player].cancel()

            # Schedule log commit
            def commit():
                d = self._pending_credit[player]
                if d != 0:
                    val = getattr(self.state, field)
                    sign = "+" if d > 0 else ""
                    self.log.record(
                        self.state.round, player, theme.SYM_CREDIT,
                        f"{sign}{d} credits → {val}¢",
                    )
                # Always clean up badge + bar
                self._pending_credit[player] = 0
                delta_ref.visible = False
                timer_bar.visible = False
                self._refresh_log()

            self._credit_timer[player] = threading.Timer(0.45, commit)
            self._credit_timer[player].start()

            self.refresh()
        return handle
```

- [ ] **Step 2: Wire credit_row into panel builders**

In `_build_corp_panel`, replace the credits `stat_row` with `credit_row`:

```python
            ui.credit_row(
                theme.CORP_ACCENT,
                self._corp_credits_text,
                self._corp_credits_delta,
                self._corp_credits_timer_bar,
                self._credit_adjuster("corp", -1),
                self._credit_adjuster("corp",  1),
            ),
```

In `_build_runner_panel`, replace the credits `stat_row` with `credit_row`:

```python
            ui.credit_row(
                theme.RUNNER_ACCENT,
                self._runner_credits_text,
                self._runner_credits_delta,
                self._runner_credits_timer_bar,
                self._credit_adjuster("runner", -1),
                self._credit_adjuster("runner",  1),
            ),
```

- [ ] **Step 3: Verify app launches**

Run: `python3 main.py &; sleep 5; kill $!`
Expected: App launches, credit +/- shows delta badge

- [ ] **Step 4: Commit**

```bash
git add tracker.py
git commit -m "feat: credit debounce with delta badge and timer bar"
```

### Task 7: Improve click token UX — count display + refill button

**Files:**
- Modify: `tracker.py`

- [ ] **Step 1: Add refill handlers**

Add after `_runner_token_tap`:

```python
    def _on_refill_corp(self, e) -> None:
        self.state.corp_clicks = GameState.CORP_CLICKS_PER_TURN
        self.refresh()

    def _on_refill_runner(self, e) -> None:
        self.state.runner_clicks = GameState.RUNNER_CLICKS_PER_TURN
        self.refresh()
```

- [ ] **Step 2: Update _build_corp_panel click section**

Replace the `clicks_section` in `_build_corp_panel`:

```python
        corp_is_active = active

        clicks_section = ft.Container(
            content=ft.Column(
                [
                    ui.section_label("CLICKS", theme.CORP_ACCENT),
                    self._corp_clicks_row,
                    ft.Row(
                        [
                            self._corp_clicks_count,
                            ft.Container(expand=True),
                            ui.refill_button(theme.CORP_ACCENT, self._on_refill_corp)
                            if corp_is_active else ft.Container(),
                        ],
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                ],
                spacing=6,
            ),
            padding=ft.Padding.symmetric(horizontal=8, vertical=4),
            opacity=1.0 if corp_is_active else 0.35,
        )
```

- [ ] **Step 3: Update _build_runner_panel click section**

Replace the `clicks_section` in `_build_runner_panel`:

```python
        runner_is_active = active

        clicks_section = ft.Container(
            content=ft.Column(
                [
                    ui.section_label("CLICKS", theme.RUNNER_ACCENT),
                    self._runner_clicks_row,
                    ft.Row(
                        [
                            self._runner_clicks_count,
                            ft.Container(expand=True),
                            ui.refill_button(theme.RUNNER_ACCENT, self._on_refill_runner)
                            if runner_is_active else ft.Container(),
                        ],
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                ],
                spacing=6,
            ),
            padding=ft.Padding.symmetric(horizontal=8, vertical=4),
            opacity=1.0 if runner_is_active else 0.35,
        )
```

- [ ] **Step 4: Update refresh() to pass None for inactive player tokens**

In `refresh()`, replace the click token lines:

```python
        # Active player gets tappable tokens; inactive player gets display-only
        self._corp_clicks_row.controls = ui.click_tokens_row(
            s.corp_clicks, 3, theme.CORP_ACCENT,
            self._corp_token_tap if corp_is_active else None,
        )
        self._runner_clicks_row.controls = ui.click_tokens_row(
            s.runner_clicks, 4, theme.RUNNER_ACCENT,
            self._runner_token_tap if not corp_is_active else None,
        )
```

This requires `corp_is_active` to be available in `refresh()`. It already is — the existing code computes `cp = s.active_player == "corp"`. Use `cp` in the guard:

```python
        self._corp_clicks_row.controls = ui.click_tokens_row(
            s.corp_clicks, 3, theme.CORP_ACCENT,
            self._corp_token_tap if cp else None,
        )
        self._runner_clicks_row.controls = ui.click_tokens_row(
            s.runner_clicks, 4, theme.RUNNER_ACCENT,
            self._runner_token_tap if not cp else None,
        )
```

- [ ] **Step 5: Final full verification**

Run: `python3 main.py &; sleep 5; kill $!`
Expected: App launches cleanly. All features work: log panel visible, click tokens tappable for active player, refill button shows for active player, credit debounce shows delta badge.

- [ ] **Step 6: Commit**

```bash
git add tracker.py
git commit -m "feat: click token UX with count display, refill, and inactive dimming"
```

---

## Final Verification

### Task 8: Full integration test

- [ ] **Step 1: Run the app and verify all features**

Run: `python3 main.py`

Manual test checklist:
1. App launches showing "CORP TURN · Round 1" banner
2. Corp clicks: 3 filled tokens, tappable — tap one, see "2 / 3 remaining" + log entry
3. Corp credits: tap + several times rapidly, see delta badge "+N", log commits as one entry after ~0.5s
4. End Corp turn: click "END CORP TURN", banner switches to "RUNNER TURN", runner tokens become tappable, corp tokens dim
5. Runner clicks: 4 filled tokens, tappable
6. End Runner turn: round advances, corp gets fresh clicks
7. Tap +1 on tags/brain/net/bad pub: each gets an immediate log entry
8. Score agendas: pips fill, reach 7 = winner banner
9. Log panel: collapsible via header tap, shows all events
10. Reset: clears log, resets all state

- [ ] **Step 2: Final commit with all files**

```bash
git add -A
git status
git commit -m "feat: complete UX overhaul — game log, credit debounce, improved click tokens"
```
