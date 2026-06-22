[assembly_guide.md](https://github.com/user-attachments/files/29190359/assembly_guide.md)
# Assembly Guide – Truck Shock Absorber Durability Test Bench

## 1. Overview

This guide describes the mechanical and electrical assembly of the low-cost
durability test bench for truck shock absorbers.

---

## 2. Mechanical Assembly

### 2.1 Frame

| Item | Specification |
|------|--------------|
| Material | 40 × 40 mm steel square tube |
| Height | ~800 mm |
| Base plate | 300 × 300 × 6 mm steel |
| Welding | MIG or TIG, fully penetrated joints |

### 2.2 Eccentric Mechanism

1. Mount a **200–300 W DC motor** on the lower frame bracket.
2. Attach a **crank disk** (Ø 60 mm) to the motor shaft using a key-way.
3. Bolt a **connecting rod** (length ≈ 200 mm) between the crank pin and the moving platform.
4. The stroke is set by the crank pin offset: **15 mm offset → 30 mm stroke**.

### 2.3 Shock Absorber Fixture

- Upper mount: bolt through the load cell lower plate.
- Lower mount: bolt through the moving platform clevis bracket.
- Use the OEM shock absorber bushings and hardware.

### 2.4 Load Cell Installation

```
  Upper Frame
      │
  [Load Cell]   ← sandwiched between two steel adapter plates (M10 bolts)
      │
  Shock Absorber (upper eye)
```

Torque M10 bolts to **35 N·m**.

---

## 3. Electrical Wiring

### 3.1 Arduino Uno Pinout

| Signal | Arduino Pin |
|--------|-------------|
| HX711 DOUT | D3 |
| HX711 SCK  | D4 |
| Motor IN1  | D5 |
| Motor IN2  | D6 |
| Motor EN   | D9 (PWM) |
| SD CS      | D10 |
| SD MOSI    | D11 |
| SD MISO    | D12 |
| SD SCK     | D13 |
| MPU6050 SDA | A4 |
| MPU6050 SCL | A5 |

### 3.2 Power Rails

| Rail | Source | Consumers |
|------|--------|-----------|
| 5 V  | Arduino USB or 7805 regulator | MPU6050, HX711, SD module |
| 12 V | External PSU | DC Motor via BTS7960 |

> **⚠ Warning:** Keep motor power and logic power grounds connected at one common point to avoid ground loops and sensor noise.

### 3.3 BTS7960 Motor Driver

```
BTS7960 Pin → Arduino
  RPWM     → D9  (PWM)
  LPWM     → D6
  R_EN     → D5
  L_EN     → D5
  VCC      → 5 V
  GND      → GND
  Motor A/B → DC Motor
```

---

## 4. MPU6050 Mounting

- Mount the MPU6050 breakout board **directly on the moving platform** (as close to the shock absorber lower mount as possible).
- Use M2 nylon standoffs to isolate the board from metal-to-metal contact.
- Secure wires with cable ties to avoid fatigue failures.

---

## 5. SD Card Module

- Use a **SPI micro-SD breakout** (3.3 V logic level).
- Format the card as **FAT32**.
- Maximum recommended card size: **32 GB**.

---

## 6. Load Cell Calibration

1. Apply a **known mass** (e.g. 20 kg certified weight).
2. Read the raw HX711 output via Serial Monitor.
3. Calculate the calibration factor:

```
calibration_factor = raw_reading / known_mass_kg
```

4. Update `scale.set_scale(calibration_factor)` in `durability_test.ino`.

---

## 7. Initial Function Check

- [ ] Motor rotates in both directions when commanded
- [ ] Serial Monitor shows MPU6050 data (non-zero Ax, Ay, Az)
- [ ] HX711 reads ≈ 0 kg with no load (after tare)
- [ ] SD card creates `log.csv` and writes at least 10 rows
- [ ] Cycle counter increments correctly

---

## 8. Safety

- Enclose the eccentric mechanism with a **sheet-metal guard**.
- Do not operate above **5 Hz** without structural FEA validation.
- Wear safety glasses during operation.
- Use an **emergency stop button** wired to the motor EN pin (pull low to stop).
