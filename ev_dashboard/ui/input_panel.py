# ============================================================
# EV Dashboard — Left Input Panel (Production Overhaul)
# ============================================================
# This file builds the LEFT COLUMN of the dashboard — the scrollable
# panel where the user sets all their inputs:
#   - Speed, Battery, Temperature sliders
#   - Riding mode dropdown (Eco / Normal / Sport)
#   - Traffic and Road surface dropdowns
#   - Rider weight, pillion checkbox, luggage sliders
#   - Battery health and charge cycles
#   - Destination distance (optional)
#   - The big "CALCULATE RANGE" button
#
# When "Calculate" is pressed, all inputs are validated and then
# passed to the calculation engine via the on_calculate callback.
# ============================================================

import tkinter as tk
from tkinter import messagebox   # For showing popup error dialogs when inputs are invalid

# Import all design colors and fonts from our constants file
from core.constants import (
    BG_CARD, BG_INPUT, BG_DEEP,
    ACCENT, GREEN, AMBER, RED, TEXT_PRI, TEXT_SEC, BORDER,
    FONT_TITLE, FONT_SECTION, FONT_LABEL, FONT_VALUE,
    FONT_BTN, _MONO, _UI,
)

# Import our reusable widget builder functions from the widgets helper file
from ui.widgets import make_slider_row, make_section_header, make_option_menu


class InputPanel:
    """
    The scrollable left panel — 340px wide with large, readable text.
    
    It holds all the user-adjustable inputs.
    The panel is scrollable because there are more controls than fit on screen.
    
    When the user clicks "Calculate":
      1. All inputs are read and validated
      2. If valid: on_calculate(inputs) is called (wired up in main.py)
      3. If invalid: an error popup shows which fields need fixing
    
    Key public attributes (used by main.py for live slider sync):
        speed_var   — DoubleVar for speed slider (traced in main.py)
        battery_var — DoubleVar for battery slider (traced in main.py)
        temp_var    — DoubleVar for temperature slider (traced in main.py)
    """

    def __init__(self, parent: tk.Widget, on_calculate):
        self._on_calculate = on_calculate   # Callback function set after creation (in main.py)
        self._build(parent)                 # Build all the widgets

    # ──────────────────────────────────────────────────────────
    def _build(self, parent: tk.Widget):
        """
        Creates the scrollable canvas + inner frame structure.
        
        Why a Canvas instead of just a Frame?
        → tkinter Frames cannot scroll. To make the panel scrollable,
          we put a Canvas inside the parent, attach a Scrollbar to the Canvas,
          and then place a Frame INSIDE the Canvas as the scrollable content.
        
        Structure:
          parent (left_holder Frame)
            └─ Canvas (scrollable area)
                 └─ Scrollbar (vertical, right side)
                 └─ inner Frame (contains all the actual widgets)
        """
        # ── Scrollable Canvas ─────────────────────────────────
        # The Canvas is the "viewport" — it shows a portion of the inner frame.
        canvas = tk.Canvas(parent, bg=BG_CARD, highlightthickness=0)

        # Vertical scrollbar linked to the canvas
        scrollbar = tk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)   # Scrollbar controls canvas, canvas updates scrollbar

        scrollbar.pack(side="right", fill="y")            # Scrollbar on the right edge
        canvas.pack(side="left", fill="both", expand=True)  # Canvas fills the rest

        # ── Inner frame (the actual scrollable content) ───────
        # All widgets are placed inside this frame.
        # The frame is embedded in the canvas using create_window().
        inner = tk.Frame(canvas, bg=BG_CARD)
        self._inner = inner
        # Create the inner frame inside the canvas at position (0,0), anchored top-left
        self._canvas_window = canvas.create_window((0, 0), window=inner, anchor="nw")

        # ── Event handlers for dynamic resizing ───────────────

        def _on_canvas_resize(event):
            """When the canvas is resized (e.g., window resize), stretch the inner frame to match."""
            canvas.itemconfig(self._canvas_window, width=event.width)

        def _on_inner_resize(event):
            """When inner frame changes size (widgets added), update the scroll region."""
            canvas.configure(scrollregion=canvas.bbox("all"))

        canvas.bind("<Configure>", _on_canvas_resize)  # Called when canvas is resized
        inner.bind("<Configure>", _on_inner_resize)    # Called when inner frame changes size

        # ── Mouse wheel scrolling ─────────────────────────────
        def _on_mousewheel(event):
            """Scroll the panel up/down when the user scrolls their mouse wheel."""
            # event.delta / 120 converts raw delta to scroll units
            # -1 * inverts direction so scrolling down moves content up (natural direction)
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        canvas.bind_all("<MouseWheel>", _on_mousewheel)   # bind_all = works when hovering anywhere

        # ── App title at the top of the panel ─────────────────
        # "🛵 EV Telemetry" in bold cyan
        tk.Label(
            inner, text="🛵  EV Telemetry",
            font=FONT_TITLE, fg=ACCENT, bg=BG_CARD, anchor="w",
        ).pack(fill=tk.X, padx=14, pady=(16, 4))

        # "Range Estimator" subtitle in smaller grey text
        tk.Label(
            inner, text="Range Estimator",
            font=(_UI, 10), fg=TEXT_SEC, bg=BG_CARD, anchor="w",
        ).pack(fill=tk.X, padx=14, pady=(0, 10))

        # Thin cyan decorative line under the title
        tk.Frame(inner, height=2, bg=ACCENT).pack(fill=tk.X, padx=14, pady=(0, 16))

        # ── Build each section ────────────────────────────────
        # Each method adds a group of related widgets to the inner frame
        self._build_riding_conditions(inner)   # Speed, Battery, Temperature, Mode
        self._build_conditions(inner)          # Traffic pattern, Road surface
        self._build_rider_load(inner)          # Weight, Pillion, Luggage, Total load
        self._build_battery_health(inner)      # Battery health %, Charge cycles
        self._build_destination(inner)         # Optional destination distance

        # ── Calculate button (at the very bottom) ─────────────
        tk.Frame(inner, height=16, bg=BG_CARD).pack()   # Spacer above the button

        btn = tk.Button(
            inner,
            text="⚡   CALCULATE RANGE",   # Button label with lightning bolt icon
            font=FONT_BTN,                 # 14pt bold
            bg=ACCENT,                     # Cyan background
            fg=BG_DEEP,                    # Dark text on cyan (high contrast)
            activebackground="#00C8D4",    # Slightly different cyan when pressed
            activeforeground=BG_DEEP,
            relief="flat",                 # No 3D border — flat modern look
            cursor="hand2",               # Shows pointer cursor when hovering
            pady=14,                       # Extra vertical padding = taller button
            width=28,
            command=self._on_click,        # Calls _on_click when pressed
        )
        btn.pack(fill=tk.X, padx=14, pady=(0, 20))

    # ─── Section: Riding Conditions ───────────────────────────
    def _build_riding_conditions(self, inner: tk.Frame):
        """
        Builds the RIDING CONDITIONS section with 3 sliders and a dropdown.
        
        Contains:
          - Speed slider (0–120 km/h), default 40
          - Battery Level slider (0–100%), default 80
          - Temperature slider (-5 to 50°C), default 25
          - Riding Mode dropdown (Eco / Normal / Sport), default Normal
        
        WHY these as a group?
          These are the most important real-time variables — they directly
          affect the range estimate and are likely to change mid-journey.
        """
        make_section_header(inner, "⚡  RIDING CONDITIONS")   # Amber section title

        # Speed slider: linked to self.speed_var (also traced in main.py for live updates)
        self.speed_var = tk.DoubleVar(value=40)   # Default: 40 km/h
        make_slider_row(inner, "Speed (km/h)", self.speed_var, 0, 120, unit=" km/h")

        # Battery level slider: 0–100%, default 80%
        self.battery_var = tk.DoubleVar(value=80)
        make_slider_row(inner, "Battery Level (%)", self.battery_var, 0, 100, unit="%")

        # Temperature slider: -5°C to 50°C, default 25°C
        self.temp_var = tk.DoubleVar(value=25)
        make_slider_row(inner, "Temperature (°C)", self.temp_var, -5, 50, unit="°C")

        # ── Riding Mode dropdown ──────────────────────────────
        # Mode affects energy consumption directly (Eco saves, Sport drains)
        tk.Label(inner, text="Riding Mode", font=FONT_LABEL, fg=TEXT_PRI,
                 bg=BG_CARD, anchor="w").pack(fill=tk.X, padx=12, pady=(4, 2))

        mode_row = tk.Frame(inner, bg=BG_CARD)
        mode_row.pack(fill=tk.X, padx=12, pady=(0, 12))

        self.mode_var = tk.StringVar(value="Normal")   # Default: Normal mode
        opt = make_option_menu(mode_row, self.mode_var, "Eco", "Normal", "Sport")
        opt.pack(side=tk.LEFT)

        tk.Frame(inner, height=12, bg=BG_CARD).pack()   # Visual spacer between sections

    # ─── Section: Road & Traffic Conditions ───────────────────
    def _build_conditions(self, inner: tk.Frame):
        """
        Builds the CONDITIONS section with 2 dropdowns.
        
        Contains:
          - Traffic Pattern dropdown (City / Highway / Delivery / Rural)
          - Road Surface dropdown (Smooth / Pothole / Hilly / Wet)
        
        WHY these together?
          Both relate to the external environment the rider encounters —
          the road type they're on and how much traffic is around them.
        """
        make_section_header(inner, "🛣️  CONDITIONS")

        # ── Traffic Pattern dropdown ──────────────────────────
        # City: stop-and-go | Highway: steady | Delivery: worst | Rural: light
        tk.Label(inner, text="Traffic Pattern", font=FONT_LABEL, fg=TEXT_PRI,
                 bg=BG_CARD, anchor="w").pack(fill=tk.X, padx=12, pady=(4, 2))

        traffic_row = tk.Frame(inner, bg=BG_CARD)
        traffic_row.pack(fill=tk.X, padx=12, pady=(0, 10))

        self.traffic_var = tk.StringVar(value="City")   # Default: City traffic
        opt = make_option_menu(traffic_row, self.traffic_var,
                               "City", "Highway", "Delivery", "Rural")
        opt.pack(side=tk.LEFT)

        # ── Road Surface dropdown ─────────────────────────────
        # Smooth: ideal | Pothole: rough | Hilly: climbs | Wet: slippery
        tk.Label(inner, text="Road Surface", font=FONT_LABEL, fg=TEXT_PRI,
                 bg=BG_CARD, anchor="w").pack(fill=tk.X, padx=12, pady=(4, 2))

        road_row = tk.Frame(inner, bg=BG_CARD)
        road_row.pack(fill=tk.X, padx=12, pady=(0, 12))

        self.road_var = tk.StringVar(value="Smooth")   # Default: smooth road
        opt2 = make_option_menu(road_row, self.road_var,
                                "Smooth", "Pothole", "Hilly", "Wet")
        opt2.pack(side=tk.LEFT)

        tk.Frame(inner, height=12, bg=BG_CARD).pack()

    # ─── Section: Rider Load ──────────────────────────────────
    def _build_rider_load(self, inner: tk.Frame):
        """
        Builds the RIDER LOAD section.
        
        Contains:
          - Rider Weight slider (40–150 kg), default 70 kg
          - Pillion Passenger checkbox (adds 65 kg if checked)
          - Luggage slider (0–30 kg), default 0 kg
          - "Total Load: XX kg" summary label (updates live)
        
        WHY total load matters?
          Heavier loads require more energy to accelerate and go uphill.
          The engine calculates a "load penalty" that reduces range.
          Every kg above 80 kg baseline causes a small range reduction.
        """
        make_section_header(inner, "🧍  RIDER LOAD")

        # ── Rider weight slider ───────────────────────────────
        self.weight_var = tk.DoubleVar(value=70)   # Default: 70 kg rider
        make_slider_row(inner, "Rider Weight (kg)", self.weight_var, 40, 150, unit=" kg")

        # ── Pillion passenger checkbox ────────────────────────
        # Checking this adds a fixed 65 kg to the total load calculation.
        # The total load label updates immediately when checked/unchecked.
        tk.Label(inner, text="Pillion Passenger (+65 kg)", font=FONT_LABEL,
                 fg=TEXT_PRI, bg=BG_CARD, anchor="w").pack(fill=tk.X, padx=12, pady=(4, 2))

        pill_row = tk.Frame(inner, bg=BG_CARD)
        pill_row.pack(fill=tk.X, padx=12, pady=(0, 8))

        self.pillion_var = tk.BooleanVar(value=False)   # Default: no pillion passenger
        tk.Checkbutton(
            pill_row,
            variable=self.pillion_var,            # Linked to the BooleanVar (True/False)
            text="Add pillion",
            font=FONT_LABEL,
            bg=BG_CARD, fg=TEXT_PRI,
            selectcolor=BG_INPUT,                 # Background color when checked
            activebackground=BG_CARD,
            activeforeground=ACCENT,
            highlightthickness=0,
            command=self._update_total_load,      # Update total load display when toggled
        ).pack(side=tk.LEFT)

        # ── Luggage slider ────────────────────────────────────
        # Extra weight for bags, packages, or cargo
        self.luggage_var = tk.DoubleVar(value=0)   # Default: 0 kg luggage
        make_slider_row(inner, "Luggage (kg)", self.luggage_var, 0, 30, unit=" kg")

        # ── Total Load display label ──────────────────────────
        # Shows the sum: rider weight + pillion (if any) + luggage
        # Updates automatically whenever any of the three inputs change
        self._total_load_lbl = tk.Label(
            inner,
            text=f"Total Load: {self.weight_var.get():.0f} kg",   # Initial value
            font=(_MONO, 12, "bold"),    # Bold monospaced font
            fg=AMBER,                   # Amber/warning color (load affects range)
            bg=BG_CARD,
            anchor="w",
        )
        self._total_load_lbl.pack(fill=tk.X, padx=14, pady=(0, 12))

        # trace_add("write", callback) = call _update_total_load whenever these vars change
        # This makes the total load label update as the user drags the sliders
        self.weight_var.trace_add("write", self._update_total_load)
        self.luggage_var.trace_add("write", self._update_total_load)

        tk.Frame(inner, height=12, bg=BG_CARD).pack()

    def _update_total_load(self, *_):
        """
        Recalculates and displays the total load whenever weight, pillion, or luggage changes.
        
        Formula: total = rider_weight + (65 if pillion checked) + luggage_weight
        Called automatically via trace_add() on weight_var and luggage_var,
        and directly from the pillion Checkbutton command.
        """
        w  = self.weight_var.get()                       # Current rider weight
        l_ = self.luggage_var.get()                      # Current luggage weight
        p  = 65 if self.pillion_var.get() else 0         # 65 kg if pillion checked, else 0
        self._total_load_lbl.config(text=f"Total Load: {w + p + l_:.0f} kg")

    # ─── Section: Battery Health ───────────────────────────────
    def _build_battery_health(self, inner: tk.Frame):
        """
        Builds the BATTERY HEALTH section.
        
        Contains:
          - Battery Health slider (60–100%), default 90%
          - Charge Cycles text entry (0–1000), default 100
        
        WHY these matter?
          Lithium batteries degrade over time. A battery that's been charged
          500 times has noticeably less capacity than a new one.
          
          Battery Health % = current max capacity as a % of factory capacity
            e.g., 85% health → battery holds 85% of its original charge
          
          Charge Cycles = how many full charge-discharge cycles completed
            Penalty: 0.005% extra efficiency loss per cycle
            At 1000 cycles: ~5% additional range reduction
        """
        make_section_header(inner, "🔋  BATTERY HEALTH")

        # Battery health slider (60% minimum — we assume you'd replace below that)
        self.health_var = tk.DoubleVar(value=90)   # Default: 90% health (fairly new battery)
        make_slider_row(inner, "Battery Health (%)", self.health_var, 60, 100, unit="%")

        # Charge cycles — entered as a number in a text box (not a slider)
        # Text entry is used because cycles can be any integer, and entering a specific
        # number is more accurate than a slider for values like "347 cycles".
        tk.Label(inner, text="Charge Cycles (0–1000)", font=FONT_LABEL,
                 fg=TEXT_PRI, bg=BG_CARD, anchor="w").pack(fill=tk.X, padx=12, pady=(4, 2))

        self.cycles_entry = tk.Entry(
            inner,
            width=8,                    # Small width — only needs a few digits
            font=FONT_VALUE,            # Bold monospaced font
            bg=BG_INPUT,               # Dark background
            fg=ACCENT,                  # Cyan text color
            insertbackground=ACCENT,    # Cursor color
            relief="flat",
            highlightthickness=1,
            highlightbackground=BORDER,
        )
        self.cycles_entry.insert(0, "100")   # Pre-fill with default value: 100 cycles
        self.cycles_entry.pack(anchor="w", padx=14, pady=(0, 12))

        tk.Frame(inner, height=12, bg=BG_CARD).pack()

    # ─── Section: Destination ─────────────────────────────────
    def _build_destination(self, inner: tk.Frame):
        """
        Builds the DESTINATION section — an optional text field.
        
        Contains:
          - Text entry for destination distance in km (optional, 1–200 km)
          - Helper text: "Leave blank to skip destination check"
        
        WHY optional?
          Not every user has a fixed destination. If left blank, the
          destination reachability check is skipped and the right panel
          shows "Enter destination km in input panel" as a placeholder.
          
          If filled in, the engine checks: can the scooter REACH that destination?
          If YES → shows "✅ REACHABLE" with how many km of margin
          If NO  → shows "❌ CANNOT REACH" with how much short, and a suggested speed
        """
        make_section_header(inner, "📍  DESTINATION")

        tk.Label(inner, text="Distance to destination (km)", font=FONT_LABEL,
                 fg=TEXT_PRI, bg=BG_CARD, anchor="w").pack(fill=tk.X, padx=12, pady=(4, 2))

        # Text entry for the destination distance
        self.dest_entry = tk.Entry(
            inner,
            width=12,
            font=FONT_VALUE,
            bg=BG_INPUT,
            fg=ACCENT,
            insertbackground=ACCENT,
            relief="flat",
            highlightthickness=1,
            highlightbackground=BORDER,
        )
        self.dest_entry.pack(anchor="w", padx=14, pady=(0, 4))

        # Helper text below the entry box
        tk.Label(inner, text="Leave blank to skip destination check",
                 font=(_UI, 9), fg=TEXT_SEC, bg=BG_CARD, anchor="w",
                 ).pack(fill=tk.X, padx=14, pady=(0, 12))

    # ─── Validation + Calculate callback ──────────────────────
    def _on_click(self):
        """
        Called when the user clicks the "⚡ CALCULATE RANGE" button.
        
        Gets validated inputs and calls the calculate callback if all inputs are valid.
        If any input is invalid, get_inputs() shows an error popup and returns None.
        """
        inputs = self.get_inputs()          # Read and validate all inputs
        if inputs is not None:              # None means there was a validation error
            self._on_calculate(inputs)      # Call the engine + update UI panels

    def get_inputs(self) -> dict | None:
        """
        Reads all input widgets, validates each value, and returns a clean dict.
        
        Validation rules:
          - Speed: 0–120 km/h (float)
          - Battery: 0–100% (float)
          - Temperature: -5 to 50°C (float)
          - Charge cycles: 0–1000 (integer)
          - Destination: 1–200 km (float, optional)
        
        If ANY validation fails:
          → The error message is added to the 'errors' list
          → After checking all fields, a popup shows ALL errors at once
          → Returns None (signals to _on_click that calculation should not proceed)
        
        If ALL validations pass:
          → Returns a dictionary with all input values
          → This dict is passed to calculate_range() in the engine
        
        Returns:
            dict  — all validated inputs ready for the calculation engine
            None  — if any validation failed (error popup already shown)
        """
        errors = []   # Collect all validation errors to show together

        # ── Validate Speed ───────────────────────────────────
        try:
            speed = float(self.speed_var.get())
            assert 0 <= speed <= 120   # Must be within valid range
        except Exception:
            speed = 0                  # Fallback value (not used if there's an error)
            errors.append("Speed must be 0–120 km/h")

        # ── Validate Battery Level ───────────────────────────
        try:
            battery = float(self.battery_var.get())
            assert 0 <= battery <= 100
        except Exception:
            battery = 0
            errors.append("Battery must be 0–100%")

        # ── Validate Temperature ─────────────────────────────
        try:
            temperature = float(self.temp_var.get())
            assert -5 <= temperature <= 50
        except Exception:
            temperature = 0
            errors.append("Temperature must be -5 to 50°C")

        # ── Validate Charge Cycles ───────────────────────────
        # int() used (not float) because cycles must be whole numbers
        try:
            cycles = int(self.cycles_entry.get())
            assert 0 <= cycles <= 1000
        except Exception:
            cycles = 0
            errors.append("Charge cycles must be 0–1000 (integer)")

        # ── Validate Destination (optional) ──────────────────
        dest_input = self.dest_entry.get().strip()   # Read and remove whitespace
        destination_km = None                        # Default: no destination
        if dest_input:                               # Only validate if the user typed something
            try:
                destination_km = float(dest_input)
                assert 0 < destination_km <= 200     # Must be a positive distance up to 200 km
            except Exception:
                errors.append("Destination must be 1–200 km (or leave blank)")

        # ── Show errors if any validation failed ──────────────
        if errors:
            # Show all errors in a single popup (user sees everything wrong at once)
            messagebox.showerror("Input Error", "\n".join(errors))
            return None   # Signal failure — do not proceed with calculation

        # ── Return clean, validated inputs ───────────────────
        # This dict matches exactly what calculate_range() expects as input
        return {
            "speed":          speed,
            "battery":        battery,
            "temperature":    temperature,
            "mode":           self.mode_var.get(),        # e.g., "Normal"
            "traffic":        self.traffic_var.get(),     # e.g., "City"
            "rider_weight":   self.weight_var.get(),      # e.g., 70.0
            "pillion":        self.pillion_var.get(),     # True or False
            "luggage":        self.luggage_var.get(),     # e.g., 0.0
            "road":           self.road_var.get(),        # e.g., "Smooth"
            "battery_health": self.health_var.get(),      # e.g., 90.0
            "charge_cycles":  cycles,                     # e.g., 100
            "destination_km": destination_km,             # e.g., 50.0 or None
        }
