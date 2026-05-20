# ============================================================
# EV Dashboard — Design Constants (Production Overhaul)
# ============================================================
# This file stores ALL visual design values used across the app.
# By keeping them here, changing one value updates the whole app.
# Think of it like a "theme file" for the dashboard.
# ============================================================

import sys  # Used to detect which operating system we're on (Mac / Windows / Linux)

# ----- Color Palette -----
# These are HEX color codes (#RRGGBB) used throughout the dashboard.
# Keeping all colors here means we can change the theme in one place.

BG_DEEP   = "#0A0A0F"   # Darkest background — used for the main window behind all cards
BG_CARD   = "#12121A"   # Card/panel background — slightly lighter dark, used for each box
BG_INPUT  = "#1A1A26"   # Input area background — slider troughs, entry boxes, dropdowns
ACCENT    = "#00F5FF"   # Bright cyan — used for important values, the title, active elements
GREEN     = "#00FF88"   # Bright green — used for "good" values (high battery, reachable, savings)
AMBER     = "#FFB800"   # Amber/orange — used for "warning" values and section headers
RED       = "#FF3B3B"   # Bright red — used for "critical" / danger values
ORANGE    = "#FF7700"   # Orange — used for "high" anxiety level (between amber and red)
PURPLE    = "#A855F7"   # Purple — available for use (reserved, currently unused in main UI)
TEXT_PRI  = "#E8E8F0"   # Primary (main) text color — near-white, for labels and normal text
TEXT_SEC  = "#6B6B8A"   # Secondary (dimmed) text color — for units, sub-labels, hints
BORDER    = "#1E1E30"   # Border/separator color — the thin lines between cards
TEAL      = "#00CCAA"   # Teal — used for CO₂ savings value in the cost card

# ----- Cross-platform font families -----
# Different operating systems have different built-in fonts.
# We check which OS is being used and pick the best available font for that OS.
# This ensures text looks crisp on all platforms.

if sys.platform == "darwin":
    # macOS — uses Apple's built-in fonts
    _MONO = "Menlo"             # Monospaced (fixed-width) font for numbers
    _UI   = "Helvetica Neue"    # Clean sans-serif font for labels and text
elif sys.platform == "win32":
    # Windows — uses Microsoft's built-in fonts
    _MONO = "Consolas"          # Monospaced font for numbers on Windows
    _UI   = "Segoe UI"          # Clean sans-serif for Windows labels
else:
    # Linux / Other — uses open-source fonts
    _MONO = "DejaVu Sans Mono"  # Monospaced for Linux
    _UI   = "Sans"              # Generic sans-serif for Linux

# ----- Production Font Scale -----
# Each font is a tuple: (font_family, size, "style")
# Larger numbers = bigger text. "bold" makes text heavier/thicker.
# Each constant is used in exactly one kind of widget — easy to adjust individually.

FONT_TITLE     = (_MONO, 17, "bold")   # "🛵 EV Telemetry" title at the top-left
FONT_SECTION   = (_UI,   12, "bold")   # Section headers like "RIDING CONDITIONS", "RIDER LOAD"
FONT_LABEL     = (_UI,   11)           # Input labels like "Speed (km/h)", "Battery Level (%)"
FONT_VALUE     = (_MONO, 13, "bold")   # Live value shown beside sliders (e.g., "40 km/h")
FONT_CARD_HEAD = (_UI,   12, "bold")   # Card titles like "REGENERATIVE BRAKING", "BATTERY HEALTH"
FONT_TELEMETRY = (_MONO, 52, "bold")   # The BIG numbers at the top (Speed: 40, Battery: 80, Temp: 25)
FONT_UNIT      = (_UI,   13)           # Small unit labels below big numbers ("km/h", "%", "°C")
FONT_STAT_HEAD = (_UI,   12)           # Tiny labels ABOVE the big numbers ("SPEED", "BATTERY", "TEMPERATURE")
FONT_RANGE_NUM = (_MONO, 72, "bold")   # The HUGE estimated range number in the center card
FONT_RANGE_KM  = (_UI,   16)          # The "km" label under the huge range number
FONT_DETAIL    = (_UI,   11)           # Smaller details like factor breakdowns and sub-labels
FONT_BADGE     = (_MONO, 10, "bold")   # Factor badges (e.g., "Speed ×1.00", "Load ×0.95")
FONT_PANEL_HDR = (_UI,   13, "bold")   # Right panel card headers (e.g., "ECO ASSISTANT")
FONT_PANEL_VAL = (_UI,   12)           # Right panel body text (cost labels, destination text)
FONT_COST_VAL  = (_MONO, 13, "bold")   # ₹ rupee amount values in the cost savings card
FONT_YEARLY    = (_MONO, 18, "bold")   # The large yearly savings number at the bottom of cost card
FONT_TIP       = (_UI,   11)           # Eco tips shown in the Eco Assistant card
FONT_BTN       = (_UI,   14, "bold")   # The "⚡ CALCULATE RANGE" button text
FONT_ANXIETY   = (_MONO, 38, "bold")   # Score number shown inside the anxiety gauge (Matplotlib)
FONT_ANXI_LBL  = (_UI,   13)          # Label like "Low" / "Medium" below the gauge score

# ----- Backwards Compatibility Aliases -----
# These old names are kept so that older parts of the code that still use them don't break.
FONT_MONO_LG = FONT_TELEMETRY   # Old name for the big telemetry font
FONT_MONO_MD = FONT_VALUE        # Old name for the slider value font
FONT_MONO_SM = (_MONO, 10)       # Small monospaced font (not currently used but kept just in case)
FONT_HEAD    = FONT_CARD_HEAD    # Old name for card header font
