# ============================================================
# EV Dashboard — Core Calculation Engine
# ============================================================
# This is the BRAIN of the application — pure math, no GUI here.
#
# The function calculate_range() takes all the user's inputs
# (speed, battery %, temperature, riding mode, load, etc.)
# and returns a dictionary of calculated results
# (estimated range, anxiety score, cost savings, eco tips, etc.)
#
# Why keep this separate from the UI?
# → So the math can be tested independently without opening any window.
# → Clean separation: UI files handle display, this file handles logic.
# ============================================================


def calculate_range(inputs: dict) -> dict:
    """
    Calculate EV scooter estimated range and all derived metrics.

    Parameters (what goes IN as 'inputs' dict)
    ----------
    speed          : float  — current riding speed in km/h
    battery        : float  — current battery level in % (0–100)
    temperature    : float  — ambient temperature in °C
    mode           : str    — riding mode: "Eco" | "Normal" | "Sport"
    traffic        : str    — traffic pattern: "City" | "Highway" | "Delivery" | "Rural"
    rider_weight   : float  — rider's body weight in kg
    pillion        : bool   — True if a second person (pillion passenger) is on the scooter
    luggage        : float  — extra luggage weight in kg
    road           : str    — road surface: "Smooth" | "Pothole" | "Hilly" | "Wet"
    battery_health : float  — battery health % (degrades over time and charge cycles)
    charge_cycles  : int    — number of times battery has been fully charged (0–1000)
    destination_km : float | None — destination distance in km (None = no destination set)

    Returns (what comes OUT as a dict)
    -------
    A dictionary with all calculated output values described below.
    """

    # ── Step 1: Extract all inputs from the dictionary ───────
    # We pull each value out of the 'inputs' dict and convert to the right data type.
    # float() converts strings/ints to decimal numbers.
    # int() converts to whole numbers.
    # bool() converts to True/False.
    speed        = float(inputs["speed"])           # e.g., 40.0 km/h
    battery      = float(inputs["battery"])         # e.g., 80.0 %
    temperature  = float(inputs["temperature"])     # e.g., 25.0 °C
    mode         = inputs["mode"]                   # e.g., "Normal"
    traffic      = inputs["traffic"]                # e.g., "City"
    rider_weight = float(inputs["rider_weight"])    # e.g., 70.0 kg
    pillion      = bool(inputs["pillion"])          # e.g., False
    luggage      = float(inputs["luggage"])         # e.g., 0.0 kg
    road         = inputs["road"]                   # e.g., "Smooth"
    battery_health = float(inputs["battery_health"])  # e.g., 90.0 %
    charge_cycles  = int(inputs["charge_cycles"])     # e.g., 100
    # .get() is used here because destination_km is optional — returns None if not provided
    destination_km = inputs.get("destination_km")  # e.g., 50.0 km, or None

    # ============================================================
    # RANGE CALCULATION LOGIC
    # The final range is calculated by multiplying a BASE RANGE
    # by several FACTORS (each between 0 and 1, or slightly above 1).
    # Each factor represents how much one condition affects the range.
    # Example: if everything is perfect, all factors = 1.0
    #          if the battery is old (health=60%), health_factor ≈ 0.60
    # ============================================================

    # ── Step 2: Base Range ────────────────────────────────────
    # This is the theoretical maximum range if conditions were perfect.
    # Formula: each 1% battery = 4 km of range (so 100% battery = 400 km MAX)
    # Reality: this gets reduced by all the factors below.
    base_range = (battery / 100) * 400   # e.g., 80% battery → 320 km base range

    # ── Step 3: Speed Factor ─────────────────────────────────
    # Speed affects efficiency:
    #   Too slow (city crawl < 20 km/h) → inefficient (lots of stop-start) → 0.88 (12% range loss)
    #   Sweet spot (20–45 km/h) → most efficient for a scooter → 1.00 (no loss)
    #   Fast (45–60 km/h) → slight drag increase → 0.92 (8% range loss)
    #   Very fast (> 60 km/h) → high air resistance, motor working hard → 0.78 (22% range loss)
    if speed < 20:
        speed_factor = 0.88    # Slow city traffic — inefficient stop-start driving
    elif speed <= 45:
        speed_factor = 1.00    # Optimal speed range for EV scooters
    elif speed <= 60:
        speed_factor = 0.92    # Slightly faster — small drag penalty
    else:
        speed_factor = 0.78    # Highway speeds — significant aerodynamic drag

    # ── Step 4: Temperature Factor ───────────────────────────
    # Battery chemistry is sensitive to temperature:
    #   Very cold (< 10°C) → battery doesn't deliver full power → 0.80 (20% range loss)
    #   Cool (10–25°C) → below-optimal, slight loss → 0.92
    #   Warm (25–35°C) → ideal operating range for lithium batteries → 1.00
    #   Hot (35–40°C) → slight efficiency drop due to thermal protection → 0.93
    #   Very hot (> 40°C) → battery management throttles output → 0.85 (15% loss)
    if temperature < 10:
        temp_factor = 0.80     # Cold weather — lithium batteries lose capacity in cold
    elif temperature < 25:
        temp_factor = 0.92     # Cool weather — slightly below optimal
    elif temperature <= 35:
        temp_factor = 1.00     # Sweet spot — ideal battery temperature
    elif temperature <= 40:
        temp_factor = 0.93     # Getting hot — slight thermal management penalty
    else:
        temp_factor = 0.85     # Overheating risk — battery management limits power

    # ── Step 5: Mode Factor ───────────────────────────────────
    # The riding mode directly controls how aggressively the motor uses power:
    #   Eco:    Limits top speed and acceleration → saves energy → +15% range
    #   Normal: Standard mode → no adjustment → 1.00
    #   Sport:  Maximum power, sharp acceleration → drains battery faster → -18% range
    # dict lookup: {"Eco": 1.15, ...}["Normal"] → returns 1.00
    mode_factor = {"Eco": 1.15, "Normal": 1.00, "Sport": 0.82}[mode]

    # ── Step 6: Traffic Factor ────────────────────────────────
    # How the traffic pattern affects energy consumption:
    #   City:     Lots of braking and acceleration → -20% range (BUT regen braking helps)
    #   Highway:  Steady cruising → most efficient → 1.00
    #   Delivery: Constant stopping and starting at many stops → worst case → -28% range
    #   Rural:    Mostly open roads, some variation → -10% range
    traffic_factor = {
        "City":     0.80,   # Urban stop-and-go traffic
        "Highway":  1.00,   # Open highway — steady speed, best efficiency
        "Delivery": 0.72,   # Package delivery — worst case (constant stops)
        "Rural":    0.90,   # Village/rural roads — moderate efficiency
    }[traffic]

    # ── Step 7: Load Factor ───────────────────────────────────
    # Heavier total weight = more energy needed to accelerate and climb hills.
    # total_load = rider weight + pillion (65 kg if present) + luggage
    total_load = rider_weight + (65 if pillion else 0) + luggage

    # Penalty kicks in only when load exceeds 80 kg (typical single rider)
    # Every kg above 80 adds 0.2% range loss
    # max(0, ...) ensures penalty is never negative (no bonus for being light)
    load_penalty = max(0, (total_load - 80) * 0.002)

    # Clamp at 0.65 — even worst case (very heavy load) never drops below 65% efficiency
    load_factor = max(0.65, 1.0 - load_penalty)

    # ── Step 8: Road Factor ───────────────────────────────────
    # Road surface determines rolling resistance and stability losses:
    #   Smooth:  New tarmac → no loss → 1.00
    #   Pothole: Rough roads → motor works harder to maintain speed → -12% range
    #   Hilly:   Uphill sections drain battery fast → -18% range
    #   Wet:     Water increases rolling resistance, need cautious throttle → -15% range
    road_factor = {
        "Smooth":  1.00,   # Perfect road surface
        "Pothole": 0.88,   # Rough/damaged road surface
        "Hilly":   0.82,   # Hills — climbing uses significantly more energy
        "Wet":     0.85,   # Wet roads — resistance and safety throttling
    }[road]

    # ── Step 9: Battery Health Factor ────────────────────────
    # Battery health degrades over time (measured in charge cycles).
    # A battery with 90% health can only deliver 90% of its rated capacity.
    #
    # cycle_penalty: each full charge cycle degrades the battery slightly
    #   (0.005% per cycle → 100 cycles = 0.5% extra loss on top of the health %)
    # max(0.60, ...) — even a very old battery retains at least 60% of its capacity
    cycle_penalty = charge_cycles * 0.00005   # Very small penalty per cycle
    health_factor = max(0.60, (battery_health / 100) - cycle_penalty)

    # ── Step 10: Final Range (multiply all factors together) ─
    # This is the KEY formula — all seven factors multiplied together.
    # Example: 320 km base × 1.00 speed × 1.00 temp × 1.00 mode × 0.80 city
    #          × 0.98 load × 1.00 road × 0.90 health = 225.9 km
    final_range = (
        base_range
        * speed_factor
        * temp_factor
        * mode_factor
        * traffic_factor
        * load_factor
        * road_factor
        * health_factor
    )

    # ── Step 11: Regenerative Braking Bonus ──────────────────
    # Regenerative braking means the motor acts as a generator when braking,
    # sending electricity BACK into the battery instead of wasting it as heat.
    # This ONLY applies in City or Delivery traffic (lots of braking opportunities).
    # Highway/Rural = few braking events → no meaningful regen gain.
    #
    # Eco mode: 10% range bonus from regen (Eco mode optimises regen capture)
    # Normal/Sport: 8% range bonus
    if traffic in ["City", "Delivery"]:
        regen_gain_pct    = 10 if mode == "Eco" else 8   # % of range recovered via regen
        regen_range_bonus = final_range * (regen_gain_pct / 100)   # km added back
    else:
        regen_gain_pct    = 0     # No regen benefit on Highway/Rural
        regen_range_bonus = 0.0

    # Effective range = calculated range + any regenerative braking bonus
    effective_range = final_range + regen_range_bonus

    # ── Step 12: Range Anxiety Score (0–100) ─────────────────
    # This is a custom "stress score" that tells you HOW WORRIED to be about range.
    # Score 0 = no worries | Score 100 = critical anxiety (likely to get stranded)
    #
    # Points are ADDED based on risk factors:
    #   Low battery contributes the most (up to 35 points)
    #   City/Delivery traffic adds points (more uncertainty about range)
    #   Bad roads add points
    #   Extreme temperature adds points (hotter/colder = less predictable range)
    #   Heavy load adds points
    score = 0

    # Battery level contribution (biggest driver of anxiety)
    if battery < 20:
        score += 35   # Critical — battery critically low, could strand you
    elif battery < 40:
        score += 20   # Low — should charge soon
    elif battery < 60:
        score += 10   # Medium — worth keeping an eye on

    # Traffic contribution (unpredictable range in heavy stop-start traffic)
    if traffic == "City":
        score += 15   # City traffic is unpredictable
    elif traffic == "Delivery":
        score += 20   # Delivery is worst — constant stops drain battery unevenly

    # Road surface contribution (rough/hilly = harder to predict exact drain)
    if road in ["Pothole", "Hilly"]:
        score += 10

    # Temperature contribution (both extremes reduce battery performance)
    # abs(temperature - 30) = how many degrees away from the ideal 30°C
    # min(15, ...) caps this at 15 points maximum
    score += min(15, abs(temperature - 30))

    # Load contribution (heavier = more uncertain range)
    if total_load > 120:
        score += 10   # Very heavy — two people + luggage
    elif total_load > 100:
        score += 5    # Moderately heavy

    # Cap score at 100 maximum
    score = min(100, score)

    # Convert score to a human-readable label
    anxiety_label = (
        "Low"      if score < 30 else   # Green zone — no worries
        "Medium"   if score < 55 else   # Amber zone — stay aware
        "High"     if score < 75 else   # Orange zone — take precautions
        "Critical"                      # Red zone — charge immediately
    )

    # ── Step 13: Destination Reachability Check ───────────────
    # If the user entered a destination distance, check if the scooter can reach it.
    # All set to None by default — only populated if destination_km was provided.
    can_reach        = None   # True = can reach, False = cannot reach, None = not checked
    speed_suggestion = None   # If cannot reach, suggest a lower speed that would work
    shortfall_km     = None   # How many km short of the destination
    margin_km        = None   # How many km of extra range beyond the destination

    if destination_km is not None and destination_km > 0:
        if effective_range >= destination_km:
            # Can reach! Calculate how much range is left over after reaching destination.
            can_reach = True
            margin_km = effective_range - destination_km   # Extra km beyond destination
        else:
            # Cannot reach at current settings.
            can_reach    = False
            shortfall_km = destination_km - effective_range   # How many km short

            # Try to find a lower speed that WOULD allow reaching the destination.
            # We test speeds from 20 km/h up to 64 km/h.
            # If we find a speed where the range is >= destination, suggest it.
            for test_speed in range(20, 65):
                s = test_speed
                # Recalculate speed factor for this test speed
                sf = (
                    0.88 if s < 20 else
                    1.00 if s <= 45 else
                    0.92 if s <= 60 else
                    0.78
                )
                # Recalculate range with this test speed (all other factors stay the same)
                tr = (
                    base_range * sf * temp_factor * mode_factor
                    * traffic_factor * load_factor * road_factor * health_factor
                )
                # Add regen bonus if applicable
                regen_b = tr * 0.08 if traffic in ["City", "Delivery"] else 0
                if (tr + regen_b) >= destination_km:
                    speed_suggestion = test_speed   # Found the minimum speed that works
                    break   # Stop testing — we found the answer

    # ── Step 14: Cost Savings vs Petrol ──────────────────────
    # Compare what it costs to ride the EV vs a petrol scooter.
    # Assumptions:
    #   8 hours of riding per day (typical delivery/commute worker)
    #   26 working days per month
    #   EV electricity cost: ₹0.15 per km
    #   Petrol cost: ₹2.80 per km (fuel + servicing combined)
    monthly_km          = speed * 8 * 26           # Total km ridden per month
    monthly_ev_cost     = monthly_km * 0.15        # Cost to run EV for that distance
    monthly_petrol_cost = monthly_km * 2.80        # Cost to run petrol scooter same distance
    monthly_savings     = monthly_petrol_cost - monthly_ev_cost   # How much saved per month
    yearly_savings      = monthly_savings * 12     # Annualised savings
    co2_saved_kg        = monthly_km * 0.0021      # CO₂ not emitted vs petrol (kg per km)

    # ── Step 15: Eco Tips ─────────────────────────────────────
    # Generate actionable tips based on the user's current settings.
    # Only include tips that are actually relevant (use if conditions).
    # Maximum 3 tips are shown at once (eco_tips[:3]).
    eco_tips = []

    if speed > 60:
        # Calculate how much range is WASTED by going above 60 km/h
        saved = round((final_range * (1 - 0.78 / speed_factor)), 1)
        eco_tips.append(f"Reduce speed below 60 km/h → save ~{saved} km")

    if mode == "Sport":
        eco_tips.append("Switch to Eco mode → gain ~18% more range")

    if total_load > 130:
        eco_tips.append("Heavy load detected → reduce luggage for better range")

    if battery < 20:
        # Urgent tip — tell user to find charging before the battery dies
        eco_tips.append(
            f"⚠ Low battery — find charging within "
            f"{round(effective_range * 0.8)} km"   # 80% of range as safe buffer
        )

    if temperature > 38:
        eco_tips.append(
            "Park in shade to cool battery and recover ~5% capacity"
        )

    if road == "Pothole":
        eco_tips.append("Smooth route saves ~12% range")

    if traffic == "City" and mode != "Eco":
        eco_tips.append(
            "Eco mode maximizes regen braking — extra gains in city traffic"
        )

    # Keep only the top 3 most relevant tips
    eco_tips = eco_tips[:3]

    # ── Step 16: Return all calculated results ────────────────
    # Everything the UI needs is packed into this dictionary.
    # The UI panels read from this dict to display values.
    return {
        # ── Range breakdown ──────────────────────────────────
        "base_range":         round(base_range, 1),          # Theoretical max range from battery %
        "final_range":        round(final_range, 1),         # Range after all factors applied
        "regen_gain_pct":     regen_gain_pct,                # % bonus from regenerative braking
        "regen_range_bonus":  round(regen_range_bonus, 1),   # Extra km from regen braking
        "effective_range":    round(effective_range, 1),     # FINAL ANSWER: range including regen

        # ── Individual factors (shown as badges in UI) ───────
        "speed_factor":       round(speed_factor, 2),        # Effect of speed on range
        "temp_factor":        round(temp_factor, 2),         # Effect of temperature on range
        "mode_factor":        round(mode_factor, 2),         # Effect of riding mode
        "traffic_factor":     round(traffic_factor, 2),      # Effect of traffic pattern
        "load_factor":        round(load_factor, 2),         # Effect of total weight
        "road_factor":        round(road_factor, 2),         # Effect of road surface
        "health_factor":      round(health_factor, 2),       # Effect of battery age/health

        # ── Load summary ─────────────────────────────────────
        "total_load":         round(total_load, 1),          # Total weight in kg (rider+pillion+luggage)

        # ── Anxiety score ────────────────────────────────────
        "anxiety_score":      score,                         # 0–100 score (shown on semicircle gauge)
        "anxiety_label":      anxiety_label,                 # "Low" / "Medium" / "High" / "Critical"

        # ── Destination check ────────────────────────────────
        "can_reach":          can_reach,                     # True/False/None
        "margin_km":          round(margin_km, 1) if margin_km is not None else None,
        "shortfall_km":       round(shortfall_km, 1) if shortfall_km is not None else None,
        "speed_suggestion":   speed_suggestion,              # Suggested lower speed to reach destination

        # ── Cost savings ─────────────────────────────────────
        "monthly_ev_cost":    round(monthly_ev_cost),        # ₹ EV cost per month
        "monthly_petrol_cost": round(monthly_petrol_cost),  # ₹ Petrol cost per month
        "monthly_savings":    round(monthly_savings),        # ₹ Saved per month vs petrol
        "yearly_savings":     round(yearly_savings),         # ₹ Saved per year vs petrol
        "co2_saved_kg":       round(co2_saved_kg, 1),        # kg of CO₂ not emitted per month

        # ── Eco tips ─────────────────────────────────────────
        "eco_tips":           eco_tips,                      # List of up to 3 actionable tips
    }
