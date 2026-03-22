# Netrunner Tracker UX Overhaul — Design Spec

**Date**: 2026-03-21
**Status**: Approved

## Problem

The tracker works but three interactions feel rough:
1. No game log — players can't review what happened
2. Credits change too noisily (each +1 tap is a discrete event)
3. Click tokens lack clarity — no count, no feedback on whose turn, no correction affordance

## Decisions

| Decision | Choice | Alternatives considered |
|---|---|---|
| Log placement | Collapsible bottom panel | Right sidebar strip; slide-up drawer |
| Credit feedback | Delta badge + draining timer bar | Silent batching; hold-to-change buttons |
| Click interaction | Tap individual tokens (improved) | Big "SPEND CLICK" button; whole-area tap zone |
| Log verbosity | Standard + all stat changes | Minimal (turns/agendas only); Verbose (every toggle) |

## 1. Game Log

### Data model (`game_log.py` — new file)

```
LogEntry (frozen dataclass):
  round: int
  player: "corp" | "runner" | "game"
  symbol: str (unicode glyph)
  message: str

GameLog:
  entries: list[LogEntry]  — newest first, ring buffer capped at 80
  record(round, player, symbol, message) → insert at index 0
  clear() → empty the list
```

Separated from GameState because the log is presentational — it doesn't affect game rules.

### What gets logged

| Event | Symbol | Example message |
|---|---|---|
| Click spent | ◆ | `Click spent (2/3)` |
| Credits changed (debounced) | ¢ | `+3 credits → 8¢` |
| Tags changed | ⊕ | `+1 tag → 2` |
| Brain damage changed | ⊗ | `+1 brain → 2 (hand=3)` |
| Net damage changed | ⚡ | `+2 net damage → 4` |
| Bad pub changed | ☢ | `+1 bad pub → 3` |
| Agenda scored/removed | ★ | `+1 agenda → 4 pts` or `−1 agenda → 3 pts` |
| Turn ended (Corp→Runner) | → | `Corp turn ended · Runner begins` |
| Round advanced (Runner→Corp) | ↺ | `Round 2 complete · Round 3 begins` |
| Game won | ★ | `Corporation wins!` |
| Game reset | ↺ | `Game reset` |

**Not logged** (corrections, not game events): click restored, mandatory draw toggled, turn counter manually adjusted.

### UI layout

- Position: below the action buttons row
- Header (always visible): `◎ GAME LOG  ● N events  ▼/▲`
- Body (collapsible): `ft.ListView` with fixed height ~160px, scrollable
- Each entry row: `[R2·CORP]  ◆ Click spent (2/3)` — player label is faction-colored
- Starts expanded; tap header to collapse/expand
- `_log_expanded: bool` state on tracker
- **Scroll strategy**: newest entries appear at the top (insert at index 0). No auto-scroll needed — the most recent event is always visible without scrolling. This is intentional: top-insertion avoids the need for scroll-to-bottom behavior.
- **Ring buffer eviction**: when the 81st entry arrives, the oldest entry silently vanishes from the bottom of the ListView. The header count `● N events` reflects the current buffer size (capped at 80), not total-ever.

### Entry row layout (`log_entry_row` component)

```
[round·player label]   [symbol]   [message text]
  ↑ 60px, faction color   ↑ 18px     ↑ expand, TEXT_PRIMARY
```

**`log_entry_row(entry: LogEntry)` → `ft.Container`:**
- Parameters: one `LogEntry`
- Player label color: `CORP_ACCENT` for "corp", `RUNNER_ACCENT` for "runner", `AGENDA_GOLD` for "game"
- Player label format: `f"R{entry.round}·{entry.player.upper()}"`, size 9, opacity 0.6
- Symbol: size 12, same faction color
- Message: size 10, `TEXT_PRIMARY`, expand to fill remaining width
- Container: padding horizontal 10px, vertical 4px, bottom border 1px at 10% opacity

### Round field semantics

Log entries are written **after** the state mutation. So when `end_turn()` is called:
- Corp→Runner transition: `state.round` has NOT incremented yet, log uses current round
- Runner→Corp transition: `state.end_turn()` increments `state.round`, log uses the **new** round value

The implementer must call `state.end_turn()` first, then write the log entry using `state.round`.

## 2. Credit Debounce

### Behavior

1. User taps +/− on credits
2. `GameState.adjust()` fires immediately → value updates on screen
3. A pending delta accumulates: `_pending_credit[player] += delta`
4. A `threading.Timer(0.45)` is started (or restarted if already running)
5. While timer is running:
   - A delta badge appears next to the credit value: `+3` (green) or `−2` (red)
   - A thin timer bar (2px, green) shows at full width, static (not animated — Flet ProgressBar lacks smooth CSS-style drain)
6. When timer fires:
   - If `_pending_credit[player] == 0` (taps netted to zero): **suppress log entry**, just hide badge + bar
   - Otherwise: log entry written with the batched delta
   - Delta badge + timer bar disappear (`visible=False`)
   - `_pending_credit[player]` resets to 0

### Widget refs needed

Per player:
- `_corp_credits_delta` / `_runner_credits_delta`: `ft.Text` — the "+N" badge, `visible=False` when idle
- `_corp_credits_timer_bar` / `_runner_credits_timer_bar`: `ft.Container` — 2px-tall green bar, `visible=False` when idle (simple colored Container, not ProgressBar, to avoid animation complexity)

### `credit_row` component

**`credit_row(color, value_ref, delta_ref, timer_bar_ref, on_decrement, on_increment)` → `ft.Container`:**

Layout:
```
[¢ icon 22px]  [Credits label]  [value_ref  delta_ref]  [timer_bar below]  [−] [+]
```
- `value_ref`: the main credit number (size 26, bold, faction color)
- `delta_ref`: the pending badge (size 13, bold, green/red, initially hidden)
- `timer_bar_ref`: positioned below the value+delta, full row width, 2px tall
- +/− buttons: standard steppers (32x32)

### Thread safety

`threading.Timer` callback modifies `_pending_credit` (a plain dict with int values), updates widget visibility, and calls `page.update()`. CPython's GIL makes simple int reads/writes atomic, and Flet's `page.update()` is documented as thread-safe. No explicit lock is needed for this use case. If the app ever moves to free-threaded Python, a `threading.Lock` should be added.

## 3. Click Token UX

### Token sizing

- **48×48px** container (intentional increase from current 44px for better touch targets)
- Inner NSG icon stays at **26×26px** within the container
- Active player: full opacity, tappable
- Inactive player: same size, **opacity 0.35**, non-interactive
- Keeps using NSG `click.svg` / `click_spent.svg` assets with SRC_IN tinting

### Interaction

- Tap filled token → `state.spend_click(player)` → log "Click spent (N/M)"
- Tap spent token → `state.restore_click(player)` → **no log** (correction)
- Refill button → resets clicks to max → **no log** (correction)

### Count display

Below the tokens row:
```
◆◆◇  2 / 3 remaining     [↺ refill]
```
- Left: `ft.Text` with `"{current} / {max} remaining"`, secondary color
- Right: small refill `ft.Container` button, muted, only used for corrections

### Refill button

Each player's panel has its own refill button. It resets **that player's** clicks to their maximum (3 for Corp, 4 for Runner). The inactive player's refill button is **hidden** (`visible=False`) since corrections on the inactive player's clicks are rare — if needed, switching turns first is cleaner.

### Inactive player dimming

The entire clicks section (label + tokens + count + refill) gets `opacity=0.35` when the player is not active. The refill button is hidden.

### Changes to `components.py`

- `click_token(filled, color, on_tap=None)`: when `on_tap` is `None`, return plain `ft.Container` (no `GestureDetector` wrapper)
- `click_tokens_row(current, max, color, on_token_tap=None)`: when `on_token_tap` is `None`, pass `on_tap=None` to each `click_token` (skipping the `on_token_tap(i, filled)` factory call entirely). Guard: `on_tap = on_token_tap(i, i < current) if on_token_tap else None`
- Remove +/− stepper buttons from click sections (tokens + refill handle everything)
- Add `refill_button(color, on_click)` → small `ft.Container` with `↺ refill` text

## 4. Stat Change Logging (non-credit stats)

All other stats (tags, brain, net, bad pub, agendas) use **immediate** logging — no debounce. These change infrequently enough that individual entries are meaningful. Both increments and decrements are logged (removing a tag is as meaningful as adding one).

### New handler factory

`_stat_adjuster(attr, delta, min_val, max_val, symbol, label)` → handler that:
1. Calls `state.adjust(attr, delta, min_val, max_val)`
2. Determines player from `attr` prefix: `"corp"` if `attr.startswith("corp_")` else `"runner"`
3. Writes a log entry immediately with the new value from `getattr(state, attr)`
4. Calls `refresh()` + `_refresh_log()`

Replaces `_adjuster()` for all stat rows **including agenda controls** (both +/− on agendas get logged). Credits use `_credit_adjuster()` instead.

## 5. File changes summary

| File | Change |
|---|---|
| `game_log.py` | **New** — `LogEntry` (frozen dataclass), `GameLog` (ring buffer) |
| `theme.py` | Add `SYM_CLICK`, `SYM_CREDIT`, `SYM_TAG`, `SYM_BRAIN`, `SYM_NET`, `SYM_BAD_PUB` unicode constants |
| `state.py` | No changes |
| `components.py` | Update `click_token` (optional `on_tap`), update `click_tokens_row` (null guard on factory), add `refill_button`, add `log_entry_row`, add `credit_row` (with delta + timer bar ref slots) |
| `tracker.py` | Add `GameLog`, debounce timers/dicts, log panel + toggle, `_stat_adjuster`, `_credit_adjuster`, `_refresh_log`, improved click sections with count + refill |
| `main.py` | No changes |

## 6. Non-goals

- Undo/redo system (out of scope)
- Log persistence across sessions (out of scope)
- Animated timer bar drain (Flet ProgressBar lacks smooth CSS drain; static indicator is sufficient)
- Log export/share functionality
