# arm.py
#
# Moving the arm and the claw. Positions are motor degrees counted from the
# homed position: the arm all the way down and the claw wide open.
#
# There are no limit switches, so the code finds the ends of travel by
# stalling: it pushes gently and waits until the motor stops turning. A
# motor that turns less than STALL_DEG in STALL_MS has reached a stop. Every
# move has a time limit and the stop button works throughout.

from settings import *
from geometry import clamp


def run_until_stalled(robot, spin, stop, degrees, pct, timeout_ms):
    """Spin one motor at pct until it stalls. True if it stalled, False if
    timeout_ms passed first. The motor is stopped either way."""
    hw = robot.hw
    start = hw.time_ms()
    window_start = start
    window_degrees = degrees()
    spin(pct)
    while True:
        robot.tick()
        now = hw.time_ms()
        if now - window_start >= STALL_MS:
            if abs(degrees() - window_degrees) < STALL_DEG:
                stop()
                return True
            window_start = now
            window_degrees = degrees()
        if now - start > timeout_ms:
            stop()
            return False


def home(robot):
    """Push the arm down and the claw open onto their stops, and call those
    positions zero. Returns None, or a short message if one did not stop."""
    hw = robot.hw
    if not run_until_stalled(robot, hw.arm_spin, hw.arm_stop, hw.arm_degrees,
                             -ARM_HOME_PCT, HOME_TIMEOUT_MS):
        return "arm not homed"
    hw.reset_arm_degrees()
    if not run_until_stalled(robot, hw.claw_spin, hw.claw_stop, hw.claw_degrees,
                             -CLAW_HOME_PCT, HOME_TIMEOUT_MS):
        return "claw not homed"
    hw.reset_claw_degrees()
    return None


def move_arm(robot, target):
    """Move the arm to target degrees. True when it gets there, False if
    ARM_TIMEOUT_MS passes first. The arm motor holds where it stops."""
    hw = robot.hw
    start = hw.time_ms()
    while True:
        error = target - hw.arm_degrees()
        if abs(error) <= ARM_TOLERANCE_DEG:
            hw.arm_stop()
            return True
        if hw.time_ms() - start > ARM_TIMEOUT_MS:
            hw.arm_stop()
            return False
        power = clamp(ARM_KP * error, -ARM_MAX_PCT, ARM_MAX_PCT)
        if abs(power) < ARM_MIN_PCT:
            if error > 0:
                power = ARM_MIN_PCT
            else:
                power = -ARM_MIN_PCT
        hw.arm_spin(power)
        robot.tick()


def close_claw(robot):
    """Close the claw until it stops on something, or shuts. Returns the
    claw position where it stopped, or None if it never stopped."""
    hw = robot.hw
    if not run_until_stalled(robot, hw.claw_spin, hw.claw_stop, hw.claw_degrees,
                             CLAW_CLOSE_PCT, CLAW_TIMEOUT_MS):
        return None
    return hw.claw_degrees()


def open_claw(robot):
    """Open the claw onto its open stop. True when it is open."""
    hw = robot.hw
    return run_until_stalled(robot, hw.claw_spin, hw.claw_stop, hw.claw_degrees,
                             -CLAW_OPEN_PCT, CLAW_TIMEOUT_MS)


def holding_ball(claw_stopped_at, brightness, gate):
    """The claw holds a ball when it stopped well short of fully closed and
    the Optical Sensor in the claw sees something bright enough."""
    if claw_stopped_at is None:
        return False
    return (claw_stopped_at < CLAW_EMPTY_CLOSED_DEG - CLAW_GRIP_MARGIN_DEG
            and brightness >= gate)
