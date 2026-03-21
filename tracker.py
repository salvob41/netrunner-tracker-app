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
        p.padding    = 16
        p.theme_mode = ft.ThemeMode.DARK

        # Window icon — PNG for cross-platform compatibility.
        # macOS dock icon can't be changed (Flet limitation), but this
        # works for Android builds and some desktop window managers.
        p.window.icon = "/icon.png"

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
        self._corp_bad_pub_text = ft.Text(
            "0", size=26, weight=ft.FontWeight.BOLD, color=theme.BAD_PUB_COLOR,
        )

        # ── Runner ────────────────────────────────────────────────────────────
        self._runner_clicks_row   = ft.Row(spacing=6)
        self._runner_credits_text = ft.Text(
            "5", size=26, weight=ft.FontWeight.BOLD, color=theme.RUNNER_ACCENT,
        )
        self._runner_tags_text  = ft.Text(
            "0", size=26, weight=ft.FontWeight.BOLD, color=theme.AGENDA_GOLD,
        )
        self._runner_brain_text = ft.Text(
            "0", size=26, weight=ft.FontWeight.BOLD, color=theme.PURPLE_ACCENT,
        )
        self._runner_net_text   = ft.Text(
            "0", size=26, weight=ft.FontWeight.BOLD, color=theme.DANGER_RED,
        )
        self._runner_hand_text  = ft.Text(
            "5", size=18, weight=ft.FontWeight.BOLD, color=theme.TEXT_SECONDARY,
        )

        # ── Agenda ───────────────────────────────────────────────────────────
        self._corp_agenda_text   = ft.Text(
            "0", size=40, weight=ft.FontWeight.BOLD, color=theme.CORP_ACCENT,
        )
        self._runner_agenda_text = ft.Text(
            "0", size=40, weight=ft.FontWeight.BOLD, color=theme.RUNNER_ACCENT,
        )
        self._agenda_pip_row = ft.Row(
            spacing=5,
            alignment=ft.MainAxisAlignment.CENTER,
        )

        # ── Panels (rebuilt on active player change) ──────────────────────────
        # We store the outer Row so we can replace its children when the
        # active player changes — panels rebuild cheaply.
        self._panels_row = ft.Row(spacing=12, vertical_alignment=ft.CrossAxisAlignment.START)

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
        self._corp_clicks_row.controls = ui.click_tokens_row(
            s.corp_clicks, 3, theme.CORP_ACCENT,
            self._corp_token_tap if cp else None,
        )
        self._runner_clicks_row.controls = ui.click_tokens_row(
            s.runner_clicks, 4, theme.RUNNER_ACCENT,
            self._runner_token_tap if not cp else None,
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
        self._runner_net_text.value     = str(s.runner_net)
        self._runner_hand_text.value    = str(s.runner_hand_size)

        # ── Agenda pips ───────────────────────────────────────────────────────
        self._corp_agenda_text.value   = str(s.corp_agenda)
        self._runner_agenda_text.value = str(s.runner_agenda)
        self._agenda_pip_row.controls  = ui.agenda_pip_row(
            s.corp_agenda, s.runner_agenda,
        ).controls

        # ── Panels (rebuild when active player changes so highlighting is fresh)
        corp_is_active   = s.active_player == "corp"
        self._panels_row.controls = [
            self._build_corp_panel(active=corp_is_active),
            self._build_runner_panel(active=not corp_is_active),
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
        Like _adjuster but writes an immediate log entry.
        Player is inferred from the attr prefix (corp_ or runner_).
        suffix_fn: optional callable(state) -> str for extra context.
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
        """
        Corp panel: mandatory draw, clicks, credits, bad publicity.
        Bad publicity lives here (not the Runner panel) because it is a Corp
        resource — placed on Corp during runs, giving Runner free credits.
        """
        s = self.state

        corp_is_active = active

        clicks_section = ft.Container(
            content=ft.Column(
                [
                    # "draw first" hint replaces the old mandatory draw toggle
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

        return ui.panel("CORP", theme.CORP_ACCENT, [
            clicks_section,
            ui.divider(),
            ui.credit_row(
                theme.CORP_ACCENT,
                self._corp_credits_text,
                self._corp_credits_delta,
                self._corp_credits_timer_bar,
                self._credit_adjuster("corp", -1),
                self._credit_adjuster("corp",  1),
            ),
            ui.stat_row(
                theme.ASSET_BAD_PUB, theme.BAD_PUB_COLOR,
                "Bad Pub", self._corp_bad_pub_text, theme.BAD_PUB_COLOR,
                self._stat_adjuster("corp_bad_pub", -1, symbol=theme.SYM_BAD_PUB, label="bad pub"),
                self._stat_adjuster("corp_bad_pub",  1, symbol=theme.SYM_BAD_PUB, label="bad pub"),
            ),
        ], active=active)

    def _build_runner_panel(self, active: bool) -> ft.Container:
        """
        Runner panel: clicks, credits, damage counters, computed hand size.
        All damage types are Runner-only — the Corp inflicts them, the Runner
        accumulates them.  Brain damage is permanent (reduces hand size),
        so hand_size is a computed property on GameState.
        """
        hand_row = ft.Container(
            content=ft.Row(
                [
                    ui.nsg_icon(theme.ASSET_HAND, 20, theme.TEXT_SECONDARY),
                    ft.Text("Hand", size=11, color=theme.TEXT_SECONDARY, width=62),
                    self._runner_hand_text,
                    ft.Text("5 − core", size=10, color=theme.TEXT_SECONDARY, italic=True),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=ft.Padding.symmetric(horizontal=8, vertical=4),
        )

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

        return ui.panel("RUNNER", theme.RUNNER_ACCENT, [
            clicks_section,
            ui.divider(),
            ui.credit_row(
                theme.RUNNER_ACCENT,
                self._runner_credits_text,
                self._runner_credits_delta,
                self._runner_credits_timer_bar,
                self._credit_adjuster("runner", -1),
                self._credit_adjuster("runner",  1),
            ),
            ui.divider(),
            ui.stat_row(
                theme.ASSET_TAG, theme.AGENDA_GOLD,
                "Tags", self._runner_tags_text, theme.AGENDA_GOLD,
                self._stat_adjuster("runner_tags", -1, symbol=theme.SYM_TAG, label="tag"),
                self._stat_adjuster("runner_tags",  1, symbol=theme.SYM_TAG, label="tag"),
            ),
            ui.stat_row(
                theme.ASSET_CORE_DAMAGE, theme.PURPLE_ACCENT,
                "Core", self._runner_brain_text, theme.PURPLE_ACCENT,
                self._stat_adjuster("runner_brain", -1, symbol=theme.SYM_BRAIN, label="core dmg",
                                    suffix_fn=lambda s: f"(hand={s.runner_hand_size})"),
                self._stat_adjuster("runner_brain",  1, symbol=theme.SYM_BRAIN, label="core dmg",
                                    suffix_fn=lambda s: f"(hand={s.runner_hand_size})"),
            ),
            ui.stat_row(
                theme.ASSET_CORE_DAMAGE, theme.DANGER_RED,
                "Net Dmg", self._runner_net_text, theme.DANGER_RED,
                self._stat_adjuster("runner_net", -1, symbol=theme.SYM_NET, label="net dmg"),
                self._stat_adjuster("runner_net",  1, symbol=theme.SYM_NET, label="net dmg"),
            ),
            ui.divider(),
            hand_row,
        ], active=active)

    # ── Agenda section ────────────────────────────────────────────────────────

    def _build_agenda_section(self) -> ft.Container:
        """
        Agenda scoreboard with pip display.

        The pip row (●●●○○○○  |  ●○○○○○○) gives players an immediate
        visual of how far each faction is from winning without needing to
        read numbers — modelled on physical agenda-tracking dials.
        The numeric scores stay alongside for precision.
        """
        return ft.Container(
            bgcolor=theme.PANEL_BG,
            border_radius=10,
            border=ft.Border.all(1, ft.Colors.with_opacity(0.45, theme.AGENDA_GOLD)),
            padding=ft.Padding.symmetric(horizontal=16, vertical=12),
            content=ft.Column(
                [
                    # Header — NSG agenda icon instead of unicode stars
                    ft.Row(
                        [
                            ui.nsg_icon(theme.ASSET_AGENDA, 16, theme.AGENDA_GOLD),
                            ft.Text(
                                "AGENDA SCORE",
                                size=11,
                                color=theme.AGENDA_GOLD,
                                style=ft.TextStyle(
                                    weight=ft.FontWeight.BOLD,
                                    letter_spacing=2.0,
                                ),
                            ),
                            ui.nsg_icon(theme.ASSET_AGENDA, 16, theme.AGENDA_GOLD),
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                        spacing=8,
                    ),
                    ft.Divider(
                        height=1,
                        color=ft.Colors.with_opacity(0.2, theme.AGENDA_GOLD),
                    ),
                    # Scores + pip row
                    ft.Row(
                        [
                            # Corp score + controls
                            ft.Column(
                                [
                                    ft.Text("CORP", size=10, color=theme.CORP_ACCENT),
                                    self._corp_agenda_text,
                                    ft.Row(
                                        [
                                            ui.stepper("−", self._stat_adjuster("corp_agenda", -1, 0, 7, symbol=theme.SYM_AGENDA, label="agenda", suffix_fn=lambda s: "pts"), theme.CORP_ACCENT),
                                            ui.stepper("+", self._stat_adjuster("corp_agenda",  1, 0, 7, symbol=theme.SYM_AGENDA, label="agenda", suffix_fn=lambda s: "pts"), theme.CORP_ACCENT),
                                        ],
                                        spacing=4,
                                    ),
                                ],
                                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                spacing=4,
                            ),
                            # Pip display — this is the visual centrepiece
                            ft.Column(
                                [
                                    ft.Text(
                                        "FIRST TO 7",
                                        size=9,
                                        color=theme.TEXT_SECONDARY,
                                        text_align=ft.TextAlign.CENTER,
                                    ),
                                    self._agenda_pip_row,
                                ],
                                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                spacing=8,
                                expand=True,
                            ),
                            # Runner score + controls
                            ft.Column(
                                [
                                    ft.Text("RUNNER", size=10, color=theme.RUNNER_ACCENT),
                                    self._runner_agenda_text,
                                    ft.Row(
                                        [
                                            ui.stepper("−", self._stat_adjuster("runner_agenda", -1, 0, 7, symbol=theme.SYM_AGENDA, label="agenda", suffix_fn=lambda s: "pts"), theme.RUNNER_ACCENT),
                                            ui.stepper("+", self._stat_adjuster("runner_agenda",  1, 0, 7, symbol=theme.SYM_AGENDA, label="agenda", suffix_fn=lambda s: "pts"), theme.RUNNER_ACCENT),
                                        ],
                                        spacing=4,
                                    ),
                                ],
                                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                spacing=4,
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                ],
                spacing=10,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        )

    # ── Layout assembly ───────────────────────────────────────────────────────

    def _build_layout(self) -> None:
        """
        Assemble all sections into the page.

        Order follows the natural Netrunner turn reading flow:
        whose turn → agenda state → both players' boards → end-turn action.
        """
        title_bar = ft.Container(
            content=ft.Column(
                [
                    ft.Text(
                        "NETRUNNER",
                        size=22,
                        color=theme.NEON_GREEN,
                        text_align=ft.TextAlign.CENTER,
                        style=ft.TextStyle(
                            weight=ft.FontWeight.BOLD,
                            letter_spacing=7.0,
                        ),
                    ),
                    ft.Text(
                        "G A M E  T R A C K E R",
                        size=9,
                        color=theme.TEXT_SECONDARY,
                        text_align=ft.TextAlign.CENTER,
                        style=ft.TextStyle(letter_spacing=3.0),
                    ),
                ],
                spacing=2,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            alignment=ft.Alignment.CENTER,
            padding=ft.Padding.only(bottom=4),
        )

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
