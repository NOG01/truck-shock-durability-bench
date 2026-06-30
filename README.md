# Truck Shock Absorber Durability Test Bench

## Overview

This project presents a low-cost durability test bench for truck shock absorbers using Arduino Uno, MPU6050, HX711 load cell amplifier, SD card logging and Python-based vibration analysis.

The system performs accelerated durability testing by repeatedly compressing and extending a shock absorber while measuring:

* Applied force
* Vibration levels
* Cycle count
* Performance degradation
* Failure indicators

The objective is to evaluate shock absorber performance throughout thousands of test cycles and identify degradation using vibration analysis, FFT and force monitoring.

---

## Features

### Embedded System

* Arduino Uno based controller
* MPU6050 vibration monitoring
* Load Cell + HX711 force measurement
* SD card data logging
* Automatic cycle counting
* Configurable test duration
* Automatic failure detection

### Data Analysis

* Statistical analysis
* RMS vibration calculation
* FFT spectrum analysis
* Degradation trend analysis
* Failure detection algorithms
* Dashboard visualization

### Engineering Documentation

* Assembly guide
* FMEA analysis
* Test methodology
* Report template
* Experimental data structure

---

## System Architecture

```text
                   +-------------------+
                   |   Shock Absorber  |
                   +---------+---------+
                             |
                             |
                     +-------+------+
                     | Load Cell    |
                     +-------+------+
                             |
                             |
+-----------+      +---------+---------+
| MPU6050   |----->| Arduino Uno       |
+-----------+      |                   |
                   | - Data Logging    |
                   | - Cycle Counter   |
                   | - Motor Control   |
                   +----+---------+----+
                        |         |
                        |         |
                 +------+         +------+
                 |                     |
                 v                     v
           SD Card Module        Motor Driver
                                       |
                                       |
                                       v
                                  DC Motor
```

---

## Mechanical Concept

```text
        Upper Frame
             |
             |
      +-------------+
      | Load Cell   |
      +-------------+
             |
       Shock Absorber
             |
      Moving Platform
             |
      Eccentric Mechanism
             |
          DC Motor
```

---

## Hardware

| Component        | Quantity |
| ---------------- | -------- |
| Arduino Uno      | 1        |
| MPU6050          | 1        |
| Load Cell 100kg  | 1        |
| HX711 Module     | 1        |
| SD Card Module   | 1        |
| BTS7960 or L298N | 1        |
| DC Motor         | 1        |
| Power Supply     | 1        |
| Steel Structure  | 1        |

---

## Sensors

### MPU6050

Measured Variables:

* Acceleration X
* Acceleration Y
* Acceleration Z

Applications:

* Vibration monitoring
* Cycle detection
* FFT analysis

### Load Cell

Measured Variables:

* Compression force
* Degradation monitoring

Applications:

* Shock absorber performance evaluation
* Failure detection

---

## Test Parameters

Example setup:

| Parameter         | Value    |
| ----------------- | -------- |
| Test Cycles       | 10,000   |
| Frequency         | 3 Hz     |
| Stroke            | 30 mm    |
| Sampling Interval | 50 ms    |
| Force Range       | 0-100 kg |
| Logging Format    | CSV      |

---

## Data Logging Format

Example:

```csv
Time_ms,Cycle,Ax,Ay,Az,Force_kg

0,0,123,-55,16200,48.2
50,0,140,-40,16090,49.1
100,1,155,-31,-15980,50.4
```

---

## Data Analysis Workflow

```text
CSV Data
   |
   v
Python Analysis
   |
   +---- Statistics
   |
   +---- RMS Vibration
   |
   +---- FFT Spectrum
   |
   +---- Trend Analysis
   |
   +---- Failure Detection
```

---

## Failure Detection Logic

The system can flag potential failures when:

### Force Loss

```text
Force Reduction > 20%
```

### Vibration Increase

```text
RMS Increase > 30%
```

### Spectral Changes

```text
New FFT Peaks
```

### Visual Inspection

```text
Oil Leakage
Rod Damage
Structural Cracks
```

---

## Example Results

### Force Degradation

| Stage   | Mean Force |
| ------- | ---------- |
| Initial | 50 kg      |
| Final   | 40 kg      |

Result:

```text
20% Force Reduction
```

### Vibration RMS

| Stage   | RMS    |
| ------- | ------ |
| Initial | 0.82 g |
| Final   | 1.12 g |

Result:

```text
36.6% Increase
```

### FFT

Main Frequency:

```text
3 Hz
```

Secondary Frequency Detected:

```text
7 Hz
```

Possible internal wear indication.

---

## Dashboard

The project includes a Streamlit dashboard for:

* Live CSV visualization
* Force trend monitoring
* FFT plotting
* RMS monitoring
* Automatic fault detection

Launch:

```bash
streamlit run python/dashboard.py
```

---

## Repository Structure

```text
truck-shock-durability-bench/

├── README.md
├── LICENSE
├── .gitignore
├── requirements.txt
│
├── arduino/
│   └── durability_test.ino
│
├── python/
│   ├── analysis.py
│   ├── fft_analysis.py
│   ├── fault_detection.py
│   └── dashboard.py
│
├── docs/
│   ├── assembly_guide.md
│   ├── fmea.md
│   └── report_template.md
│
├── data/
│   └── sample_data.csv
│
├── images/
│   ├── bench_overview.jpg
│   ├── electronics.jpg
│   ├── fft_result.png
│   └── dashboard.png
│
└── results/
    ├── force_trend.png
    ├── vibration_fft.png
    └── final_report.pdf
```

---

## Installation

Clone repository:

```bash
git clone https://github.com/nog01/truck-shock-durability-bench.git
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Run analysis:

```bash
python python/analysis.py
```

Run dashboard:

```bash
streamlit run python/dashboard.py
```

---
