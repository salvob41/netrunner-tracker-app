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

def click_token(filled: bool, color: str, on_tap=None, size: int = 48) -> ft.Control:
    """
    One click token using the official NSG click symbol.

    When on_tap is provided, the token is wrapped in a GestureDetector
    for tap interaction.  When None (inactive player), it returns a
    plain Container — no tap handler, used as display-only.
    size: container size in px (48 desktop, 40 mobile).
    """
    asset = theme.ASSET_CLICK if filled else theme.ASSET_CLICK_SPENT
    icon_color = color if filled else ft.Colors.with_opacity(0.30, color)
    bg = ft.Colors.with_opacity(0.15, color) if filled else "transparent"
    border_color = ft.Colors.with_opacity(0.7, color) if filled else ft.Colors.with_opacity(0.22, color)
    icon_size = int(size * 0.55)

    token_container = ft.Container(
        width=size,
        height=size,
        border_radius=6,
        bgcolor=bg,
        border=ft.Border.all(2, border_color),
        alignment=ft.Alignment.CENTER,
        content=ft.Image(
            src=asset,
            width=icon_size,
            height=icon_size,
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
    token_size: int = 48,
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
            size=token_size,
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

    # Use PNG asset if available, otherwise fall back to text symbol
    asset_info = theme.SYM_ASSET_MAP.get(entry.symbol)
    if asset_info:
        asset_path, asset_color = asset_info
        icon_widget = nsg_icon(asset_path, 14, asset_color or color)
    else:
        icon_widget = ft.Text(
            entry.symbol, size=12, color=color,
            text_align=ft.TextAlign.CENTER,
        )

    return ft.Container(
        content=ft.Row(
            [
                ft.Text(
                    f"R{entry.round}·{entry.player.upper()}",
                    size=9,
                    color=ft.Colors.with_opacity(0.6, color),
                    width=64,
                ),
                ft.Container(
                    width=20,
                    alignment=ft.Alignment.CENTER,
                    content=icon_widget,
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
