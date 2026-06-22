[fmea.md](https://github.com/user-attachments/files/29190367/fmea.md)
# FMEA – Truck Shock Absorber Durability Test Bench

**FMEA Type:** Design & Process  
**Prepared by:** NOG01  
**Date:** 2025  
**Revision:** 1.0

---

## RPN Formula

```
RPN = Severity (S) × Occurrence (O) × Detection (D)
```

Scale: 1 (low) to 10 (high)  
Action required when **RPN ≥ 80**.

---

## FMEA Table

| # | Component | Failure Mode | Effect | S | Potential Cause | O | Current Control | D | RPN | Recommended Action |
|---|-----------|-------------|--------|---|-----------------|---|-----------------|---|-----|--------------------|
| 1 | Eccentric Mechanism | Connecting rod fracture | Sudden release of moving platform; injury | 9 | Fatigue, insufficient section | 3 | Visual inspection | 6 | **162** | Safety guard + FEA analysis; use 12 mm steel rod |
| 2 | Load Cell | Overload / yielding | Loss of force measurement accuracy | 7 | Shock load > 100 kg | 4 | Rated capacity | 5 | 140 | Add mechanical travel stop limiting to 80% rated load |
| 3 | MPU6050 | Connector fatigue failure | Loss of vibration data | 5 | Cable flex cycle | 6 | None | 4 | 120 | Use flexible silicone wire; strain-relief tie wraps |
| 4 | DC Motor | Thermal overload | Test interruption | 6 | Continuous duty at max PWM | 5 | None | 5 | **150** | Add NTC thermistor; software over-temperature cutoff |
| 5 | SD Card | Write failure / card full | Data loss | 6 | Card >32 GB or FAT32 corruption | 4 | FAT32 format check | 5 | 120 | Monitor file size; alert via Serial LED if write fails |
| 6 | HX711 Module | EMI noise from motor | Force reading drift | 5 | PWM harmonics on signal wire | 6 | Separated wiring | 4 | 120 | Add 10 µF bypass capacitor near HX711 VCC; shielded cable |
| 7 | Shock Absorber Mount | Bolt loosening | Misalignment; false vibration readings | 6 | Cyclic loading, inadequate torque | 5 | Torque on assembly | 4 | 120 | Apply Loctite 243; re-check torque every 2,000 cycles |
| 8 | Power Supply | Output ripple | ADC noise, erratic readings | 4 | Cheap SMPS | 4 | None | 6 | 96 | Add 1000 µF electrolytic cap on 5 V bus |
| 9 | Arduino Uno | Firmware hang (watchdog) | Test stops undetected | 7 | Infinite loop, stack overflow | 2 | None | 5 | 70 | Enable hardware watchdog timer (WDT) in firmware |
| 10 | Frame Welds | Fatigue crack | Structural collapse | 9 | Undercut, porosity in weld | 2 | Visual pre-test check | 4 | 72 | Dye-penetrant inspection before first use |

---

## High-RPN Action Plan

| Priority | Item | Action | Owner | Target |
|----------|------|--------|-------|--------|
| 1 | Connecting rod (#1) | FEA + safety guard | Mechanical | Before first run |
| 2 | DC Motor thermal (#4) | NTC + software cutoff | Firmware | v1.1 |
| 3 | Load cell overload (#2) | Travel stop | Mechanical | Before first run |

---

## Revision History

| Rev | Date | Change |
|-----|------|--------|
| 1.0 | 2025 | Initial release |
