# Icon-First Single-Screen Redesign Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Redesign the tracker UI to be icon-only, single-screen with a vertical agenda tug-of-war bar and tap/long-press stat interactions.

**Architecture:** Four files change: `theme.py` gets new constants, `state.py` loses dead code, `components.py` gets new tap-stat and agenda-bar widgets (old pip/stat-row widgets removed), `tracker.py` gets restructured layout with sidebar agenda and tap/long-press handlers.

**Tech Stack:** Python 3, Flet (Flutter for Python), `ft.GestureDetector` for tap/long-press

**Spec:** `docs/superpowers/specs/2026-04-04-icon-first-single-screen-redesign.md`

---

## File Structure

| File | Action | Responsibility |
|------|--------|----------------|
| `src/theme.py` | Modify | Add `AGENDA_BAR_WIDTH`, `AGENDA_BAR_DEAD_ZONE` constants |
| `src/state.py` | Modify | Remove unused `agenda_bar_ratio` property |
| `src/components.py` | Modify | Add `tap_stat()`, `tap_credit_row()`, `agenda_bar()`. Remove `stat_row()`, `compact_stat()`, `hand_row()` text labels → `stepper_stat()`. Remove `_pip()`, `agenda_pips_split()`, `agenda_pip_row()` |
| `src/tracker.py` | Modify | Restructure layout: sidebar agenda, tap/long-press handlers, move actions below log |

---

## Chunk 1: Theme and State Cleanup

### Task 1: Add agenda bar constants to theme.py

**Files:**
- Modify: `src/theme.py:30` (after shared accent colors section)

- [ ] **Step 1: Add constants**

Add after line 37 (after `LINK_COLOR`):

```python
# ── Agenda bar dimensions ────────────────────────────────────────────────────
AGENDA_BAR_WIDTH     = 40   # px — width of the vertical sidebar
AGENDA_BAR_DEAD_ZONE = 8    # px — no-tap zone around the center divider
```

- [ ] **Step 2: Commit**

```bash
git add src/theme.py
git commit -m "feat: add agenda bar dimension constants to theme"
```

### Task 2: Remove unused agenda_bar_ratio from state.py

**Files:**
- Modify: `src/state.py:70-77`

- [ ] **Step 1: Delete the `agenda_bar_ratio` property**

Remove lines 70-77 (the `@property` block for `agenda_bar_ratio`).

- [ ] **Step 2: Verify no other code references it**

```bash
cd /Users/totolasso/repos/personal/netrunner-tracker-app && grep -r "agenda_bar_ratio" src/
```

Expected: no output (the only consumer was the old agenda section in tracker.py, which already uses `agenda_pips_split` instead).

- [ ] **Step 3: Commit**

```bash
git add src/state.py
git commit -m "refactor: remove unused agenda_bar_ratio property"
```

---

## Chunk 2: Component Changes

### Task 3: Remove old components (BEFORE adding new ones to keep line refs stable)

**Files:**
- Modify: `src/components.py`

- [ ] **Step 1: Delete `stat_row()` function** (lines 127-159)

- [ ] **Step 2: Delete `compact_stat()` function** (lines 164-196)

- [ ] **Step 3: Delete `hand_row()` function** (lines 201-231)

- [ ] **Step 4: Delete `_pip()`, `agenda_pips_split()`, `agenda_pip_row()` functions** (lines 236-301)

- [ ] **Step 5: Delete `credit_row()` function** (lines 420-461)

- [ ] **Step 6: Commit**

```bash
git add src/components.py
git commit -m "refactor: remove old stat_row, compact_stat, hand_row, pip, credit_row components"
```

### Task 4: Add `tap_stat()` component

**Files:**
- Modify: `src/components.py`

- [ ] **Step 1: Add `tap_stat()` function**

Add after the `stepper()` function (after line 122). This replaces `stat_row()` and `compact_stat()` for stats that use tap/long-press instead of stepper buttons:

```python
# ── Tap stat (icon + value, tap to +1, long-press to -1) ────────────────────

def tap_stat(
    asset_path: str,
    asset_color: str,
    value_ref: ft.Text,
    on_tap,
    on_long_press,
    icon_size: int = 18,
) -> ft.Container:
    """
    Compact stat: NSG icon + value only. No text label, no stepper buttons.
    Tap anywhere to increment, long-press to decrement.
    Long-press triggers a brief opacity flash as visual feedback.
    """
    content = ft.Row(
        [
            nsg_icon(asset_path, icon_size, asset_color),
            value_ref,
        ],
        spacing=6,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
    )
    container = ft.Container(
        content=content,
        padding=ft.Padding.symmetric(horizontal=8, vertical=6),
        border_radius=6,
        ink=True,
        animate_opacity=ft.Animation(150, ft.AnimationCurve.EASE_OUT),
    )

    def _on_long_press(e):
        # Flash feedback: dim then restore
        container.opacity = 0.4
        container.update()
        if on_long_press:
            on_long_press(e)
        container.opacity = 1.0
        container.update()

    return ft.GestureDetector(
        content=container,
        on_tap=on_tap,
        on_long_press_start=_on_long_press,
    )
```

- [ ] **Step 2: Commit**

```bash
git add src/components.py
git commit -m "feat: add tap_stat component for tap/long-press interaction"
```

### Task 5: Add `tap_credit_row()` component

**Files:**
- Modify: `src/components.py`

- [ ] **Step 1: Add `tap_credit_row()` function**

Add after `tap_stat()`. This replaces the current `credit_row()` — same debounce delta badge and timer bar, but tap/long-press instead of steppers:

```python
def tap_credit_row(
    color: str,
    value_ref: ft.Text,
    delta_ref: ft.Text,
    timer_bar_ref: ft.Container,
    on_tap,
    on_long_press,
) -> ft.Container:
    """
    Credits stat with tap/long-press and debounce feedback.
    Shows icon + value + pending delta badge + timer bar.
    No text label, no stepper buttons.
    """
    content = ft.Column(
        [
            ft.Row(
                [
                    nsg_icon(theme.ASSET_CREDIT, 22, color),
                    ft.Row(
                        [value_ref, delta_ref],
                        spacing=6,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                ],
                spacing=6,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            timer_bar_ref,
        ],
        spacing=2,
    )
    container = ft.Container(
        content=content,
        padding=ft.Padding.symmetric(horizontal=8, vertical=5),
        border_radius=6,
        ink=True,
    )
    return ft.GestureDetector(
        content=container,
        on_tap=on_tap,
        on_long_press_start=on_long_press,
    )
```

- [ ] **Step 2: Commit**

```bash
git add src/components.py
git commit -m "feat: add tap_credit_row component with debounce support"
```

### Task 6: Add `stepper_stat()` component

**Files:**
- Modify: `src/components.py`

- [ ] **Step 1: Add `stepper_stat()` function**

Add after `tap_credit_row()`. This is the icon-only version of `hand_row()` — keeps stepper buttons but drops the text label:

```python
def stepper_stat(
    asset_path: str,
    asset_color: str,
    value_ref: ft.Text,
    color: str,
    on_decrement,
    on_increment,
    icon_size: int = 20,
) -> ft.Container:
    """
    Stat with icon + value + stepper buttons. No text label.
    Used for Hand Size, MU, Link — stats where tap/long-press
    would be confusing.
    """
    return ft.Container(
        content=ft.Row(
            [
                nsg_icon(asset_path, icon_size, asset_color),
                value_ref,
                ft.Container(expand=True),
                ft.Row(
                    [
                        stepper("−", on_decrement, color),
                        stepper("+", on_increment, color),
                    ],
                    spacing=4,
                ),
            ],
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        padding=ft.Padding.symmetric(horizontal=8, vertical=5),
    )
```

- [ ] **Step 2: Commit**

```bash
git add src/components.py
git commit -m "feat: add stepper_stat component (icon-only, no text label)"
```

### Task 7: Add `agenda_bar()` component

**Files:**
- Modify: `src/components.py`

- [ ] **Step 1: Add `agenda_bar()` function**

Add after `stepper_stat()`. This is the vertical tug-of-war sidebar:

```python
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
    bar_height: int = 300,
) -> ft.Container:
    """
    Vertical tug-of-war agenda bar. Top half = Corp (fills downward),
    bottom half = Runner (fills upward). Tap to +1, long-press to -1.
    8px dead zone around the center divider.
    """
    half_height = bar_height // 2
    dead_zone = theme.AGENDA_BAR_DEAD_ZONE
    bar_width = theme.AGENDA_BAR_WIDTH

    # Corp fill: score/7 of the top half, filling from top down
    corp_fill_pct = min(corp_score / 7, 1.0) if corp_score > 0 else 0
    corp_fill_h = int(half_height * corp_fill_pct)

    # Runner fill: score/7 of the bottom half, filling from bottom up
    runner_fill_pct = min(runner_score / 7, 1.0) if runner_score > 0 else 0
    runner_fill_h = int(half_height * runner_fill_pct)

    # Corp half (top): fill grows downward from the top
    corp_half = ft.GestureDetector(
        content=ft.Container(
            width=bar_width,
            height=half_height - dead_zone // 2,
            bgcolor=theme.PANEL_BG,
            border_radius=ft.BorderRadius.only(top_left=6, top_right=6),
            clip_behavior=ft.ClipBehavior.HARD_EDGE,
            content=ft.Column(
                [
                    # Score number at top
                    ft.Container(
                        content=corp_score_ref,
                        alignment=ft.Alignment.CENTER,
                        padding=ft.Padding.only(top=4),
                    ),
                    # Fill bar grows downward from score number
                    ft.Container(
                        width=bar_width,
                        height=corp_fill_h,
                        bgcolor=ft.Colors.with_opacity(0.6, theme.CORP_ACCENT),
                        border_radius=2,
                    ),
                    ft.Container(expand=True),
                ],
                spacing=0,
                expand=True,
            ),
        ),
        on_tap=on_corp_tap,
        on_long_press_start=on_corp_long_press,
    )

    # Center divider
    divider_line = ft.Container(
        width=bar_width,
        height=2,
        bgcolor=theme.AGENDA_GOLD,
    )

    # Dead zone spacers
    dead_top = ft.Container(width=bar_width, height=dead_zone // 2)
    dead_bottom = ft.Container(width=bar_width, height=dead_zone // 2)

    # Runner half (bottom): fill grows upward from the bottom
    runner_half = ft.GestureDetector(
        content=ft.Container(
            width=bar_width,
            height=half_height - dead_zone // 2,
            bgcolor=theme.PANEL_BG,
            border_radius=ft.BorderRadius.only(bottom_left=6, bottom_right=6),
            clip_behavior=ft.ClipBehavior.HARD_EDGE,
            content=ft.Column(
                [
                    ft.Container(expand=True),
                    # Fill bar grows upward toward the center
                    ft.Container(
                        width=bar_width,
                        height=runner_fill_h,
                        bgcolor=ft.Colors.with_opacity(0.6, theme.RUNNER_ACCENT),
                        border_radius=2,
                    ),
                    # Score number at bottom
                    ft.Container(
                        content=runner_score_ref,
                        alignment=ft.Alignment.CENTER,
                        padding=ft.Padding.only(bottom=4),
                    ),
                ],
                spacing=0,
                expand=True,
            ),
        ),
        on_tap=on_runner_tap,
        on_long_press_start=on_runner_long_press,
    )

    return ft.Container(
        content=ft.Column(
            [corp_half, dead_top, divider_line, dead_bottom, runner_half],
            spacing=0,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        border=ft.Border.all(1, ft.Colors.with_opacity(0.45, theme.AGENDA_GOLD)),
        border_radius=8,
        clip_behavior=ft.ClipBehavior.HARD_EDGE,
    )
```

- [ ] **Step 2: Commit**

```bash
git add src/components.py
git commit -m "feat: add vertical agenda_bar component with tug-of-war fill"
```

---

## Chunk 3: Tracker Rewiring

### Task 8: Add tap/long-press event handlers to tracker

**Files:**
- Modify: `src/tracker.py`

- [ ] **Step 1: Add tap/long-press handler factories**

Add after `_credit_adjuster()` method (after line 557). These wrap the existing `_stat_adjuster` and `_credit_adjuster` to work with `on_tap` (no event arg needed) and `on_long_press_start`:

```python
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
```

- [ ] **Step 2: Commit**

```bash
git add src/tracker.py
git commit -m "feat: add tap/long-press and agenda tap handler factories"
```

### Task 9: Update widget refs for new layout

**Files:**
- Modify: `src/tracker.py` — `_create_widget_refs()` method

- [ ] **Step 1: Remove old agenda pip row refs**

Delete these lines from `_create_widget_refs()` (around lines 157-167):

```python
        self._agenda_pip_row = ft.Row(
            spacing=5,
            alignment=ft.MainAxisAlignment.CENTER,
        )
        # Split pips for compact layout (score above each side)
        self._agenda_pip_row_corp = ft.Row(
            spacing=3, alignment=ft.MainAxisAlignment.CENTER,
        )
        self._agenda_pip_row_runner = ft.Row(
            spacing=3, alignment=ft.MainAxisAlignment.CENTER,
        )
```

- [ ] **Step 2: Update agenda text refs for vertical bar**

Change the agenda text sizes to be smaller (they'll sit inside a 40px-wide bar):

```python
        # ── Agenda ───────────────────────────────────────────────────────────
        self._corp_agenda_text   = ft.Text(
            "0", size=16, weight=ft.FontWeight.BOLD, color=theme.CORP_ACCENT,
            text_align=ft.TextAlign.CENTER,
        )
        self._runner_agenda_text = ft.Text(
            "0", size=16, weight=ft.FontWeight.BOLD, color=theme.RUNNER_ACCENT,
            text_align=ft.TextAlign.CENTER,
        )
```

- [ ] **Step 3: Change panels_container to always be a Column**

Both panels always stack vertically now. Replace the mobile/desktop branching (around lines 174-177):

```python
        # ── Panels (always stacked vertically) ──────────────────────────────
        self._panels_container = ft.Column(spacing=8)
```

- [ ] **Step 4: Commit**

```bash
git add src/tracker.py
git commit -m "refactor: update widget refs for vertical agenda bar and stacked panels"
```

### Task 10: Rewrite `refresh()` for new layout

**Files:**
- Modify: `src/tracker.py` — `refresh()` method

- [ ] **Step 1: Remove old agenda pip refresh logic**

In `refresh()`, remove these lines (around lines 306-315):

```python
        # ── Agenda pips ───────────────────────────────────────────────────────
        self._corp_agenda_text.value   = str(s.corp_agenda)
        self._runner_agenda_text.value = str(s.runner_agenda)
        self._agenda_pip_row.controls  = ui.agenda_pip_row(
            s.corp_agenda, s.runner_agenda,
        ).controls
        # Split pips for compact layout
        corp_pips, runner_pips = ui.agenda_pips_split(s.corp_agenda, s.runner_agenda)
        self._agenda_pip_row_corp.controls = corp_pips
        self._agenda_pip_row_runner.controls = runner_pips
```

Replace with:

```python
        # ── Agenda ────────────────────────────────────────────────────────────
        self._corp_agenda_text.value   = str(s.corp_agenda)
        self._runner_agenda_text.value = str(s.runner_agenda)
```

- [ ] **Step 2: Update panels_container rebuild**

The panels container now includes the agenda bar sidebar. Replace the panels rebuild (around lines 317-322):

```python
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
```

- [ ] **Step 3: Commit**

```bash
git add src/tracker.py
git commit -m "refactor: update refresh() for agenda sidebar layout"
```

### Task 11: Rewrite panel builders for icon-only stats

**Files:**
- Modify: `src/tracker.py` — `_build_corp_panel()` and `_build_runner_panel()`

- [ ] **Step 1: Rewrite `_build_corp_panel()`**

Replace the entire `_build_corp_panel()` method (lines 636-692):

```python
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
```

- [ ] **Step 2: Rewrite `_build_runner_panel()`**

Replace the entire `_build_runner_panel()` method (lines 694-815):

```python
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
```

- [ ] **Step 3: Commit**

```bash
git add src/tracker.py
git commit -m "feat: rewrite panel builders for icon-only tap/long-press stats"
```

### Task 12: Add `_build_agenda_bar()` method and restructure layout

**Files:**
- Modify: `src/tracker.py`

- [ ] **Step 1: Replace `_build_agenda_section()` with `_build_agenda_bar()`**

Delete the entire `_build_agenda_section()` method (lines 819-896) and replace with:

```python
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
```

- [ ] **Step 2: Restructure `_build_layout()`**

Replace `_build_layout()` (lines 900-1021). Key changes: remove title bar (save space), move actions below log, wrap panels + agenda bar in a Row:

```python
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
```

- [ ] **Step 3: Commit**

```bash
git add src/tracker.py
git commit -m "feat: restructure layout with agenda sidebar and actions below log"
```

---

## Chunk 4: Verification

### Task 13: Run the app and verify

- [ ] **Step 1: Run the app**

```bash
cd /Users/totolasso/repos/personal/netrunner-tracker-app && flet run src/main.py
```

- [ ] **Step 2: Verify checklist**

Manual verification:
- Both panels visible on one screen without scrolling
- Agenda bar visible on right side with tug-of-war fill
- Tap on credits/tags/bad pub/core damage increments, long-press decrements
- Hand size/MU/Link still have +/- stepper buttons
- No text labels on stats (icon + value only)
- Click tokens unchanged (tokens + counter + refill)
- Game log accordion works (expand/collapse)
- Action buttons at bottom below log
- Turn banner works
- Winner detection works when agenda hits 7

- [ ] **Step 3: Fix any issues found**

- [ ] **Step 4: Final commit**

```bash
git add -A
git commit -m "feat: icon-first single-screen redesign complete"
```
