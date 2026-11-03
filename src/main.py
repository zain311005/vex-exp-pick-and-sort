# main.py
#
# What runs when the program starts on the Brain. run() takes any hardware
# object, so the simulator and the tests call it with SimHardware instead.
#
# Milestone 1: calibrate the gyro, then do RUN_MODE (see settings.py).
# The pick-and-sort behaviour is added in milestone 3.

from settings import *
from hardware import VexHardware
from robot import Robot, StopRequested
from paths import get_path
from bringup import sensor_check, motor_check

MODES = ["sensor_check", "motor_check", "path"]


def settings_problem(mode, path_name):
    """A short message if the settings cannot run, otherwise None."""
    if mode not in MODES:
        return "Bad RUN_MODE"
    if mode == "path":
        try:
            get_path(path_name)
        except ValueError:
            return "Bad path setting"
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


def run(hw, mode=RUN_MODE, path_name=SELECTED_PATH):
    """Run the program on the given hardware. Returns a short result word."""
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

        if mode == "motor_check":
            hint = "Lift wheels!"
        else:
            hint = "Path " + path_name
        robot.set_lines(["Clawbot sorter", hint, "CHECK = start", "L/R = stop"])
        if not robot.wait_for_start():
            robot.set_lines(["Not started.", "Program ended."])
            return "no_start"
        robot.pause(START_DELAY_MS)
        if mode == "motor_check":
            return motor_check(robot)
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
