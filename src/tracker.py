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
        self._corp_clicks_row   = ft.Row(spacing=5)
        self._corp_credits_text = ft.Text(
            "5", size=36, weight=ft.FontWeight.BOLD, color=theme.CORP_ACCENT,
        )
        self._corp_bad_pub_text = ft.Text(
            "0", size=28, weight=ft.FontWeight.BOLD, color=theme.BAD_PUB_COLOR,
        )

        # ── Runner ───────────────────────────────────────────────────────
        self._runner_clicks_row   = ft.Row(spacing=5)
        self._runner_credits_text = ft.Text(
            "5", size=36, weight=ft.FontWeight.BOLD, color=theme.RUNNER_ACCENT,
        )
        self._runner_tags_text  = ft.Text(
            "0", size=28, weight=ft.FontWeight.BOLD, color=theme.AGENDA_GOLD,
        )
        self._runner_brain_text = ft.Text(
            "0", size=28, weight=ft.FontWeight.BOLD, color=theme.PURPLE_ACCENT,
        )
        self._runner_hand_text = ft.Text(
            "5", size=28, weight=ft.FontWeight.BOLD, color=theme.RUNNER_ACCENT,
        )
        self._runner_mu_text = ft.Text(
            "4", size=28, weight=ft.FontWeight.BOLD, color=theme.MU_COLOR,
        )
        self._runner_link_text = ft.Text(
            "0", size=28, weight=ft.FontWeight.BOLD, color=theme.LINK_COLOR,
        )

        # ── Agenda ───────────────────────────────────────────────────────
        self._corp_agenda_text   = ft.Text(
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
        self._end_turn_btn_label  = ft.Text(
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
        """
        Push GameState into every widget ref, then page.update().
        """
        s   = self.state
        cp  = s.active_player == "corp"
        color = theme.CORP_ACCENT if cp else theme.RUNNER_ACCENT

        # ── Turn banner ──────────────────────────────────────────────────
        self._banner_text.value      = "CORP TURN" if cp else "RUNNER TURN"
        self._banner_text.color      = color
        self._banner_round_text.value = f"Round {s.round}"
        self._turn_banner.bgcolor     = (theme.CORP_BANNER if cp else theme.RUNNER_BANNER)
        self._turn_banner.border      = ft.Border.all(1, ft.Colors.with_opacity(0.5, color))

        # ── Click tokens ─────────────────────────────────────────────────
        pw = self.page.width or 400
        tsz = max(32, min(48, int(pw * 0.09))) if self._is_mobile else 44
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

        # ── Corp stats ───────────────────────────────────────────────────
        self._corp_credits_text.value  = str(s.corp_credits)
        self._corp_bad_pub_text.value  = str(s.corp_bad_pub)

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

        # ── Panels + agenda halves ────────────────────────────────────────
        corp_active = s.active_player == "corp"
        corp_agenda, runner_agenda = self._build_agenda_halves()

        corp = self._build_corp_panel(active=corp_active)
        corp.expand = True
        runner = self._build_runner_panel(active=not corp_active)
        runner.expand = True

        # Each panel + its agenda half side by side
        corp_row = ft.Row(
            [corp, corp_agenda], spacing=5, expand=True,
        )
        runner_row = ft.Row(
            [runner, runner_agenda], spacing=5, expand=True,
        )

        self._panels_container.controls = [
            corp_row,
            self._end_turn_btn,
            runner_row,
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

            self.refresh()

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
        # Hide delta badge
        if attr in self._delta_refs:
            self._delta_refs[attr].visible = False
            self._delta_refs[attr].update()
        self._refresh_log_inline()
        self._log_list.update()
        self._log_count_text.update()

    def _split_handler(self, attr: str, min_val: int = 0, max_val: int = 99,
                       symbol: str = "·", label: str = "", suffix_fn=None,
                       debounce_ms: int = 800):
        """
        Returns (on_dec, on_inc) handlers for a split_tap_stat.
        Left tap = -1, right tap = +1. Both debounced.
        """
        dec = self._stat_adjuster(attr, -1, min_val, max_val,
                                  symbol=symbol, label=label, suffix_fn=suffix_fn,
                                  debounce_ms=debounce_ms)
        inc = self._stat_adjuster(attr, +1, min_val, max_val,
                                  symbol=symbol, label=label, suffix_fn=suffix_fn,
                                  debounce_ms=debounce_ms)
        return dec, inc

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

    # ── Action button handlers ─────────────────────────────────────────────────

    def _action_spend_click(self, player: str) -> bool:
        """Spend a click for an action. Returns False if no clicks left."""
        clicks = getattr(self.state, f"{player}_clicks")
        if clicks <= 0:
            return False
        self.state.spend_click(player)
        return True

    def _on_corp_draw(self, e) -> None:
        if not self._action_spend_click("corp"):
            return
        remaining = self.state.corp_clicks
        self.log.record(
            self.state.round, "corp", theme.SYM_CLICK,
            f"Drew a card ({remaining}/{GameState.CORP_CLICKS_PER_TURN})",
        )
        self.refresh()

    def _on_corp_take_credit(self, e) -> None:
        if not self._action_spend_click("corp"):
            return
        self.state.adjust("corp_credits", +1)
        remaining = self.state.corp_clicks
        creds = self.state.corp_credits
        self.log.record(
            self.state.round, "corp", theme.SYM_CREDIT,
            f"Took 1¢ → {creds}¢ ({remaining}/{GameState.CORP_CLICKS_PER_TURN})",
        )
        self.refresh()

    def _on_runner_draw(self, e) -> None:
        if not self._action_spend_click("runner"):
            return
        remaining = self.state.runner_clicks
        self.log.record(
            self.state.round, "runner", theme.SYM_CLICK,
            f"Drew a card ({remaining}/{GameState.RUNNER_CLICKS_PER_TURN})",
        )
        self.refresh()

    def _on_runner_take_credit(self, e) -> None:
        if not self._action_spend_click("runner"):
            return
        self.state.adjust("runner_credits", +1)
        remaining = self.state.runner_clicks
        creds = self.state.runner_credits
        self.log.record(
            self.state.round, "runner", theme.SYM_CREDIT,
            f"Took 1¢ → {creds}¢ ({remaining}/{GameState.RUNNER_CLICKS_PER_TURN})",
        )
        self.refresh()

    def _on_rotate_corp(self, e) -> None:
        self._corp_rotated = not self._corp_rotated
        self.refresh()

    def _on_rotate_runner(self, e) -> None:
        self._runner_rotated = not self._runner_rotated
        self.refresh()

    # ── Panel builders ────────────────────────────────────────────────────────

    def _build_corp_panel(self, active: bool) -> ft.Container:
        """Corp panel: clicks + action buttons + credits | bad pub."""
        tsz = 44 if self._is_mobile else 48
        clicks_section = ft.Container(
            content=ft.Row(
                [
                    self._corp_clicks_row,
                    ft.Container(expand=True),
                    *(
                        [
                            ui.action_button(
                                "Draw", theme.ASSET_HAND, theme.CORP_ACCENT,
                                self._on_corp_draw,
                            ),
                            ui.action_button(
                                "+¢", theme.ASSET_CREDIT, theme.CORP_ACCENT,
                                self._on_corp_take_credit,
                            ),
                        ] if active else []
                    ),
                ],
                spacing=4,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=ft.Padding.only(bottom=4),
            opacity=1.0 if active else 0.35,
        )

        cred_dec, cred_inc = self._split_handler(
            "corp_credits", symbol=theme.SYM_CREDIT, label="credits",
            debounce_ms=1200,
        )
        bp_dec, bp_inc = self._split_handler(
            "corp_bad_pub", symbol=theme.SYM_BAD_PUB, label="bad pub",
        )

        stats = ft.Row([
            ui.split_tap_stat(
                theme.ASSET_CREDIT, theme.CORP_ACCENT,
                self._corp_credits_text, cred_dec, cred_inc,
                bg=ft.Colors.with_opacity(0.06, theme.CORP_ACCENT),
                delta_ref=self._delta_refs["corp_credits"],
                expand=3, icon_size=28, height=110,
            ),
            ft.Container(width=1, height=22,
                         bgcolor=ft.Colors.with_opacity(0.18, theme.TEXT_SECONDARY)),
            ui.split_tap_stat(
                theme.ASSET_BAD_PUB, theme.BAD_PUB_COLOR,
                self._corp_bad_pub_text, bp_dec, bp_inc,
                bg=ft.Colors.with_opacity(0.06, theme.BAD_PUB_COLOR),
                delta_ref=self._delta_refs["corp_bad_pub"],
            ),
        ], spacing=3)

        return ui.panel("CORP", theme.CORP_ACCENT,
                        [clicks_section, stats], active=active,
                        rotated=self._corp_rotated,
                        on_rotate=self._on_rotate_corp)

    def _build_runner_panel(self, active: bool) -> ft.Container:
        """Runner panel: clicks + action buttons + 2 rows of stats."""
        clicks_section = ft.Container(
            content=ft.Row(
                [
                    self._runner_clicks_row,
                    ft.Container(expand=True),
                    *(
                        [
                            ui.action_button(
                                "Draw", theme.ASSET_HAND, theme.RUNNER_ACCENT,
                                self._on_runner_draw,
                            ),
                            ui.action_button(
                                "+¢", theme.ASSET_CREDIT, theme.RUNNER_ACCENT,
                                self._on_runner_take_credit,
                            ),
                        ] if active else []
                    ),
                ],
                spacing=4,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=ft.Padding.only(bottom=4),
            opacity=1.0 if active else 0.35,
        )

        cred_dec, cred_inc = self._split_handler(
            "runner_credits", symbol=theme.SYM_CREDIT, label="credits",
            debounce_ms=1200,
        )
        tag_dec, tag_inc = self._split_handler(
            "runner_tags", symbol=theme.SYM_TAG, label="tag",
        )
        core_dec = self._stat_adjuster(
            "runner_brain", -1, symbol=theme.SYM_BRAIN, label="core dmg",
            suffix_fn=lambda s: f"(hand={s.runner_max_hand_size})",
        )
        core_inc = self._stat_adjuster(
            "runner_brain", +1, symbol=theme.SYM_BRAIN, label="core dmg",
            suffix_fn=lambda s: f"(hand={s.runner_max_hand_size})",
        )

        row1 = ft.Row([
            ui.split_tap_stat(
                theme.ASSET_CREDIT, theme.RUNNER_ACCENT,
                self._runner_credits_text, cred_dec, cred_inc,
                bg=ft.Colors.with_opacity(0.06, theme.RUNNER_ACCENT),
                delta_ref=self._delta_refs["runner_credits"],
                expand=2, icon_size=28, height=110,
            ),
            ft.Container(width=1, height=22,
                         bgcolor=ft.Colors.with_opacity(0.18, theme.TEXT_SECONDARY)),
            ui.split_tap_stat(
                theme.ASSET_TAG, theme.AGENDA_GOLD,
                self._runner_tags_text, tag_dec, tag_inc,
                bg=ft.Colors.with_opacity(0.06, theme.AGENDA_GOLD),
                delta_ref=self._delta_refs["runner_tags"],
            ),
            ft.Container(width=1, height=22,
                         bgcolor=ft.Colors.with_opacity(0.18, theme.TEXT_SECONDARY)),
            ui.split_tap_stat(
                theme.ASSET_CORE_DAMAGE, theme.PURPLE_ACCENT,
                self._runner_brain_text, core_dec, core_inc,
                bg=ft.Colors.with_opacity(0.06, theme.PURPLE_ACCENT),
                delta_ref=self._delta_refs["runner_brain"],
            ),
        ], spacing=3)

        hand_dec = self._stat_adjuster(
            "runner_max_hand_bonus", -1, -5, 10,
            symbol=theme.SYM_HAND, label="hand bonus",
            suffix_fn=lambda s: f"(hand={s.runner_max_hand_size})",
        )
        hand_inc = self._stat_adjuster(
            "runner_max_hand_bonus", +1, -5, 10,
            symbol=theme.SYM_HAND, label="hand bonus",
            suffix_fn=lambda s: f"(hand={s.runner_max_hand_size})",
        )
        mu_dec, mu_inc = self._split_handler(
            "runner_mu", symbol=theme.SYM_MU, label="MU",
        )
        link_dec, link_inc = self._split_handler(
            "runner_link", symbol=theme.SYM_LINK, label="link",
        )

        row2 = ft.Row([
            ui.split_tap_stat(
                theme.ASSET_HAND, theme.RUNNER_ACCENT,
                self._runner_hand_text, hand_dec, hand_inc,
                bg=ft.Colors.with_opacity(0.06, theme.RUNNER_ACCENT),
                delta_ref=self._delta_refs["runner_max_hand_bonus"],
            ),
            ft.Container(width=1, height=22,
                         bgcolor=ft.Colors.with_opacity(0.18, theme.TEXT_SECONDARY)),
            ui.split_tap_stat(
                theme.ASSET_MU, theme.MU_COLOR,
                self._runner_mu_text, mu_dec, mu_inc,
                bg=ft.Colors.with_opacity(0.06, theme.MU_COLOR),
                delta_ref=self._delta_refs["runner_mu"],
            ),
            ft.Container(width=1, height=22,
                         bgcolor=ft.Colors.with_opacity(0.18, theme.TEXT_SECONDARY)),
            ui.split_tap_stat(
                theme.ASSET_LINK, theme.LINK_COLOR,
                self._runner_link_text, link_dec, link_inc,
                bg=ft.Colors.with_opacity(0.06, theme.LINK_COLOR),
                delta_ref=self._delta_refs["runner_link"],
            ),
        ], spacing=3)

        return ui.panel("RUNNER", theme.RUNNER_ACCENT,
                        [clicks_section, row1, row2], active=active,
                        rotated=self._runner_rotated,
                        on_rotate=self._on_rotate_runner)

    # ── Agenda bar ────────────────────────────────────────────────────────────

    def _build_agenda_halves(self) -> tuple[ft.Container, ft.Container]:
        """Returns (corp_agenda_half, runner_agenda_half)."""
        s = self.state
        corp_half = ui.agenda_half(
            score=s.corp_agenda,
            score_ref=self._corp_agenda_text,
            color=theme.CORP_ACCENT,
            on_tap=self._agenda_tap("corp", +1),
            on_long_press=self._agenda_tap("corp", -1),
            score_at_top=True,
            fill_from_top=True,
        )
        runner_half = ui.agenda_half(
            score=s.runner_agenda,
            score_ref=self._runner_agenda_text,
            color=theme.RUNNER_ACCENT,
            on_tap=self._agenda_tap("runner", +1),
            on_long_press=self._agenda_tap("runner", -1),
            score_at_top=False,
            fill_from_top=False,
        )
        return corp_half, runner_half

    # ── Layout assembly ───────────────────────────────────────────────────────

    def _build_layout(self) -> None:
        """
        Assemble: turn banner, panels + agenda sidebar, log, reset.
        """
        reset_btn = ft.Container(
            content=ft.Text(
                "⟳ RESET",
                size=9,
                color=ft.Colors.with_opacity(0.6, theme.DANGER_RED),
                style=ft.TextStyle(weight=ft.FontWeight.BOLD, letter_spacing=1.0),
            ),
            border=ft.Border.all(1, ft.Colors.with_opacity(0.25, theme.DANGER_RED)),
            border_radius=4,
            padding=ft.Padding.symmetric(horizontal=12, vertical=4),
            on_click=self._on_reset,
            alignment=ft.Alignment.CENTER,
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

        # Panels area gets min_height = page height so it always fills
        # the screen. When log expands below, the page scrolls.
        page_h = self.page.height or 800
        footer_h = 50  # log header + reset approximate height
        panels_min_h = page_h - footer_h - (36 if self._is_mobile else 16)

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

        footer = ft.Column(
            [
                log_panel,
                ft.Row([reset_btn], alignment=ft.MainAxisAlignment.CENTER),
            ],
            spacing=sp,
        )

        self._main_column = ft.Column(
            [fixed_area, footer],
            spacing=sp,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )
        self.page.add(self._main_column)
