#!/usr/bin/env python3
"""
analysis.py - Statistical analysis of shock absorber durability test data.

Usage:
    python python/analysis.py [--csv data/sample_data.csv] [--window 1000]
"""

import argparse
import os
import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec

# ── CLI ────────────────────────────────────────────────────────────────────
parser = argparse.ArgumentParser(description="Shock absorber durability analysis")
parser.add_argument("--csv",    default="data/sample_data.csv", help="Input CSV path")
parser.add_argument("--window", type=int, default=1000,         help="Rolling window (rows)")
args = parser.parse_args()

CSV_PATH = args.csv
WINDOW   = args.window

# ── Load data ──────────────────────────────────────────────────────────────
print(f"Loading data from: {CSV_PATH}")
if not os.path.exists(CSV_PATH):
    sys.exit(f"ERROR: file not found → {CSV_PATH}")

df = pd.read_csv(CSV_PATH)
print(f"  Rows loaded : {len(df):,}")
print(f"  Columns     : {list(df.columns)}")

# ── Derived metrics ────────────────────────────────────────────────────────
# Vibration magnitude (g-units, 16384 LSB/g for ±2 g range)
LSB_PER_G = 16384.0
df["Ax_g"] = df["Ax"] / LSB_PER_G
df["Ay_g"] = df["Ay"] / LSB_PER_G
df["Az_g"] = df["Az"] / LSB_PER_G
df["Vmag"]  = np.sqrt(df["Ax_g"]**2 + df["Ay_g"]**2 + df["Az_g"]**2)

# Rolling RMS on Az
df["RMS_Az"] = (
    df["Az_g"]
    .rolling(window=WINDOW, min_periods=1)
    .apply(lambda x: np.sqrt(np.mean(x**2)), raw=True)
)

# Rolling mean force
df["Force_roll"] = df["Force_kg"].rolling(window=WINDOW, min_periods=1).mean()

# ── Global statistics ──────────────────────────────────────────────────────
print("\n── Force Statistics ──────────────────────────────────────────────")
print(df["Force_kg"].describe().to_string())

print("\n── Vibration Az (g) Statistics ───────────────────────────────────")
print(df["Az_g"].describe().to_string())

# ── Baseline vs final comparison ───────────────────────────────────────────
n_base  = WINDOW
n_final = WINDOW
baseline = df.head(n_base)
final    = df.tail(n_final)

base_force   = baseline["Force_kg"].mean()
final_force  = final["Force_kg"].mean()
force_loss   = (base_force - final_force) / base_force * 100

base_rms     = np.sqrt(np.mean(baseline["Az_g"]**2))
final_rms    = np.sqrt(np.mean(final["Az_g"]**2))
rms_increase = (final_rms - base_rms) / base_rms * 100

print("\n── Degradation Summary ───────────────────────────────────────────")
print(f"  Baseline Force : {base_force:.2f} kg")
print(f"  Final Force    : {final_force:.2f} kg")
print(f"  Force Reduction: {force_loss:.1f}%   {'⚠ FAULT' if force_loss > 20 else 'OK'}")
print()
print(f"  Baseline RMS Az: {base_rms:.4f} g")
print(f"  Final RMS Az   : {final_rms:.4f} g")
print(f"  RMS Increase   : {rms_increase:.1f}%   {'⚠ FAULT' if rms_increase > 30 else 'OK'}")

total_cycles = df["Cycle"].max()
duration_h   = df["Time_ms"].max() / 3_600_000
print(f"\n  Total Cycles   : {total_cycles:,}")
print(f"  Test Duration  : {duration_h:.2f} h")

# ── Cycle-level aggregation ────────────────────────────────────────────────
cycle_stats = df.groupby("Cycle").agg(
    Force_mean=("Force_kg", "mean"),
    Force_std =("Force_kg", "std"),
    RMS_Az    =("Az_g",     lambda x: np.sqrt(np.mean(x**2))),
    Vmag_mean =("Vmag",     "mean"),
).reset_index()

# ── Plotting ───────────────────────────────────────────────────────────────
fig = plt.figure(figsize=(14, 10))
fig.suptitle("Shock Absorber Durability Test – Statistical Analysis", fontsize=14, fontweight="bold")
gs  = gridspec.GridSpec(3, 2, figure=fig, hspace=0.45, wspace=0.35)

# 1. Force over time
ax1 = fig.add_subplot(gs[0, :])
ax1.plot(df["Time_ms"] / 60000, df["Force_roll"], color="#1f77b4", lw=1.5, label="Rolling mean force")
ax1.axhline(base_force * 0.80, color="red", ls="--", lw=1, label="−20% threshold")
ax1.set_xlabel("Time (min)")
ax1.set_ylabel("Force (kg)")
ax1.set_title("Force Degradation Over Test Duration")
ax1.legend(fontsize=9)
ax1.grid(True, alpha=0.3)

# 2. RMS vibration over time
ax2 = fig.add_subplot(gs[1, :])
ax2.plot(df["Time_ms"] / 60000, df["RMS_Az"], color="#ff7f0e", lw=1.2, label="Rolling RMS Az")
ax2.axhline(base_rms * 1.30, color="red", ls="--", lw=1, label="+30% threshold")
ax2.set_xlabel("Time (min)")
ax2.set_ylabel("RMS Az (g)")
ax2.set_title("Vibration RMS Trend")
ax2.legend(fontsize=9)
ax2.grid(True, alpha=0.3)

# 3. Force histogram
ax3 = fig.add_subplot(gs[2, 0])
ax3.hist(df["Force_kg"], bins=60, color="#2ca02c", edgecolor="white", alpha=0.8)
ax3.set_xlabel("Force (kg)")
ax3.set_ylabel("Count")
ax3.set_title("Force Distribution")
ax3.grid(True, alpha=0.3, axis="y")

# 4. Cycle-level RMS
ax4 = fig.add_subplot(gs[2, 1])
ax4.plot(cycle_stats["Cycle"], cycle_stats["RMS_Az"], color="#9467bd", lw=1, alpha=0.8)
ax4.set_xlabel("Cycle #")
ax4.set_ylabel("RMS Az (g)")
ax4.set_title("Per-Cycle Vibration RMS")
ax4.grid(True, alpha=0.3)

os.makedirs("results", exist_ok=True)
out = "results/force_trend.png"
plt.savefig(out, dpi=150, bbox_inches="tight")
print(f"\nPlot saved → {out}")
plt.show()
