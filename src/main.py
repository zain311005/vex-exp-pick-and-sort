# main.py
#
# What runs when the program starts on the Brain. run() takes any hardware
# object, so the simulator and the tests call it with SimHardware instead.
#
# Calibrate the gyro, then do RUN_MODE (see settings.py): a bring-up check,
# the colour calibration, a plain drive along a path, or the sort itself.

from settings import *
from hardware import VexHardware
from robot import Robot, StopRequested
from paths import get_path
from colour import colour_calibrate, load_colour_calibration
from bringup import sensor_check, motor_check
from mission import Mission, on_board

MODES = ["sensor_check", "colour_calibrate", "motor_check", "path", "sort"]


def settings_problem(mode, path_name):
    """A short message if the settings cannot run, otherwise None."""
    if mode not in MODES:
        return "Bad RUN_MODE"
    if mode == "path" or mode == "sort":
        try:
            get_path(path_name)
        except ValueError:
            return "Bad path setting"
    if mode == "sort":
        if UNKNOWN_COLOUR_ACTION != "reject" and UNKNOWN_COLOUR_ACTION != "stop":
            return "Bad unknown rule"
        for spot in list(BOX_POSITIONS.values()) + [REJECT_POSITION]:
            if on_board(spot[0], spot[1], -BOX_SIZE_MM / 2.0):
                return "Box on the board"
    return None


def run_path(robot, path_name):
    """Drive one path and show how it went. Returns "done" or "timeout"."""
    hw = robot.hw
    robot.reset_pose(START_X, START_Y, START_HEADING)
    start_ms = hw.time_ms()
    result, index = robot.follow_segments(get_path(path_name))
    seconds = (hw.time_ms() - start_ms) / 1000.0
    hw.log("path %s %s segment %d time %.1f s x %.0f y %.0f" % (
        path_name, result, index, seconds, robot.x, robot.y))
    if result == "done":
        robot.set_lines(["PATH COMPLETE", "Time %.1f s" % seconds,
                         "X %.0f Y %.0f" % (robot.x, robot.y),
                         "Heading %.1f" % hw.heading()])
        hw.beep()
    else:
        robot.set_lines(["PATH STOPPED", "Reason: " + result,
                         "At segment %d" % (index + 1)])
    return result


def run_sort(robot, path_name, references, gate):
    """Search the path and sort the balls. Returns "done" or "failed"."""
    hw = robot.hw
    hw.optical_light(OPTICAL_LIGHT_PCT)
    robot.reset_pose(START_X, START_Y, START_HEADING)
    result = Mission(robot, references, gate, path_name).run()
    hw.optical_light(0)
    return result


def run(hw, mode=RUN_MODE, path_name=None):
    """Run the program on the given hardware. Returns a short result word.

    path_name defaults to SORT_PATH for the sort and SELECTED_PATH otherwise.
    """
    if path_name is None:
        if mode == "sort":
            path_name = SORT_PATH
        else:
            path_name = SELECTED_PATH
    robot = Robot(hw)
    problem = settings_problem(mode, path_name)
    if problem is not None:
        hw.log("settings problem: %s (mode %s, path %s)" % (problem, mode, path_name))
        robot.set_lines([problem, "Fix settings.py", "Program ended."])
        return "bad_setting"
    try:
        robot.set_lines(["Clawbot sorter", "Calibrating gyro", "Keep robot still"])
        if not robot.calibrate():
            robot.set_lines(["Gyro calibration", "timed out.", "Restart program"])
            return "calibration_timeout"
        if mode == "sensor_check":
            return sensor_check(robot)
        if mode == "colour_calibrate":
            return colour_calibrate(robot)

        lines = ["Clawbot sorter"]
        if mode == "motor_check":
            lines.append("Lift wheels!")
        elif mode == "sort":
            references, gate, source = load_colour_calibration(hw)
            lines.append("Sort " + path_name)
            lines.append("Colours " + source)
        else:
            lines.append("Path " + path_name)
        robot.set_lines(lines + ["CHECK = start", "L/R = stop"])
        if not robot.wait_for_check(START_WAIT_TIMEOUT_MS):
            robot.set_lines(["Not started.", "Program ended."])
            return "no_start"
        robot.pause(START_DELAY_MS)
        if mode == "motor_check":
            return motor_check(robot)
        if mode == "sort":
            return run_sort(robot, path_name, references, gate)
        return run_path(robot, path_name)
    except StopRequested:
        hw.stop_all()
        hw.show(["STOPPED", "Stop pressed"])
        return "stopped"
    except Exception:
        hw.stop_all()
        raise


def main():
    run(VexHardware())
