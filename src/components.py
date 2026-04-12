"""
Reusable UI primitives for the Netrunner Tracker.

Each function has exactly one visual responsibility.  When the look of
something changes (e.g. click token shape), only this file changes — panel
builders and the tracker controller stay untouched.

SVG tinting strategy: ft.BlendMode.SRC_IN replaces all non-transparent
pixels in the image with `color`, giving us faction-coloured icons from
neutral NSG assets.
"""

import math

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


# ── Split-tap stat ───────────────────────────────────────────────────────────

def split_tap_stat(
    asset_path: str,
    asset_color: str,
    value_ref: ft.Text,
    on_dec,
    on_inc,
    icon_size: int = 22,
    bg: str | None = None,
    delta_ref: ft.Text | None = None,
    expand: int | bool = True,
    height: int = 80,
) -> ft.Container:
    """
    Compact stat cell: icon (left) + value (centered) + optional delta badge.
    Tap left half = decrement, tap right half = increment.
    delta_ref: if provided, shown as a small +N/-N badge in the top-right.
    expand: flex weight for Row layout (e.g. 2 = twice the space of expand=1).
    height: cell height in px.
    """
    icon = ft.Container(
        content=nsg_icon(asset_path, icon_size,
                         ft.Colors.with_opacity(0.6, asset_color)),
        padding=ft.Padding.only(left=8),
    )
    layers = [
        # Icon pinned to the left
        ft.Container(content=icon, alignment=ft.Alignment.CENTER_LEFT),
        # Value centered in the full cell
        ft.Container(content=value_ref, alignment=ft.Alignment.CENTER),
    ]
    # Delta badge in top-right corner
    if delta_ref:
        layers.append(
            ft.Container(
                content=delta_ref,
                alignment=ft.Alignment.TOP_RIGHT,
                padding=ft.Padding.only(right=6, top=4),
            ),
        )
    # Two invisible tap zones: left half = dec, right half = inc
    # Use full cell height so the entire surface is tappable
    layers.append(
        ft.Container(
            content=ft.Row([
                ft.GestureDetector(
                    content=ft.Container(
                        bgcolor=ft.Colors.TRANSPARENT,
                        height=height,
                        expand=True,
                    ),
                    on_tap=on_dec,
                    expand=True,
                ),
                ft.GestureDetector(
                    content=ft.Container(
                        bgcolor=ft.Colors.TRANSPARENT,
                        height=height,
                        expand=True,
                    ),
                    on_tap=on_inc,
                    expand=True,
                ),
            ], spacing=0, expand=True),
            height=height,
            expand=True,
        ),
    )
    cell = ft.Container(
        content=ft.Stack(layers),
        border_radius=8,
        height=height,
        bgcolor=bg,
        expand=expand,
        animate_opacity=ft.Animation(120, ft.AnimationCurve.EASE_OUT),
    )
    return cell


# ── Action button ────────────────────────────────────────────────────────────

def action_button(
    label: str,
    icon_path: str,
    color: str,
    on_click,
    icon_size: int = 14,
) -> ft.Container:
    """Compact action button with icon + label (e.g. 'Draw', '+ ¢')."""
    return ft.Container(
        content=ft.Column(
            [
                nsg_icon(icon_path, icon_size, color),
                ft.Text(
                    label, size=8, color=color,
                    style=ft.TextStyle(weight=ft.FontWeight.BOLD),
                    text_align=ft.TextAlign.CENTER,
                    no_wrap=True,
                ),
            ],
            spacing=2,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        bgcolor=ft.Colors.with_opacity(0.10, color),
        border=ft.Border.all(1, ft.Colors.with_opacity(0.35, color)),
        border_radius=6,
        padding=ft.Padding.symmetric(horizontal=6, vertical=4),
        on_click=on_click,
        width=44,
    )


# ── Vertical agenda bar ──────────────────────────────────────────────────────

def _agenda_segment(filled: bool, color: str, width: int) -> ft.Container:
    """One discrete agenda segment — filled or empty."""
    return ft.Container(
        width=width - 8,
        expand=True,
        bgcolor=ft.Colors.with_opacity(0.65, color) if filled else ft.Colors.with_opacity(0.08, color),
        border_radius=3,
        border=ft.Border.all(
            1, ft.Colors.with_opacity(0.4, color) if filled
            else ft.Colors.with_opacity(0.12, color),
        ),
    )


def agenda_half(
    score: int,
    score_ref: ft.Text,
    color: str,
    on_tap,
    on_long_press,
    score_at_top: bool = True,
    fill_from_top: bool = True,
) -> ft.Container:
    """
    One half of the agenda tug-of-war: 7 discrete segments + score.
    Place beside its faction panel — STRETCH makes it match panel height.
    fill_from_top=True: segments fill top-down (corp, outside→center).
    fill_from_top=False: segments fill bottom-up (runner, outside→center).
    """
    bar_width = theme.AGENDA_BAR_WIDTH

    segs = []
    for i in range(7):
        if fill_from_top:
            filled = i < score
        else:
            filled = (6 - i) < score
        segs.append(_agenda_segment(filled, color, bar_width))

    children = ([score_ref] + segs) if score_at_top else (segs + [score_ref])

    return ft.GestureDetector(
        content=ft.Container(
            width=bar_width,
            bgcolor=theme.PANEL_BG,
            border_radius=8,
            clip_behavior=ft.ClipBehavior.HARD_EDGE,
            padding=ft.Padding.symmetric(horizontal=4, vertical=4),
            border=ft.Border.all(1, ft.Colors.with_opacity(0.3, color)),
            content=ft.Column(
                children,
                spacing=2, expand=True,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        ),
        on_tap=on_tap,
        on_long_press_start=on_long_press,
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
    rotated: bool = False,
    on_rotate=None,
) -> ft.Container:
    """
    Faction panel card with a left-edge accent stripe.

    `active=True` brightens the border and adds a subtle background tint so
    the current player's panel is immediately obvious without needing to read
    the turn banner.  The inactive panel stays visible but clearly secondary.
    `rotated=True` flips the panel content 180° for shared-device play.
    `on_rotate` callback for the rotate toggle button.
    """
    border_opacity = 0.85 if active else 0.28
    bg             = ft.Colors.with_opacity(0.05, color) if active else theme.PANEL_BG

    rotate_btn = ft.GestureDetector(
        content=ft.Container(
            content=ft.Text(
                "⟳", size=14,
                color=ft.Colors.with_opacity(0.5 if not rotated else 0.9, color),
            ),
            padding=ft.Padding.symmetric(horizontal=4, vertical=0),
        ),
        on_tap=on_rotate,
    ) if on_rotate else ft.Container()

    header = ft.Row(
        [
            ft.Container(
                width=3, height=14, bgcolor=color, border_radius=2,
            ),
            ft.Text(
                title,
                size=11,
                color=color,
                style=ft.TextStyle(
                    weight=ft.FontWeight.BOLD,
                    letter_spacing=2.0,
                ),
            ),
            ft.Container(expand=True),
            # "YOUR TURN" pill badge
            ft.Container(
                visible=active,
                content=ft.Text(
                    "YOUR TURN",
                    size=8,
                    color=color,
                    style=ft.TextStyle(
                        weight=ft.FontWeight.BOLD,
                        letter_spacing=1.0,
                    ),
                ),
                bgcolor=ft.Colors.with_opacity(0.15, color),
                border=ft.Border.all(1, ft.Colors.with_opacity(0.5, color)),
                border_radius=4,
                padding=ft.Padding.symmetric(horizontal=5, vertical=1),
            ),
            rotate_btn,
        ],
        spacing=6,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
    )

    inner = ft.Column(
        [header, *controls],
        spacing=5,
    )

    return ft.Container(
        bgcolor=bg,
        border_radius=10,
        border=ft.Border.all(
            2 if active else 1,
            ft.Colors.with_opacity(border_opacity, color),
        ),
        padding=8,
        content=ft.Container(
            content=inner,
            rotate=ft.Rotate(math.pi) if rotated else None,
        ),
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
