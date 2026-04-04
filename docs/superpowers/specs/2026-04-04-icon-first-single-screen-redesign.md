# Icon-First Single-Screen Redesign

**Date:** 2026-04-04
**Status:** Approved

## Goal

Redesign the Netrunner tracker UI to be more compact and responsive: icons replace text labels, both player panels stay on one screen, agenda score becomes a vertical tug-of-war sidebar, and only the game log uses an accordion.

## Layout Structure

```
__________________________________
|        CORP / RUNNER TURN       |  Turn banner
|_________________________________|
|                             |C:3|
|   CORP PANEL                |███|  Vertical agenda bar
|   ─────────────────────────  |───|  (~40px wide)
|   RUNNER PANEL              |░░░|  Tug-of-war fill
|                             |R:2|
|_________________________________|
|  > Game Log (12 events)        |  Accordion
|_________________________________|
|   [End Turn]      [Reset]       |  Action buttons
|_________________________________|
```

Three horizontal zones stacked vertically:
1. **Turn banner** (top) — unchanged from current design
2. **Main area** — corp panel + runner panel stacked vertically on the left, vertical agenda bar on the right
3. **Bottom area** — collapsible game log, then action buttons

## Vertical Agenda Bar

A ~40px-wide strip running the full height of the panels area, positioned on the right edge.

### Visual design
- **Top half = Corp**: solid fill in `CORP_ACCENT` (#2fb8ff), filling downward from top. Corp score number displayed at top.
- **Bottom half = Runner**: solid fill in `RUNNER_ACCENT` (#ff5020), filling upward from bottom. Runner score number displayed at bottom.
- **Center divider**: horizontal line in `AGENDA_GOLD` (#ffbe00).
- Fill amount proportional to score out of 7 (the win threshold).
- Background: `PANEL_BG` (#0d1119) for unfilled portions.

### Interaction
- **Tap top half**: corp agenda +1 (capped at 7+, triggers winner detection)
- **Long-press top half**: corp agenda -1 (min 0)
- **Tap bottom half**: runner agenda +1 (same behavior)
- **Long-press bottom half**: runner agenda -1 (min 0)
- **Dead zone**: 8px around the center divider — taps in this zone are ignored to prevent mis-taps
- Fill is capped at 100% of each half (score 7 = fully filled). Scores above 7 are tracked in state but the bar stays visually full.

### Winner detection
Unchanged — when either player reaches `AGENDA_WIN_THRESHOLD` (7), the winner banner appears.

## Player Panels

Both panels are always visible, stacked vertically. No scrolling needed to see both. Each panel uses the existing `panel()` component shell (left accent stripe, "YOUR TURN" badge, border) but with more compact contents.

### Stat display modes

Two interaction patterns based on stat complexity:

**Tap/long-press stats** (no stepper buttons):
- Credits, Tags, Bad Pub, Core Damage
- Display: NSG icon (18px) + value (22pt bold) — no text label
- Tap anywhere on the stat to +1, long-press to -1 (uses `ft.GestureDetector` with `on_tap` and `on_long_press_start`)
- Visual feedback on long-press: brief flash/pulse of the stat value to confirm the gesture registered
- Credits retain the debounce delta badge and timer bar — implemented as a `tap_credit_row()` component (distinct from generic `tap_stat()` due to delta badge + timer bar slots)

**Stepper stats** (keep +/- buttons):
- Hand Size, MU, Link
- Display: NSG icon (18px) + value (22pt bold) + small +/- buttons — no text label

### Corp Panel contents

```
CLICKS . draw first          3/3 remaining   [refill]
[token] [token] [token]
---------------------------------------------------------
[credit_icon] 12      [bad_pub_icon] 2
                      [+ Bad Pub] toggle pill
```

- Click tokens section: unchanged (tokens + counter + refill button)
- Credits: tap/long-press, with delta badge
- Bad Pub: tap/long-press, toggled via pill (hidden by default)

### Runner Panel contents

```
CLICKS                       4/4 remaining   [refill]
[token] [token] [token] [token]
---------------------------------------------------------
[credit_icon] 8    [tag_icon] 1  |  [core_icon] 0
---------------------------------------------------------
[hand_icon] 5  [-][+]
               [+ MU] [+ Link] toggle pills
```

- Click tokens section: unchanged
- Credits: tap/long-press, with delta badge
- Tags + Core Damage: compact side-by-side, tap/long-press
- Hand Size: icon + value + steppers
- MU, Link: icon + value + steppers, toggled via pills (hidden by default)

## Game Log

- **Accordion behavior**: collapsed by default, header shows event count, tap to expand/collapse
- Only collapsible element in the entire UI
- Log content unchanged (timestamped entries, newest first, 80-entry max)

## Action Buttons

- Positioned at the very bottom, below the game log
- End Turn (green, `NEON_GREEN`) + Reset (red, `DANGER_RED`)
- Same behavior as current

## What stays the same

- `GameState` model (`state.py`) — no changes to the core model (remove unused `agenda_bar_ratio` property)
- `GameLog` model (`game_log.py`) — no changes needed
- Click tokens (visual and interaction)
- Turn banner (visual and interaction)
- Winner banner (visual and interaction)
- Credit debounce behavior
- Toggle pills for optional stats
- Corp mandatory draw toggle — unchanged behavior, stays in the clicks section header ("CLICKS . draw first")
- Mobile/desktop responsive stacking for panels (though both are always visible)

## What changes

| Area | Current | New |
|------|---------|-----|
| Stat labels | Icon + text label + value | Icon + value only |
| Stat interaction (credits, tags, bad pub, core) | +/- stepper buttons | Tap to +1, long-press to -1 |
| Agenda display | Wide two-column split with pips | Narrow vertical bar with tug-of-war fill |
| Agenda interaction | +/- stepper buttons | Tap/long-press on bar halves |
| Panel visibility | May scroll on mobile | Always both visible |
| Game log | Collapsible | Collapsible (unchanged, but now the ONLY accordion) |
| Action buttons position | Between panels and log | Bottom of screen, below log |

## Files to modify

- `src/components.py` — new `agenda_bar()` component, new `tap_stat()` component, new `tap_credit_row()` component. Remove unused: `stat_row()`, `compact_stat()`, `agenda_pip_row()`, `agenda_pips_split()`, `_pip()`
- `src/tracker.py` — restructure `_build_layout()` for sidebar agenda, rewire stat handlers for tap/long-press, move action buttons below log
- `src/state.py` — remove unused `agenda_bar_ratio` property
- `src/theme.py` — add agenda bar dimension constants (`AGENDA_BAR_WIDTH = 40`, `AGENDA_BAR_DEAD_ZONE = 8`)

## Out of scope

- Save/load game state
- Undo/redo
- Sound effects
- New game mechanics
