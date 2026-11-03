# bringup.py
#
# Two short programs for the first runs on a real robot. docs/BRINGUP.md
# says when to use each one.
#
#   sensor_check  shows live sensor readings and never moves a motor
#   motor_check   spins each motor slowly, one at a time, so you can see
#                 which way it turns while the wheels are off the ground

from settings import *


def sensor_check(robot):
    """Show live sensor readings until a stop button or the timeout.

    Returns "timeout". A stop button raises StopRequested as usual.
    """
    hw = robot.hw
    hw.optical_light(OPTICAL_LIGHT_PCT)
    start = hw.time_ms()
    while hw.time_ms() - start < SENSOR_CHECK_TIMEOUT_MS:
        distance = hw.distance_raw()
        if distance is None:
            distance_text = "Dist none"
        else:
            distance_text = "Dist %.0f mm" % distance
        robot.set_lines(["SENSOR CHECK",
                         "Head %.1f" % hw.heading(),
                         distance_text,
                         "Hue %.0f Br %.0f" % (hw.optical_hue(), hw.optical_brightness()),
                         "L/R = stop"], False)
        robot.tick()
    hw.optical_light(0)
    robot.set_lines(["SENSOR CHECK", "Timed out.", "Program ended."])
    return "timeout"


def _spin_one(robot, name, want, spin, stop, degrees):
    """Spin one motor for MOTOR_CHECK_MS. Returns how far it turned."""
    robot.set_lines(["MOTOR CHECK", name, "Want: " + want, "L/R = stop"])
    before = degrees()
    spin(MOTOR_CHECK_PCT)
    robot.pause(MOTOR_CHECK_MS)
    stop()
    robot.pause(MOTOR_CHECK_GAP_MS)
    turned = degrees() - before
    robot.hw.log("motor check: %s turned %.0f degrees" % (name, turned))
    return turned


def motor_check(robot):
    """Spin the left wheel, right wheel, arm and claw in turn.

    Lift the robot so the wheels are off the ground first, and move the arm
    and claw by hand to halfway so they have room to move. Watch that each
    part moves the way the screen says. If one goes the wrong way, change
    its *_REVERSED setting. Returns "done".
    """
    hw = robot.hw
    left = _spin_one(robot, "Left wheel", "forward",
                     lambda pct: hw.drive(pct, 0), hw.stop_drive,
                     lambda: hw.drive_degrees()[0])
    right = _spin_one(robot, "Right wheel", "forward",
                      lambda pct: hw.drive(0, pct), hw.stop_drive,
                      lambda: hw.drive_degrees()[1])
    arm = _spin_one(robot, "Arm", "up", hw.arm_spin, hw.arm_stop, hw.arm_degrees)
    claw = _spin_one(robot, "Claw", "close", hw.claw_spin, hw.claw_stop, hw.claw_degrees)
    robot.set_lines(["MOTOR CHECK DONE",
                     "L %.0f R %.0f" % (left, right),
                     "Arm %.0f Claw %.0f" % (arm, claw),
                     "0 = check cable"])
    return "done"
