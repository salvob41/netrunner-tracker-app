"""
Reusable UI primitives for the Netrunner Tracker.

Each function has exactly one visual responsibility.  When the look of
something changes (e.g. click token shape), only this file changes — panel
builders and the tracker controller stay untouched.

SVG tinting strategy: ft.BlendMode.SRC_IN replaces all non-transparent
pixels in the image with `color`, giving us faction-coloured icons from
neutral NSG assets.
"""

import flet as ft
import theme


# ── NSG icon helper ───────────────────────────────────────────────────────────

def nsg_icon(asset_path: str, size: int, color: str) -> ft.Image:
    """
    Renders a tinted NSG SVG asset.

    SRC_IN blend makes every visible pixel take on `color` — the SVG's
    internal fill is irrelevant, so all icons work regardless of their
    original palette.
    """
    return ft.Image(
        src=asset_path,
        width=size,
        height=size,
        fit=ft.BoxFit.CONTAIN,
        color=color,
        color_blend_mode=ft.BlendMode.SRC_IN,
    )


# ── Click tokens ──────────────────────────────────────────────────────────────

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


# ── Stepper button ────────────────────────────────────────────────────────────

def stepper(symbol: str, on_click, color: str) -> ft.Container:
    """
    +/− button for adjusting any numeric stat.
    Container gives tighter size control than IconButton and has a
    predictable touch target on both desktop and touchscreen.
    """
    return ft.Container(
        width=32,
        height=32,
        border_radius=4,
        bgcolor=ft.Colors.with_opacity(0.10, color),
        border=ft.Border.all(1, ft.Colors.with_opacity(0.35, color)),
        alignment=ft.Alignment.CENTER,
        on_click=on_click,
        content=ft.Text(
            symbol,
            size=18,
            color=color,
            weight=ft.FontWeight.BOLD,
            text_align=ft.TextAlign.CENTER,
        ),
    )


# ── Stat row ──────────────────────────────────────────────────────────────────

def stat_row(
    asset_path: str,
    asset_color: str,
    label: str,
    value_ref: ft.Text,
    color: str,
    on_decrement,
    on_increment,
) -> ft.Container:
    """
    One labeled game stat with an NSG icon, value display, and +/− controls.
    Using a real NSG asset instead of a generic icon lets players map the
    symbol to the one they've already seen on physical cards.
    """
    return ft.Container(
        content=ft.Row(
            [
                nsg_icon(asset_path, 22, asset_color),
                ft.Text(label, size=11, color=theme.TEXT_SECONDARY, width=62),
                value_ref,
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
        padding=ft.Padding.symmetric(horizontal=8, vertical=5),
    )


# ── Agenda pips ───────────────────────────────────────────────────────────────

def _pip(filled: bool, color: str) -> ft.Container:
    """
    A single agenda-point pip: filled solid circle = scored, empty = not.
    Small and dense so all 14 pips fit in one row without scrolling.
    """
    return ft.Container(
        width=13,
        height=13,
        border_radius=7,
        bgcolor=color if filled else "transparent",
        border=ft.Border.all(2, color if filled else ft.Colors.with_opacity(0.28, color)),
    )


def agenda_pip_row(corp_score: int, runner_score: int) -> ft.Row:
    """
    Renders  ●●●○○○○  |  ●●○○○○○  — Corp pips on the left,
    Runner pips on the right, with a vertical bar divider between them.

    This layout was chosen over a single progress bar because:
    - Each pip maps to one real agenda card, so the count is unambiguous
    - The `---|----` shape the user requested (left fill vs right fill)
      is immediately readable without needing a numeric label
    """
    corp_pips   = [_pip(i < corp_score,   theme.CORP_ACCENT)   for i in range(7)]
    runner_pips = [_pip(i < runner_score, theme.RUNNER_ACCENT) for i in range(7)]

    divider = ft.Container(
        width=2,
        height=20,
        bgcolor=ft.Colors.with_opacity(0.35, theme.TEXT_SECONDARY),
        border_radius=1,
        margin=ft.Margin.symmetric(horizontal=8),
    )

    return ft.Row(
        [*corp_pips, divider, *runner_pips],
        spacing=5,
        alignment=ft.MainAxisAlignment.CENTER,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
    )


# ── Section label ─────────────────────────────────────────────────────────────

def section_label(text: str, color: str) -> ft.Text:
    """
    Uppercase sub-heading in the same faction color (muted) so it
    doesn't compete with the values it describes.
    """
    return ft.Text(
        text,
        size=10,
        color=ft.Colors.with_opacity(0.50, color),
        style=ft.TextStyle(weight=ft.FontWeight.W_700, letter_spacing=1.8),
    )


# ── Divider ───────────────────────────────────────────────────────────────────

def divider() -> ft.Divider:
    return ft.Divider(height=1, color=theme.PANEL_BORDER)


# ── Panel shell ───────────────────────────────────────────────────────────────

def panel(
    title: str,
    color: str,
    controls: list,
    active: bool = False,
) -> ft.Container:
    """
    Faction panel card with a left-edge accent stripe.

    `active=True` brightens the border and adds a subtle background tint so
    the current player's panel is immediately obvious without needing to read
    the turn banner.  The inactive panel stays visible but clearly secondary.
    """
    border_opacity = 0.85 if active else 0.28
    bg             = ft.Colors.with_opacity(0.05, color) if active else theme.PANEL_BG

    return ft.Container(
        expand=True,
        bgcolor=bg,
        border_radius=10,
        border=ft.Border.all(
            2 if active else 1,
            ft.Colors.with_opacity(border_opacity, color),
        ),
        padding=14,
        content=ft.Column(
            [
                ft.Row(
                    [
                        ft.Container(
                            width=3, height=20, bgcolor=color, border_radius=2,
                        ),
                        ft.Text(
                            title,
                            size=13,
                            color=color,
                            style=ft.TextStyle(
                                weight=ft.FontWeight.BOLD,
                                letter_spacing=2.5,
                            ),
                        ),
                        ft.Container(expand=True),
                        # "ACTIVE" pill badge so it's readable at a glance
                        ft.Container(
                            visible=active,
                            content=ft.Text(
                                "YOUR TURN",
                                size=9,
                                color=color,
                                style=ft.TextStyle(
                                    weight=ft.FontWeight.BOLD,
                                    letter_spacing=1.2,
                                ),
                            ),
                            bgcolor=ft.Colors.with_opacity(0.15, color),
                            border=ft.Border.all(1, ft.Colors.with_opacity(0.5, color)),
                            border_radius=4,
                            padding=ft.Padding.symmetric(horizontal=6, vertical=2),
                        ),
                    ],
                    spacing=8,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                ft.Divider(height=1, color=ft.Colors.with_opacity(0.18, color)),
                *controls,
            ],
            spacing=8,
        ),
    )


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


# ── Action button ─────────────────────────────────────────────────────────────

def action_button(
    symbol: str,
    label: str,
    color: str,
    on_click,
    expand: bool = False,
) -> ft.Container:
    """
    Bordered action button.  `expand=True` for the primary End Turn action
    so it gets a larger touch target than the secondary Reset button.
    The color coding (green = safe flow, red = destructive) follows standard
    UI convention so players don't have to read the label to know the risk.
    """
    return ft.Container(
        expand=expand,
        content=ft.Row(
            [
                ft.Text(symbol, size=14, color=color),
                ft.Text(
                    label,
                    size=12,
                    color=color,
                    style=ft.TextStyle(
                        weight=ft.FontWeight.BOLD,
                        letter_spacing=1.5,
                    ),
                ),
            ],
            spacing=6,
            alignment=ft.MainAxisAlignment.CENTER,
        ),
        bgcolor=ft.Colors.with_opacity(0.12, color),
        border=ft.Border.all(1, ft.Colors.with_opacity(0.50, color)),
        border_radius=8,
        padding=ft.Padding.symmetric(horizontal=18, vertical=12),
        on_click=on_click,
    )
