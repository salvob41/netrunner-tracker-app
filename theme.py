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

# ── Text ─────────────────────────────────────────────────────────────────────
TEXT_PRIMARY   = "#ccdae8"
TEXT_SECONDARY = "#48606e"

# ── Asset paths (relative to assets/ directory) ──────────────────────────────
# Reusing the NSG official game symbols rather than hand-drawing icons
# means players immediately recognise them from their physical cards.
ASSET_CLICK       = "/click.svg"
ASSET_CLICK_SPENT = "/click_spent.svg"
ASSET_CREDIT      = "/credit.svg"
ASSET_TAG         = "/tag.svg"
ASSET_CORE_DAMAGE = "/core_damage.svg"
ASSET_BAD_PUB     = "/bad_pub.svg"
ASSET_AGENDA      = "/agenda.svg"

# ── Game symbols (unicode fallbacks / text labels) ────────────────────────────
SYM_TURN      = "↺"
SYM_DRAW      = "⊞"
SYM_DRAW_DONE = "☑"
SYM_AGENDA    = "★"
SYM_HAND      = "⎇"
SYM_CLICK   = "◆"   # click spent
SYM_CREDIT  = "¢"   # credit change
SYM_TAG     = "⊕"   # tag added/removed
SYM_BRAIN   = "⊗"   # brain damage
SYM_NET     = "⚡"   # net damage
SYM_BAD_PUB = "☢"   # bad publicity
