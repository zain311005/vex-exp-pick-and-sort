"""Run the robot program in the simulator and print what happened.

    python3 sim/run_sim.py                       drive SELECTED_PATH
    python3 sim/run_sim.py --path bringup_line   drive another path
    python3 sim/run_sim.py --slip-left 0.97      left wheel slips 3 percent
    python3 sim/run_sim.py --imu-drift 0.05      gyro drifts 0.05 degrees a second
    python3 sim/run_sim.py --plot                also save a picture in sim/out/

Laptop only. The simulator's physics are simple, so a good result here
does not mean the real robot will do the same. Nothing here is tested on
hardware.
"""

import argparse
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
for folder in ("config", "src", "sim"):
    path = os.path.join(ROOT, folder)
    if path not in sys.path:
        sys.path.insert(0, path)

from settings import *                                  # noqa: E402,F403
from geometry import distance_between, trace_segments, wrap_180  # noqa: E402
from main import MODES, run                             # noqa: E402
from paths import get_path, path_names                  # noqa: E402
from sim_hardware import SimHardware, robot_outline     # noqa: E402


def planned_end(path_name):
    """Where a perfect robot would finish the path: (x, y, heading)."""
    segments = get_path(path_name)
    points = trace_segments(START_X, START_Y, START_HEADING, segments)
    x, y = points[-1] if points else (START_X, START_Y)
    heading = START_HEADING
    for kind, value in segments:
        if kind == "turn":
            heading = value
    return x, y, heading


def save_plot(hw, path_name, filename):
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        from matplotlib.colors import is_color_like
        from matplotlib.patches import Polygon, Rectangle
    except ImportError:
        print("matplotlib is not installed, so no picture: pip install matplotlib")
        return

    fig, ax = plt.subplots(figsize=(7, 8))
    x = BOARD_MIN_X
    while x <= BOARD_MAX_X:
        ax.plot([x, x], [BOARD_MIN_Y, BOARD_MAX_Y], color="0.85", linewidth=0.8)
        x += GRID_MM
    y = BOARD_MIN_Y
    while y <= BOARD_MAX_Y:
        ax.plot([BOARD_MIN_X, BOARD_MAX_X], [y, y], color="0.85", linewidth=0.8)
        y += GRID_MM

    half = BOX_SIZE_MM / 2.0
    spots = list(BOX_POSITIONS.items()) + [("reject", REJECT_POSITION)]
    for name, (cx, cy) in spots:
        colour = name if is_color_like(name) else "0.5"
        ax.add_patch(Rectangle((cx - half, cy - half), BOX_SIZE_MM, BOX_SIZE_MM,
                               facecolor=colour, alpha=0.25, edgecolor=colour))
        ax.text(cx, cy, name, ha="center", va="center", fontsize=8)
    for x0, y0, x1, y1 in hw.obstacles[len(spots):]:
        ax.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0, facecolor="0.3", alpha=0.6))

    planned = [(START_X, START_Y)] + trace_segments(START_X, START_Y, START_HEADING,
                                                    get_path(path_name))
    ax.plot([p[0] for p in planned], [p[1] for p in planned], "--", color="0.4",
            label="planned path")
    ax.plot([p[1] for p in hw.trace], [p[2] for p in hw.trace], color="tab:blue",
            label="simulated turning centre")
    ax.add_patch(Polygon(robot_outline(hw.x, hw.y, hw.theta), closed=True, fill=False,
                         edgecolor="tab:blue", label="robot at the end"))
    ax.plot([START_X], [START_Y], "o", color="black", label="start")

    ax.set_aspect("equal")
    ax.set_xlabel("x (mm)")
    ax.set_ylabel("y (mm)")
    ax.set_title("Simulated run: %s (untested on hardware)" % path_name)
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.08), ncol=2, fontsize=8)
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    fig.savefig(filename, dpi=120, bbox_inches="tight")
    plt.close(fig)
    print("picture saved to %s" % os.path.relpath(filename, ROOT))


def main(argv):
    parser = argparse.ArgumentParser(description="Run the Clawbot program in the simulator.")
    parser.add_argument("--mode", choices=MODES, default="path")
    parser.add_argument("--path", choices=path_names(), default=SELECTED_PATH)
    parser.add_argument("--slip-left", type=float, default=1.0,
                        help="fraction of encoder distance the left wheel really covers")
    parser.add_argument("--slip-right", type=float, default=1.0)
    parser.add_argument("--imu-drift", type=float, default=0.0, help="gyro drift, degrees a second")
    parser.add_argument("--imu-noise", type=float, default=0.0, help="gyro noise, degrees")
    parser.add_argument("--stop-at", type=float, default=None,
                        help="press a stop button at this simulated time, in ms")
    parser.add_argument("--no-boxes", action="store_true", help="leave the boxes out")
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--plot", action="store_true", help="save a picture in sim/out/")
    args = parser.parse_args(argv)

    hw = SimHardware(seed=args.seed, slip_left=args.slip_left, slip_right=args.slip_right,
                     imu_drift_dps=args.imu_drift, imu_noise_deg=args.imu_noise,
                     stop_press_ms=args.stop_at, include_boxes=not args.no_boxes)
    result = run(hw, args.mode, args.path)

    print("mode %s, path %s" % (args.mode, args.path))
    print("result: %s after %.1f simulated seconds" % (result, hw.time_ms() / 1000.0))
    print("true end: x %.0f mm, y %.0f mm, heading %.1f" % (hw.x, hw.y, hw.theta % 360.0))
    if args.mode == "path":
        px, py, ph = planned_end(args.path)
        print("planned end: x %.0f mm, y %.0f mm, heading %.1f" % (px, py, ph))
        print("miss: %.0f mm, %.1f degrees" % (distance_between(hw.x, hw.y, px, py),
                                              wrap_180(hw.theta - ph)))
    print("collisions: %d" % hw.collisions)
    print("Brain screen: %s" % " | ".join(hw.screen))
    for line in hw.console:
        print("console: %s" % line)
    print("Simulator result only. UNTESTED ON HARDWARE.")
    if args.plot:
        name = args.path if args.mode == "path" else args.mode
        save_plot(hw, args.path, os.path.join(HERE, "out", name + ".png"))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
