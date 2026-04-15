# ── Phase 3: Telemetry Logging ────────────────────────────────────────────────
import csv
import time
import matplotlib.pyplot as plt
from dataclasses import dataclass, fields
from typing import List

LOG_FILE = "actuator_telemetry.csv"

@dataclass
class TelemetryFrame:
    timestamp_s:     float
    target_pos_rev:  float
    actual_pos_rev:  float
    velocity_rev_s:  float
    q_current_A:     float
    bus_voltage_V:   float
    temperature_C:   float
    phase:           str    # "MOVE" | "DWELL"


def open_csv_logger(path: str):
    """Returns (file_handle, csv.DictWriter) — caller must close the file."""
    f = open(path, "w", newline="")
    writer = csv.DictWriter(f, fieldnames=[field.name for field in fields(TelemetryFrame)])
    writer.writeheader()
    return f, writer


async def reciprocate_with_telemetry(
    controller:  moteus.Controller,
    home_offset: float,
    csv_writer:  csv.DictWriter,
    log_start:   float,
) -> List[TelemetryFrame]:
    """
    Same reciprocation logic as Phase 2, but every loop tick captures a
    TelemetryFrame and writes it to CSV in real time.
    Returns the full frame list for post-run plotting.
    """
    interval    = 1.0 / WATCHDOG_HZ
    targets     = [TRAVEL_START, TRAVEL_END]
    idx         = 0
    all_frames: List[TelemetryFrame] = []

    def record(state, target_raw: float, phase: str):
        v  = state.values
        frame = TelemetryFrame(
            timestamp_s    = time.monotonic() - log_start,
            target_pos_rev = target_raw - home_offset,          # back to app frame
            actual_pos_rev = v[moteus.Register.POSITION] - home_offset,
            velocity_rev_s = v[moteus.Register.VELOCITY],
            q_current_A    = v[moteus.Register.Q_CURRENT],
            bus_voltage_V  = v[moteus.Register.VOLTAGE],
            temperature_C  = v[moteus.Register.TEMPERATURE],
            phase          = phase,
        )
        all_frames.append(frame)
        csv_writer.writerow(frame.__dict__)
        return frame

    try:
        while True:
            target_raw = targets[idx] + home_offset

            # ── Move phase ───────────────────────────────────────────────────
            while True:
                state = await controller.set_position(
                    position       = target_raw,
                    velocity_limit = VELOCITY_LIMIT,
                    accel_limit    = ACCEL_LIMIT,
                    maximum_torque = MAX_CURRENT_A,
                    query          = True,
                )

                fault = state.values[moteus.Register.FAULT]
                if fault != 0:
                    raise RuntimeError(f"Controller fault: {fault}")

                frame = record(state, target_raw, "MOVE")

                pos, vel = frame.actual_pos_rev, frame.velocity_rev_s
                if abs((pos + home_offset) - target_raw) < 0.02 and abs(vel) < 0.05:
                    break

                await asyncio.sleep(interval)

            # ── Dwell phase (watchdog-safe) ──────────────────────────────────
            dwell_cycles = int(ENDPOINT_PAUSE / interval)
            for _ in range(dwell_cycles):
                state = await controller.set_position(
                    position       = target_raw,
                    velocity_limit = VELOCITY_LIMIT,
                    accel_limit    = ACCEL_LIMIT,
                    maximum_torque = MAX_CURRENT_A,
                    query          = True,   # query=True so we can log during dwell too
                )
                record(state, target_raw, "DWELL")
                await asyncio.sleep(interval)

            idx = 1 - idx

    except KeyboardInterrupt:
        print(f"\n[TELEMETRY] Captured {len(all_frames)} frames → {LOG_FILE}")
    finally:
        await controller.set_stop()

    return all_frames


def plot_telemetry(frames: List[TelemetryFrame]):
    """Three-panel plot: position tracking | bus voltage & temp | Iq."""
    if not frames:
        print("[PLOT] No frames to plot.")
        return

    t       = [f.timestamp_s    for f in frames]
    target  = [f.target_pos_rev for f in frames]
    actual  = [f.actual_pos_rev for f in frames]
    iq      = [f.q_current_A    for f in frames]
    voltage = [f.bus_voltage_V  for f in frames]
    temp    = [f.temperature_C  for f in frames]

    # Highlight acceleration phase = first 20% of each move segment
    # (simple proxy: |velocity| is still ramping, i.e. below 80% of VELOCITY_LIMIT)
    accel_mask = [abs(frames[i].velocity_rev_s) < 0.8 * VELOCITY_LIMIT
                  and frames[i].phase == "MOVE"
                  for i in range(len(frames))]

    fig, axes = plt.subplots(3, 1, figsize=(12, 9), sharex=True)
    fig.suptitle("Moteus Actuator Telemetry", fontsize=14, fontweight="bold")

    # ── Panel 1: Position tracking ───────────────────────────────────────────
    ax1 = axes[0]
    ax1.plot(t, target, "--", color="steelblue", linewidth=1.2, label="Target")
    ax1.plot(t, actual, color="tomato",          linewidth=1.2, label="Actual")
    ax1.set_ylabel("Position (rev)")
    ax1.legend(loc="upper right")
    ax1.set_title("Target vs Actual Position")
    ax1.grid(True, alpha=0.3)

    # ── Panel 2: Bus voltage and temperature ─────────────────────────────────
    ax2 = axes[1]
    ax2_twin = ax2.twinx()
    ax2.plot(t, voltage, color="darkorange", linewidth=1.2, label="Bus Voltage (V)")
    ax2_twin.plot(t, temp, color="mediumpurple", linewidth=1.2, linestyle="--", label="Temp (°C)")
    ax2.set_ylabel("Voltage (V)", color="darkorange")
    ax2_twin.set_ylabel("Temperature (°C)", color="mediumpurple")
    ax2.set_title("Bus Voltage & Temperature")
    # Merge legends from both y-axes
    lines1, labels1 = ax2.get_legend_handles_labels()
    lines2, labels2 = ax2_twin.get_legend_handles_labels()
    ax2.legend(lines1 + lines2, labels1 + labels2, loc="upper right")
    ax2.grid(True, alpha=0.3)

    # ── Panel 3: Iq with acceleration phase highlighted ──────────────────────
    ax3 = axes[2]
    ax3.plot(t, iq, color="seagreen", linewidth=1.2, label="Iq (A)")
    # Shade acceleration regions
    in_accel = False
    start_t  = None
    for i, is_acc in enumerate(accel_mask):
        if is_acc and not in_accel:
            start_t  = t[i]
            in_accel = True
        elif not is_acc and in_accel:
            ax3.axvspan(start_t, t[i], alpha=0.15, color="gold", label="Accel phase" if start_t == t[next(j for j,a in enumerate(accel_mask) if a)] else "")
            in_accel = False
    ax3.set_ylabel("Iq (A)")
    ax3.set_xlabel("Time (s)")
    ax3.set_title("Torque Current (Iq) — gold = acceleration phase")
    ax3.legend(loc="upper right")
    ax3.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig("actuator_telemetry.png", dpi=150)
    print("[PLOT] Saved → actuator_telemetry.png")
    plt.show()


# ── Updated main() — ties all three phases together ──────────────────────────
async def main():
    transport  = moteus.Fdcanusb()
    controller = moteus.Controller(id=CONTROLLER_ID, transport=transport)

    await configure_limits(controller)
    raw_home = await home(controller)

    log_file, csv_writer = open_csv_logger(LOG_FILE)
    log_start = time.monotonic()

    try:
        frames = await reciprocate_with_telemetry(
            controller, raw_home, csv_writer, log_start
        )
    finally:
        log_file.close()
        print(f"[LOG] CSV closed → {LOG_FILE}")

    plot_telemetry(frames)


if __name__ == "__main__":
    asyncio.run(main())