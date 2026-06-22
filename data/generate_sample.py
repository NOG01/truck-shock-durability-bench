#!/usr/bin/env python3
"""
Generate sample_data.csv simulating a 10,000-cycle durability test.
Run once: python data/generate_sample.py
"""

import csv
import math
import random

TOTAL_CYCLES  = 10000
SAMPLE_MS     = 50          # sampling interval
FREQ_HZ       = 3.0         # test frequency
PERIOD_MS     = 1000 / FREQ_HZ  # ~333 ms per cycle

FORCE_INIT    = 50.0        # kg at start
FORCE_FINAL   = 40.0        # kg at end  (20% reduction)
RMS_AZ_INIT   = 16000       # raw ADC counts ~0.82 g
RMS_AZ_FINAL  = 21900       # ~1.12 g  (36.6% increase)

random.seed(42)

rows = []
t_ms  = 0
cycle = 0

# Each cycle takes PERIOD_MS ms; we sample every SAMPLE_MS
samples_per_cycle = int(round(PERIOD_MS / SAMPLE_MS))  # ~7

total_samples = TOTAL_CYCLES * samples_per_cycle

for s in range(total_samples):
    progress = s / total_samples                    # 0 → 1
    cycle    = int(s / samples_per_cycle)

    # Degradation curves
    force = FORCE_INIT + (FORCE_FINAL - FORCE_INIT) * progress
    force += random.gauss(0, 0.4)
    force  = max(force, 0)

    az_rms = RMS_AZ_INIT + (RMS_AZ_FINAL - RMS_AZ_INIT) * progress
    phase  = 2 * math.pi * FREQ_HZ * (t_ms / 1000.0)

    # Introduce 7 Hz secondary frequency after 60% of test
    secondary = 0
    if progress > 0.60:
        secondary = int(az_rms * 0.15 * math.sin(2 * math.pi * 7.0 * (t_ms / 1000.0)))

    az = int(az_rms * math.sin(phase) + secondary + random.gauss(0, 200))
    ax = int(random.gauss(0, 300))
    ay = int(random.gauss(-55, 100))

    rows.append({
        "Time_ms":  t_ms,
        "Cycle":    cycle,
        "Ax":       ax,
        "Ay":       ay,
        "Az":       az,
        "Force_kg": round(force, 2),
    })

    t_ms += SAMPLE_MS

output = "data/sample_data.csv"
with open(output, "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=["Time_ms","Cycle","Ax","Ay","Az","Force_kg"])
    writer.writeheader()
    writer.writerows(rows)

print(f"Generated {len(rows):,} rows → {output}")
