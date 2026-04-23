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

        # Optional stat visibility
        self._show_bad_pub = False
        self._show_mu      = False
        self._show_link    = False

        # Generic stat debounce state — keyed by attr name
        self._pending_stat: dict = {}   # attr → accumulated delta
        self._stat_task: dict = {}      # attr → asyncio task

        # Delta badge refs — one per stat, shows pending change (+2, -1, etc.)
        self._delta_refs: dict[str, ft.Text] = {}
        for attr in ("corp_credits", "corp_bad_pub",
                      "runner_credits", "runner_tags", "runner_brain",
                      "runner_max_hand_bonus", "runner_mu", "runner_link"):
            self._delta_refs[attr] = ft.Text(
                "", size=11, weight=ft.FontWeight.BOLD, visible=False,
            )

        # Log panel starts collapsed
        self._log_expanded = False

        # Panel rotation state (for shared-device play)
        self._corp_rotated = False
        self._runner_rotated = False

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
        p.window.icon = "/icon.png"

        self._is_mobile = p.platform in (ft.PagePlatform.ANDROID,
                                         ft.PagePlatform.IOS)
        # Top padding pushes below Android/iOS status bar
        p.padding = ft.Padding(left=8, right=8, bottom=8,
                               top=36 if self._is_mobile else 16)

        # Keep screen on during play
        if self._is_mobile:
            async def enable_wakelock():
                wakelock = ft.Wakelock()
                await wakelock.enable()
            p.run_task(enable_wakelock)

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
        """
        # ── Turn banner ──────────────────────────────────────────────────
        self._banner_text = ft.Text(
            "", size=13, color=theme.CORP_ACCENT,
            text_align=ft.TextAlign.CENTER,
            style=ft.TextStyle(weight=ft.FontWeight.BOLD, letter_spacing=2.0),
        )
        self._banner_round_text = ft.Text(
            "", size=10, color=theme.TEXT_SECONDARY,
            text_align=ft.TextAlign.CENTER,
        )
        self._turn_banner = ft.Container(
            border_radius=8,
            padding=ft.Padding.symmetric(horizontal=12, vertical=5),
            content=ft.Column(
                [self._banner_text, self._banner_round_text],
                spacing=1,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        )

        # ── Corp ─────────────────────────────────────────────────────────
        self._corp_clicks_row = ft.Row(spacing=5)
        self._corp_clicks_count = ft.Text(
            "3/3", size=9, color=theme.TEXT_SECONDARY,
        )
        self._corp_extra_btn = ui.extra_allotted_click_button(
            theme.CORP_ACCENT, self._on_add_corp_extra,
        )
        self._corp_credits_text = ft.Text(
            "5", size=32, weight=ft.FontWeight.BOLD, color=theme.CORP_ACCENT,
        )
        self._corp_bad_pub_text = ft.Text(
            "0", size=24, weight=ft.FontWeight.BOLD, color=theme.BAD_PUB_COLOR,
        )

        # ── Runner ───────────────────────────────────────────────────────
        self._runner_clicks_row = ft.Row(spacing=5)
        self._runner_clicks_count = ft.Text(
            "4/4", size=9, color=theme.TEXT_SECONDARY,
        )
        self._runner_extra_btn = ui.extra_allotted_click_button(
            theme.RUNNER_ACCENT, self._on_add_runner_extra,
        )
        self._runner_credits_text = ft.Text(
            "5", size=32, weight=ft.FontWeight.BOLD, color=theme.RUNNER_ACCENT,
        )
        self._runner_tags_text  = ft.Text(
            "0", size=24, weight=ft.FontWeight.BOLD, color=theme.AGENDA_GOLD,
        )
        self._runner_brain_text = ft.Text(
            "0", size=24, weight=ft.FontWeight.BOLD, color=theme.PURPLE_ACCENT,
        )
        self._runner_hand_text = ft.Text(
            "5", size=24, weight=ft.FontWeight.BOLD, color=theme.RUNNER_ACCENT,
        )
        self._runner_mu_text = ft.Text(
            "4", size=24, weight=ft.FontWeight.BOLD, color=theme.MU_COLOR,
        )
        self._runner_link_text = ft.Text(
            "0", size=24, weight=ft.FontWeight.BOLD, color=theme.LINK_COLOR,
        )

        # ── Agenda ───────────────────────────────────────────────────────
        self._corp_agenda_text = ft.Text(
            "0", size=14, weight=ft.FontWeight.BOLD, color=theme.CORP_ACCENT,
            text_align=ft.TextAlign.CENTER,
        )
        self._runner_agenda_text = ft.Text(
            "0", size=14, weight=ft.FontWeight.BOLD, color=theme.RUNNER_ACCENT,
            text_align=ft.TextAlign.CENTER,
        )

        # ── Panels container ─────────────────────────────────────────────
        self._panels_container = ft.Column(spacing=4, expand=True)

        # ── End Turn button ──────────────────────────────────────────────
        self._end_turn_btn_label = ft.Text(
            "END CORP TURN",
            size=11, color=theme.NEON_GREEN,
            style=ft.TextStyle(weight=ft.FontWeight.BOLD, letter_spacing=1.5),
        )
        self._end_turn_btn = ft.Container(
            content=ft.Row(
                [ft.Text("▶", size=12, color=theme.NEON_GREEN), self._end_turn_btn_label],
                spacing=6,
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            bgcolor=ft.Colors.with_opacity(0.12, theme.NEON_GREEN),
            border=ft.Border.all(1, ft.Colors.with_opacity(0.50, theme.NEON_GREEN)),
            border_radius=6,
            padding=ft.Padding.symmetric(horizontal=12, vertical=7),
            on_click=self._on_end_turn,
        )

        # ── Winner banner ────────────────────────────────────────────────
        self._winner_banner = ft.Container(
            visible=False,
            border_radius=8,
            padding=10,
            alignment=ft.Alignment.CENTER,
            width=float("inf"),
        )

        # ── Log panel ────────────────────────────────────────────────────
        self._log_list = ft.ListView(spacing=0, height=140, padding=0)
        self._log_count_text = ft.Text(
            "0 events", size=9, color=theme.AGENDA_GOLD,
        )
        self._log_toggle_icon = ft.Text(
            "▼", size=10, color=theme.TEXT_SECONDARY,
        )
        self._log_body = ft.Container(
            content=self._log_list,
            bgcolor=ft.Colors.with_opacity(0.3, theme.BG_DARK),
            border_radius=ft.BorderRadius.only(bottom_left=8, bottom_right=8),
            visible=False,  # starts collapsed
        )

    # ── Refresh ───────────────────────────────────────────────────────────────

    def refresh(self) -> None:
        """Push GameState into every widget ref, then page.update()."""
        s   = self.state
        cp  = s.active_player == "corp"
        color = theme.CORP_ACCENT if cp else theme.RUNNER_ACCENT

        # ── Turn banner ──────────────────────────────────────────────────
        self._banner_text.value       = "CORP TURN" if cp else "RUNNER TURN"
        self._banner_text.color       = color
        self._banner_round_text.value = f"Round {s.round}"
        self._turn_banner.bgcolor     = (theme.CORP_BANNER if cp else theme.RUNNER_BANNER)
        self._turn_banner.border      = ft.Border.all(1, ft.Colors.with_opacity(0.5, color))

        # ── Click tokens ─────────────────────────────────────────────────
        pw = self.page.width or 400
        tsz = max(32, min(44, int(pw * 0.09))) if self._is_mobile else 40
        self._corp_clicks_row.controls = ui.click_tokens_row(
            s.corp_clicks, 3, theme.CORP_ACCENT,
            self._corp_token_tap if cp else None,
            token_size=tsz,
            extra_clicks=s.corp_extra_clicks,
        )
        self._runner_clicks_row.controls = ui.click_tokens_row(
            s.runner_clicks, 4, theme.RUNNER_ACCENT,
            self._runner_token_tap if not cp else None,
            token_size=tsz,
            extra_clicks=s.runner_extra_clicks,
        )

        # ── Clicks count ─────────────────────────────────────────────────
        self._corp_clicks_count.value = (
            f"{s.corp_clicks}/{GameState.CORP_CLICKS_PER_TURN}"
        )
        self._runner_clicks_count.value = (
            f"{s.runner_clicks}/{GameState.RUNNER_CLICKS_PER_TURN}"
        )

        # ── Corp stats ───────────────────────────────────────────────────
        self._corp_credits_text.value = str(s.corp_credits)
        self._corp_bad_pub_text.value = str(s.corp_bad_pub)

        # ── Runner stats ─────────────────────────────────────────────────
        self._runner_credits_text.value = str(s.runner_credits)
        self._runner_tags_text.value    = str(s.runner_tags)
        self._runner_brain_text.value   = str(s.runner_brain)
        self._runner_hand_text.value    = str(s.runner_max_hand_size)
        self._runner_mu_text.value      = str(s.runner_mu)
        self._runner_link_text.value    = str(s.runner_link)

        # ── Agenda ───────────────────────────────────────────────────────
        self._corp_agenda_text.value   = str(s.corp_agenda)
        self._runner_agenda_text.value = str(s.runner_agenda)

        # ── Panels + agenda sidebar ───────────────────────────────────────
        corp_active = s.active_player == "corp"

        corp_panel = self._build_corp_panel(active=corp_active)
        corp_panel.expand = True
        runner_panel = self._build_runner_panel(active=not corp_active)
        runner_panel.expand = True

        panels_col = ft.Column(
            [corp_panel, runner_panel],
            spacing=8,
            expand=True,
        )
        agenda = self._build_agenda_bar()

        self._panels_container.controls = [
            ft.Row(
                [panels_col, agenda],
                spacing=6,
                vertical_alignment=ft.CrossAxisAlignment.STRETCH,
                expand=True,
            )
        ]

        # ── End Turn button label ────────────────────────────────────────
        self._end_turn_btn_label.value = (
            "END CORP TURN" if cp else "END RUNNER TURN"
        )

        # ── Winner banner ────────────────────────────────────────────────
        winner = s.winner
        if winner == "corp":
            self._winner_banner.visible = True
            self._winner_banner.bgcolor = theme.CORP_DIM
            self._winner_banner.border  = ft.Border.all(1, theme.CORP_ACCENT)
            self._winner_banner.content = ft.Text(
                "CORPORATION WINS",
                size=18, weight=ft.FontWeight.BOLD,
                color=theme.CORP_ACCENT, text_align=ft.TextAlign.CENTER,
            )
        elif winner == "runner":
            self._winner_banner.visible = True
            self._winner_banner.bgcolor = theme.RUNNER_DIM
            self._winner_banner.border  = ft.Border.all(1, theme.RUNNER_ACCENT)
            self._winner_banner.content = ft.Text(
                "RUNNER WINS",
                size=18, weight=ft.FontWeight.BOLD,
                color=theme.RUNNER_ACCENT, text_align=ft.TextAlign.CENTER,
            )
        else:
            self._winner_banner.visible = False

        # ── Log panel ────────────────────────────────────────────────────
        self._refresh_log_inline()

        self.page.update()

    def _refresh_log_inline(self) -> None:
        """Update log controls without calling page.update()."""
        self._log_list.controls = [
            ui.log_entry_row(e) for e in self.log.entries
        ]
        self._log_count_text.value = f"{len(self.log.entries)} events"

    # ── Event handlers ────────────────────────────────────────────────────────

    def _apply_stat_to_display(self, attr: str) -> None:
        """Update Text refs for one state field — avoids full refresh() on every tap."""
        s = self.state
        if attr == "corp_credits":
            self._corp_credits_text.value = str(s.corp_credits)
        elif attr == "corp_bad_pub":
            self._corp_bad_pub_text.value = str(s.corp_bad_pub)
        elif attr == "runner_credits":
            self._runner_credits_text.value = str(s.runner_credits)
        elif attr == "runner_tags":
            self._runner_tags_text.value = str(s.runner_tags)
        elif attr == "runner_brain":
            self._runner_brain_text.value = str(s.runner_brain)
            self._runner_hand_text.value = str(s.runner_max_hand_size)
        elif attr == "runner_max_hand_bonus":
            self._runner_hand_text.value = str(s.runner_max_hand_size)
        elif attr == "runner_mu":
            self._runner_mu_text.value = str(s.runner_mu)
        elif attr == "runner_link":
            self._runner_link_text.value = str(s.runner_link)

    def _stat_adjuster(self, attr: str, delta: int,
                       min_val: int = 0, max_val: int = 99,
                       symbol: str = "·", label: str = "",
                       suffix_fn=None, debounce_ms: int = 800):
        """
        Debounced stat adjuster: updates state immediately but batches
        the log entry. Shows +N/-N delta badge during debounce window.
        """
        def handle(e):
            self.state.adjust(attr, delta, min_val, max_val)
            self._pending_stat[attr] = self._pending_stat.get(attr, 0) + delta

            # Update delta badge
            if attr in self._delta_refs:
                ref = self._delta_refs[attr]
                p = self._pending_stat[attr]
                if p != 0:
                    ref.value = f"+{p}" if p > 0 else str(p)
                    ref.color = theme.NEON_GREEN if p > 0 else theme.DANGER_RED
                    ref.visible = True
                else:
                    ref.visible = False

            self._apply_stat_to_display(attr)
            self.page.update()

            # Cancel existing debounce and start new one
            if attr in self._stat_task and self._stat_task[attr]:
                self._stat_task[attr].cancel()
            self._stat_task[attr] = self.page.run_task(
                self._stat_commit, attr, symbol, label, suffix_fn, debounce_ms,
            )
        return handle

    async def _stat_commit(self, attr, symbol, label, suffix_fn, debounce_ms=800):
        """Async debounce: sleep then commit the batched stat change."""
        try:
            await asyncio.sleep(debounce_ms / 1000)
        except asyncio.CancelledError:
            return
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
        if attr in self._delta_refs:
            self._delta_refs[attr].visible = False
            self._delta_refs[attr].update()
        self._refresh_log_inline()
        self._log_list.update()
        self._log_count_text.update()

    def _tap_stat_handler(self, attr: str,
                          min_val: int = 0, max_val: int = 99,
                          symbol: str = "·", label: str = "",
                          suffix_fn=None):
        """Returns (on_tap, on_long_press) for a tap_stat component."""
        inc = self._stat_adjuster(attr, +1, min_val, max_val,
                                  symbol=symbol, label=label, suffix_fn=suffix_fn)
        dec = self._stat_adjuster(attr, -1, min_val, max_val,
                                  symbol=symbol, label=label, suffix_fn=suffix_fn)
        return inc, dec

    def _tap_credit_handler(self, player: str):
        """Returns (on_tap, on_long_press) for a tap_credit_row."""
        inc = self._stat_adjuster(
            f"{player}_credits", +1, symbol=theme.SYM_CREDIT, label="credits",
            debounce_ms=1000,
        )
        dec = self._stat_adjuster(
            f"{player}_credits", -1, symbol=theme.SYM_CREDIT, label="credits",
            debounce_ms=1000,
        )
        return inc, dec

    def _corp_token_tap(self, index: int, filled: bool):
        """Tap filled token = spend click, tap spent = restore."""
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

    def _on_add_corp_extra(self, e):
        self.state.corp_extra_clicks = (self.state.corp_extra_clicks + 1) % 4
        self.log.record(
            self.state.round, "corp", theme.SYM_CLICK,
            f"Extra clicks: {self.state.corp_extra_clicks}",
        )
        self.refresh()

    def _on_add_runner_extra(self, e):
        self.state.runner_extra_clicks = (self.state.runner_extra_clicks + 1) % 4
        self.log.record(
            self.state.round, "runner", theme.SYM_CLICK,
            f"Extra clicks: {self.state.runner_extra_clicks}",
        )
        self.refresh()

    def _on_refill_corp(self, e):
        self.state.corp_clicks = GameState.CORP_CLICKS_PER_TURN
        self.refresh()

    def _on_refill_runner(self, e):
        self.state.runner_clicks = GameState.RUNNER_CLICKS_PER_TURN
        self.refresh()

    def _on_toggle_bad_pub(self, e):
        self._show_bad_pub = not self._show_bad_pub
        self.refresh()

    def _on_toggle_mu(self, e):
        self._show_mu = not self._show_mu
        self.refresh()

    def _on_toggle_link(self, e):
        self._show_link = not self._show_link
        self.refresh()

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
        self._corp_rotated = False
        self._runner_rotated = False
        self._show_bad_pub = False
        self._show_mu = False
        self._show_link = False
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
        self._log_toggle_icon.value = "▲" if self._log_expanded else "▼"
        bl = 0 if self._log_expanded else 8
        self._log_header.border_radius = ft.BorderRadius.only(
            top_left=8, top_right=8,
            bottom_left=bl, bottom_right=bl,
        )
        self.page.update()

    def _on_rotate_corp(self, e) -> None:
        self._corp_rotated = not self._corp_rotated
        self.refresh()

    def _on_rotate_runner(self, e) -> None:
        self._runner_rotated = not self._runner_rotated
        self.refresh()

    # ── Toggle pill ───────────────────────────────────────────────────────────

    def _toggle_pill(self, label: str, active: bool, key: str, color: str) -> ft.Container:
        """Toggle pill button for optional stats."""
        handler_map = {
            "bad_pub": self._on_toggle_bad_pub,
            "mu":      self._on_toggle_mu,
            "link":    self._on_toggle_link,
        }
        pill_color = color if active else theme.TEXT_SECONDARY
        return ft.Container(
            content=ft.Text(
                f"✓ {label}" if active else f"+ {label}",
                size=8, color=pill_color,
                style=ft.TextStyle(weight=ft.FontWeight.BOLD),
            ),
            on_click=handler_map.get(key),
            bgcolor=ft.Colors.with_opacity(0.10, pill_color),
            border=ft.Border.all(1, ft.Colors.with_opacity(0.30, pill_color)),
            border_radius=4,
            padding=ft.Padding.symmetric(horizontal=6, vertical=2),
        )

    # ── Panel builders ────────────────────────────────────────────────────────

    def _build_corp_panel(self, active: bool) -> ft.Container:
        """Corp panel: clicks, credits (tap/lp), bad pub (tap/lp, optional)."""
        clicks_section = ft.Container(
            content=ft.Column(
                [
                    ft.Row(
                        [
                            ui.section_label("CLICKS  ·  draw first", theme.CORP_ACCENT),
                            ft.Container(expand=True),
                            self._corp_clicks_count,
                            ui.refill_button(theme.CORP_ACCENT, self._on_refill_corp),
                        ],
                        spacing=6,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    self._corp_clicks_row,
                    ft.Row(
                        [ft.Container(expand=True), self._corp_extra_btn],
                    ),
                ],
                spacing=4,
            ),
            opacity=1.0 if active else 0.35,
        )

        corp_credit_tap, corp_credit_lp = self._tap_credit_handler("corp")
        cred_row = ui.tap_credit_row(
            theme.CORP_ACCENT,
            self._corp_credits_text,
            self._delta_refs["corp_credits"],
            corp_credit_tap,
            corp_credit_lp,
        )

        controls = [clicks_section, ui.divider(), cred_row]

        if self._show_bad_pub:
            bp_inc, bp_dec = self._tap_stat_handler(
                "corp_bad_pub", symbol=theme.SYM_BAD_PUB, label="bad pub",
            )
            controls.append(ui.tap_stat(
                theme.ASSET_BAD_PUB, theme.BAD_PUB_COLOR,
                self._corp_bad_pub_text, bp_inc, bp_dec,
            ))

        controls.append(ft.Row(
            [self._toggle_pill("Bad Pub", self._show_bad_pub, "bad_pub", theme.BAD_PUB_COLOR)],
            alignment=ft.MainAxisAlignment.END,
        ))

        return ui.panel("CORP", theme.CORP_ACCENT, controls,
                        active=active,
                        rotated=self._corp_rotated,
                        on_rotate=self._on_rotate_corp)

    def _build_runner_panel(self, active: bool) -> ft.Container:
        """Runner panel: clicks, credits (tap/lp), tags+core (tap/lp), hand/mu/link (steppers)."""
        clicks_section = ft.Container(
            content=ft.Column(
                [
                    ft.Row(
                        [
                            ui.section_label("CLICKS", theme.RUNNER_ACCENT),
                            ft.Container(expand=True),
                            self._runner_clicks_count,
                            ui.refill_button(theme.RUNNER_ACCENT, self._on_refill_runner),
                        ],
                        spacing=6,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    self._runner_clicks_row,
                    ft.Row(
                        [ft.Container(expand=True), self._runner_extra_btn],
                    ),
                ],
                spacing=4,
            ),
            opacity=1.0 if active else 0.35,
        )

        runner_credit_tap, runner_credit_lp = self._tap_credit_handler("runner")
        cred_row = ui.tap_credit_row(
            theme.RUNNER_ACCENT,
            self._runner_credits_text,
            self._delta_refs["runner_credits"],
            runner_credit_tap,
            runner_credit_lp,
        )

        # Tags + Core Damage side by side (tap/long-press)
        tag_inc, tag_dec = self._tap_stat_handler(
            "runner_tags", symbol=theme.SYM_TAG, label="tag",
        )
        core_inc = self._stat_adjuster(
            "runner_brain", +1, symbol=theme.SYM_BRAIN, label="core dmg",
            suffix_fn=lambda s: f"(hand={s.runner_max_hand_size})",
        )
        core_dec = self._stat_adjuster(
            "runner_brain", -1, symbol=theme.SYM_BRAIN, label="core dmg",
            suffix_fn=lambda s: f"(hand={s.runner_max_hand_size})",
        )

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

        # Hand size with steppers
        hand = ui.stepper_stat(
            theme.ASSET_HAND, theme.RUNNER_ACCENT,
            self._runner_hand_text, theme.RUNNER_ACCENT,
            self._stat_adjuster("runner_max_hand_bonus", -1, -5, 10,
                                symbol=theme.SYM_HAND, label="hand bonus",
                                suffix_fn=lambda s: f"(hand={s.runner_max_hand_size})"),
            self._stat_adjuster("runner_max_hand_bonus", +1, -5, 10,
                                symbol=theme.SYM_HAND, label="hand bonus",
                                suffix_fn=lambda s: f"(hand={s.runner_max_hand_size})"),
        )

        controls = [clicks_section, ui.divider(), cred_row, ui.divider(), compact_row, ui.divider(), hand]

        if self._show_mu:
            controls.append(ui.stepper_stat(
                theme.ASSET_MU, theme.MU_COLOR,
                self._runner_mu_text, theme.MU_COLOR,
                self._stat_adjuster("runner_mu", -1, symbol=theme.SYM_MU, label="MU"),
                self._stat_adjuster("runner_mu", +1, symbol=theme.SYM_MU, label="MU"),
            ))

        if self._show_link:
            controls.append(ui.stepper_stat(
                theme.ASSET_LINK, theme.LINK_COLOR,
                self._runner_link_text, theme.LINK_COLOR,
                self._stat_adjuster("runner_link", -1, symbol=theme.SYM_LINK, label="link"),
                self._stat_adjuster("runner_link", +1, symbol=theme.SYM_LINK, label="link"),
            ))

        toggle_row = ft.Row(
            [
                self._toggle_pill("MU", self._show_mu, "mu", theme.MU_COLOR),
                self._toggle_pill("Link", self._show_link, "link", theme.LINK_COLOR),
            ],
            spacing=4,
            alignment=ft.MainAxisAlignment.END,
        )
        controls.append(toggle_row)

        return ui.panel("RUNNER", theme.RUNNER_ACCENT, controls,
                        active=active,
                        rotated=self._runner_rotated,
                        on_rotate=self._on_rotate_runner)

    # ── Agenda bar ────────────────────────────────────────────────────────────

    def _build_agenda_bar(self) -> ft.Container:
        """Build unified vertical tug-of-war agenda sidebar."""
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
        Assemble: turn banner, panels + agenda sidebar, log, actions.
        End Turn and Reset are at the bottom below the game log.
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
            padding=ft.Padding.only(top=4),
        )

        self._log_header = ft.Container(
            content=ft.Row(
                [
                    ft.Text("◎", size=12, color=theme.TEXT_SECONDARY),
                    ft.Text(
                        "GAME LOG",
                        size=10,
                        color=theme.TEXT_SECONDARY,
                        style=ft.TextStyle(
                            weight=ft.FontWeight.BOLD,
                            letter_spacing=1.5,
                        ),
                    ),
                    ft.Container(expand=True),
                    ft.Text("●", size=7, color=theme.AGENDA_GOLD),
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
                bottom_left=8, bottom_right=8,
            ),
            padding=ft.Padding.symmetric(horizontal=12, vertical=7),
            on_click=self._on_toggle_log,
        )

        log_panel = ft.Column(
            [self._log_header, self._log_body],
            spacing=0,
        )

        sp = 4 if self._is_mobile else 6

        page_h = self.page.height or 800
        footer_h = 110
        panels_min_h = max(300, page_h - footer_h - (36 if self._is_mobile else 16) - 50 - sp * 4)

        fixed_area = ft.Container(
            content=ft.Column(
                [
                    self._turn_banner,
                    self._winner_banner,
                    self._panels_container,
                ],
                spacing=sp,
                expand=True,
            ),
            height=panels_min_h,
        )

        self._main_column = ft.Column(
            [fixed_area, log_panel, actions_row],
            spacing=sp,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )
        self.page.add(self._main_column)
