#!/usr/bin/env python3
# ============================================================
# EV Scooter Range Estimator & Smart Telemetry Dashboard
# ============================================================
# This is the ENTRY POINT of the application.
# When you run `python main.py`, Python starts here.
#
# What this file does:
#   1. Sets up the 3-column window layout (left / center / right)
#   2. Creates the three main panels (InputPanel, TelemetryPanel, AdvisorPanel)
#   3. Connects everything together:
#      - When a slider moves → live update stat cards and cost savings
#      - When "Calculate" is pressed → run the engine → update all panels
#
# Run: python main.py
# Requires: pip install matplotlib
# ============================================================

import sys          # Used to modify the Python module search path
import os           # Used to get the current file's directory
import tkinter as tk  # The main GUI library — creates windows, buttons, labels, etc.

# Add the current folder to Python's search path so we can import our own modules
# (e.g., "from core.engine import calculate_range")
sys.path.insert(0, os.path.dirname(__file__))

# ── Import our own modules ───────────────────────────────────
# BG_DEEP, BG_CARD, ACCENT = colors from our design constants file
from core.constants import BG_DEEP, BG_CARD, ACCENT

# calculate_range = the main function that does all the EV math
from core.engine    import calculate_range

# InputPanel = the left scrollable panel with all sliders and inputs
from ui.input_panel import InputPanel

# TelemetryPanel = the center panel showing speed/battery/temp + range
from ui.telemetry   import TelemetryPanel

# AdvisorPanel = the right panel showing eco tips, anxiety gauge, cost savings
from ui.advisor     import AdvisorPanel


def build_ui(root: tk.Tk) -> None:
    """
    Set up the entire window layout and wire all panels together.
    
    The window is divided into 3 columns:
      Column 0 (left):   InputPanel   — sliders, dropdowns, text inputs (fixed 340px wide)
      Column 1 (center): TelemetryPanel — stat cards + range + regen + battery health (stretches)
      Column 2 (right):  AdvisorPanel — eco tips, gauge, destination, cost savings (fixed 380px wide)
    """
    root.title("🛵  EV Telemetry Dashboard")   # Window title shown in the title bar
    root.geometry("1600x900")                   # Default window size: 1600px wide × 900px tall
    root.minsize(1400, 800)                     # Minimum resize limit so cards don't overlap
    root.configure(bg=BG_DEEP)                  # Window background color (darkest black)

    # ── Root grid: 3 columns ──────────────────────────────────
    # weight=0 means that column does NOT stretch when window is resized (fixed width)
    # weight=1 means that column DOES stretch to fill available space
    root.columnconfigure(0, weight=0, minsize=340)   # Left panel — fixed 340px, never stretches
    root.columnconfigure(1, weight=1)                # Center panel — fills all remaining space
    root.columnconfigure(2, weight=0, minsize=380)   # Right panel — fixed 380px, never stretches
    root.rowconfigure(0, weight=1)                   # Single row — stretches to fill window height

    # ── Column 0 — Left input panel (scrollable) ──────────────
    # This frame holds the InputPanel. It is 340px wide and sticks to all sides (nsew).
    # grid_propagate(False) prevents the frame from shrinking to fit its children.
    left_holder = tk.Frame(root, bg=BG_CARD, width=340)
    left_holder.grid(row=0, column=0, sticky="nsew")    # Placed in column 0, stretches to fill
    left_holder.grid_propagate(False)                    # Lock the width at 340px

    # ── Column 1 — Center telemetry ───────────────────────────
    # This frame holds the TelemetryPanel (stat cards, range estimate, etc.)
    center_holder = tk.Frame(root, bg=BG_DEEP)
    center_holder.grid(row=0, column=1, sticky="nsew")  # Stretches to fill all center space

    # ── Column 2 — Right advisor panel ───────────────────────
    # This frame holds the AdvisorPanel (eco tips, gauge, destination check, cost savings).
    right_holder = tk.Frame(root, bg=BG_DEEP, width=380)
    right_holder.grid(row=0, column=2, sticky="nsew")   # Placed in column 2
    right_holder.grid_propagate(False)                  # Lock the width at 380px

    # ── Instantiate the three panels ─────────────────────────
    # Each panel is a class that builds its own widgets inside the given parent frame.
    telemetry   = TelemetryPanel(center_holder)          # Center: big numbers and charts
    advisor     = AdvisorPanel(right_holder)             # Right: eco assistant, gauge, cost
    input_panel = InputPanel(left_holder, on_calculate=None)  # Left: all user inputs (callback added below)

    # ── Wire the Calculate button callback ───────────────────
    # This function is called when the user presses "⚡ CALCULATE RANGE".
    # It:
    #   1. Takes all inputs from the input panel (speed, battery, etc.)
    #   2. Passes them to the calculation engine
    #   3. Updates the telemetry center panel with the results
    #   4. Updates the advisor right panel with eco tips, anxiety score, cost
    def on_calculate(inputs: dict) -> None:
        result = calculate_range(inputs)   # Run the math engine — returns a dict of results
        telemetry.update(inputs, result)   # Update center panel (range, badges, regen, health)
        advisor.update(result)             # Update right panel (eco tips, gauge, destination, cost)

    # Attach our callback to the input panel
    # (The input panel was created with on_calculate=None, now we set the real function)
    input_panel._on_calculate = on_calculate

    # ── Live slider → stat card sync (FIX 1 + 6) ────────────
    # These three functions are called EVERY TIME the slider moves (not just on Calculate).
    # They update the big numbers at the top (Speed / Battery / Temperature) in real time.

    def _sync_speed(*_):
        """Called when speed slider moves — updates the SPEED stat card immediately."""
        try:
            v = int(float(input_panel.speed_var.get()))   # Read current slider value as integer
        except Exception:
            v = 0   # If reading fails for any reason, default to 0
        telemetry.set_stat("speed", v)   # Push value to the big SPEED display card

    def _sync_battery(*_):
        """Called when battery slider moves — updates the BATTERY stat card immediately."""
        try:
            v = int(float(input_panel.battery_var.get()))
        except Exception:
            v = 0
        telemetry.set_stat("battery", v)

    def _sync_temp(*_):
        """Called when temperature slider moves — updates the TEMPERATURE stat card immediately."""
        try:
            v = int(float(input_panel.temp_var.get()))
        except Exception:
            v = 0
        telemetry.set_stat("temp", v)

    # trace_add("write", callback) means: "whenever this variable changes, call this function"
    # This is what makes the stat cards update instantly as you drag the sliders
    input_panel.speed_var.trace_add("write", _sync_speed)
    input_panel.battery_var.trace_add("write", _sync_battery)
    input_panel.temp_var.trace_add("write", _sync_temp)

    # ── Live speed slider → cost savings sync (FIX 5) ────────
    # The Cost Savings card in the right panel updates LIVE as the speed slider moves.
    # It uses a simplified formula (not the full engine) to estimate costs from speed alone.
    # This gives instant feedback without requiring the user to click "Calculate".
    def _sync_cost_live(*_):
        """Called when speed changes — updates the cost savings card live (no full calculation needed)."""
        try:
            spd = float(input_panel.speed_var.get())   # Read the current speed value
            advisor.update_cost_live(spd)              # Update cost card with simplified estimate
        except Exception:
            pass   # If anything fails (e.g., slider not ready yet), silently ignore

    input_panel.speed_var.trace_add("write", _sync_cost_live)

    # ── Initialize display once widgets are rendered ──────────
    # We wait 120ms after startup (using root.after) before updating the stat cards.
    # This is because tkinter needs to finish drawing the window before we can write to labels.
    # Without this delay, the labels might not exist yet when we try to update them.
    def _init_display():
        """Run once after window loads to show initial slider values in all stat cards."""
        _sync_speed()       # Set the SPEED card to the slider's starting value (40 km/h)
        _sync_battery()     # Set the BATTERY card to the slider's starting value (80%)
        _sync_temp()        # Set the TEMPERATURE card to the slider's starting value (25°C)
        _sync_cost_live()   # Set the cost savings card to the starting speed estimate

    root.after(120, _init_display)   # Schedule _init_display to run 120ms after the window opens


def main() -> None:
    """
    Application entry point.
    Creates the Tkinter root window, builds the UI, and starts the event loop.
    
    root.mainloop() is what keeps the window open and responsive —
    it continuously listens for user events (clicks, drags, key presses)
    and calls the right functions when events happen.
    """
    root = tk.Tk()    # Create the main application window
    build_ui(root)    # Build all panels and wire all callbacks
    root.mainloop()   # Start the event loop — this blocks until the window is closed


# ── Standard Python entry guard ──────────────────────────────
# This means: only run main() if THIS file is run directly (python main.py)
# If another file imports main.py, main() will NOT be called automatically.
if __name__ == "__main__":
    main()
