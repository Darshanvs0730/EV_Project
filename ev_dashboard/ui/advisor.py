# ============================================================
# EV Dashboard — Right Advisor Panel
# ============================================================
# This builds the RIGHT COLUMN of the dashboard with 4 stacked cards:
#
#   Card 0 (compact):  ECO ASSISTANT       — eco tips (up to 3 bullet points)
#   Card 1 (dominant): RANGE ANXIETY GAUGE — semicircle gauge (Matplotlib)
#   Card 2 (compact):  DESTINATION CHECK   — reachability result
#   Card 3 (medium):   COST SAVINGS vs PETROL — ₹ monthly/yearly comparison
#
# The Cost Savings card updates LIVE as the speed slider moves (no Calculate needed).
# Everything else updates after the Calculate button is pressed.
# ============================================================

import tkinter as tk
import numpy as np                          # For math when drawing the arc gauge
import matplotlib                           # The charting library
matplotlib.use("TkAgg")                     # Tell matplotlib to draw inside a tkinter window
import matplotlib.pyplot as plt             # For creating the figure/axes
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg   # Embed matplotlib in tkinter

from core.constants import (
    BG_CARD, BG_INPUT, BG_DEEP,
    ACCENT, GREEN, AMBER, RED, ORANGE, TEAL,
    TEXT_PRI, TEXT_SEC, BORDER,
    FONT_PANEL_HDR, FONT_PANEL_VAL, FONT_TIP,
    FONT_COST_VAL, FONT_YEARLY, _MONO, _UI,
)


def _arc_color(score: int) -> str:
    """
    Returns the color for the gauge needle/score text based on the anxiety score.
      score < 30  → GREEN  (Low anxiety — all good)
      score < 55  → AMBER  (Medium — stay aware)
      score < 75  → ORANGE (High — take action)
      score >= 75 → RED    (Critical — charge now!)
    """
    if score < 30:  return GREEN
    if score < 55:  return AMBER
    if score < 75:  return ORANGE
    return RED


class AdvisorPanel:
    """
    Right panel — 380px wide, 4 stacked cards.
    
    Initializes with placeholder content (dim gauge, "—" cost values).
    
    Public methods:
        update(result)          — full refresh after Calculate is pressed
        update_cost_live(speed) — quick cost refresh from speed slider (no Calculate needed)
    """

    def __init__(self, parent: tk.Widget):
        self._build(parent)
        self._draw_gauge_placeholder()   # Show dim arc + "Press Calculate" before first run

    def _build(self, parent: tk.Widget):
        """Sets up the 4-row grid and delegates each card to its builder method."""
        root = tk.Frame(parent, bg=BG_DEEP)
        root.pack(fill=tk.BOTH, expand=True)
        self._root = root

        root.columnconfigure(0, weight=1)
        # Row weights control how much vertical space each card gets
        root.rowconfigure(0, weight=1)   # Eco tips — compact
        root.rowconfigure(1, weight=4)   # Gauge — dominant (gets most space)
        root.rowconfigure(2, weight=1)   # Destination — compact
        root.rowconfigure(3, weight=2)   # Cost savings — medium

        self._build_eco_card(root)
        self._build_gauge_card(root)
        self._build_dest_card(root)
        self._build_cost_card(root)

    # ─── Card factory helper ────────────────────────────────────
    def _make_card(self, parent: tk.Widget, row: int,
                   title: str, title_color: str = AMBER) -> tk.Frame:
        """
        Creates a standard card with a title header + separator line.
        Returns the CONTENT frame (inner area below the header) for the caller to populate.
        
        Structure:
          card Frame
            └─ header Frame → title Label
            └─ separator Frame (1px line)
            └─ content Frame (returned to caller)
        """
        card = tk.Frame(parent, bg=BG_CARD,
                        highlightthickness=1, highlightbackground=BORDER)
        card.grid(row=row, column=0, sticky="nsew", padx=10, pady=(6, 0))

        hdr = tk.Frame(card, bg=BG_CARD)
        hdr.pack(fill=tk.X, padx=14, pady=(12, 6))
        tk.Label(hdr, text=title, font=FONT_PANEL_HDR,
                 fg=title_color, bg=BG_CARD, anchor="w").pack(side="left")
        tk.Frame(card, height=1, bg=BORDER).pack(fill=tk.X, padx=14)

        content = tk.Frame(card, bg=BG_CARD)
        content.pack(fill=tk.BOTH, expand=True, padx=14, pady=10)
        return content

    # ─── Card 0: Eco Assistant ─────────────────────────────────
    def _build_eco_card(self, parent: tk.Widget):
        """
        Creates the ECO ASSISTANT card with up to 3 actionable eco tips.
        
        Initial state: "✓ Riding efficiently — no suggestions" (green, visible)
        After Calculate: tips appear if there are inefficiencies, else green message stays.
        
        Each tip row has: "▸" bullet (cyan) + tip text (white, wraps if long)
        All 3 tip rows are created upfront and hidden; shown/hidden per update.
        
        Constrained to height=120 to stay compact — eco tips should be brief.
        """
        root_card = tk.Frame(parent, bg=BG_CARD,
                             highlightthickness=1, highlightbackground=BORDER)
        root_card.grid(row=0, column=0, sticky="nsew", padx=10, pady=(6, 0))
        root_card.configure(height=120)       # Fixed compact height
        root_card.pack_propagate(False)       # Prevent expanding beyond 120px

        hdr = tk.Frame(root_card, bg=BG_CARD)
        hdr.pack(fill=tk.X, padx=14, pady=(10, 4))
        tk.Label(hdr, text="🧠  ECO ASSISTANT", font=FONT_PANEL_HDR,
                 fg=AMBER, bg=BG_CARD, anchor="w").pack(side="left")
        tk.Frame(root_card, height=1, bg=BORDER).pack(fill=tk.X, padx=14)

        content = tk.Frame(root_card, bg=BG_CARD)
        content.pack(fill=tk.BOTH, expand=True, padx=14, pady=8)
        self._eco_content = content

        # Pre-create 3 tip rows (hidden by default with pack_forget)
        self._tip_rows: list[tk.Frame] = []
        for _ in range(3):
            row = tk.Frame(content, bg=BG_CARD)
            row.pack(fill=tk.X, pady=2)
            # Cyan "▸" bullet point
            tk.Label(row, text="▸", font=FONT_TIP, fg=ACCENT, bg=BG_CARD).pack(side="left")
            # Tip text — wraps at 310px wide
            tk.Label(row, text="", font=FONT_TIP, fg=TEXT_PRI, bg=BG_CARD,
                     wraplength=310, justify="left", anchor="w"
                     ).pack(side="left", padx=(6, 0), fill=tk.X, expand=True)
            row.pack_forget()   # Start hidden
            self._tip_rows.append(row)

        # "No tips" message shown when all is efficient
        self._no_tips_lbl = tk.Label(
            content,
            text="✓  Riding efficiently — no suggestions",
            font=FONT_TIP, fg=GREEN, bg=BG_CARD, anchor="w",
        )
        self._no_tips_lbl.pack(anchor="w")

    def _update_eco(self, tips: list[str]):
        """
        Shows/hides eco tip rows based on the list of tips from the engine.
        
        If tips list is non-empty:
          - Hide the "no suggestions" green message
          - Show each tip row with its text, hide unused rows
        If tips list is empty:
          - Hide all tip rows, show green "Riding efficiently" message
        """
        tips = tips[:3]   # Maximum 3 tips
        if tips:
            self._no_tips_lbl.pack_forget()
            for i, row in enumerate(self._tip_rows):
                if i < len(tips):
                    lbl = row.winfo_children()[1]   # Second child = the text label
                    lbl.config(text=tips[i])
                    row.pack(fill=tk.X, pady=2)
                else:
                    row.pack_forget()
        else:
            for row in self._tip_rows:
                row.pack_forget()
            self._no_tips_lbl.pack(anchor="w")

    # ─── Card 1: Range Anxiety Gauge ───────────────────────────
    def _build_gauge_card(self, parent: tk.Widget):
        """
        Creates the RANGE ANXIETY GAUGE card using Matplotlib embedded in tkinter.
        
        The gauge is a semicircle arc (like a speedometer):
          - Background: dark arc from 0° to 180°
          - Filled arc: colored from left (0 = no anxiety) to right (100 = critical)
          - Color zones: GREEN (0–30) → AMBER (30–55) → ORANGE (55–75) → RED (75–100)
          - Center text: score number + label below it
        
        Before Calculate: dim arc with "—" and "Press Calculate"
        After Calculate: colored arc fills to score position + score number in matching color
        
        Uses FigureCanvasTkAgg to embed the matplotlib figure as a tkinter widget.
        """
        content = self._make_card(parent, 1, "😰  RANGE ANXIETY", RED)

        # Create a matplotlib figure (3.4 × 2.2 inches, colored to match dashboard)
        self._fig, _ = plt.subplots(figsize=(3.4, 2.2), facecolor=BG_CARD)

        # Embed the figure as a tkinter canvas widget inside the card's content frame
        self._mpl_canvas = FigureCanvasTkAgg(self._fig, master=content)
        self._mpl_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, pady=(0, 4))

        # Score label below the gauge: "Score: — | Press Calculate" initially
        self._anxiety_score_lbl = tk.Label(
            content, text="Score: —  |  Press Calculate",
            font=(_UI, 12, "bold"), fg=TEXT_SEC, bg=BG_CARD,
        )
        self._anxiety_score_lbl.pack()

    def _draw_gauge_placeholder(self):
        """
        Draws the initial placeholder gauge — dark arc only, no color, dim "—" text.
        Called once during __init__ before any data is available.
        
        Uses numpy to generate arc coordinates:
          np.linspace(np.pi, 0, 200) = 200 evenly-spaced angles from 180° to 0°
          np.cos(theta) = x coordinates of arc points
          np.sin(theta) = y coordinates of arc points
        This traces a semicircle from left to right.
        """
        self._fig.clear()
        ax = self._fig.add_subplot(111)   # Create one plot (1 row, 1 col, plot 1)
        ax.set_facecolor(BG_CARD)
        ax.set_xlim(-1.4, 1.4)
        ax.set_ylim(-0.3, 1.4)
        ax.axis("off")   # No axes, labels, or borders — pure custom drawing

        # Draw dark background arc (the empty track)
        theta_bg = np.linspace(np.pi, 0, 200)
        ax.plot(np.cos(theta_bg), np.sin(theta_bg),
                color="#1E1E30", linewidth=22, solid_capstyle="round")

        # Dim "—" placeholder in the center of the semicircle
        ax.text(0, 0.08, "—",
                ha="center", va="center",
                fontsize=36, fontweight="bold",
                color="#3A3A5A", fontfamily="monospace")

        # "Press Calculate" helper text below the dash
        ax.text(0, -0.20, "Press Calculate",
                ha="center", va="center",
                fontsize=10, color="#3A3A5A")

        self._fig.patch.set_facecolor(BG_CARD)
        self._fig.tight_layout(pad=0.1)
        self._mpl_canvas.draw()   # Re-render the figure into the tkinter canvas

    def _draw_gauge(self, score: int, label: str):
        """
        Draws the animated anxiety gauge filled to the given score.
        
        HOW IT WORKS:
        The arc is drawn in colored SEGMENTS (Green / Amber / Orange / Red zones).
        For each segment, we check if the score reaches into that zone.
        If it does, we draw that portion of the arc in that zone's color.
        
        Example: score = 45
          - Green segment (0–30): score >= 0 → draw full green segment
          - Amber segment (30–55): score >= 30 → draw amber from 30 to min(45,55)=45
          - Orange segment (55–75): score < 55 → skip
          - Red segment (75–100): score < 75 → skip
        
        The filled arc goes from LEFT (score=0) to RIGHT (score=100).
        angle = π - (score/100 × π) converts score to radians
        """
        self._fig.clear()
        ax = self._fig.add_subplot(111)
        ax.set_facecolor(BG_CARD)
        ax.set_xlim(-1.4, 1.4)
        ax.set_ylim(-0.3, 1.4)
        ax.axis("off")

        # Background track (always drawn — dark grey full semicircle)
        theta_bg = np.linspace(np.pi, 0, 200)
        ax.plot(np.cos(theta_bg), np.sin(theta_bg),
                color="#1E1E30", linewidth=22, solid_capstyle="round")

        # Four color zones — each drawn only if score reaches into that zone
        segments = [
            (0,  30,  GREEN),    # Low anxiety — green
            (30, 55,  AMBER),    # Medium — amber
            (55, 75,  ORANGE),   # High — orange
            (75, 100, RED),      # Critical — red
        ]
        for seg_start, seg_end, seg_color in segments:
            if score >= seg_start:
                fill_end = min(score, seg_end)          # Don't overshoot the segment
                # Convert score percentages to radian angles on the semicircle
                a_start = np.pi - (seg_start / 100) * np.pi
                a_end   = np.pi - (fill_end  / 100) * np.pi
                theta_seg = np.linspace(a_start, a_end, 50)
                ax.plot(np.cos(theta_seg), np.sin(theta_seg),
                        color=seg_color, linewidth=22, solid_capstyle="round")

        # Score number in center — color matches the zone the score falls in
        arc_col = _arc_color(score)
        ax.text(0, 0.08, str(score),
                ha="center", va="center",
                fontsize=42, fontweight="bold",
                color=arc_col, fontfamily="monospace")

        # Label below the number — e.g., "Low" / "Medium" / "High" / "Critical"
        ax.text(0, -0.20, label,
                ha="center", va="center",
                fontsize=13, color=TEXT_SEC)

        self._fig.patch.set_facecolor(BG_CARD)
        self._fig.tight_layout(pad=0.1)
        self._mpl_canvas.draw()

        # Update the text label below the gauge
        self._anxiety_score_lbl.config(
            text=f"Score: {score}  |  {label}", fg=arc_col,
        )

    # ─── Card 2: Destination Check ─────────────────────────────
    def _build_dest_card(self, parent: tk.Widget):
        """
        Creates the DESTINATION CHECK card.
        
        Initial state: "Enter destination km in input panel" (grey helper text)
        
        After Calculate:
          If destination was entered AND reachable:
            → "✅ REACHABLE" (green) + "Margin: +XX km"
          If destination was entered AND NOT reachable:
            → "❌ CANNOT REACH" (red) + "Short by: XX km" + "Ride at XX km/h to reach"
          If no destination entered:
            → Shows the initial helper text again
        """
        content = self._make_card(parent, 2, "📍  DESTINATION CHECK", ACCENT)

        # Main status label (reachable / cannot reach / placeholder)
        self._dest_main = tk.Label(
            content,
            text="Enter destination km in input panel",
            font=FONT_PANEL_VAL, fg=TEXT_SEC, bg=BG_CARD,
            wraplength=320, justify="left", anchor="w",
        )
        self._dest_main.pack(anchor="w", pady=(2, 0))

        # Secondary label (margin or shortfall + speed suggestion)
        self._dest_sub = tk.Label(
            content, text="",
            font=FONT_PANEL_VAL, fg=AMBER, bg=BG_CARD, anchor="w",
        )
        self._dest_sub.pack(anchor="w")

    def _update_dest(self, result: dict):
        """
        Updates the destination card based on engine result.
        
        result["can_reach"]:
          None  → no destination entered → show placeholder text
          True  → can reach → show green REACHABLE + margin km
          False → cannot reach → show red CANNOT REACH + shortfall + speed suggestion
        """
        can_reach = result["can_reach"]

        if can_reach is None:
            # No destination was entered
            self._dest_main.config(
                text="Enter destination km in input panel",
                font=FONT_PANEL_VAL, fg=TEXT_SEC,
            )
            self._dest_sub.config(text="")
            return

        if can_reach:
            margin = result["margin_km"]
            self._dest_main.config(
                text="✅  REACHABLE",
                font=(_MONO, 16, "bold"), fg=GREEN,
            )
            self._dest_sub.config(
                text=f"Margin: +{margin} km", fg=GREEN,
            )
        else:
            shortfall  = result["shortfall_km"]
            suggestion = result["speed_suggestion"]   # Optimal speed to just reach destination
            self._dest_main.config(
                text="❌  CANNOT REACH",
                font=(_MONO, 16, "bold"), fg=RED,
            )
            detail = f"Short by: {shortfall} km"
            if suggestion:
                detail += f"\nRide at {suggestion} km/h to reach"
            self._dest_sub.config(text=detail, fg=AMBER)

    # ─── Card 3: Cost Savings vs Petrol ────────────────────────
    def _build_cost_card(self, parent: tk.Widget):
        """
        Creates the COST SAVINGS vs PETROL card with a grid of label-value pairs.
        
        Rows (in order):
          EV cost / month       ← how much electricity costs to ride this far
          Petrol cost / month   ← how much petrol would cost for same distance
          Monthly savings       ← petrol - EV (how much you save per month)
          CO₂ saved / month     ← kg of carbon not emitted vs petrol
          [separator line]
          Yearly savings        ← monthly savings × 12 (large number, bigger font)
        
        All values show "—" initially (before Calculate or speed change).
        Values update LIVE from the speed slider via update_cost_live().
        Values update precisely after Calculate via _update_cost().
        
        Uses setattr(self, attr, lbl) to store each label dynamically:
          self._cost_ev, self._cost_petrol, self._cost_monthly, self._cost_co2
        """
        content = self._make_card(parent, 3, "💰  COST SAVINGS vs PETROL", GREEN)

        content.columnconfigure(0, weight=1)   # Label column — expands
        content.columnconfigure(1, weight=0)   # Value column — fixed, right-aligned

        # Define all 4 rows: (display label text, attribute name, value color)
        rows_def = [
            ("EV cost / month",     "_cost_ev",      TEXT_SEC),   # White/grey — neutral
            ("Petrol cost / month", "_cost_petrol",  TEXT_SEC),   # White/grey — neutral
            ("Monthly savings",     "_cost_monthly", GREEN),      # Green — positive!
            ("CO₂ saved / month",   "_cost_co2",     TEAL),       # Teal — environmental benefit
        ]
        for i, (lbl_txt, attr, val_col) in enumerate(rows_def):
            # Left side: row description label
            tk.Label(content, text=lbl_txt, font=FONT_PANEL_VAL,
                     fg=TEXT_SEC, bg=BG_CARD, anchor="w",
                     ).grid(row=i, column=0, sticky="w", pady=3)
            # Right side: value label (starts as "—", updated later)
            lbl = tk.Label(content, text="—", font=FONT_COST_VAL,
                           fg=val_col, bg=BG_CARD, anchor="e")
            lbl.grid(row=i, column=1, sticky="e", pady=3)
            setattr(self, attr, lbl)   # Store reference as self._cost_ev etc.

        # Thin separator line between monthly and yearly
        tk.Frame(content, height=1, bg=BORDER).grid(
            row=4, column=0, columnspan=2, sticky="ew", pady=8)

        # Yearly savings row — larger font to emphasize the big annual number
        tk.Label(content, text="Yearly savings", font=FONT_PANEL_VAL,
                 fg=TEXT_SEC, bg=BG_CARD, anchor="w",
                 ).grid(row=5, column=0, sticky="w")
        self._cost_yearly = tk.Label(content, text="—",
                                     font=FONT_YEARLY, fg=GREEN, bg=BG_CARD, anchor="e")
        self._cost_yearly.grid(row=5, column=1, sticky="e")

    def update_cost_live(self, speed_kmh: float):
        """
        Quick cost estimate called whenever the speed slider moves — no Calculate needed.
        
        Uses a simplified formula (speed × hours/day × working days × rate per km)
        to give instant cost feedback without running the full engine.
        
        Assumptions (same as engine):
          8 hours riding per day × 26 working days per month
          EV: ₹0.15/km electricity cost
          Petrol: ₹2.80/km fuel+servicing cost
        
        Called from main.py via:  input_panel.speed_var.trace_add("write", _sync_cost_live)
        """
        rupee = "\u20B9"   # ₹ symbol (Unicode)
        try:
            monthly_km  = speed_kmh * 8 * 26           # Total km per month at this speed
            ev_cost     = round(monthly_km * 0.15)      # EV electricity cost
            petrol_cost = round(monthly_km * 2.80)      # Equivalent petrol cost
            savings     = petrol_cost - ev_cost         # Monthly savings
            yearly      = savings * 12                  # Annual savings
            co2         = round(monthly_km * 0.0021, 1) # CO₂ saved in kg

            # Update all the cost labels in the card
            self._cost_ev.config(      text=f"{rupee}{ev_cost:,}")
            self._cost_petrol.config(  text=f"{rupee}{petrol_cost:,}")
            self._cost_monthly.config( text=f"{rupee}{savings:,}")
            self._cost_co2.config(     text=f"{co2} kg")
            self._cost_yearly.config(  text=f"{rupee}{yearly:,}")
        except Exception:
            pass   # Silently ignore if slider value isn't ready yet

    def _update_cost(self, result: dict):
        """
        Precise cost update using the full engine result after Calculate is pressed.
        Uses exact values from result dict (which uses the same formulas as update_cost_live).
        """
        rupee = "\u20B9"
        self._cost_ev.config(      text=f"{rupee}{result['monthly_ev_cost']:,}")
        self._cost_petrol.config(  text=f"{rupee}{result['monthly_petrol_cost']:,}")
        self._cost_monthly.config( text=f"{rupee}{result['monthly_savings']:,}")
        self._cost_co2.config(     text=f"{result['co2_saved_kg']} kg")
        self._cost_yearly.config(  text=f"{rupee}{result['yearly_savings']:,}")

    # ─── Public update (called after Calculate) ─────────────────
    def update(self, result: dict):
        """
        Full refresh of the entire advisor panel — called by main.py after engine runs.
        
        Delegates to each card's private update method:
          _update_eco()   — show/hide eco tip bullets
          _draw_gauge()   — redraw the semicircle gauge with new score
          _update_dest()  — show REACHABLE / CANNOT REACH / placeholder
          _update_cost()  — update ₹ cost values from engine's precise result
        """
        self._update_eco(result["eco_tips"])
        self._draw_gauge(result["anxiety_score"], result["anxiety_label"])
        self._update_dest(result)
        self._update_cost(result)
