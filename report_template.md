/*
 * Truck Shock Absorber Durability Test Bench
 * Arduino Uno - Main Firmware
 *
 * Hardware:
 *   - MPU6050  : I2C (SDA=A4, SCL=A5)
 *   - HX711    : DOUT=3, SCK=4
 *   - SD Card  : SPI (MOSI=11, MISO=12, SCK=13, CS=10)
 *   - Motor    : IN1=5, IN2=6, EN=9 (BTS7960 or L298N)
 *
 * Data format (CSV):
 *   Time_ms,Cycle,Ax,Ay,Az,Force_kg
 */

#include <Wire.h>
#include <SD.h>
#include <SPI.h>
#include "HX711.h"

// ─── Pin Definitions ───────────────────────────────────────────────────────
#define HX711_DOUT     3
#define HX711_SCK      4
#define MOTOR_IN1      5
#define MOTOR_IN2      6
#define MOTOR_EN       9
#define SD_CS          10

// ─── MPU6050 Registers ─────────────────────────────────────────────────────
#define MPU_ADDR       0x68
#define PWR_MGMT_1     0x6B
#define ACCEL_XOUT_H   0x3B

// ─── Test Parameters ───────────────────────────────────────────────────────
#define TOTAL_CYCLES      10000UL
#define SAMPLE_INTERVAL   50       // ms
#define MOTOR_SPEED       180      // 0-255 PWM
#define CYCLE_HALF_MS     167      // ~3 Hz => period 333ms, half = 167ms

// Failure thresholds
#define FORCE_LOSS_THRESHOLD   0.20f  // 20% force reduction
#define RMS_INCREASE_THRESHOLD 0.30f  // 30% RMS increase

// ─── Globals ───────────────────────────────────────────────────────────────
HX711  scale;
File   logFile;

unsigned long cycleCount       = 0;
unsigned long lastSampleTime   = 0;
unsigned long lastCycleTime    = 0;
bool          motorDirection   = true;

float baselineForce   = 0.0f;
float baselineRMS     = 0.0f;
bool  baselineSet     = false;
bool  faultDetected   = false;

// Running RMS window (last 20 samples of Az)
#define RMS_WINDOW 20
int16_t azWindow[RMS_WINDOW];
uint8_t azIndex = 0;

// ─── Setup ─────────────────────────────────────────────────────────────────
void setup() {
  Serial.begin(115200);
  Serial.println(F("=== Truck Shock Absorber Durability Test Bench ==="));

  // Motor pins
  pinMode(MOTOR_IN1, OUTPUT);
  pinMode(MOTOR_IN2, OUTPUT);
  pinMode(MOTOR_EN,  OUTPUT);
  motorStop();

  // MPU6050 init
  Wire.begin();
  Wire.beginTransmission(MPU_ADDR);
  Wire.write(PWR_MGMT_1);
  Wire.write(0x00);  // Wake up MPU6050
  Wire.endTransmission(true);
  Serial.println(F("MPU6050 initialized"));

  // HX711 init
  scale.begin(HX711_DOUT, HX711_SCK);
  scale.set_scale(2280.f);  // Calibration factor – adjust per your load cell
  scale.tare();
  Serial.println(F("HX711 tared"));

  // SD Card init
  if (!SD.begin(SD_CS)) {
    Serial.println(F("SD card initialization FAILED. Halting."));
    while (true);
  }
  Serial.println(F("SD card initialized"));

  // Create or append log file
  logFile = SD.open("log.csv", FILE_WRITE);
  if (!logFile) {
    Serial.println(F("Failed to open log.csv. Halting."));
    while (true);
  }
  // Write header if file is empty
  if (logFile.size() == 0) {
    logFile.println(F("Time_ms,Cycle,Ax,Ay,Az,Force_kg"));
  }
  logFile.flush();
  Serial.println(F("Log file ready: log.csv"));

  // Collect baseline (first 100 samples with motor OFF)
  Serial.println(F("Collecting baseline (100 samples)..."));
  collectBaseline();

  Serial.println(F("Starting test..."));
  lastSampleTime = millis();
  lastCycleTime  = millis();
  motorForward();
}

// ─── Loop ──────────────────────────────────────────────────────────────────
void loop() {
  if (cycleCount >= TOTAL_CYCLES || faultDetected) {
    motorStop();
    logFile.close();
    Serial.println(F("Test COMPLETE or FAULT detected."));
    Serial.print(F("Total cycles: "));
    Serial.println(cycleCount);
    while (true);
  }

  unsigned long now = millis();

  // ── Motor cycle toggling at ~3 Hz ──────────────────────────────────────
  if (now - lastCycleTime >= CYCLE_HALF_MS) {
    lastCycleTime = now;
    if (motorDirection) {
      motorReverse();
      motorDirection = false;
    } else {
      motorForward();
      motorDirection = true;
      cycleCount++;
    }
  }

  // ── Data sampling every SAMPLE_INTERVAL ms ─────────────────────────────
  if (now - lastSampleTime >= SAMPLE_INTERVAL) {
    lastSampleTime = now;

    int16_t ax, ay, az;
    readMPU6050(ax, ay, az);

    float force = scale.get_units(1);
    if (force < 0) force = 0;

    // Update RMS window
    azWindow[azIndex % RMS_WINDOW] = az;
    azIndex++;
    float rms = computeRMS();

    // Set baseline after 20 warm-up samples
    if (!baselineSet && azIndex >= RMS_WINDOW) {
      baselineForce = force;
      baselineRMS   = rms;
      baselineSet   = true;
      Serial.print(F("Baseline Force: ")); Serial.print(baselineForce);
      Serial.print(F(" kg | Baseline RMS: ")); Serial.println(baselineRMS);
    }

    // Failure detection
    if (baselineSet) {
      faultDetected = checkFault(force, rms);
    }

    // Log to SD
    logFile.print(now);        logFile.print(',');
    logFile.print(cycleCount); logFile.print(',');
    logFile.print(ax);         logFile.print(',');
    logFile.print(ay);         logFile.print(',');
    logFile.print(az);         logFile.print(',');
    logFile.println(force);
    logFile.flush();

    // Serial monitor
    Serial.print(F("Cycle:")); Serial.print(cycleCount);
    Serial.print(F(" Ax:")); Serial.print(ax);
    Serial.print(F(" Ay:")); Serial.print(ay);
    Serial.print(F(" Az:")); Serial.print(az);
    Serial.print(F(" F:")); Serial.print(force, 2);
    Serial.print(F("kg RMS:")); Serial.println(rms, 4);
  }
}

// ─── MPU6050 ───────────────────────────────────────────────────────────────
void readMPU6050(int16_t &ax, int16_t &ay, int16_t &az) {
  Wire.beginTransmission(MPU_ADDR);
  Wire.write(ACCEL_XOUT_H);
  Wire.endTransmission(false);
  Wire.requestFrom((uint8_t)MPU_ADDR, (uint8_t)6, (uint8_t)true);

  ax = (Wire.read() << 8) | Wire.read();
  ay = (Wire.read() << 8) | Wire.read();
  az = (Wire.read() << 8) | Wire.read();
}

// ─── RMS Calculation ───────────────────────────────────────────────────────
float computeRMS() {
  long sum = 0;
  for (uint8_t i = 0; i < RMS_WINDOW; i++) {
    sum += (long)azWindow[i] * azWindow[i];
  }
  return sqrt((float)sum / RMS_WINDOW);
}

// ─── Fault Detection ───────────────────────────────────────────────────────
bool checkFault(float currentForce, float currentRMS) {
  if (baselineForce > 0) {
    float forceLoss = (baselineForce - currentForce) / baselineForce;
    if (forceLoss > FORCE_LOSS_THRESHOLD) {
      Serial.println(F("!!! FAULT: Force loss > 20% !!!"));
      return true;
    }
  }
  if (baselineRMS > 0) {
    float rmsIncrease = (currentRMS - baselineRMS) / baselineRMS;
    if (rmsIncrease > RMS_INCREASE_THRESHOLD) {
      Serial.println(F("!!! FAULT: RMS vibration increase > 30% !!!"));
      return true;
    }
  }
  return false;
}

// ─── Baseline Collection ───────────────────────────────────────────────────
void collectBaseline() {
  float sumForce = 0;
  long  sumAz2   = 0;

  for (uint8_t i = 0; i < 100; i++) {
    int16_t ax, ay, az;
    readMPU6050(ax, ay, az);
    float f = scale.get_units(1);
    if (f < 0) f = 0;
    sumForce += f;
    sumAz2   += (long)az * az;
    delay(SAMPLE_INTERVAL);
  }

  baselineForce = sumForce / 100.0f;
  baselineRMS   = sqrt((float)sumAz2 / 100.0f);
  baselineSet   = true;

  Serial.print(F("Baseline | Force: "));
  Serial.print(baselineForce);
  Serial.print(F(" kg | RMS: "));
  Serial.println(baselineRMS);
}

// ─── Motor Control ─────────────────────────────────────────────────────────
void motorForward() {
  digitalWrite(MOTOR_IN1, HIGH);
  digitalWrite(MOTOR_IN2, LOW);
  analogWrite(MOTOR_EN, MOTOR_SPEED);
}

void motorReverse() {
  digitalWrite(MOTOR_IN1, LOW);
  digitalWrite(MOTOR_IN2, HIGH);
  analogWrite(MOTOR_EN, MOTOR_SPEED);
}

void motorStop() {
  digitalWrite(MOTOR_IN1, LOW);
  digitalWrite(MOTOR_IN2, LOW);
  analogWrite(MOTOR_EN, 0);
}
