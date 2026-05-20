# ============================================================
# EV Dashboard — Widget Helpers (Production Overhaul)
# ============================================================
# This file contains REUSABLE building blocks used across
# the input panel and telemetry panel.
#
# Instead of repeating the same slider-creation code everywhere,
# we define it once here and call make_slider_row() wherever needed.
# Same idea for section headers, progress bars, and dropdown menus.
# ============================================================

import tkinter as tk          # Standard Python GUI library
from tkinter import ttk       # ttk = "themed tkinter" — gives us styled progressbars

# Import our color and font constants from the design file
from core.constants import (
    BG_CARD, BG_INPUT, ACCENT, GREEN, AMBER, RED,
    TEXT_PRI, TEXT_SEC, BORDER,
    FONT_LABEL, FONT_VALUE, FONT_SECTION,
)


def make_section_header(parent: tk.Widget, text: str, color: str = AMBER) -> None:
    """
    Creates a bold section title + a thin horizontal separator line below it.
    
    Used in the left input panel to visually group related inputs.
    Example output: "⚡  RIDING CONDITIONS" with an amber line underneath.
    
    Parameters:
        parent — the tkinter widget (frame) to place this inside
        text   — the header text (e.g., "⚡  RIDING CONDITIONS")
        color  — text color (defaults to AMBER/orange)
    """
    # Create the bold amber section title label
    tk.Label(
        parent, text=text,
        font=FONT_SECTION,   # Bold, 12pt UI font
        fg=color,            # Amber color by default
        bg=BG_CARD,          # Same dark background as the panel
        anchor="w",          # Left-align the text
        pady=8,              # Vertical padding inside the label
    ).pack(fill=tk.X, padx=10)  # Stretch horizontally with 10px left/right margin

    # Create the thin 1px separator line below the header
    tk.Frame(parent, height=1, bg=BORDER).pack(fill=tk.X, padx=10, pady=(0, 6))


def make_slider_row(
    parent: tk.Widget,
    label: str,
    var: tk.DoubleVar,
    from_: float,
    to: float,
    resolution: float = 1,    # Step size of the slider (default: moves in whole numbers)
    unit: str = "",            # Unit to show after the number (e.g., " km/h", "%", "°C")
    bg: str = BG_CARD,         # Background color (matches the panel background)
) -> tk.Label:
    """
    Creates a two-row input widget combining a label, a slider, and a live value badge.
    
    Layout:
      Row A:  [Label text]              ← e.g., "Speed (km/h)"
      Row B:  [━━━━━●━━━━━━━━]  [40 km/h]   ← slider on left, value on right
    
    The value badge updates INSTANTLY as the slider is dragged.
    
    Parameters:
        parent     — parent frame to place this in
        label      — descriptive label shown above the slider
        var        — tkinter DoubleVar that stores the current value (shared with the slider)
        from_      — minimum value of the slider (left end)
        to         — maximum value of the slider (right end)
        resolution — step size (default 1 = whole numbers)
        unit       — unit suffix for the value badge (e.g., " km/h")
        bg         — background color
    
    Returns:
        val_lbl — the Label widget that shows the current value (in case caller needs to update it)
    """
    # ── Row A: Label text above the slider ────────────────────
    tk.Label(
        parent,
        text=label,            # e.g., "Speed (km/h)"
        font=FONT_LABEL,       # Normal 11pt text
        fg=TEXT_PRI,           # Near-white color for readability
        bg=bg,
        anchor="w",            # Left-aligned
    ).pack(fill=tk.X, padx=12, pady=(4, 0))

    # ── Row B: Slider + Value badge ───────────────────────────
    row = tk.Frame(parent, bg=bg)
    row.pack(fill=tk.X, padx=12, pady=(2, 8))

    # Value badge (shown on the RIGHT side of the slider)
    # Shows the current slider value with its unit, e.g., "40 km/h"
    val_lbl = tk.Label(
        row,
        text=f"{var.get():.0f}{unit}",   # e.g., "40 km/h" — initial value from the variable
        font=FONT_VALUE,                  # Bold monospace font for numbers
        fg=ACCENT,                        # Bright cyan color
        bg=BG_INPUT,                      # Slightly lighter background than the panel
        width=9,                          # Fixed width so the badge doesn't resize as value changes
        anchor="center",                  # Center the text in the badge
    )
    val_lbl.pack(side=tk.RIGHT, padx=(6, 0))   # Right side, with a small gap from the slider

    def _update(*_):
        """
        Called every time the slider moves — updates the value badge with the new number.
        The *_ means "accept any extra arguments" (tkinter passes some we don't need).
        """
        v = var.get()   # Read the current slider value from the DoubleVar
        if resolution < 1:
            # If the slider uses decimal steps (e.g., resolution=0.5), show one decimal place
            val_lbl.config(text=f"{v:.1f}{unit}")
        else:
            # For whole-number steps, show no decimal places (cleaner display)
            val_lbl.config(text=f"{v:.0f}{unit}")

    # ── The actual slider widget ──────────────────────────────
    slider = tk.Scale(
        row,
        variable=var,              # Linked to the DoubleVar — auto-syncs slider ↔ variable
        from_=from_, to=to,        # Min and max values
        resolution=resolution,     # Step size per tick
        orient=tk.HORIZONTAL,      # Horizontal slider (left=min, right=max)
        showvalue=False,           # Hide the built-in value display (we use our own badge)
        bg=bg,
        fg=TEXT_SEC,               # Slider tick color
        troughcolor=BG_INPUT,      # Color of the slider track (the groove)
        activebackground=ACCENT,   # Color when hovered
        highlightthickness=0,      # No focus outline
        bd=0,                      # No border
        sliderlength=16,           # Width of the draggable thumb in pixels
        length=280,                # Total length of the slider track in pixels
        command=_update,           # Called every time slider moves → updates badge
    )
    slider.pack(side=tk.LEFT, fill=tk.X, expand=True)   # Left side, expands to fill space

    return val_lbl   # Return the badge label in case the caller needs to reference it


def health_color(value: float) -> str:
    """
    Returns a color based on battery health percentage.
    
    This is used to color-code the battery health bar and heading:
        ≥ 85%  → GREEN  (battery is in great shape)
        ≥ 70%  → AMBER  (battery is ageing, worth watching)
        < 70%  → RED    (battery needs attention or replacement soon)
    
    Parameters:
        value — battery health as a percentage (0–100)
    Returns:
        A hex color string (e.g., "#00FF88" for green)
    """
    if value >= 85:
        return GREEN   # Good — battery is healthy
    if value >= 70:
        return AMBER   # Warning — battery is ageing
    return RED         # Bad — battery health is low, consider replacement


def make_styled_progressbar(
    parent: tk.Widget,
    style_name: str,    # A unique name for this progressbar style (e.g., "Health.Horizontal.TProgressbar")
    maximum: float,     # The value at which the bar is 100% full
    value: float,       # The current fill value (0 to maximum)
    color: str,         # Fill color of the bar
    thickness: int = 22,  # Height of the bar in pixels
    length: int = 400,    # Width of the bar in pixels
) -> ttk.Progressbar:
    """
    Creates a thick, colored horizontal progressbar with a custom style.
    
    Why use ttk.Style?
    → tkinter's regular progressbars don't let you change the fill color easily.
    → ttk.Style allows us to define a named style with our exact colors.
    → By using a unique style_name for each bar, we can have differently-colored bars.
    
    Used for:
      - The Regenerative Braking bar (cyan/ACCENT color)
      - The Battery Health bar (green/amber/red depending on health)
    
    Parameters:
        parent     — parent frame to place the bar in
        style_name — unique style identifier (must end with ".TProgressbar")
        maximum    — the 100% value (e.g., 100 for percentage, 15 for regen %)
        value      — current fill amount
        color      — fill color
        thickness  — bar height in pixels
        length     — bar width in pixels
    
    Returns:
        A configured ttk.Progressbar widget (caller must .pack() or .grid() it)
    """
    style = ttk.Style()            # Get the global style manager
    style.theme_use("default")     # Use the plain default theme (required to fully control colors)

    # Configure our named style with the desired colors and dimensions
    style.configure(
        style_name,
        troughcolor=BG_INPUT,   # Background track color (unfilled portion)
        background=color,       # Fill color (the colored portion)
        borderwidth=0,          # No border
        lightcolor=color,       # Highlight color (set same as fill to remove 3D effect)
        darkcolor=color,        # Shadow color (set same as fill to keep it flat)
        thickness=thickness,    # Bar height in pixels
    )

    # Create the actual progressbar widget using our named style
    pb = ttk.Progressbar(
        parent,
        style=style_name,         # Apply our custom style
        orient=tk.HORIZONTAL,     # Horizontal bar (fills left to right)
        mode="determinate",       # "determinate" = shows exact progress (vs "indeterminate" = animation)
        maximum=maximum,          # What value = 100% full
        value=value,              # Current fill value
        length=length,            # Bar width in pixels
    )
    return pb   # Caller decides where to place it (pack/grid)


def make_option_menu(parent: tk.Widget, var: tk.StringVar, *options) -> tk.OptionMenu:
    """
    Creates a dark-themed dropdown menu (OptionMenu) styled to match the dashboard.
    
    tkinter's default OptionMenu looks very plain/grey — this function applies
    the dark background, cyan highlight, and matching fonts from our design system.
    
    Parameters:
        parent  — parent frame to place the dropdown in
        var     — tkinter StringVar that stores the selected option (shared with the menu)
        *options — any number of string options (e.g., "City", "Highway", "Delivery", "Rural")
    
    Returns:
        A styled tk.OptionMenu widget (caller must .pack() or .grid() it)
    
    Usage example:
        self.traffic_var = tk.StringVar(value="City")
        opt = make_option_menu(row, self.traffic_var, "City", "Highway", "Delivery", "Rural")
        opt.pack(side=tk.LEFT)
    """
    # Create the OptionMenu with all provided options
    # tk.OptionMenu(parent, variable, option1, option2, ...) — *options unpacks the tuple
    opt = tk.OptionMenu(parent, var, *options)

    # Style the main button part of the dropdown
    opt.config(
        bg=BG_INPUT,              # Dark background when closed
        fg=TEXT_PRI,              # Near-white text color
        activebackground=ACCENT,  # Cyan highlight when hovering/clicking
        activeforeground=BG_CARD, # Dark text on cyan background (high contrast)
        font=FONT_LABEL,          # 11pt sans-serif font
        width=14,                 # Fixed width so all dropdowns are the same size
        relief="flat",            # No 3D border effect
        highlightthickness=1,     # Thin 1px border
        highlightbackground=BORDER,  # Border color
        bd=0,                     # No extra border
    )

    # Style the dropdown list that appears when you click the menu
    opt["menu"].config(
        bg=BG_INPUT,              # Dark background for each option row
        fg=TEXT_PRI,              # Near-white text
        activebackground=ACCENT,  # Cyan highlight when hovering an option
        activeforeground=BG_CARD, # Dark text on highlighted option
        font=FONT_LABEL,          # Same font as the button
    )

    return opt
