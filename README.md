High-Speed Reciprocating Actuator with Telemetry Logging
Overview

This project implements a high-speed reciprocating actuator system using the moteus motor controller SDK.

The system performs:

Automated homing
Controlled back-and-forth motion between two positions
Real-time telemetry logging
Post-run data visualization

The goal is to evaluate control performance, system stability, and actuator behavior under dynamic conditions.

Features
High-speed cyclic motion between two positions
Real-time telemetry capture:
Position (target vs actual)
Velocity
Torque current (Iq)
Bus voltage
Temperature
CSV logging for analysis
Automated plotting after execution
Watchdog-safe control loop
Fault detection and safe shutdown
Hardware Requirements
moteus controller (n1 / r4.x / c1)
BLDC motor
Communication interface:
fdcanusb (used in this project)
or pi3hat
Power supply
Software Requirements
Python 3.8+
moteus Python SDK
Required libraries:
pip install matplotlib
Project Structure
project/
│
├── main.py                  # Main control script
├── actuator_telemetry.csv   # Logged telemetry data (generated)
├── actuator_telemetry.png   # Plot output (generated)
└── README.md
How It Works
1. Homing Phase
The actuator slowly moves until mechanical resistance is detected.
The position is recorded as the home offset.
2. Reciprocating Motion
The motor moves between:
TRAVEL_START
TRAVEL_END
Motion constraints:
Velocity limit
Acceleration limit
Torque limit
3. Telemetry Logging

Each control loop iteration logs:

Parameter	Description
timestamp_s	Time since start
target_pos_rev	Target position
actual_pos_rev	Measured position
velocity_rev_s	Motor velocity
q_current_A	Torque current
bus_voltage_V	Supply voltage
temperature_C	Motor temperature
phase	MOVE or DWELL

Data is saved to:

actuator_telemetry.csv
Running the Project
python main.py

During execution:

The actuator will continuously reciprocate
Press Ctrl + C to stop safely
Output
CSV Log
File: actuator_telemetry.csv
Contains full telemetry dataset for analysis
Plot Visualization

Automatically generated after execution:

actuator_telemetry.png

Includes:

Target vs Actual Position
Bus Voltage & Temperature
Torque Current (Iq) with acceleration phase highlighted
Plot Details
Position Tracking
Shows control accuracy
Helps identify lag or overshoot
Voltage & Temperature
Monitors electrical and thermal stability
Torque Current (Iq)
Indicates load and effort
Acceleration phases are highlighted for analysis
Safety Features
Fault detection:
fault = state.values[moteus.Register.FAULT]
Immediate stop on error
Safe shutdown using:
await controller.set_stop()
Key Functions
Telemetry Logging
open_csv_logger()
reciprocate_with_telemetry()
Visualization
plot_telemetry()
Main Execution
async def main()
Customization

You can tune:

VELOCITY_LIMIT
ACCEL_LIMIT
MAX_CURRENT_A
TRAVEL_START
TRAVEL_END
ENDPOINT_PAUSE
Future Improvements
Closed-loop PID tuning integration
Real-time dashboard (ROS / GUI)
Frequency-based motion control
Multi-axis synchronization
ROS 2 integration