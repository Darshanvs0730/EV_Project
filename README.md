# 🛵 EV Scooter Range Estimator & Smart Telemetry Dashboard

An interactive, high-fidelity desktop dashboard application built with **Python 3.10+** using **Tkinter** and **Matplotlib**. It serves as an EV range estimator and smart telemetry system tailored for Indian riding conditions, temperatures, traffic profiles, and road characteristics.

---

## 🚀 Features

### 1. Range Estimation Engine
- **Base Range Calculation**: 4 km per 1% battery capacity (400 km max at 100% health).
- **Dynamic Adjustments**: Multipliers account for:
  - **Speed**: Stop-go speed inefficiencies vs. optimal cruising speeds.
  - **Riding Modes**: Eco (1.15x range), Normal (1.00x), and Sport (0.82x).
  - **Traffic Profiles**: City (20% penalty), Highway (no penalty), Delivery (28% penalty), and Rural (10% penalty).
  - **Passenger & Luggage Payload**: Real-time load calculations for rider, luggage, and pillion passenger.
  - **Road Conditions**: Smooth, potholed, hilly, or wet roads.
  - **Battery Degradation & Wear**: Accounts for overall health percentage and battery charge cycles.

### 2. Live Telemetry & Gauges
- **Speed, Battery, and Temperature Displays**: Clear gauges tracking input states.
- **Regenerative Braking Bonus**: Shows recovered range (`+X.X km` and `+X%` charge) when riding in city traffic or delivery modes.
- **Thermal Alert Banner**: Displays thermal throttling warnings if the climate exceeds 35°C–40°C, or cold warnings below 10°C.
- **Battery Remaining Useful Life (RUL)**: Dynamically evaluates and displays the battery's health status and remaining useful cycles.

### 3. Interactive Advisor & Eco-Assistant
- **Range Anxiety Ring**: A Matplotlib-rendered ring gauge (green → yellow → orange → red) that dynamically reflects range anxiety score based on current battery levels, road types, payloads, and temperature.
- **Destination Check**: Checks if the vehicle can reach a target destination distance. If not, it calculates and recommends an **optimal cruising speed** to ensure you reach the destination safely.
- **Cost Savings Calculator**: Evaluates monthly and yearly savings compared to an equivalent petrol scooter, along with monthly CO₂ savings in kilograms.
- **Smart Eco Tips**: Real-time contextual tips based on the active inputs (e.g., advising eco mode during city traffic to maximize regen).

---

## 🎨 UI Design System

The application conforms to a strict, cyberpunk-inspired, monospace dark dashboard theme:
- **Background**: Pure Dark (`#0A0A0F`)
- **Accent**: Electric Cyan (`#00F5FF`) for live readouts and active elements
- **Status Colors**: 
  - 🟢 **Safe**: Neon Green (`#00FF88`)
  - 🟡 **Warning**: Neon Amber (`#FFB800`)
  - 🔴 **Danger**: Neon Red (`#FF3B3B`)
- **Typography**: Monospace layout fonts (`Consolas`, `Courier New`) to resemble active EV terminal readouts.
- **Visuals**: Unicode symbol badges (🛵, ⚡, 🌡️, ✅, ❌) and embedded Matplotlib canvas charts for a clean, zero-asset-dependency configuration.

---

## 📂 Project Structure

```
.
├── README.md                 # This file
├── .gitignore                # Git exclusions (pycache, env, etc.)
├── ev_dashboard_spec.md      # Detailed specification document
├── ev_dashboard/
│   ├── main.py               # Main Tkinter application entry point
│   ├── core/
│   │   ├── __init__.py
│   │   ├── engine.py         # Range calculation logic
│   │   └── constants.py      # Multipliers, multipliers, and thresholds
│   └── ui/
│       ├── __init__.py
│       ├── dashboard.py      # Core dashboard layout frame
│       ├── input_panel.py    # Left-hand user input controls
│       ├── telemetry.py      # Center-hand gauges and alerts
│       ├── advisor.py        # Right-hand assistant, anxiety ring, and savings calculator
│       └── widgets.py        # Reusable gauge, meter, and progress UI elements
```

---

## 🛠️ Tech Stack & Dependencies

- **Python 3.10+**
- **Tkinter** & **ttk** (Python standard library)
- **Matplotlib** (Used for telemetry rendering)

---

## ⚙️ Installation & Running

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/Darshanvs0730/EV_Project.git
   cd EV_Project
   ```

2. **Install Dependencies**:
   ```bash
   pip install matplotlib
   ```

3. **Run the Application**:
   ```bash
   python ev_dashboard/main.py
   ```
