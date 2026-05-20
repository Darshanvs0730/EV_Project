# ============================================================
# EV Dashboard — Center Telemetry Panel
# ============================================================
# This builds the CENTER COLUMN of the dashboard with 4 rows:
#   Row 0: Three stat cards — SPEED | BATTERY | TEMPERATURE
#   Row 1: Main range estimate card (huge number + factor badges)
#   Row 2: Regenerative Braking card + Battery Health card (side by side)
#   Row 3: Thermal warning banners (hot/cold, shown only when needed)
# ============================================================

import tkinter as tk
from tkinter import ttk
from core.constants import (
    BG_DEEP, BG_CARD, BG_INPUT,
    ACCENT, GREEN, AMBER, RED, TEXT_PRI, TEXT_SEC, BORDER,
    FONT_TELEMETRY, FONT_UNIT, FONT_STAT_HEAD,
    FONT_RANGE_NUM, FONT_RANGE_KM, FONT_DETAIL,
    FONT_BADGE, FONT_CARD_HEAD, _MONO, _UI,
)
from ui.widgets import health_color, make_styled_progressbar


class TelemetryPanel:
    """
    Center panel — uses grid layout to distribute space across 4 rows.
    
    Row 0 (weight=1): Stat cards — Speed / Battery / Temperature
    Row 1 (weight=2): Main range card — big range number, factor badges
    Row 2 (weight=1): Regen Braking card + Battery Health card
    Row 3 (weight=0): Thermal banners (hidden unless temperature is extreme)
    
    Public methods:
        set_stat(which, value) — called by slider traces in main.py to update stat cards live
        update(inputs, result) — called after Calculate to refresh everything
    """

    def __init__(self, parent: tk.Widget):
        self._parent = parent
        self._calculated_once = False   # Tracks whether Calculate has been pressed yet
        self._build(parent)

    def _build(self, parent: tk.Widget):
        """Creates the root frame and delegates to each row builder."""
        root_frame = tk.Frame(parent, bg=BG_DEEP)
        root_frame.pack(fill=tk.BOTH, expand=True)
        self._root = root_frame

        # Row weights control how vertical space is shared between rows
        root_frame.rowconfigure(0, weight=1)   # Stat cards — compact
        root_frame.rowconfigure(1, weight=2)   # Range card — gets the most space
        root_frame.rowconfigure(2, weight=1)   # Regen + Health — compact
        root_frame.rowconfigure(3, weight=0)   # Thermal banners — fixed height, hidden by default
        root_frame.columnconfigure(0, weight=1)

        self._build_stat_row(root_frame)
        self._build_range_card(root_frame)
        self._build_regen_health_row(root_frame)
        self._build_thermal_banners(root_frame)

    # ─── Row 0: Three stat cards ──────────────────────────────
    def _build_stat_row(self, parent: tk.Frame):
        """
        Creates a row of 3 equally-sized cards showing SPEED, BATTERY, TEMPERATURE.
        Each card has: title label → big number → unit → optional warning label.
        All three cards update LIVE as sliders move (via set_stat() calls from main.py).
        """
        row = tk.Frame(parent, bg=BG_DEEP)
        row.grid(row=0, column=0, sticky="nsew", padx=6, pady=(8, 4))
        # Three equal-width columns for the three cards
        row.columnconfigure(0, weight=1)
        row.columnconfigure(1, weight=1)
        row.columnconfigure(2, weight=1)

        # _stat_card returns (value_label, warning_label) for each card
        self._spd_val,  self._spd_warn  = self._stat_card(row, 0, "SPEED",       "km/h")
        self._batt_val, self._batt_warn = self._stat_card(row, 1, "BATTERY",     "%")
        self._temp_val, self._temp_warn = self._stat_card(row, 2, "TEMPERATURE", "°C")

    def _stat_card(self, parent, col: int, title: str, unit: str):
        """
        Creates one stat card (used 3 times for Speed, Battery, Temperature).
        
        Layout inside the card:
          [SPEED]       ← dim grey title
          [40]          ← big cyan number (FONT_TELEMETRY, 52pt bold)
          [km/h]        ← small grey unit label
          [warning msg] ← amber/red warning text (empty until needed)
        
        Returns:
            (val_label, warn_label) — both tk.Labels the caller stores for later updates
        """
        card = tk.Frame(parent, bg=BG_CARD,
                        highlightthickness=1, highlightbackground=BORDER)
        card.grid(row=0, column=col, sticky="nsew", padx=4, pady=2)
        card.configure(height=160)     # Fixed minimum height so cards don't collapse
        card.pack_propagate(False)     # Prevent card from shrinking to fit children

        # Title (e.g., "SPEED") — small, grey, centered
        tk.Label(card, text=title, font=FONT_STAT_HEAD,
                 fg=TEXT_SEC, bg=BG_CARD).pack(pady=(12, 0))

        # Big number — starts as "—" (dash) until slider sync runs
        # set_stat() replaces this with the actual slider value immediately on startup
        val = tk.Label(card, text="—", font=FONT_TELEMETRY,
                       fg=ACCENT, bg=BG_CARD)
        val.pack()

        # Unit label (e.g., "km/h") — small, grey
        tk.Label(card, text=unit, font=FONT_UNIT,
                 fg=TEXT_SEC, bg=BG_CARD).pack()

        # Warning label — empty until Calculate detects a problem
        # e.g., battery < 20% shows "⚠ CRITICAL — Charge now!" in red
        warn = tk.Label(card, text="", font=FONT_DETAIL,
                        fg=AMBER, bg=BG_CARD)
        warn.pack(pady=(2, 12))

        return val, warn

    # ─── Public: update a single stat card (called by slider traces) ──
    def set_stat(self, which: str, value: int):
        """
        Updates just ONE stat card display — called by slider trace in main.py.
        
        This is the method that makes the top numbers update LIVE as sliders move,
        without needing to press Calculate.
        
        Parameters:
            which — which card to update: 'speed' | 'battery' | 'temp'
            value — the new integer value to display
        """
        if which == "speed":
            self._spd_val.config(text=str(value))
        elif which == "battery":
            self._batt_val.config(text=str(value))
        elif which == "temp":
            self._temp_val.config(text=str(value))

    # ─── Row 1: Main range card ────────────────────────────────
    def _build_range_card(self, parent: tk.Frame):
        """
        Creates the large center card that shows the ESTIMATED RANGE.
        
        Before Calculate is pressed:
          - Shows dim "--" placeholder (so the card isn't blank)
          - Factor badges and breakdown text are hidden
        
        After Calculate is pressed (update() method):
          - Shows the actual range in bright green (e.g., "182.4")
          - Reveals the breakdown text ("Base: 320 km → Effective: 182.4 km")
          - Reveals the factor badges (Speed ×1.00, Temp ×1.00, Mode ×1.15, etc.)
        
        Uses a grid inside the card with spacer rows (weight=1) to vertically center content.
        """
        card = tk.Frame(parent, bg=BG_CARD,
                        highlightthickness=1, highlightbackground=BORDER)
        card.grid(row=1, column=0, sticky="nsew", padx=10, pady=4)

        card.columnconfigure(0, weight=1)
        card.rowconfigure(0, weight=1)   # Top spacer — pushes content to vertical center
        card.rowconfigure(1, weight=0)   # "ESTIMATED RANGE" label
        card.rowconfigure(2, weight=0)   # Big number
        card.rowconfigure(3, weight=0)   # "km" unit
        card.rowconfigure(4, weight=0)   # Breakdown text (hidden until Calculate)
        card.rowconfigure(5, weight=0)   # Factor badges (hidden until Calculate)
        card.rowconfigure(6, weight=1)   # Bottom spacer — keeps content centered

        # "ESTIMATED RANGE" heading above the number
        tk.Label(card, text="ESTIMATED RANGE", font=FONT_STAT_HEAD,
                 fg=TEXT_SEC, bg=BG_CARD).grid(row=1, column=0, pady=(0, 4))

        # Big range number — dim "--" before Calculate, bright green number after
        # fg="#2A2A3A" is a very dark grey — almost invisible, used as a placeholder
        self._range_num = tk.Label(card, text="--", font=FONT_RANGE_NUM,
                                   fg="#2A2A3A", bg=BG_CARD)
        self._range_num.grid(row=2, column=0)

        # "km" label below the number
        tk.Label(card, text="km", font=FONT_RANGE_KM,
                 fg=TEXT_SEC, bg=BG_CARD).grid(row=3, column=0, pady=(0, 8))

        # Breakdown text — e.g., "Base: 320 km → Effective: 182.4 km (incl. +14.6 km regen)"
        # NOT added to grid yet — only shown after first Calculate
        self._range_sub = tk.Label(card, text="", font=FONT_DETAIL,
                                   fg=TEXT_SEC, bg=BG_CARD)

        # Factor badges container — NOT added to grid yet either
        # After Calculate: shows colored badges like "Speed ×1.00", "Load ×0.95"
        self._badge_frame = tk.Frame(card, bg=BG_CARD)
        self._badge_labels: list[tk.Label] = []   # List of badge widgets for cleanup on next update

    def _redraw_badges(self, result: dict):
        """
        Destroys old factor badges and draws fresh ones from the latest result.
        
        Each badge shows one factor name and its multiplier value.
        Color coding:
          GREEN = factor >= 1.0  (beneficial — e.g., Eco mode = ×1.15)
          AMBER = factor >= 0.90 (small penalty)
          RED   = factor < 0.90  (significant penalty)
        
        Badges are built as: outer border Frame → inner Label with text
        This gives the "pill" appearance with a thin colored border.
        """
        # Remove all existing badges before drawing new ones
        for w in self._badge_labels:
            w.destroy()
        self._badge_labels.clear()

        # All seven factors from the engine result
        factors = [
            ("Speed",   result["speed_factor"]),
            ("Temp",    result["temp_factor"]),
            ("Mode",    result["mode_factor"]),
            ("Traffic", result["traffic_factor"]),
            ("Load",    result["load_factor"]),
            ("Road",    result["road_factor"]),
            ("Health",  result["health_factor"]),
        ]
        for name, val in factors:
            # Choose color based on how much this factor penalizes range
            fg = GREEN if val >= 1.0 else (AMBER if val >= 0.90 else RED)

            # Outer frame acts as a colored border (1px border trick)
            outer = tk.Frame(self._badge_frame, bg=BORDER, padx=1, pady=1)
            outer.pack(side=tk.LEFT, padx=3, pady=4)

            lbl = tk.Label(outer, text=f" {name} ×{val:.2f} ",
                           font=FONT_BADGE,
                           bg=BG_INPUT, fg=fg,
                           padx=8, pady=4)
            lbl.pack()
            self._badge_labels.append(outer)

    # ─── Row 2: Regen + Health side by side ───────────────────
    def _build_regen_health_row(self, parent: tk.Frame):
        """
        Creates two cards in a horizontal row:
          Left:  Regenerative Braking card — shows regen gain % and km recovered
          Right: Battery Health card — shows health bar, cycles, remaining life
        
        Both show "Press Calculate to begin" until the button is clicked.
        """
        row = tk.Frame(parent, bg=BG_DEEP)
        row.grid(row=2, column=0, sticky="nsew", padx=6, pady=4)
        row.columnconfigure(0, weight=1)
        row.columnconfigure(1, weight=1)
        row.rowconfigure(0, weight=1)

        # ── Left: Regenerative Braking card ──────────────────
        regen_card = tk.Frame(row, bg=BG_CARD,
                              highlightthickness=1, highlightbackground=BORDER)
        regen_card.grid(row=0, column=0, sticky="nsew", padx=(4, 2), pady=2)

        tk.Label(regen_card, text="⚡  REGENERATIVE BRAKING",
                 font=FONT_CARD_HEAD, fg=ACCENT, bg=BG_CARD, anchor="w",
                 ).pack(fill=tk.X, padx=14, pady=(12, 6))
        tk.Frame(regen_card, height=1, bg=BORDER).pack(fill=tk.X, padx=14)

        regen_inner = tk.Frame(regen_card, bg=BG_CARD)
        regen_inner.pack(fill=tk.X, padx=14, pady=10)

        # Progress bar shows regen gain as a visual bar (0–15% scale)
        # Starts at 0 — fills after Calculate based on traffic/mode
        self._regen_pb = make_styled_progressbar(
            regen_inner, "Regen.Horizontal.TProgressbar",
            maximum=15, value=0, color=ACCENT, thickness=22,
        )
        self._regen_pb.pack(fill=tk.X, pady=(0, 8))

        # Text label showing e.g., "+14.6 km recovered | +8% efficiency"
        self._regen_lbl = tk.Label(regen_inner, text="Press Calculate to begin",
                                   font=FONT_DETAIL, fg=TEXT_SEC,
                                   bg=BG_CARD, anchor="w")
        self._regen_lbl.pack(fill=tk.X)

        # ── Right: Battery Health card ────────────────────────
        health_card = tk.Frame(row, bg=BG_CARD,
                               highlightthickness=1, highlightbackground=BORDER)
        health_card.grid(row=0, column=1, sticky="nsew", padx=(2, 4), pady=2)

        # Header color changes based on health level (green → amber → red)
        self._health_head = tk.Label(health_card, text="🔋  BATTERY HEALTH",
                                     font=FONT_CARD_HEAD, fg=GREEN, bg=BG_CARD, anchor="w")
        self._health_head.pack(fill=tk.X, padx=14, pady=(12, 6))
        tk.Frame(health_card, height=1, bg=BORDER).pack(fill=tk.X, padx=14)

        health_inner = tk.Frame(health_card, bg=BG_CARD)
        health_inner.pack(fill=tk.X, padx=14, pady=10)

        # Container frame for the health progressbar
        # (We swap the bar on each update to change its color)
        self._health_pb_frame = tk.Frame(health_inner, bg=BG_CARD)
        self._health_pb_frame.pack(fill=tk.X, pady=(0, 8))

        # Initial health bar at 0 — shows correct value after Calculate
        self._health_pb = make_styled_progressbar(
            self._health_pb_frame, "Health.Horizontal.TProgressbar",
            maximum=100, value=0, color=GREEN, thickness=22,
        )
        self._health_pb.pack(fill=tk.X)

        # Text label: "Health: 90% | Cycles: 100 | Life remaining: 90%"
        self._health_lbl = tk.Label(health_inner,
                                    text="Press Calculate to begin",
                                    font=FONT_DETAIL, fg=TEXT_SEC,
                                    bg=BG_CARD, anchor="w")
        self._health_lbl.pack(fill=tk.X)

        # Warning label shown if health < 75% or cycles > 700
        self._health_warn = tk.Label(health_inner, text="",
                                     font=FONT_DETAIL, fg=AMBER,
                                     bg=BG_CARD, anchor="w")
        self._health_warn.pack(fill=tk.X)

    # ─── Row 3: Thermal warning banners ───────────────────────
    def _build_thermal_banners(self, parent: tk.Frame):
        """
        Creates two banner widgets that appear ONLY when temperature is extreme.
        
        Hot banner  (> 38°C): Dark red background, "THERMAL THROTTLING RISK" warning
        Cold banner (< 10°C): Dark blue background, "COLD BATTERY WARNING"
        
        Banners are initially hidden (not added to grid).
        _show_thermal() / _hide_thermal() toggle them based on temperature input.
        """
        # Hot weather warning banner
        self._hot_banner = tk.Frame(parent, bg="#3A1010")   # Dark red background
        tk.Label(
            self._hot_banner,
            text="⚠️   THERMAL THROTTLING RISK — Battery efficiency severely reduced",
            font=(_UI, 13, "bold"), fg=RED, bg="#3A1010", pady=10,
        ).pack()

        # Cold weather warning banner
        self._cold_banner = tk.Frame(parent, bg="#1A3A6B")   # Dark blue background
        tk.Label(
            self._cold_banner,
            text="❄️   COLD BATTERY WARNING — Reduced range due to low temperature",
            font=(_UI, 13, "bold"), fg="#88BBFF", bg="#1A3A6B", pady=10,
        ).pack()

        # Track visibility state to avoid redundant grid calls
        self._hot_visible  = False
        self._cold_visible = False

    def _show_thermal(self, which: str):
        """Shows the hot or cold banner by adding it to the grid (if not already visible)."""
        if which == "hot" and not self._hot_visible:
            self._hot_banner.grid(row=3, column=0, sticky="ew", padx=10, pady=(0, 6))
            self._hot_visible = True
        elif which == "cold" and not self._cold_visible:
            self._cold_banner.grid(row=3, column=0, sticky="ew", padx=10, pady=(0, 6))
            self._cold_visible = True

    def _hide_thermal(self, which: str):
        """Hides the hot or cold banner by removing it from the grid (if currently visible)."""
        if which == "hot" and self._hot_visible:
            self._hot_banner.grid_remove()   # Removes from layout but keeps widget in memory
            self._hot_visible = False
        elif which == "cold" and self._cold_visible:
            self._cold_banner.grid_remove()
            self._cold_visible = False

    # ─── Public: full update after Calculate ──────────────────
    def update(self, inputs: dict, result: dict):
        """
        Full refresh of all telemetry displays — called after the engine runs.
        
        Updates in order:
          1. Stat cards (speed/battery/temp values + any warnings)
          2. Thermal banners (show/hide based on temperature)
          3. Range card (bright green number + breakdown + badges)
          4. Regen card (progress bar + km recovered text)
          5. Battery health card (colored bar + health/cycle info)
        """
        self._calculated_once = True

        # ── 1. Update the three stat cards ────────────────────
        # Show the exact values from the inputs dict (formatted as integers)
        self._spd_val.config(text=f"{inputs['speed']:.0f}",       fg=ACCENT)
        self._batt_val.config(text=f"{inputs['battery']:.0f}",    fg=ACCENT)
        self._temp_val.config(text=f"{inputs['temperature']:.0f}", fg=ACCENT)

        # Battery warning messages based on charge level
        batt = inputs["battery"]
        if batt < 20:
            self._batt_warn.config(text="⚠ CRITICAL — Charge now!", fg=RED)
        elif batt < 40:
            self._batt_warn.config(text="Low battery", fg=AMBER)
        else:
            self._batt_warn.config(text="", fg=AMBER)   # Clear warning for healthy battery

        # Temperature warnings
        temp = inputs["temperature"]
        if temp > 38:
            self._temp_warn.config(text="🌡️ Heat warning", fg=RED)
        elif temp < 10:
            self._temp_warn.config(text="❄️ Too cold", fg="#5599FF")
        else:
            self._temp_warn.config(text="", fg=AMBER)

        # ── 2. Thermal banners ────────────────────────────────
        if temp > 38:
            self._show_thermal("hot")
        else:
            self._hide_thermal("hot")
        if temp < 10:
            self._show_thermal("cold")
        else:
            self._hide_thermal("cold")

        # ── 3. Range card ─────────────────────────────────────
        eff = result["effective_range"]
        self._range_num.config(text=f"{eff:.1f}", fg=GREEN)   # e.g., "182.4" in bright green

        # Build the breakdown subtitle text
        base_r  = result["base_range"]
        regen_b = result["regen_range_bonus"]
        sub = f"Base: {base_r} km  →  Effective: {eff} km"
        if regen_b > 0:
            sub += f"  (incl. +{regen_b} km regen)"
        self._range_sub.config(text=sub)

        # Reveal the hidden elements (only hidden before first Calculate)
        self._range_sub.grid(row=4, column=0, pady=(0, 4))
        self._badge_frame.grid(row=5, column=0, pady=(0, 8))
        self._redraw_badges(result)   # Draw fresh factor badges

        # ── 4. Regen card ─────────────────────────────────────
        regen_pct   = result["regen_gain_pct"]
        regen_bonus = result["regen_range_bonus"]
        self._regen_pb.config(value=regen_pct)   # Update progress bar fill

        if regen_pct > 0:
            # Regen applies (City or Delivery traffic)
            self._regen_lbl.config(
                text=f"+{regen_bonus} km recovered  |  +{regen_pct}% efficiency",
                fg=GREEN,
            )
        else:
            # No regen on Highway/Rural — show informational message
            self._regen_lbl.config(
                text="— Not applicable on this route (Highway / Rural)",
                fg=TEXT_SEC,
            )

        # ── 5. Battery health card ────────────────────────────
        health = inputs["battery_health"]
        cycles = inputs["charge_cycles"]
        hc = health_color(health)   # GREEN / AMBER / RED based on health %

        self._health_head.config(fg=hc)   # Update card title color to match health

        # Destroy old progressbar and create a new one with the correct color and value
        # (ttk progressbars can't change color after creation — must recreate)
        for w in self._health_pb_frame.winfo_children():
            w.destroy()
        pb = make_styled_progressbar(
            self._health_pb_frame, "Health.Horizontal.TProgressbar",
            maximum=100, value=health, color=hc, thickness=22,
        )
        pb.pack(fill=tk.X)
        self._health_pb = pb

        # Calculate estimated battery life remaining (degrades 0.1% per cycle)
        life = max(0, 100 - cycles * 0.1)
        self._health_lbl.config(
            text=f"Health: {health:.0f}%  |  Cycles: {cycles}  |  Life remaining: {life:.0f}%",
            fg=hc,
        )

        # Show warning if battery health is low or heavily cycled
        if health < 75 or cycles > 700:
            parts = []
            if health < 75:
                parts.append(f"⚠ Low health ({health:.0f}%)")
            if cycles > 700:
                parts.append(f"⚠ High cycles ({cycles}) — battery ageing")
            self._health_warn.config(text="  |  ".join(parts), fg=AMBER)
        else:
            self._health_warn.config(text="")   # Clear warning for healthy battery
