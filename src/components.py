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


# ── Split-tap stat ───────────────────────────────────────────────────────────

def split_tap_stat(
    asset_path: str,
    asset_color: str,
    value_ref: ft.Text,
    on_dec,
    on_inc,
    icon_size: int = 18,
    bg: str | None = None,
    delta_ref: ft.Text | None = None,
) -> ft.Container:
    """
    Compact stat cell: icon (left) + value (centered) + optional delta badge.
    Tap left half = decrement, tap right half = increment.
    delta_ref: if provided, shown as a small +N/-N badge in the top-right.
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
    # Explicit height + expand ensures zones fill the full 48px cell
    layers.append(
        ft.Container(
            content=ft.Row([
                ft.GestureDetector(
                    content=ft.Container(
                        bgcolor=ft.Colors.TRANSPARENT,
                        height=48,
                        expand=True,
                    ),
                    on_tap=on_dec,
                    expand=True,
                ),
                ft.GestureDetector(
                    content=ft.Container(
                        bgcolor=ft.Colors.TRANSPARENT,
                        height=48,
                        expand=True,
                    ),
                    on_tap=on_inc,
                    expand=True,
                ),
            ], spacing=0, expand=True),
            height=48,
            expand=True,
        ),
    )
    cell = ft.Container(
        content=ft.Stack(layers),
        border_radius=8,
        height=48,
        bgcolor=bg,
        expand=True,
        animate_opacity=ft.Animation(120, ft.AnimationCurve.EASE_OUT),
    )
    return cell


# ── Vertical agenda bar ──────────────────────────────────────────────────────

def agenda_bar(
    corp_score: int,
    runner_score: int,
    corp_score_ref: ft.Text,
    runner_score_ref: ft.Text,
    on_corp_tap,
    on_corp_long_press,
    on_runner_tap,
    on_runner_long_press,
) -> ft.Container:
    """
    Vertical tug-of-war agenda bar. Top half = Corp, bottom half = Runner.
    Fills grow OUTWARD from the center divider.
    Uses expand so it stretches to match sibling height.
    Tap to +1, long-press to -1. Dead zone around center.
    """
    dead_zone = theme.AGENDA_BAR_DEAD_ZONE
    bar_width = theme.AGENDA_BAR_WIDTH

    # Fill proportions (expand ratios to approximate score/7)
    corp_fill = max(corp_score, 0)
    corp_empty = max(7 - corp_score, 0)
    runner_fill = max(runner_score, 0)
    runner_empty = max(7 - runner_score, 0)

    # Corp half (top): empty space at top, fill near center, score near center
    corp_children = []
    if corp_empty > 0:
        corp_children.append(ft.Container(expand=corp_empty))
    if corp_fill > 0:
        corp_children.append(ft.Container(
            expand=corp_fill,
            bgcolor=ft.Colors.with_opacity(0.6, theme.CORP_ACCENT),
            border_radius=2,
        ))
    corp_children.append(ft.Container(
        content=corp_score_ref,
        alignment=ft.Alignment.CENTER,
        padding=ft.Padding.only(bottom=3),
    ))

    corp_half = ft.GestureDetector(
        content=ft.Container(
            width=bar_width,
            bgcolor=theme.PANEL_BG,
            border_radius=ft.BorderRadius.only(top_left=6, top_right=6),
            clip_behavior=ft.ClipBehavior.HARD_EDGE,
            expand=True,
            content=ft.Column(corp_children, spacing=0, expand=True),
        ),
        on_tap=on_corp_tap,
        on_long_press_start=on_corp_long_press,
    )

    # Center divider + dead zones
    # Dead zone includes the divider line so total gap = AGENDA_BAR_DEAD_ZONE
    divider_height = 2
    dead_zone_padding = max(0, dead_zone - divider_height)
    dead_top = ft.Container(width=bar_width, height=dead_zone_padding // 2)
    divider_line = ft.Container(width=bar_width, height=divider_height, bgcolor=theme.AGENDA_GOLD)
    dead_bottom = ft.Container(width=bar_width, height=dead_zone_padding - dead_zone_padding // 2)

    # Runner half (bottom): score near center, fill near center, empty at bottom
    runner_children = [
        ft.Container(
            content=runner_score_ref,
            alignment=ft.Alignment.CENTER,
            padding=ft.Padding.only(top=3),
        ),
    ]
    if runner_fill > 0:
        runner_children.append(ft.Container(
            expand=runner_fill,
            bgcolor=ft.Colors.with_opacity(0.6, theme.RUNNER_ACCENT),
            border_radius=2,
        ))
    if runner_empty > 0:
        runner_children.append(ft.Container(expand=runner_empty))

    runner_half = ft.GestureDetector(
        content=ft.Container(
            width=bar_width,
            bgcolor=theme.PANEL_BG,
            border_radius=ft.BorderRadius.only(bottom_left=6, bottom_right=6),
            clip_behavior=ft.ClipBehavior.HARD_EDGE,
            expand=True,
            content=ft.Column(runner_children, spacing=0, expand=True),
        ),
        on_tap=on_runner_tap,
        on_long_press_start=on_runner_long_press,
    )

    return ft.Container(
        content=ft.Column(
            [corp_half, dead_top, divider_line, dead_bottom, runner_half],
            spacing=0,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            expand=True,
        ),
        border=ft.Border.all(1, ft.Colors.with_opacity(0.45, theme.AGENDA_GOLD)),
        border_radius=8,
        clip_behavior=ft.ClipBehavior.HARD_EDGE,
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
        padding=8,
        content=ft.Column(
            [
                ft.Row(
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
                    ],
                    spacing=6,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                *controls,
            ],
            spacing=5,
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
