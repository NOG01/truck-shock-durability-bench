#!/usr/bin/env python3
"""
fft_analysis.py - FFT spectrum analysis of shock absorber vibration data.

Usage:
    python python/fft_analysis.py [--csv data/sample_data.csv]
                                  [--channel Az]
                                  [--segment-size 1024]
                                  [--stage-pct 0.10]
"""

import argparse
import os
import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from scipy.signal import welch

# ── CLI ────────────────────────────────────────────────────────────────────
parser = argparse.ArgumentParser(description="FFT vibration spectrum analysis")
parser.add_argument("--csv",          default="data/sample_data.csv")
parser.add_argument("--channel",      default="Az",   choices=["Ax","Ay","Az","Vmag"])
parser.add_argument("--segment-size", type=int, default=1024)
parser.add_argument("--stage-pct",    type=float, default=0.10,
                    help="Fraction of data used per stage (initial / final)")
args = parser.parse_args()

CSV_PATH  = args.csv
CHANNEL   = args.channel
SEG_SIZE  = args.segment_size
STAGE_PCT = args.stage_pct
FS        = 1000.0 / 50.0   # 50 ms → 20 Hz sampling rate
LSB_PER_G = 16384.0
PEAK_THRESH_G = 0.02         # minimum peak amplitude (g) to report

# ── Load ───────────────────────────────────────────────────────────────────
print(f"Loading: {CSV_PATH}")
if not os.path.exists(CSV_PATH):
    sys.exit(f"ERROR: not found → {CSV_PATH}")

df = pd.read_csv(CSV_PATH)

# Convert raw ADC to g
for col in ["Ax","Ay","Az"]:
    df[f"{col}_g"] = df[col] / LSB_PER_G

if CHANNEL == "Vmag":
    df["Vmag"] = np.sqrt(df["Ax_g"]**2 + df["Ay_g"]**2 + df["Az_g"]**2)
    signal_col = "Vmag"
else:
    signal_col = f"{CHANNEL}_g"

print(f"Channel : {signal_col} | Fs={FS} Hz | Rows={len(df):,}")

# ── Split into stages ──────────────────────────────────────────────────────
n_stage = max(SEG_SIZE, int(len(df) * STAGE_PCT))
initial = df[signal_col].iloc[:n_stage].values
final   = df[signal_col].iloc[-n_stage:].values


def compute_fft(signal, fs):
    """Return (frequencies, amplitude_spectrum) using Welch PSD + magnitude."""
    n   = len(signal)
    win = np.hanning(n)
    sig = (signal - signal.mean()) * win
    sp  = np.fft.rfft(sig) / (n / 2)
    fr  = np.fft.rfftfreq(n, d=1.0/fs)
    amp = np.abs(sp)
    return fr, amp


def find_peaks(freqs, amps, threshold=PEAK_THRESH_G, min_freq=0.5):
    """Return list of (freq, amp) for dominant peaks."""
    from scipy.signal import find_peaks as sp_peaks
    idx, props = sp_peaks(amps, height=threshold, distance=int(len(freqs)*0.05))
    peaks = [(freqs[i], amps[i]) for i in idx if freqs[i] >= min_freq]
    peaks.sort(key=lambda x: -x[1])
    return peaks


freq_init, amp_init = compute_fft(initial, FS)
freq_final, amp_final = compute_fft(final, FS)

peaks_init  = find_peaks(freq_init,  amp_init)
peaks_final = find_peaks(freq_final, amp_final)

# ── Dominant frequency identification ─────────────────────────────────────
def dominant(peaks):
    return peaks[0] if peaks else (0, 0)

dom_init  = dominant(peaks_init)
dom_final = dominant(peaks_final)

print("\n── Initial Stage FFT Peaks ───────────────────────────────────────")
for f, a in peaks_init[:6]:
    print(f"  {f:6.2f} Hz   {a:.4f} g")

print("\n── Final Stage FFT Peaks ─────────────────────────────────────────")
for f, a in peaks_final[:6]:
    print(f"  {f:6.2f} Hz   {a:.4f} g")

# Detect new peaks in final not present in initial (±0.5 Hz tolerance)
new_peaks = []
for fq, amp in peaks_final:
    is_new = all(abs(fq - fi) > 0.5 for fi, _ in peaks_init)
    if is_new:
        new_peaks.append((fq, amp))

print("\n── New Frequencies Detected in Final Stage ───────────────────────")
if new_peaks:
    for f, a in new_peaks:
        print(f"  {f:.2f} Hz  (amp={a:.4f} g) ← possible wear indicator")
else:
    print("  None")

# ── Welch PSD (smoother representation) ───────────────────────────────────
nperseg = min(SEG_SIZE, len(initial)//4)
f_w_init,  psd_init  = welch(initial, fs=FS, nperseg=nperseg)
f_w_final, psd_final = welch(final,   fs=FS, nperseg=nperseg)

# ── Plotting ───────────────────────────────────────────────────────────────
fig = plt.figure(figsize=(14, 9))
fig.suptitle(f"FFT Spectrum Analysis – Channel: {signal_col}", fontsize=14, fontweight="bold")
gs  = gridspec.GridSpec(2, 2, figure=fig, hspace=0.45, wspace=0.35)

# 1. Raw FFT – Initial
ax1 = fig.add_subplot(gs[0, 0])
ax1.plot(freq_init, amp_init, lw=1, color="#1f77b4")
for f, a in peaks_init[:3]:
    ax1.annotate(f"{f:.1f} Hz", xy=(f, a), xytext=(f+0.2, a*1.05), fontsize=7, color="darkblue")
ax1.set_xlim(0, FS/2)
ax1.set_xlabel("Frequency (Hz)")
ax1.set_ylabel("Amplitude (g)")
ax1.set_title("FFT – Initial Stage")
ax1.grid(True, alpha=0.3)

# 2. Raw FFT – Final
ax2 = fig.add_subplot(gs[0, 1])
ax2.plot(freq_final, amp_final, lw=1, color="#ff7f0e")
for f, a in peaks_final[:3]:
    ax2.annotate(f"{f:.1f} Hz", xy=(f, a), xytext=(f+0.2, a*1.05), fontsize=7, color="darkorange")
ax2.set_xlim(0, FS/2)
ax2.set_xlabel("Frequency (Hz)")
ax2.set_ylabel("Amplitude (g)")
ax2.set_title("FFT – Final Stage")
ax2.grid(True, alpha=0.3)

# 3. Welch PSD overlay
ax3 = fig.add_subplot(gs[1, :])
ax3.semilogy(f_w_init,  psd_init,  lw=2, label="Initial", color="#1f77b4")
ax3.semilogy(f_w_final, psd_final, lw=2, label="Final",   color="#ff7f0e")
for f, a in new_peaks[:3]:
    ax3.axvline(f, color="red", ls="--", lw=1, alpha=0.7)
    ax3.text(f+0.1, ax3.get_ylim()[0]*10, f"{f:.1f} Hz\n(new)", fontsize=7, color="red")
ax3.set_xlim(0, FS/2)
ax3.set_xlabel("Frequency (Hz)")
ax3.set_ylabel("PSD (g²/Hz) – log scale")
ax3.set_title("Welch PSD Comparison (Initial vs Final)")
ax3.legend()
ax3.grid(True, alpha=0.3)

os.makedirs("results", exist_ok=True)
out = "results/vibration_fft.png"
plt.savefig(out, dpi=150, bbox_inches="tight")
print(f"\nPlot saved → {out}")
plt.show()
