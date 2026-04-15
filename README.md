# High-Speed Reciprocating Actuator with Telemetry Logging

## Overview
This project implements a high-speed reciprocating actuator using the **moteus motor controller SDK**.  
It performs controlled cyclic motion while logging real-time telemetry data and generating post-run analysis plots.

---
## File Structure

.
├── Actuator.py
├── writeup.txt   
└── README.md


## Features

- Automated homing sequence
- High-speed reciprocating motion
- Real-time telemetry logging
- CSV data export
- Automatic plotting and visualization
- Fault detection and safe shutdown
- Watchdog-safe control loop

---

## Hardware Requirements

- moteus controller (n1 / r4.x / c1)
- BLDC motor
- fdcanusb or pi3hat communication interface
- Power supply

---

## Software Requirements

- Python 3.8+
- moteus Python SDK
- matplotlib

Install dependencies:
```bash
pip install matplotlib




VELOCITY_LIMIT
ACCEL_LIMIT
MAX_CURRENT_A
TRAVEL_START
TRAVEL_END
ENDPOINT_PAUSE
WATCHDOG_HZ