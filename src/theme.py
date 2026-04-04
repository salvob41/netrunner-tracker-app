"""
Visual identity for the Netrunner Tracker.

All colors, symbols, and asset paths live here so the rest of the
codebase never hard-codes hex strings, glyphs, or file paths.
Changing the theme means changing ONE file.

Color intent:
  Corp   = cold electric blue  — sterile megacorp authority
  Runner = burning orange-red  — scrappy hacker energy
  Agenda = gold                — both factions fight over it
  Active turn panel gets a stronger glow so the current player is obvious
"""

# ── Backgrounds & surfaces ────────────────────────────────────────────────────
BG_DARK      = "#07090d"
PANEL_BG     = "#0d1119"
PANEL_BORDER = "#1a2535"

# ── Corp faction ─────────────────────────────────────────────────────────────
CORP_ACCENT  = "#2fb8ff"   # electric blue
CORP_DIM     = "#091d30"   # dim fill for corp active/used states
CORP_BANNER  = "#071a2d"   # turn banner background during Corp turn

# ── Runner faction ───────────────────────────────────────────────────────────
RUNNER_ACCENT = "#ff5020"  # molten orange
RUNNER_DIM    = "#2e0e04"  # dim fill for runner active/used states
RUNNER_BANNER = "#2e0e04"  # turn banner background during Runner turn

# ── Shared accent colors ─────────────────────────────────────────────────────
AGENDA_GOLD   = "#ffbe00"  # both factions score agendas
NEON_GREEN    = "#00f0a0"  # positive actions (end turn)
DANGER_RED    = "#ff1e3a"  # destructive actions (reset)
PURPLE_ACCENT = "#b560ff"  # brain damage is psychological
BAD_PUB_COLOR = "#1dbd55"  # green — bad publicity gives the Runner an advantage
MU_COLOR      = "#20c0e0"  # cyan — memory units
LINK_COLOR    = "#40d080"  # teal-green — link strength

# ── Agenda bar dimensions ────────────────────────────────────────────────────
AGENDA_BAR_WIDTH     = 40   # px — width of the vertical sidebar
AGENDA_BAR_DEAD_ZONE = 8    # px — no-tap zone around the center divider

# ── Text ─────────────────────────────────────────────────────────────────────
TEXT_PRIMARY   = "#ccdae8"
TEXT_SECONDARY = "#48606e"

# ── Asset paths (relative to assets/ directory) ──────────────────────────────
# PNG instead of SVG — SVG tinting via SRC_IN doesn't render on Android.
# PNGs with SRC_IN tinting work identically on all platforms.
ASSET_CLICK       = "/click.png"
ASSET_CLICK_SPENT = "/click_spent.png"
ASSET_CREDIT      = "/credit.png"
ASSET_TAG         = "/tag.png"
ASSET_CORE_DAMAGE = "/core_damage.png"
ASSET_BAD_PUB     = "/bad_pub.png"
ASSET_AGENDA      = "/agenda.png"
ASSET_HAND        = "/hand.png"
ASSET_MU          = "/mu.png"
ASSET_LINK        = "/link.png"

# ── Game symbols (used as log keys + fallback display) ────────────────────────
SYM_TURN    = "↺"
SYM_AGENDA  = "⬡"   # agenda point
SYM_CLICK   = "◆"   # click spent
SYM_CREDIT  = "¢"   # credit change
SYM_TAG     = "⊕"   # tag added/removed
SYM_BRAIN   = "⊗"   # core damage
SYM_HAND    = "✋"   # hand size change
SYM_BAD_PUB = "☢"   # bad publicity
SYM_MU      = "⬢"   # memory units
SYM_LINK    = "⟐"   # link strength

# ── Symbol → asset mapping (for log entries to use same icons as UI) ──────
SYM_ASSET_MAP = {
    SYM_AGENDA:  (ASSET_AGENDA,      AGENDA_GOLD),
    SYM_CLICK:   (ASSET_CLICK,       None),       # color set per player
    SYM_CREDIT:  (ASSET_CREDIT,      None),       # color set per player
    SYM_TAG:     (ASSET_TAG,         AGENDA_GOLD),
    SYM_BRAIN:   (ASSET_CORE_DAMAGE, PURPLE_ACCENT),
    SYM_HAND:    (ASSET_HAND,        None),
    SYM_BAD_PUB: (ASSET_BAD_PUB,     BAD_PUB_COLOR),
    SYM_MU:      (ASSET_MU,          MU_COLOR),
    SYM_LINK:    (ASSET_LINK,        LINK_COLOR),
}
