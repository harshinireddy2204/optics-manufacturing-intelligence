"""
Synthetic Data Generator for Coherent Optical Transceiver Manufacturing
========================================================================
Simulates realistic test data from a 800G/1.6T coherent pluggable optics
manufacturing line - modeled on what Cisco/Acacia's Optics Operations team
handles daily across DSP parametrics, optical alignment, burn-in, and final test.

Test parameters based on real coherent transceiver specifications:
- Optical output power (dBm)
- Receiver sensitivity (dBm)
- Bit Error Rate (pre-FEC BER)
- Extinction ratio (dB)
- OSNR (dB)
- Laser bias current (mA)
- Wavelength accuracy (nm offset from ITU grid)
- TDECQ (dB) - Transmitter Dispersion Eye Closure for PAM4
- Module power consumption (W)
- Insertion loss (dB)
- Eye diagram margin (%)
- DSP lock time (ms)

Manufacturing stations modeled:
1. Wafer-level chip test (DSP ASIC + PIC)
2. Optical alignment & coupling
3. Module-level parametric test
4. Burn-in (accelerated aging)
5. Final test & calibration
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import json
import os

np.random.seed(42)

# ── Configuration ──────────────────────────────────────────────────────────
NUM_MODULES = 12000  # ~3 months of production data
START_DATE = datetime(2025, 12, 1)
END_DATE = datetime(2026, 4, 30)

PRODUCT_LINES = {
    "800G-ZR-QSFP-DD": {"weight": 0.40, "gen": "Delphi", "form_factor": "QSFP-DD"},
    "800G-ZR+-OSFP": {"weight": 0.25, "gen": "Delphi", "form_factor": "OSFP"},
    "400G-ZR+-QSFP-DD": {"weight": 0.20, "gen": "Greylock", "form_factor": "QSFP-DD"},
    "1.6T-DR8-OSFP": {"weight": 0.15, "gen": "Kibo", "form_factor": "OSFP"},
}

MANUFACTURING_LINES = ["Line-A-Maynard", "Line-B-Maynard", "Line-C-Lowell"]
SHIFTS = ["Day", "Swing", "Night"]

# Spec limits based on real coherent transceiver parameters
SPEC_LIMITS = {
    "tx_optical_power_dBm":     {"LSL": -1.0,  "USL": 3.0,   "target": 1.0},
    "rx_sensitivity_dBm":       {"LSL": -22.0, "USL": -14.0, "target": -18.0},
    "pre_fec_ber":              {"LSL": 0,     "USL": 4.5e-3,"target": 1e-4},
    "extinction_ratio_dB":      {"LSL": 4.0,   "USL": 15.0,  "target": 8.5},
    "osnr_dB":                  {"LSL": 28.0,  "USL": 45.0,  "target": 36.0},
    "laser_bias_current_mA":    {"LSL": 15.0,  "USL": 80.0,  "target": 40.0},
    "wavelength_offset_pm":     {"LSL": -12.5, "USL": 12.5,  "target": 0.0},
    "tdecq_dB":                 {"LSL": 0.5,   "USL": 3.5,   "target": 2.0},
    "module_power_W":           {"LSL": 10.0,  "USL": 30.0,  "target": 20.0},
    "insertion_loss_dB":        {"LSL": 0.5,   "USL": 3.5,   "target": 1.8},
    "eye_margin_pct":           {"LSL": 15.0,  "USL": 95.0,  "target": 65.0},
    "dsp_lock_time_ms":         {"LSL": 5.0,   "USL": 500.0, "target": 80.0},
}

TEST_STATIONS = [
    "WaferTest", "OpticalAlignment", "ModuleParametric", "BurnIn", "FinalTest"
]


def generate_serial_numbers(n):
    """Generate realistic Acacia-style serial numbers."""
    serials = []
    for i in range(n):
        product_code = np.random.choice(["ACA", "DPH", "KBO", "GRL"])
        batch = f"{np.random.randint(1000, 9999)}"
        unit = f"{i:05d}"
        serials.append(f"{product_code}-{batch}-{unit}")
    return serials


def generate_test_data():
    """Generate comprehensive manufacturing test dataset."""
    records = []
    dates = pd.date_range(START_DATE, END_DATE, periods=NUM_MODULES)
    serials = generate_serial_numbers(NUM_MODULES)

    # Assign products by weight
    products = np.random.choice(
        list(PRODUCT_LINES.keys()),
        size=NUM_MODULES,
        p=[v["weight"] for v in PRODUCT_LINES.values()]
    )

    for i in range(NUM_MODULES):
        product = products[i]
        pinfo = PRODUCT_LINES[product]
        date = dates[i]
        serial = serials[i]
        line = np.random.choice(MANUFACTURING_LINES)
        shift = np.random.choice(SHIFTS)
        lot_id = f"LOT-{date.strftime('%y%m')}-{np.random.randint(100,999)}"

        # ── Introduce realistic process variations ──
        # Line-C-Lowell has slightly worse alignment (newer line, still ramping)
        line_offset = 0.15 if line == "Line-C-Lowell" else 0.0
        # Night shift has slightly more variability
        shift_var = 1.1 if shift == "Night" else 1.0
        # 1.6T products are harder to manufacture (lower yield)
        product_difficulty = 1.3 if "1.6T" in product else 1.0

        # ── Simulate a process drift starting mid-March (the kind of thing SPC catches) ──
        drift = 0.0
        if date >= pd.Timestamp("2026-03-15") and line == "Line-A-Maynard":
            days_since_drift = (date - pd.Timestamp("2026-03-15")).days
            drift = min(days_since_drift * 0.02, 0.5)  # Gradual optical power drift

        for station in TEST_STATIONS:
            # Station-specific pass rates
            station_noise = {
                "WaferTest": 0.7,
                "OpticalAlignment": 1.0,
                "ModuleParametric": 0.9,
                "BurnIn": 0.8,
                "FinalTest": 0.85,
            }[station]

            var_scale = station_noise * shift_var * product_difficulty

            record = {
                "serial_number": serial,
                "product_line": product,
                "dsp_generation": pinfo["gen"],
                "form_factor": pinfo["form_factor"],
                "manufacturing_line": line,
                "shift": shift,
                "lot_id": lot_id,
                "test_station": station,
                "test_datetime": date + timedelta(
                    hours=TEST_STATIONS.index(station) * 4 + np.random.uniform(-0.5, 0.5)
                ),
                # ── Test parameters ──
                "tx_optical_power_dBm": np.clip(
                    np.random.normal(1.0 + drift + line_offset * 0.3, 0.4 * var_scale),
                    -3, 5
                ),
                "rx_sensitivity_dBm": np.random.normal(-18.0 - line_offset, 1.2 * var_scale),
                "pre_fec_ber": np.abs(np.random.lognormal(-9.2, 1.5 * var_scale)) * 1e-1,
                "extinction_ratio_dB": np.random.normal(8.5, 0.8 * var_scale),
                "osnr_dB": np.random.normal(36.0 - line_offset * 2, 2.0 * var_scale),
                "laser_bias_current_mA": np.random.normal(40.0 + line_offset * 5, 5.0 * var_scale),
                "wavelength_offset_pm": np.random.normal(0.0 + drift * 2, 2.0 * var_scale),
                "tdecq_dB": np.random.normal(2.0 + line_offset * 0.2, 0.3 * var_scale),
                "module_power_W": np.random.normal(
                    20.0 + (5 if "1.6T" in product else 0), 2.0 * var_scale
                ),
                "insertion_loss_dB": np.random.normal(1.8 + line_offset * 0.3, 0.3 * var_scale),
                "eye_margin_pct": np.random.normal(65.0 - line_offset * 5, 8.0 * var_scale),
                "dsp_lock_time_ms": np.abs(np.random.normal(80.0 + line_offset * 20, 30.0 * var_scale)),
            }

            # Clip BER to realistic range
            record["pre_fec_ber"] = np.clip(record["pre_fec_ber"], 1e-15, 1e-1)

            records.append(record)

    df = pd.DataFrame(records)

    # ── Introduce data quality issues (the hygiene problems the role must fix) ──
    n = len(df)
    # 1. Missing values (~2% of records have some nulls)
    for col in ["tx_optical_power_dBm", "osnr_dB", "wavelength_offset_pm", "eye_margin_pct"]:
        mask = np.random.random(n) < 0.02
        df.loc[mask, col] = np.nan

    # 2. Duplicate records (~0.5%)
    dup_idx = np.random.choice(n, size=int(n * 0.005), replace=False)
    dups = df.iloc[dup_idx].copy()
    # Slightly different timestamps (the kind of duplicate from double-logging)
    dups["test_datetime"] = dups["test_datetime"] + pd.Timedelta(seconds=3)
    df = pd.concat([df, dups], ignore_index=True)

    # 3. Malformed serial numbers (~0.3%)
    bad_idx = np.random.choice(len(df), size=int(len(df) * 0.003), replace=False)
    for idx in bad_idx:
        corruption = np.random.choice(["missing_dash", "extra_char", "lowercase"])
        sn = df.at[idx, "serial_number"]
        if corruption == "missing_dash":
            df.at[idx, "serial_number"] = sn.replace("-", "", 1)
        elif corruption == "extra_char":
            df.at[idx, "serial_number"] = sn + "X"
        else:
            df.at[idx, "serial_number"] = sn.lower()

    # 4. Inconsistent product line names (~0.2%)
    bad_product_idx = np.random.choice(len(df), size=int(len(df) * 0.002), replace=False)
    for idx in bad_product_idx:
        p = df.at[idx, "product_line"]
        variants = {
            "800G-ZR-QSFP-DD": "800G_ZR_QSFPDD",
            "800G-ZR+-OSFP": "800G-ZR+ OSFP",
            "400G-ZR+-QSFP-DD": "400g-zr+-qsfp-dd",
            "1.6T-DR8-OSFP": "1600G-DR8-OSFP",
        }
        df.at[idx, "product_line"] = variants.get(p, p)

    # 5. Out-of-range values (sensor glitches ~0.1%)
    glitch_idx = np.random.choice(len(df), size=int(len(df) * 0.001), replace=False)
    df.loc[glitch_idx, "tx_optical_power_dBm"] = np.random.choice([99.9, -99.9, 0.0], size=len(glitch_idx))

    return df


def generate_equipment_registry():
    """Generate test equipment metadata for cross-system reconciliation."""
    equipment = []
    eq_id = 1000
    for line in MANUFACTURING_LINES:
        for station in TEST_STATIONS:
            for unit in range(1, np.random.randint(2, 5)):
                equipment.append({
                    "equipment_id": f"EQ-{eq_id}",
                    "equipment_type": f"{station}_Unit_{unit}",
                    "manufacturing_line": line,
                    "test_station": station,
                    "last_calibration": (datetime.now() - timedelta(days=np.random.randint(1, 180))).strftime("%Y-%m-%d"),
                    "calibration_due": (datetime.now() + timedelta(days=np.random.randint(1, 180))).strftime("%Y-%m-%d"),
                    "status": np.random.choice(["Active", "Active", "Active", "Needs Calibration", "Down for Maintenance"]),
                    "firmware_version": f"v{np.random.randint(2,5)}.{np.random.randint(0,9)}.{np.random.randint(0,20)}",
                })
                eq_id += 1
    return pd.DataFrame(equipment)


def generate_yield_targets():
    """Generate yield targets by product line and station."""
    targets = []
    for product in PRODUCT_LINES:
        for station in TEST_STATIONS:
            base_target = 0.98 if "400G" in product else (0.95 if "800G" in product else 0.90)
            station_adj = {"WaferTest": 0.0, "OpticalAlignment": -0.02, "ModuleParametric": -0.01,
                          "BurnIn": -0.005, "FinalTest": -0.01}[station]
            targets.append({
                "product_line": product,
                "test_station": station,
                "yield_target_pct": round((base_target + station_adj) * 100, 1),
                "cpk_target": 1.33,
            })
    return pd.DataFrame(targets)


if __name__ == "__main__":
    out_dir = os.path.dirname(os.path.abspath(__file__))

    print("Generating test data...")
    df_test = generate_test_data()
    df_test.to_csv(os.path.join(out_dir, "optics_test_data.csv"), index=False)
    print(f"  → {len(df_test)} test records generated")

    print("Generating equipment registry...")
    df_equip = generate_equipment_registry()
    df_equip.to_csv(os.path.join(out_dir, "equipment_registry.csv"), index=False)
    print(f"  → {len(df_equip)} equipment records")

    print("Generating yield targets...")
    df_targets = generate_yield_targets()
    df_targets.to_csv(os.path.join(out_dir, "yield_targets.csv"), index=False)
    print(f"  → {len(df_targets)} yield target records")

    # Save spec limits as JSON
    with open(os.path.join(out_dir, "spec_limits.json"), "w") as f:
        json.dump(SPEC_LIMITS, f, indent=2)
    print("  → Spec limits saved")

    print("\n✅ All data generated successfully!")