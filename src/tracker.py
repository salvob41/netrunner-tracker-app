"""
NetrunnerTracker — wires GameState to the Flet UI.

Thin glue layer only: creates widget refs, maps state→widgets in refresh(),
and dispatches user actions to GameState.  No rules, no visual decisions.

Whose turn it is drives the entire visual state:
  - Turn banner changes color and label
  - Active player's panel gets the bright border and "YOUR TURN" badge
  - End Turn button label reflects the current player
"""

import asyncio

import flet as ft

import theme
import components as ui
from state import GameState
from game_log import GameLog


class NetrunnerTracker:
    """
    Single-session controller.

    Class over closure: widget refs and handlers are attributes rather than
    free variables, which makes debugging and future extension much easier.
    """

    def __init__(self, page: ft.Page) -> None:
        self.page  = page
        self.state = GameState()
        self.log = GameLog()
        self.log.record(0, "game", theme.SYM_TURN, "Game started")

        # Credit debounce state — uses page.run_task() with async sleep
        # (same pattern as the working MTG life counter)
        self._pending_credit = {"corp": 0, "runner": 0}
        self._credit_task: dict = {"corp": None, "runner": None}

        # Generic stat debounce state — keyed by attr name
        self._pending_stat: dict = {}   # attr → accumulated delta
        self._stat_task: dict = {}      # attr → asyncio task

        # Log panel starts expanded
        self._log_expanded = True

        self._configure_page()
        self._create_widget_refs()
        self._build_layout()
        self.refresh()

    # ── Page configuration ────────────────────────────────────────────────────

    def _configure_page(self) -> None:
        p = self.page
        p.title      = "NETRUNNER TRACKER"
        p.bgcolor    = theme.BG_DARK
        p.theme_mode = ft.ThemeMode.DARK

        # Window icon — PNG for cross-platform compatibility.
        # macOS dock icon can't be changed (Flet limitation), but this
        # works for Android builds and some desktop window managers.
        p.window.icon = "/icon.png"

        # Track if we're on mobile — panels stack vertically instead of
        # side-by-side because phone screens are too narrow for two panels.
        self._is_mobile = p.platform in (ft.PagePlatform.ANDROID,
                                         ft.PagePlatform.IOS)

        # Tighter padding on mobile to maximize screen real estate
        p.padding = 8 if self._is_mobile else 16

        # Window constraints only apply on desktop — Flet ignores them on
        # Android, but the guard prevents spurious log warnings.
        if p.platform in (ft.PagePlatform.WINDOWS,
                          ft.PagePlatform.MACOS,
                          ft.PagePlatform.LINUX):
            p.window.width  = 740
            p.window.height = 900

    # ── Widget refs ───────────────────────────────────────────────────────────

    def _create_widget_refs(self) -> None:
        """
        Allocate every mutable widget once.
        refresh() writes to these refs; Flet diffs only what changed.
        Keeping allocation separate from layout prevents the two concerns
        from tangling.
        """
        # ── Turn banner ───────────────────────────────────────────────────────
        # The banner is the primary turn signal: colour + text change together
        # so players get two simultaneous cues instead of one.
        self._banner_text = ft.Text(
            "", size=15, color=theme.CORP_ACCENT,
            text_align=ft.TextAlign.CENTER,
            style=ft.TextStyle(weight=ft.FontWeight.BOLD, letter_spacing=2.5),
        )
        self._banner_round_text = ft.Text(
            "", size=11, color=theme.TEXT_SECONDARY,
            text_align=ft.TextAlign.CENTER,
        )
        self._turn_banner = ft.Container(
            border_radius=8,
            padding=ft.Padding.symmetric(horizontal=16, vertical=10),
            content=ft.Column(
                [self._banner_text, self._banner_round_text],
                spacing=2,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        )

        # ── Corp ──────────────────────────────────────────────────────────────
        self._corp_clicks_row   = ft.Row(spacing=6)
        self._corp_credits_text = ft.Text(
            "5", size=26, weight=ft.FontWeight.BOLD, color=theme.CORP_ACCENT,
        )

        # ── Runner ────────────────────────────────────────────────────────────
        self._runner_clicks_row   = ft.Row(spacing=6)
        self._runner_credits_text = ft.Text(
            "5", size=26, weight=ft.FontWeight.BOLD, color=theme.RUNNER_ACCENT,
        )
        self._runner_tags_text  = ft.Text(
            "0", size=22, weight=ft.FontWeight.BOLD, color=theme.AGENDA_GOLD,
        )
        self._runner_brain_text = ft.Text(
            "0", size=22, weight=ft.FontWeight.BOLD, color=theme.PURPLE_ACCENT,
        )
        self._runner_hand_text = ft.Text(
            "5", size=22, weight=ft.FontWeight.BOLD, color=theme.RUNNER_ACCENT,
        )

        # ── Optional stats (toggleable) ─────────────────────────────────────
        self._corp_bad_pub_text = ft.Text(
            "0", size=22, weight=ft.FontWeight.BOLD, color=theme.BAD_PUB_COLOR,
        )
        self._runner_mu_text = ft.Text(
            "4", size=22, weight=ft.FontWeight.BOLD, color=theme.MU_COLOR,
        )
        self._runner_link_text = ft.Text(
            "0", size=22, weight=ft.FontWeight.BOLD, color=theme.LINK_COLOR,
        )
        # Toggle state for optional rows
        self._show_bad_pub = False
        self._show_mu = False
        self._show_link = False

        # ── Agenda ───────────────────────────────────────────────────────────
        self._corp_agenda_text   = ft.Text(
            "0", size=16, weight=ft.FontWeight.BOLD, color=theme.CORP_ACCENT,
            text_align=ft.TextAlign.CENTER,
        )
        self._runner_agenda_text = ft.Text(
            "0", size=16, weight=ft.FontWeight.BOLD, color=theme.RUNNER_ACCENT,
            text_align=ft.TextAlign.CENTER,
        )

        # ── Panels (always stacked vertically) ──────────────────────────────
        self._panels_container = ft.Column(spacing=8)

        # ── End Turn button ───────────────────────────────────────────────────
        self._end_turn_btn_label  = ft.Text(
            "END CORP TURN",
            size=12, color=theme.NEON_GREEN,
            style=ft.TextStyle(weight=ft.FontWeight.BOLD, letter_spacing=1.5),
        )
        self._end_turn_btn = ft.Container(
            expand=True,
            content=ft.Row(
                [ft.Text("▶", size=14, color=theme.NEON_GREEN), self._end_turn_btn_label],
                spacing=6,
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            bgcolor=ft.Colors.with_opacity(0.12, theme.NEON_GREEN),
            border=ft.Border.all(1, ft.Colors.with_opacity(0.50, theme.NEON_GREEN)),
            border_radius=8,
            padding=ft.Padding.symmetric(horizontal=18, vertical=12),
            on_click=self._on_end_turn,
        )

        # ── Winner banner ─────────────────────────────────────────────────────
        self._winner_banner = ft.Container(
            visible=False,
            border_radius=8,
            padding=12,
            alignment=ft.Alignment.CENTER,
            width=float("inf"),
        )

        # ── Credit delta badges ──────────────────────────────────────────
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

        # ── Click count displays ─────────────────────────────────────────
        self._corp_clicks_count = ft.Text(
            "3 / 3 remaining", size=11, color=theme.TEXT_SECONDARY,
        )
        self._runner_clicks_count = ft.Text(
            "4 / 4 remaining", size=11, color=theme.TEXT_SECONDARY,
        )

        # ── Log panel ────────────────────────────────────────────────────
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

    # ── Refresh ───────────────────────────────────────────────────────────────

    def refresh(self) -> None:
        """
        Push GameState into every widget ref, then page.update().

        All mutations funnel here — one place to add logging, haptics,
        animation triggers, or undo snapshots in the future.
        """
        s   = self.state
        cp  = s.active_player == "corp"
        color = theme.CORP_ACCENT if cp else theme.RUNNER_ACCENT

        # ── Turn banner ───────────────────────────────────────────────────────
        self._banner_text.value      = "CORP TURN" if cp else "RUNNER TURN"
        self._banner_text.color      = color
        self._banner_round_text.value = f"Round {s.round}"
        # Banner background shifts faction color so the current player is
        # unmistakable even at a glance from across a table.
        self._turn_banner.bgcolor     = (theme.CORP_BANNER if cp else theme.RUNNER_BANNER)
        self._turn_banner.border      = ft.Border.all(1, ft.Colors.with_opacity(0.5, color))

        # ── Click tokens ──────────────────────────────────────────────────────
        # Active player gets tappable tokens; inactive player gets display-only
        # Smaller tokens on mobile (40px) to fit phone screens
        tsz = 40 if self._is_mobile else 48
        self._corp_clicks_row.controls = ui.click_tokens_row(
            s.corp_clicks, 3, theme.CORP_ACCENT,
            self._corp_token_tap if cp else None,
            token_size=tsz,
        )
        self._runner_clicks_row.controls = ui.click_tokens_row(
            s.runner_clicks, 4, theme.RUNNER_ACCENT,
            self._runner_token_tap if not cp else None,
            token_size=tsz,
        )

        # ── Click counts ─────────────────────────────────────────────────
        self._corp_clicks_count.value = (
            f"{s.corp_clicks} / {GameState.CORP_CLICKS_PER_TURN} remaining"
        )
        self._runner_clicks_count.value = (
            f"{s.runner_clicks} / {GameState.RUNNER_CLICKS_PER_TURN} remaining"
        )

        # ── Corp stats ────────────────────────────────────────────────────────
        self._corp_credits_text.value  = str(s.corp_credits)
        self._corp_bad_pub_text.value  = str(s.corp_bad_pub)

        # ── Runner stats ──────────────────────────────────────────────────────
        self._runner_credits_text.value = str(s.runner_credits)
        self._runner_tags_text.value    = str(s.runner_tags)
        self._runner_brain_text.value   = str(s.runner_brain)
        self._runner_hand_text.value    = str(s.runner_max_hand_size)
        self._runner_mu_text.value      = str(s.runner_mu)
        self._runner_link_text.value    = str(s.runner_link)

        # ── Agenda ────────────────────────────────────────────────────────────
        self._corp_agenda_text.value   = str(s.corp_agenda)
        self._runner_agenda_text.value = str(s.runner_agenda)

        # ── Panels + agenda sidebar ───────────────────────────────────────────
        corp_is_active   = s.active_player == "corp"
        panels_col = ft.Column(
            [
                self._build_corp_panel(active=corp_is_active),
                self._build_runner_panel(active=not corp_is_active),
            ],
            spacing=8,
            expand=True,
        )
        agenda = self._build_agenda_bar()
        self._panels_container.controls = [
            ft.Row(
                [panels_col, agenda],
                spacing=6,
                vertical_alignment=ft.CrossAxisAlignment.START,
                expand=True,
            ),
        ]

        # ── End Turn button label ─────────────────────────────────────────────
        self._end_turn_btn_label.value = (
            "END CORP TURN" if cp else "END RUNNER TURN"
        )

        # ── Winner banner ─────────────────────────────────────────────────────
        winner = s.winner
        if winner == "corp":
            self._winner_banner.visible = True
            self._winner_banner.bgcolor = theme.CORP_DIM
            self._winner_banner.border  = ft.Border.all(1, theme.CORP_ACCENT)
            self._winner_banner.content = ft.Text(
                "CORPORATION WINS",
                size=20, weight=ft.FontWeight.BOLD,
                color=theme.CORP_ACCENT, text_align=ft.TextAlign.CENTER,
            )
        elif winner == "runner":
            self._winner_banner.visible = True
            self._winner_banner.bgcolor = theme.RUNNER_DIM
            self._winner_banner.border  = ft.Border.all(1, theme.RUNNER_ACCENT)
            self._winner_banner.content = ft.Text(
                "RUNNER WINS",
                size=20, weight=ft.FontWeight.BOLD,
                color=theme.RUNNER_ACCENT, text_align=ft.TextAlign.CENTER,
            )
        else:
            self._winner_banner.visible = False

        # ── Log panel ────────────────────────────────────────────────────
        self._refresh_log_inline()

        self.page.update()

    def _refresh_log(self) -> None:
        """Update just the log panel — called after debounce timer fires."""
        self._log_list.controls = [
            ui.log_entry_row(e) for e in self.log.entries
        ]
        self._log_count_text.value = f"{len(self.log.entries)} events"
        self.page.update()

    def _refresh_log_inline(self) -> None:
        """Update log controls without calling page.update() — used inside refresh()."""
        self._log_list.controls = [
            ui.log_entry_row(e) for e in self.log.entries
        ]
        self._log_count_text.value = f"{len(self.log.entries)} events"

    # ── Event handlers ────────────────────────────────────────────────────────

    def _adjuster(self, attr: str, delta: int,
                  min_val: int = 0, max_val: int = 99):
        """
        Factory: returns a handler that calls GameState.adjust and refreshes.
        Using a factory keeps each button's handler self-contained without
        duplicating the clamp logic across the codebase.
        """
        def handle(e):
            self.state.adjust(attr, delta, min_val, max_val)
            self.refresh()
        return handle

    def _stat_adjuster(self, attr: str, delta: int,
                       min_val: int = 0, max_val: int = 99,
                       symbol: str = "·", label: str = "",
                       suffix_fn=None):
        """
        Debounced stat adjuster: updates state immediately but batches
        the log entry (800ms) so rapid taps produce one log line.
        """
        def handle(e):
            self.state.adjust(attr, delta, min_val, max_val)
            self._pending_stat[attr] = self._pending_stat.get(attr, 0) + delta
            self.refresh()
            # Cancel existing debounce and start new one
            if attr in self._stat_task and self._stat_task[attr]:
                self._stat_task[attr].cancel()
            self._stat_task[attr] = self.page.run_task(
                self._stat_commit, attr, symbol, label, suffix_fn,
            )
        return handle

    async def _stat_commit(self, attr, symbol, label, suffix_fn):
        """Async debounce: sleep then commit the batched stat change."""
        await asyncio.sleep(0.8)
        d = self._pending_stat.get(attr, 0)
        if d != 0:
            val = getattr(self.state, attr)
            player = "corp" if attr.startswith("corp_") else "runner"
            sign = "+" if d > 0 else ""
            msg = f"{sign}{d} {label} → {val}"
            if suffix_fn:
                msg += f" {suffix_fn(self.state)}"
            self.log.record(self.state.round, player, symbol, msg)
        self._pending_stat[attr] = 0
        self._refresh_log_inline()
        self._log_list.update()
        self._log_count_text.update()

    def _corp_token_tap(self, index: int, filled: bool):
        """
        Returns a handler for one Corp click token.
        Tapping a filled token spends the click; tapping a spent token
        restores it — mirrors the feel of physically flipping a token.
        """
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

    def _runner_token_tap(self, index: int, filled: bool):
        """Same tap-to-toggle mechanic for Runner clicks."""
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

    def _on_refill_corp(self, e) -> None:
        self.state.corp_clicks = GameState.CORP_CLICKS_PER_TURN
        self.refresh()

    def _on_refill_runner(self, e) -> None:
        self.state.runner_clicks = GameState.RUNNER_CLICKS_PER_TURN
        self.refresh()

    def _toggle_pill(self, label: str, active: bool, key: str, color: str) -> ft.Container:
        """Small pill button to toggle optional stat visibility."""
        return ft.Container(
            content=ft.Text(
                f"{'−' if active else '+'} {label}",
                size=9,
                color=color if active else ft.Colors.with_opacity(0.4, color),
            ),
            bgcolor=ft.Colors.with_opacity(0.15 if active else 0.05, color),
            border=ft.Border.all(1, ft.Colors.with_opacity(0.4 if active else 0.15, color)),
            border_radius=10,
            padding=ft.Padding.symmetric(horizontal=8, vertical=3),
            on_click=self._on_toggle_stat(key),
        )

    def _on_toggle_stat(self, key: str):
        """Factory: returns handler that toggles an optional stat's visibility."""
        def handle(e):
            attr = f"_show_{key}"
            setattr(self, attr, not getattr(self, attr))
            self.refresh()
        return handle

    def _core_damage_adjuster(self, delta: int):
        """
        Core damage adjusts runner_brain AND reduces max hand size.
        Debounced like other stats.
        """
        return self._stat_adjuster(
            "runner_brain", delta, 0, 99,
            symbol=theme.SYM_BRAIN, label="core dmg",
            suffix_fn=lambda s: f"(hand={s.runner_max_hand_size})",
        )

    def _max_hand_adjuster(self, delta: int):
        """
        Adjusts max hand size bonus from card effects (e.g. Public Sympathy).
        Debounced like other stats.
        """
        return self._stat_adjuster(
            "runner_max_hand_bonus", delta, -5, 10,
            symbol=theme.SYM_HAND, label="hand bonus",
            suffix_fn=lambda s: f"(hand={s.runner_max_hand_size})",
        )

    def _credit_adjuster(self, player: str, delta: int):
        """
        Adjusts credits immediately but debounces the log entry.
        Uses page.run_task() + async sleep (same pattern as the working
        MTG life counter) instead of threading.Timer.
        """
        field = f"{player}_credits"
        delta_ref = (self._corp_credits_delta if player == "corp"
                     else self._runner_credits_delta)
        timer_bar = (self._corp_credits_timer_bar if player == "corp"
                     else self._runner_credits_timer_bar)
        credit_ref = (self._corp_credits_text if player == "corp"
                      else self._runner_credits_text)

        def handle(e):
            # Immediate state update
            self.state.adjust(field, delta, 0, 99)
            self._pending_credit[player] += delta

            # Update credit value display immediately
            credit_ref.value = str(getattr(self.state, field))

            # Update delta badge
            p = self._pending_credit[player]
            if p == 0:
                delta_ref.visible = False
                delta_ref.opacity = 0
            else:
                delta_ref.value = f"+{p}" if p > 0 else str(p)
                delta_ref.color = theme.NEON_GREEN if p > 0 else theme.DANGER_RED
                delta_ref.visible = True
                delta_ref.opacity = 1

            # Show timer bar
            timer_bar.visible = True

            # Push only the changed widgets — no full panel rebuild
            credit_ref.update()
            delta_ref.update()
            timer_bar.update()

            # Cancel existing debounce task and start a new one
            if self._credit_task[player]:
                self._credit_task[player].cancel()
            self._credit_task[player] = self.page.run_task(
                self._credit_commit, player, delta_ref, timer_bar, field,
            )
        return handle

    def _tap_stat_handler(self, attr: str, delta: int,
                          min_val: int = 0, max_val: int = 99,
                          symbol: str = "·", label: str = "",
                          suffix_fn=None):
        """
        Returns (on_tap, on_long_press) handlers for a tap_stat component.
        on_tap increments by +abs(delta), on_long_press decrements by -abs(delta).
        """
        inc = self._stat_adjuster(attr, abs(delta), min_val, max_val,
                                  symbol=symbol, label=label, suffix_fn=suffix_fn)
        dec = self._stat_adjuster(attr, -abs(delta), min_val, max_val,
                                  symbol=symbol, label=label, suffix_fn=suffix_fn)
        return inc, dec

    def _tap_credit_handler(self, player: str):
        """
        Returns (on_tap, on_long_press) handlers for a tap_credit_row.
        on_tap = +1 credit, on_long_press = -1 credit.
        """
        inc = self._credit_adjuster(player, +1)
        dec = self._credit_adjuster(player, -1)
        return inc, dec

    def _agenda_tap(self, player: str, delta: int):
        """Returns a handler for agenda bar tap/long-press."""
        def handle(e):
            attr = f"{player}_agenda"
            self.state.adjust(attr, delta, 0, 99)
            val = getattr(self.state, attr)
            sign = "+" if delta > 0 else ""
            self.log.record(
                self.state.round, player, theme.SYM_AGENDA,
                f"{sign}{delta} agenda → {val} pts",
            )
            self.refresh()
        return handle

    async def _credit_commit(self, player, delta_ref, timer_bar, field):
        """Async debounce: sleep then commit the batched credit change."""
        await asyncio.sleep(0.8)
        d = self._pending_credit[player]
        if d != 0:
            val = getattr(self.state, field)
            sign = "+" if d > 0 else ""
            self.log.record(
                self.state.round, player, theme.SYM_CREDIT,
                f"{sign}{d} credits → {val}¢",
            )
        self._pending_credit[player] = 0
        delta_ref.visible = False
        delta_ref.opacity = 0
        timer_bar.visible = False
        # Update only the changed widgets + log
        delta_ref.update()
        timer_bar.update()
        self._refresh_log_inline()
        self._log_list.update()
        self._log_count_text.update()

    def _on_end_turn(self, e) -> None:
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

        winner = self.state.winner
        if winner:
            label = "Corporation" if winner == "corp" else "Runner"
            self.log.record(
                self.state.round, "game", theme.SYM_AGENDA,
                f"{label} wins!",
            )

        self.refresh()

    def _on_reset(self, e) -> None:
        self.state.reset()
        self._pending_credit = {"corp": 0, "runner": 0}
        for player in ("corp", "runner"):
            if self._credit_task[player]:
                self._credit_task[player].cancel()
                self._credit_task[player] = None
        for task in self._stat_task.values():
            if task:
                task.cancel()
        self._pending_stat.clear()
        self._stat_task.clear()
        self.log.clear()
        self.log.record(0, "game", theme.SYM_TURN, "Game reset")
        self.refresh()

    def _on_toggle_log(self, e) -> None:
        self._log_expanded = not self._log_expanded
        self._log_body.visible = self._log_expanded
        self._log_toggle_icon.value = "▼" if self._log_expanded else "▲"
        bl = 0 if self._log_expanded else 8
        self._log_header.border_radius = ft.BorderRadius.only(
            top_left=8, top_right=8,
            bottom_left=bl, bottom_right=bl,
        )
        self.page.update()

    # ── Panel builders ────────────────────────────────────────────────────────

    def _build_corp_panel(self, active: bool) -> ft.Container:
        """Corp panel: clicks, credits (tap), bad pub (tap, optional)."""
        s = self.state
        corp_is_active = active

        clicks_section = ft.Container(
            content=ft.Column(
                [
                    ui.section_label("CLICKS  ·  draw first", theme.CORP_ACCENT),
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

        corp_credit_tap, corp_credit_lp = self._tap_credit_handler("corp")

        controls = [
            clicks_section,
            ui.divider(),
            ui.tap_credit_row(
                theme.CORP_ACCENT,
                self._corp_credits_text,
                self._corp_credits_delta,
                self._corp_credits_timer_bar,
                corp_credit_tap,
                corp_credit_lp,
            ),
        ]
        if self._show_bad_pub:
            bp_inc, bp_dec = self._tap_stat_handler(
                "corp_bad_pub", 1, symbol=theme.SYM_BAD_PUB, label="bad pub",
            )
            controls.append(ui.tap_stat(
                theme.ASSET_BAD_PUB, theme.BAD_PUB_COLOR,
                self._corp_bad_pub_text, bp_inc, bp_dec,
            ))
        controls.append(ft.Row(
            [self._toggle_pill("Bad Pub", self._show_bad_pub, "bad_pub", theme.BAD_PUB_COLOR)],
            alignment=ft.MainAxisAlignment.END,
        ))
        return ui.panel("CORP", theme.CORP_ACCENT, controls, active=active)

    def _build_runner_panel(self, active: bool) -> ft.Container:
        """Runner panel: clicks, credits (tap), tags + core (tap), hand (stepper)."""
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

        runner_credit_tap, runner_credit_lp = self._tap_credit_handler("runner")

        # Tags: tap/long-press
        tag_inc, tag_dec = self._tap_stat_handler(
            "runner_tags", 1, symbol=theme.SYM_TAG, label="tag",
        )
        # Core damage: tap/long-press (with hand size suffix)
        core_inc = self._core_damage_adjuster(1)
        core_dec = self._core_damage_adjuster(-1)

        # Tags and Core Damage side by side (compact, tap/long-press)
        compact_row = ft.Row(
            [
                ft.Container(
                    expand=True,
                    content=ui.tap_stat(
                        theme.ASSET_TAG, theme.AGENDA_GOLD,
                        self._runner_tags_text, tag_inc, tag_dec,
                    ),
                ),
                ft.Container(
                    width=1, height=28,
                    bgcolor=ft.Colors.with_opacity(0.15, theme.TEXT_SECONDARY),
                ),
                ft.Container(
                    expand=True,
                    content=ui.tap_stat(
                        theme.ASSET_CORE_DAMAGE, theme.PURPLE_ACCENT,
                        self._runner_brain_text, core_inc, core_dec,
                    ),
                ),
            ],
            spacing=4,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

        # Hand size: icon + value + steppers (no label)
        hand = ui.stepper_stat(
            theme.ASSET_HAND, theme.RUNNER_ACCENT,
            self._runner_hand_text, theme.RUNNER_ACCENT,
            self._max_hand_adjuster(-1),
            self._max_hand_adjuster(1),
        )

        # Optional stats (MU, Link) — stepper_stat, toggled via pills
        optional_controls = []
        if self._show_mu:
            optional_controls.append(ui.stepper_stat(
                theme.ASSET_MU, theme.MU_COLOR,
                self._runner_mu_text, theme.MU_COLOR,
                self._stat_adjuster("runner_mu", -1, symbol=theme.SYM_MU, label="MU"),
                self._stat_adjuster("runner_mu",  1, symbol=theme.SYM_MU, label="MU"),
                icon_size=18,
            ))
        if self._show_link:
            optional_controls.append(ui.stepper_stat(
                theme.ASSET_LINK, theme.LINK_COLOR,
                self._runner_link_text, theme.LINK_COLOR,
                self._stat_adjuster("runner_link", -1, symbol=theme.SYM_LINK, label="link"),
                self._stat_adjuster("runner_link",  1, symbol=theme.SYM_LINK, label="link"),
                icon_size=18,
            ))

        toggle_row = ft.Row(
            [
                self._toggle_pill("MU", self._show_mu, "mu", theme.MU_COLOR),
                self._toggle_pill("Link", self._show_link, "link", theme.LINK_COLOR),
            ],
            spacing=4,
            alignment=ft.MainAxisAlignment.END,
        )

        controls = [
            clicks_section,
            ui.divider(),
            ui.tap_credit_row(
                theme.RUNNER_ACCENT,
                self._runner_credits_text,
                self._runner_credits_delta,
                self._runner_credits_timer_bar,
                runner_credit_tap,
                runner_credit_lp,
            ),
            ui.divider(),
            compact_row,
            ui.divider(),
            hand,
        ]
        for oc in optional_controls:
            controls.append(oc)
        controls.append(toggle_row)

        return ui.panel("RUNNER", theme.RUNNER_ACCENT, controls, active=active)

    # ── Agenda bar ────────────────────────────────────────────────────────────

    def _build_agenda_bar(self) -> ft.Container:
        """Vertical tug-of-war agenda sidebar."""
        s = self.state
        return ui.agenda_bar(
            corp_score=s.corp_agenda,
            runner_score=s.runner_agenda,
            corp_score_ref=self._corp_agenda_text,
            runner_score_ref=self._runner_agenda_text,
            on_corp_tap=self._agenda_tap("corp", +1),
            on_corp_long_press=self._agenda_tap("corp", -1),
            on_runner_tap=self._agenda_tap("runner", +1),
            on_runner_long_press=self._agenda_tap("runner", -1),
        )

    # ── Layout assembly ───────────────────────────────────────────────────────

    def _build_layout(self) -> None:
        """
        Assemble all sections: turn banner, panels + agenda sidebar, log, actions.
        """
        reset_btn = ft.Container(
            content=ft.Row(
                [
                    ft.Text("⟳", size=14, color=theme.DANGER_RED),
                    ft.Text(
                        "RESET",
                        size=12,
                        color=theme.DANGER_RED,
                        style=ft.TextStyle(
                            weight=ft.FontWeight.BOLD,
                            letter_spacing=1.5,
                        ),
                    ),
                ],
                spacing=6,
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            bgcolor=ft.Colors.with_opacity(0.08, theme.DANGER_RED),
            border=ft.Border.all(1, ft.Colors.with_opacity(0.40, theme.DANGER_RED)),
            border_radius=8,
            padding=ft.Padding.symmetric(horizontal=18, vertical=12),
            on_click=self._on_reset,
        )

        actions_row = ft.Container(
            content=ft.Row(
                [self._end_turn_btn, reset_btn],
                spacing=10,
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            padding=ft.Padding.only(top=6),
        )

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

        log_panel = ft.Column(
            [self._log_header, self._log_body],
            spacing=0,
        )

        sp = 6 if self._is_mobile else 10
        self.page.add(
            ft.Column(
                [
                    self._turn_banner,
                    self._winner_banner,
                    self._panels_container,
                    log_panel,
                    actions_row,
                ],
                spacing=sp,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                scroll=ft.ScrollMode.AUTO,
                expand=True,
            )
        )
