# 🛵 EV Scooter Range Estimator & Smart Telemetry Dashboard
## Project Specification — Build From Scratch

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Language | Python 3.10+ |
| GUI Framework | Tkinter + ttk |
| Styling | Custom dark theme via tk.configure |
| Data | In-memory only (no database) |
| Charts | matplotlib embedded in Tkinter canvas |
| Dependencies | `matplotlib`, `tkinter` (stdlib) |

---

## Project Structure

```
ev_dashboard/
├── main.py               # App entry point, root window setup
├── core/
│   ├── __init__.py
│   ├── engine.py         # Range estimation engine (all calculation logic)
│   └── constants.py      # All constants, multipliers, thresholds
├── ui/
│   ├── __init__.py
│   ├── dashboard.py      # Main dashboard frame
│   ├── input_panel.py    # Left panel: all user inputs
│   ├── telemetry.py      # Center panel: live telemetry gauges
│   ├── advisor.py        # Right panel: eco assistant + anxiety score
│   └── widgets.py        # Reusable custom widgets (gauge, meter, badge)
└── assets/
    └── (no external assets required)
```

---

## Core Engine: `core/engine.py`

### `calculate_range(inputs: dict) -> dict`

Single function that takes all inputs and returns all computed outputs.

**Inputs dict keys:**
```
speed           float   km/h        (0–120)
battery         float   %           (0–100)
temperature     float   °C          (-5 to 50)
mode            str     Eco/Normal/Sport
traffic         str     City/Highway/Rural/Delivery
rider_weight    float   kg          (40–150)
pillion         bool    True/False
luggage         float   kg          (0–30)
road            str     Smooth/Pothole/Hilly/Wet
battery_health  float   %           (60–100)
charge_cycles   int     count       (0–1000)
destination_km  float   km          (0–200, optional)
```

**Output dict keys:**
```
base_range          float   km   — 4 km per 1% battery
speed_factor        float        — multiplier from speed
temp_factor         float        — multiplier from temperature
traffic_factor      float        — multiplier from traffic mode
load_factor         float        — multiplier from weight/pillion/luggage
road_factor         float        — multiplier from road condition
health_factor       float        — multiplier from battery health + cycles
mode_factor         float        — multiplier from riding mode
final_range         float   km   — product of all factors × base_range
regen_gain_pct      float   %    — energy recovered via regen braking
regen_range_bonus   float   km   — extra km from regen
effective_range     float   km   — final_range + regen_range_bonus
anxiety_score       int     0–100
anxiety_label       str     Low/Medium/High/Critical
can_reach           bool         — if destination_km provided
speed_suggestion    float   km/h — optimal speed to reach destination
monthly_ev_cost     float   ₹
monthly_petrol_cost float   ₹
monthly_savings     float   ₹
yearly_savings      float   ₹
co2_saved_kg        float   kg/month
eco_tips            list[str]    — 1 to 3 active suggestions
```

---

## Feature Specifications

### 1. Range Estimation Algorithm

**Base:** `base_range = (battery / 100) × 400` km

**Speed factor:**
- speed < 20: × 0.88 (stop-go inefficiency)
- 20 ≤ speed ≤ 45: × 1.00 (optimal)
- 45 < speed ≤ 60: × 0.92
- speed > 60: × 0.78

**Temperature factor:**
- temp < 10: × 0.80
- 10 ≤ temp < 25: × 0.92
- 25 ≤ temp ≤ 35: × 1.00
- 35 < temp ≤ 40: × 0.93
- temp > 40: × 0.85

**Mode factor:**
- Eco: × 1.15
- Normal: × 1.00
- Sport: × 0.82

**Traffic factor:**
- City: × 0.80
- Highway: × 1.00
- Delivery: × 0.72
- Rural: × 0.90

**Load factor:**
```python
total_load = rider_weight + (pillion × 65) + luggage
load_penalty = max(0, (total_load - 80) × 0.002)
load_factor = 1.0 - load_penalty  # floor at 0.65
```

**Road factor:**
- Smooth: × 1.00
- Pothole: × 0.88
- Hilly: × 0.82
- Wet: × 0.85

**Battery health factor:**
```python
cycle_penalty = charge_cycles × 0.00005
health_factor = (battery_health / 100) - cycle_penalty
# floor at 0.60
```

**Final range:**
```python
final_range = base_range × speed_factor × temp_factor × mode_factor
              × traffic_factor × load_factor × road_factor × health_factor
```

---

### 2. Regenerative Braking Efficiency

Only active when traffic = City or Delivery.

```python
if traffic in ["City", "Delivery"]:
    regen_gain_pct = 8 + (2 if mode == "Eco" else 0)   # 8–10%
    regen_range_bonus = final_range × (regen_gain_pct / 100)
else:
    regen_gain_pct = 0
    regen_range_bonus = 0

effective_range = final_range + regen_range_bonus
```

Display: animated fill bar, show `+X.X km` and `+X%` recovered.

---

### 3. Range Anxiety Score

```python
score = 0
if battery < 20: score += 35
elif battery < 40: score += 20
elif battery < 60: score += 10

if traffic == "City": score += 15
elif traffic == "Delivery": score += 20

if road in ["Pothole", "Hilly"]: score += 10

temp_extreme = abs(temperature - 30)
score += min(15, temp_extreme)

total_load = rider_weight + (pillion × 65) + luggage
if total_load > 120: score += 10
elif total_load > 100: score += 5

score = min(100, score)

if score < 30: label = "Low"
elif score < 55: label = "Medium"
elif score < 75: label = "High"
else: label = "Critical"
```

Display: color-coded ring gauge (green → yellow → orange → red).

---

### 4. Indian Traffic Simulation

Four traffic modes with distinct UX indicators:

| Mode | Range Impact | Regen | Visual Indicator |
|------|-------------|-------|-----------------|
| City Traffic | −20% | +8–10% | Yellow pulse |
| Highway Ride | 0% | 0% | Green steady |
| Delivery Mode | −28% | +10% | Orange pulse |
| Rural Roads | −10% | 0% | Blue steady |

---

### 5. Rider Load & Pillion System

Inputs:
- Rider weight slider: 40–150 kg
- Pillion checkbox (adds 65 kg default)
- Luggage slider: 0–30 kg
- Show total load in kg and penalty %

---

### 6. Indian Climate Heat Model

Temperature slider: −5 to 50°C

Visual alerts:
- temp > 40: "⚠️ Thermal Throttling Risk — range reduced significantly"
- temp > 35: "🌡️ High heat load detected"
- temp < 10: "❄️ Cold battery warning — reduced capacity"

---

### 7. Battery Health & Degradation

Inputs:
- Battery health %: slider 60–100
- Charge cycles: entry 0–1000

Display:
- Health bar with color (green ≥ 85, yellow ≥ 70, red < 70)
- Estimated remaining useful life: `(1000 - charge_cycles) / 1000 × 100`%
- Warning if health < 75 or cycles > 700

---

### 8. Road Condition Impact

Four road modes with range penalty display:
- Smooth Road: 0% penalty
- Pothole Roads: −12% range
- Hilly Terrain: −18% range
- Wet/Monsoon Roads: −15% range + safety alert

---

### 9. Smart Eco-Riding Assistant

Generates real-time tips based on current inputs. Rules:

```
speed > 60        → "Reduce speed below 60 km/h to save X km"
mode == "Sport"   → "Switch to Eco mode to gain ~15% range"
load > 130 kg     → "Heavy load detected — minimize luggage"
battery < 20%     → "Low battery — find charging within X km"
temp > 38         → "Park in shade when possible to cool battery"
road == "Pothole" → "Smooth road path saves ~12% range"
traffic == "City" and mode != "Eco" → "Eco mode maximizes regen braking gains"
```

Show max 3 active tips at once. Each tip shows exact km impact.

---

### 10. Destination Predictor

Input: destination distance (km)

```python
if destination_km <= effective_range:
    can_reach = True
    margin_km = effective_range - destination_km
else:
    can_reach = False
    shortfall_km = destination_km - effective_range
    # Suggest optimal speed
    for test_speed in range(20, 60):
        test_range = recalculate_with_speed(test_speed)
        if test_range >= destination_km:
            speed_suggestion = test_speed
            break
```

Display:
- ✅ Green: "You can reach! X km margin"
- ❌ Red: "Cannot reach. Short by X km. Ride at Y km/h to reach."

---

### 11. Cost Savings Calculator (India)

```python
# Assumptions (shown to user)
monthly_km = speed × 8 × 26           # 8hr/day, 26 days
ev_cost_per_km = 0.15                 # ₹0.15/km (electricity)
petrol_cost_per_km = 2.80             # ₹2.80/km (45 kmpl, ₹126/L)

monthly_ev_cost = monthly_km × ev_cost_per_km
monthly_petrol_cost = monthly_km × petrol_cost_per_km
monthly_savings = monthly_petrol_cost - monthly_ev_cost
yearly_savings = monthly_savings × 12
co2_saved_kg = monthly_km × 0.0021   # petrol CO₂ emission factor
```

Display in a styled card with ₹ amounts and CO₂ metric.

---

## UI Layout

```
┌─────────────────────────────────────────────────────────────────┐
│  🛵  EV SCOOTER TELEMETRY DASHBOARD          [CALCULATE]        │
├──────────────┬──────────────────────────┬───────────────────────┤
│  INPUT PANEL │    TELEMETRY GAUGES      │   ADVISOR PANEL       │
│              │                          │                       │
│ Speed        │  [Speed] [Battery] [Temp]│  Eco Tips             │
│ Battery      │                          │                       │
│ Temperature  │  Estimated Range: XXX km │  Anxiety Score Ring   │
│ Mode         │                          │                       │
│ Traffic      │  Regen Braking Meter     │  Destination Check    │
│ Road         │                          │                       │
│ Rider Weight │  Battery Health Bar      │  Cost Savings Card    │
│ Pillion      │                          │                       │
│ Luggage      │  Thermal Alert Banner    │                       │
│ Battery Hlth │                          │                       │
│ Charge Cycles│                          │                       │
│ Destination  │                          │                       │
└──────────────┴──────────────────────────┴───────────────────────┘
```

---

## UI Design Rules

- **Theme:** Pure dark (`#0A0A0F` background)
- **Accent:** Electric cyan (`#00F5FF`) for live values
- **Warning:** Neon amber (`#FFB800`)
- **Danger:** Neon red (`#FF3B3B`)
- **Safe:** Neon green (`#00FF88`)
- **Font:** `Courier New` or `Consolas` for numbers (monospace EV feel)
- **No images/icons from files** — use Unicode symbols only (🛵 ⚡ 🌡️ ✅ ❌)
- **Window size:** 1400 × 800 minimum, resizable
- **All inputs have labels showing current value live**
- **Calculate button triggers full recalculation — NO auto-update loops**
- Matplotlib canvas for regen bar and anxiety ring embedded in Tkinter

---

## Input Validation Rules

| Field | Rule |
|-------|------|
| Speed | 0–120 km/h, numeric only |
| Battery | 0–100%, numeric only |
| Temperature | −5 to 50°C |
| Rider weight | 40–150 kg |
| Luggage | 0–30 kg |
| Battery health | 60–100% |
| Charge cycles | 0–1000, integer |
| Destination | 0–200 km, optional |

On invalid: show inline red error label, block calculation.

---

## What NOT to Build

- No database, no file I/O, no SQLite
- No trip history / analytics (needs persistence)
- No live sensor simulation / animation loops
- No external API calls
- No threading
- No mobile layout
- No web server

---

## Dependency Install

```bash
pip install matplotlib
# tkinter is stdlib — no install needed
```

---

## Deliverable

Single command to run:
```bash
python main.py
```

All features work on first run. No setup beyond `pip install matplotlib`.