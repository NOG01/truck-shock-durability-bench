#!/usr/bin/env python3
"""
fault_detection.py - Automatic failure detection for shock absorber durability test.

Detection criteria (from README):
  1. Force loss > 20% from baseline
  2. RMS vibration increase > 30% from baseline
  3. New spectral peaks (FFT) not present in initial data

Usage:
    python python/fault_detection.py [--csv data/sample_data.csv]
                                     [--baseline-cycles 500]
                                     [--rolling-window 200]
                                     [--report results/fault_report.txt]
"""

import argparse
import os
import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from scipy.signal import find_peaks

# ── CLI ────────────────────────────────────────────────────────────────────
parser = argparse.ArgumentParser(description="Fault detection for durability bench")
parser.add_argument("--csv",              default="data/sample_data.csv")
parser.add_argument("--baseline-cycles",  type=int,   default=500,
                    help="Number of initial cycles used to compute baseline")
parser.add_argument("--rolling-window",   type=int,   default=200,
                    help="Rolling window in rows for online fault monitoring")
parser.add_argument("--report",           default="results/fault_report.txt")
args = parser.parse_args()

# ── Thresholds ─────────────────────────────────────────────────────────────
FORCE_LOSS_THR   = 0.20   # 20%
RMS_INCREASE_THR = 0.30   # 30%
FS               = 20.0   # Hz (50 ms sample interval)
LSB_PER_G        = 16384.0
FFT_PEAK_MIN_AMP = 0.01   # g

# ── Load ───────────────────────────────────────────────────────────────────
print(f"Loading: {args.csv}")
if not os.path.exists(args.csv):
    sys.exit(f"ERROR: {args.csv} not found")

df = pd.read_csv(args.csv)
df["Az_g"] = df["Az"] / LSB_PER_G

print(f"  Rows: {len(df):,}  |  Cycles: {df['Cycle'].max():,}")

# ── Baseline ───────────────────────────────────────────────────────────────
baseline_df = df[df["Cycle"] < args.baseline_cycles]
if len(baseline_df) < 10:
    sys.exit("ERROR: not enough baseline data – reduce --baseline-cycles")

baseline_force = baseline_df["Force_kg"].mean()
baseline_rms   = np.sqrt(np.mean(baseline_df["Az_g"]**2))

# Baseline FFT peaks
az_base = baseline_df["Az_g"].values
n_base  = len(az_base)
fft_base = np.abs(np.fft.rfft(az_base - az_base.mean())) / (n_base/2)
freq_base = np.fft.rfftfreq(n_base, d=1.0/FS)
pk_idx_base, _ = find_peaks(fft_base, height=FFT_PEAK_MIN_AMP, distance=3)
base_peak_freqs = set(round(freq_base[i], 1) for i in pk_idx_base)

print(f"\nBaseline Force : {baseline_force:.2f} kg")
print(f"Baseline RMS   : {baseline_rms:.4f} g")
print(f"Baseline FFT peaks (Hz): {sorted(base_peak_freqs)}")

# ── Rolling fault detection ────────────────────────────────────────────────
W = args.rolling_window

force_roll = df["Force_kg"].rolling(W, min_periods=W//2).mean()
rms_roll   = df["Az_g"].rolling(W, min_periods=W//2).apply(
    lambda x: np.sqrt(np.mean(x**2)), raw=True
)

force_loss_pct   = (baseline_force - force_roll) / baseline_force * 100
rms_increase_pct = (rms_roll - baseline_rms)   / baseline_rms   * 100

# Boolean fault flags per row
df["fault_force"] = force_loss_pct   > (FORCE_LOSS_THR   * 100)
df["fault_rms"]   = rms_increase_pct > (RMS_INCREASE_THR * 100)
df["fault_any"]   = df["fault_force"] | df["fault_rms"]

# First occurrence of each fault
first_force = df[df["fault_force"]].iloc[0] if df["fault_force"].any() else None
first_rms   = df[df["fault_rms"]].iloc[0]   if df["fault_rms"].any()   else None
first_any   = df[df["fault_any"]].iloc[0]   if df["fault_any"].any()   else None

# ── FFT on final stage ─────────────────────────────────────────────────────
n_final  = min(len(baseline_df), 5000)
az_final = df["Az_g"].iloc[-n_final:].values
fft_fin  = np.abs(np.fft.rfft(az_final - az_final.mean())) / (n_final/2)
freq_fin = np.fft.rfftfreq(n_final, d=1.0/FS)
pk_idx_fin, _ = find_peaks(fft_fin, height=FFT_PEAK_MIN_AMP, distance=3)
final_peak_freqs = {round(freq_fin[i], 1) for i in pk_idx_fin}

new_freqs = {f for f in final_peak_freqs if min(abs(f - b) for b in base_peak_freqs or [99]) > 0.5}
fault_fft = len(new_freqs) > 0

print(f"\nFinal FFT peaks (Hz): {sorted(final_peak_freqs)}")
print(f"New peaks detected  : {sorted(new_freqs)}")

# ── Report ─────────────────────────────────────────────────────────────────
os.makedirs("results", exist_ok=True)

lines = [
    "=" * 60,
    "  FAULT DETECTION REPORT",
    "  Truck Shock Absorber Durability Test Bench",
    "=" * 60,
    f"  CSV File        : {args.csv}",
    f"  Total Rows      : {len(df):,}",
    f"  Total Cycles    : {df['Cycle'].max():,}",
    "",
    "── Baseline ──────────────────────────────────────────",
    f"  Force           : {baseline_force:.2f} kg",
    f"  RMS Az          : {baseline_rms:.4f} g",
    f"  Peak Freqs (Hz) : {sorted(base_peak_freqs)}",
    "",
    "── Fault Results ─────────────────────────────────────",
]

def fault_line(label, detected, first_row=None):
    status = "⚠  FAULT DETECTED" if detected else "✔  OK"
    line   = f"  {label:<25} {status}"
    if detected and first_row is not None:
        line += f"  (cycle {int(first_row['Cycle'])}, t={int(first_row['Time_ms'])} ms)"
    return line

lines.append(fault_line("Force Loss > 20%",       df["fault_force"].any(), first_force))
lines.append(fault_line("RMS Increase > 30%",     df["fault_rms"].any(),   first_rms))
lines.append(fault_line("New FFT Peaks",           fault_fft))

if fault_fft:
    lines.append(f"    New frequencies : {sorted(new_freqs)} Hz")

lines += [
    "",
    "── Overall ───────────────────────────────────────────",
    fault_line("Any Fault Detected",      df["fault_any"].any(), first_any),
    "=" * 60,
]

report_text = "\n".join(lines)
print("\n" + report_text)

with open(args.report, "w") as f:
    f.write(report_text + "\n")
print(f"\nReport saved → {args.report}")

# ── Plotting ───────────────────────────────────────────────────────────────
fig = plt.figure(figsize=(14, 9))
fig.suptitle("Fault Detection Dashboard", fontsize=14, fontweight="bold")
gs  = gridspec.GridSpec(2, 2, figure=fig, hspace=0.45, wspace=0.35)

cycle_axis = df["Cycle"]

# 1. Force with threshold
ax1 = fig.add_subplot(gs[0, :])
ax1.plot(cycle_axis, force_roll, lw=1.2, color="#1f77b4", label="Rolling Force")
ax1.axhline(baseline_force,           color="green", ls="--", lw=1, label="Baseline")
ax1.axhline(baseline_force * 0.80,    color="red",   ls="--", lw=1, label="−20% limit")
if df["fault_force"].any():
    fc = first_force["Cycle"]
    ax1.axvline(fc, color="red", lw=1.5, alpha=0.6, label=f"Fault @ cycle {int(fc)}")
ax1.set_xlabel("Cycle #")
ax1.set_ylabel("Force (kg)")
ax1.set_title("Force Monitoring")
ax1.legend(fontsize=8)
ax1.grid(True, alpha=0.3)

# 2. RMS with threshold
ax2 = fig.add_subplot(gs[1, 0])
ax2.plot(cycle_axis, rms_roll, lw=1.2, color="#ff7f0e", label="Rolling RMS")
ax2.axhline(baseline_rms,              color="green", ls="--", lw=1, label="Baseline")
ax2.axhline(baseline_rms * 1.30,       color="red",   ls="--", lw=1, label="+30% limit")
if df["fault_rms"].any():
    rc = first_rms["Cycle"]
    ax2.axvline(rc, color="red", lw=1.5, alpha=0.6, label=f"Fault @ {int(rc)}")
ax2.set_xlabel("Cycle #")
ax2.set_ylabel("RMS Az (g)")
ax2.set_title("Vibration RMS Monitoring")
ax2.legend(fontsize=8)
ax2.grid(True, alpha=0.3)

# 3. FFT comparison
ax3 = fig.add_subplot(gs[1, 1])
ax3.plot(freq_base, fft_base, lw=1.5, label="Initial", color="#1f77b4", alpha=0.8)
ax3.plot(freq_fin,  fft_fin,  lw=1.5, label="Final",   color="#ff7f0e", alpha=0.8)
for nf in sorted(new_freqs):
    ax3.axvline(nf, color="red", ls=":", lw=1)
    ax3.text(nf+0.1, ax3.get_ylim()[1]*0.9, f"{nf} Hz", fontsize=7, color="red")
ax3.set_xlim(0, FS/2)
ax3.set_xlabel("Frequency (Hz)")
ax3.set_ylabel("Amplitude (g)")
ax3.set_title("FFT: Initial vs Final")
ax3.legend(fontsize=8)
ax3.grid(True, alpha=0.3)

out_png = "results/fault_detection.png"
plt.savefig(out_png, dpi=150, bbox_inches="tight")
print(f"Plot saved → {out_png}")
plt.show()
