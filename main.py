import flet as ft

# -- Cyberpunk color palette --
BG_DARK = "#0a0a0f"
PANEL_BG = "#12121a"
PANEL_BORDER = "#2a2a3a"
CORP_ACCENT = "#4a9eff"
CORP_DIM = "#1a3a5a"
RUNNER_ACCENT = "#ff6b35"
RUNNER_DIM = "#5a2a1a"
AGENDA_GOLD = "#ffd700"
AGENDA_DIM = "#3a3500"
TEXT_PRIMARY = "#e0e0e0"
TEXT_SECONDARY = "#888899"
NEON_GREEN = "#00ff88"
DANGER_RED = "#ff3355"
PURPLE_ACCENT = "#b366ff"


def main(page: ft.Page):
    page.title = "NETRUNNER TRACKER"
    page.bgcolor = BG_DARK
    page.padding = 20
    page.window.width = 720
    page.window.height = 820
    page.theme_mode = ft.ThemeMode.DARK
    page.fonts = {"Mono": "RobotoMono"}

    # ── State ──
    state = {
        "turn": 1,
        "corp_clicks": 3,
        "corp_credits": 5,
        "corp_agenda": 0,
        "corp_drew": False,
        "runner_clicks": 4,
        "runner_credits": 5,
        "runner_agenda": 0,
        "runner_tags": 0,
        "runner_brain": 0,
        "runner_net": 0,
    }

    # ── Helpers ──
    def click_dot(filled: bool, color: str) -> ft.Container:
        return ft.Container(
            width=18,
            height=18,
            border_radius=9,
            bgcolor=color if filled else "transparent",
            border=ft.Border.all(2, color),
            margin=ft.Margin.only(right=4),
        )

    def build_clicks_row(current: int, maximum: int, color: str) -> ft.Row:
        dots = [click_dot(i < current, color) for i in range(maximum)]
        return ft.Row(dots, spacing=2)

    def stat_button(icon: str, on_click, color: str, size: int = 28) -> ft.IconButton:
        return ft.IconButton(
            icon=icon,
            icon_color=color,
            icon_size=size,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=6),
                overlay_color=ft.Colors.with_opacity(0.1, color),
            ),
            on_click=on_click,
            width=36,
            height=36,
        )

    def section_title(text: str, color: str) -> ft.Text:
        return ft.Text(
            text,
            size=11,
            color=TEXT_SECONDARY,
            weight=ft.FontWeight.W_600,
        )

    # ── UI refs ──
    turn_text = ft.Text("1", size=28, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY)

    corp_clicks_row = ft.Row(spacing=2)
    corp_credits_text = ft.Text("5", size=26, weight=ft.FontWeight.BOLD, color=CORP_ACCENT)
    corp_draw_icon = ft.Container(
        content=ft.Icon(ft.Icons.DOWNLOAD_ROUNDED, color=TEXT_SECONDARY, size=20),
        width=32,
        height=32,
        border_radius=6,
        bgcolor=PANEL_BG,
        border=ft.Border.all(1, PANEL_BORDER),
        alignment=ft.Alignment.CENTER,
        tooltip="Mandatory draw",
    )

    runner_clicks_row = ft.Row(spacing=2)
    runner_credits_text = ft.Text("5", size=26, weight=ft.FontWeight.BOLD, color=RUNNER_ACCENT)
    runner_tags_text = ft.Text("0", size=22, weight=ft.FontWeight.BOLD, color=AGENDA_GOLD)
    runner_brain_text = ft.Text("0", size=22, weight=ft.FontWeight.BOLD, color=PURPLE_ACCENT)
    runner_net_text = ft.Text("0", size=22, weight=ft.FontWeight.BOLD, color=DANGER_RED)
    runner_hand_text = ft.Text("5", size=16, weight=ft.FontWeight.BOLD, color=TEXT_SECONDARY)

    corp_agenda_text = ft.Text("0", size=32, weight=ft.FontWeight.BOLD, color=CORP_ACCENT)
    runner_agenda_text = ft.Text("0", size=32, weight=ft.FontWeight.BOLD, color=RUNNER_ACCENT)

    agenda_bar = ft.ProgressBar(
        value=0,
        width=200,
        height=6,
        color=CORP_ACCENT,
        bgcolor=RUNNER_DIM,
        border_radius=3,
    )

    winner_banner = ft.Container(visible=False)

    # ── Update UI ──
    def refresh():
        turn_text.value = str(state["turn"])

        # Corp clicks
        corp_clicks_row.controls = [
            click_dot(i < state["corp_clicks"], CORP_ACCENT) for i in range(3)
        ]

        # Corp draw indicator
        if state["corp_drew"]:
            corp_draw_icon.bgcolor = CORP_DIM
            corp_draw_icon.border = ft.Border.all(1, CORP_ACCENT)
            corp_draw_icon.content = ft.Icon(ft.Icons.CHECK_ROUNDED, color=CORP_ACCENT, size=20)
        else:
            corp_draw_icon.bgcolor = PANEL_BG
            corp_draw_icon.border = ft.Border.all(1, PANEL_BORDER)
            corp_draw_icon.content = ft.Icon(ft.Icons.DOWNLOAD_ROUNDED, color=TEXT_SECONDARY, size=20)

        corp_credits_text.value = str(state["corp_credits"])
        runner_clicks_row.controls = [
            click_dot(i < state["runner_clicks"], RUNNER_ACCENT) for i in range(4)
        ]
        runner_credits_text.value = str(state["runner_credits"])
        runner_tags_text.value = str(state["runner_tags"])
        runner_brain_text.value = str(state["runner_brain"])
        runner_net_text.value = str(state["runner_net"])

        hand_size = max(0, 5 - state["runner_brain"])
        runner_hand_text.value = str(hand_size)

        corp_agenda_text.value = str(state["corp_agenda"])
        runner_agenda_text.value = str(state["runner_agenda"])

        # Agenda bar: 0.5 = even, <0.5 = runner ahead, >0.5 = corp ahead
        total = state["corp_agenda"] + state["runner_agenda"]
        if total > 0:
            agenda_bar.value = state["corp_agenda"] / total
        else:
            agenda_bar.value = 0.5

        # Win check
        if state["corp_agenda"] >= 7:
            winner_banner.visible = True
            winner_banner.content = ft.Text(
                "CORP WINS", size=24, weight=ft.FontWeight.BOLD,
                color=CORP_ACCENT, text_align=ft.TextAlign.CENTER,
            )
            winner_banner.bgcolor = CORP_DIM
        elif state["runner_agenda"] >= 7:
            winner_banner.visible = True
            winner_banner.content = ft.Text(
                "RUNNER WINS", size=24, weight=ft.FontWeight.BOLD,
                color=RUNNER_ACCENT, text_align=ft.TextAlign.CENTER,
            )
            winner_banner.bgcolor = RUNNER_DIM
        else:
            winner_banner.visible = False

        page.update()

    # ── Event handlers ──
    def adjust(key: str, delta: int, min_val: int = 0, max_val: int = 99):
        def handler(e):
            state[key] = max(min_val, min(max_val, state[key] + delta))
            refresh()
        return handler

    def toggle_draw(e):
        state["corp_drew"] = not state["corp_drew"]
        refresh()

    def new_turn(e):
        state["turn"] += 1
        state["corp_clicks"] = 3
        state["runner_clicks"] = 4
        state["corp_drew"] = False
        refresh()

    def reset_game(e):
        state.update({
            "turn": 1,
            "corp_clicks": 3, "corp_credits": 5, "corp_agenda": 0, "corp_drew": False,
            "runner_clicks": 4, "runner_credits": 5, "runner_agenda": 0,
            "runner_tags": 0, "runner_brain": 0, "runner_net": 0,
        })
        refresh()

    # ── Build stat row ──
    def stat_row(label: str, icon_name: str, value_widget: ft.Text, color: str, key: str) -> ft.Container:
        return ft.Container(
            content=ft.Row(
                [
                    ft.Icon(icon_name, color=color, size=18),
                    ft.Text(label, size=12, color=TEXT_SECONDARY, width=50),
                    value_widget,
                    ft.Row(
                        [
                            stat_button(ft.Icons.REMOVE, adjust(key, -1), color),
                            stat_button(ft.Icons.ADD, adjust(key, 1), color),
                        ],
                        spacing=0,
                    ),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=ft.Padding.symmetric(horizontal=8, vertical=2),
        )

    # ── Panel builder ──
    def panel(title: str, color: str, content_controls: list) -> ft.Container:
        return ft.Container(
            expand=True,
            bgcolor=PANEL_BG,
            border_radius=12,
            border=ft.Border.all(1, PANEL_BORDER),
            padding=16,
            content=ft.Column(
                [
                    ft.Text(title, size=14, weight=ft.FontWeight.BOLD, color=color),
                    ft.Divider(height=1, color=PANEL_BORDER),
                    *content_controls,
                ],
                spacing=10,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        )

    # ── Corp panel ──
    corp_panel = panel("CORP", CORP_ACCENT, [
        # Mandatory draw
        ft.Container(
            content=ft.Row(
                [
                    ft.Text("MANDATORY DRAW", size=10, color=TEXT_SECONDARY),
                    ft.GestureDetector(
                        content=corp_draw_icon,
                        on_tap=toggle_draw,
                    ),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=8,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=ft.Padding.only(bottom=4),
        ),
        # Clicks
        ft.Container(
            content=ft.Column([
                section_title("CLICKS", CORP_ACCENT),
                ft.Row(
                    [
                        corp_clicks_row,
                        ft.Row(
                            [
                                stat_button(ft.Icons.REMOVE, adjust("corp_clicks", -1, 0, 3), CORP_ACCENT),
                                stat_button(ft.Icons.ADD, adjust("corp_clicks", 1, 0, 3), CORP_ACCENT),
                            ],
                            spacing=0,
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
            ], spacing=4),
        ),
        # Credits
        stat_row("Credits", ft.Icons.MONETIZATION_ON_OUTLINED, corp_credits_text, CORP_ACCENT, "corp_credits"),
    ])

    # ── Runner panel ──
    runner_panel = panel("RUNNER", RUNNER_ACCENT, [
        # Clicks
        ft.Container(
            content=ft.Column([
                section_title("CLICKS", RUNNER_ACCENT),
                ft.Row(
                    [
                        runner_clicks_row,
                        ft.Row(
                            [
                                stat_button(ft.Icons.REMOVE, adjust("runner_clicks", -1, 0, 4), RUNNER_ACCENT),
                                stat_button(ft.Icons.ADD, adjust("runner_clicks", 1, 0, 4), RUNNER_ACCENT),
                            ],
                            spacing=0,
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
            ], spacing=4),
        ),
        # Credits
        stat_row("Credits", ft.Icons.MONETIZATION_ON_OUTLINED, runner_credits_text, RUNNER_ACCENT, "runner_credits"),
        ft.Divider(height=1, color=PANEL_BORDER),
        # Tags
        stat_row("Tags", ft.Icons.LOCAL_OFFER_OUTLINED, runner_tags_text, AGENDA_GOLD, "runner_tags"),
        # Brain damage
        stat_row("Brain", ft.Icons.PSYCHOLOGY_OUTLINED, runner_brain_text, PURPLE_ACCENT, "runner_brain"),
        # Net damage
        stat_row("Net", ft.Icons.FLASH_ON_OUTLINED, runner_net_text, DANGER_RED, "runner_net"),
        ft.Divider(height=1, color=PANEL_BORDER),
        # Hand size (read-only)
        ft.Container(
            content=ft.Row(
                [
                    ft.Icon(ft.Icons.BACK_HAND_OUTLINED, color=TEXT_SECONDARY, size=18),
                    ft.Text("Hand", size=12, color=TEXT_SECONDARY, width=50),
                    runner_hand_text,
                    ft.Text("(5 - brain)", size=10, color=TEXT_SECONDARY, italic=True),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=ft.Padding.symmetric(horizontal=8, vertical=2),
        ),
    ])

    # ── Agenda section (top center) ──
    agenda_section = ft.Container(
        bgcolor=PANEL_BG,
        border_radius=12,
        border=ft.Border.all(1, PANEL_BORDER),
        padding=20,
        content=ft.Column(
            [
                ft.Text("AGENDA SCORE", size=12, weight=ft.FontWeight.BOLD,
                         color=AGENDA_GOLD, text_align=ft.TextAlign.CENTER),
                ft.Divider(height=1, color=PANEL_BORDER),
                ft.Row(
                    [
                        # Corp agenda
                        ft.Column(
                            [
                                ft.Text("CORP", size=10, color=CORP_ACCENT),
                                corp_agenda_text,
                                ft.Row([
                                    stat_button(ft.Icons.REMOVE, adjust("corp_agenda", -1, 0, 7), CORP_ACCENT),
                                    stat_button(ft.Icons.ADD, adjust("corp_agenda", 1, 0, 7), CORP_ACCENT),
                                ], spacing=0),
                            ],
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            spacing=2,
                        ),
                        # Progress bar
                        ft.Column(
                            [
                                ft.Text("FIRST TO 7", size=9, color=TEXT_SECONDARY),
                                agenda_bar,
                            ],
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            spacing=6,
                            expand=True,
                        ),
                        # Runner agenda
                        ft.Column(
                            [
                                ft.Text("RUNNER", size=10, color=RUNNER_ACCENT),
                                runner_agenda_text,
                                ft.Row([
                                    stat_button(ft.Icons.REMOVE, adjust("runner_agenda", -1, 0, 7), RUNNER_ACCENT),
                                    stat_button(ft.Icons.ADD, adjust("runner_agenda", 1, 0, 7), RUNNER_ACCENT),
                                ], spacing=0),
                            ],
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            spacing=2,
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

    # ── Winner banner ──
    winner_banner.border_radius = 8
    winner_banner.padding = 12
    winner_banner.alignment = ft.Alignment.CENTER
    winner_banner.width = float("inf")

    # ── Turn header ──
    turn_header = ft.Container(
        content=ft.Row(
            [
                ft.Text("TURN", size=14, color=TEXT_SECONDARY, weight=ft.FontWeight.W_600),
                stat_button(ft.Icons.CHEVRON_LEFT, adjust("turn", -1, 1), TEXT_SECONDARY),
                turn_text,
                stat_button(ft.Icons.CHEVRON_RIGHT, adjust("turn", 1, 1), TEXT_SECONDARY),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=4,
        ),
    )

    # ── Title ──
    title_bar = ft.Container(
        content=ft.Text(
            "NETRUNNER TRACKER",
            size=20,
            weight=ft.FontWeight.BOLD,
            color=NEON_GREEN,

            text_align=ft.TextAlign.CENTER,
        ),
        alignment=ft.Alignment.CENTER,
        padding=ft.Padding.only(bottom=4),
    )

    # ── Action buttons ──
    actions_row = ft.Container(
        content=ft.Row(
            [
                ft.Button(
                    "New Turn",
                    icon=ft.Icons.SKIP_NEXT_ROUNDED,
                    on_click=new_turn,
                    style=ft.ButtonStyle(
                        bgcolor=CORP_DIM,
                        color=TEXT_PRIMARY,
                        shape=ft.RoundedRectangleBorder(radius=8),
                        padding=ft.Padding.symmetric(horizontal=24, vertical=12),
                    ),
                ),
                ft.OutlinedButton(
                    "Reset Game",
                    icon=ft.Icons.RESTART_ALT_ROUNDED,
                    on_click=reset_game,
                    style=ft.ButtonStyle(
                        color=DANGER_RED,
                        side=ft.BorderSide(1, DANGER_RED),
                        shape=ft.RoundedRectangleBorder(radius=8),
                        padding=ft.Padding.symmetric(horizontal=24, vertical=12),
                    ),
                ),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=16,
        ),
        padding=ft.Padding.only(top=8),
    )

    # ── Layout ──
    page.add(
        ft.Column(
            [
                title_bar,
                turn_header,
                winner_banner,
                agenda_section,
                ft.Row(
                    [corp_panel, runner_panel],
                    spacing=12,
                    vertical_alignment=ft.CrossAxisAlignment.START,
                ),
                actions_row,
            ],
            spacing=12,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            expand=True,
        )
    )

    # Initial render
    refresh()


ft.run(main)
