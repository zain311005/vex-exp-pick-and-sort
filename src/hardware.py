# hardware.py
#
# The only code that talks to the VEX EXP API. Everything else in src/ calls
# the methods of this class, and sim/sim_hardware.py provides a class with
# the same methods, so the same robot logic runs on the Brain and in the
# simulator.
#
# Each method is a thin wrapper around one documented VEX EXP Python call
# (https://api.vex.com/exp/home/python/index.html). Keep logic out of here.

try:
    from vex import *
except ImportError:
    # On a laptop there is no vex module. The simulator supplies its own
    # hardware class, so nothing below is used there.
    pass

from settings import *


def smart_port(number):
    """Ports.PORT1 .. Ports.PORT10 from a plain port number."""
    return getattr(Ports, "PORT%d" % number)


class VexHardware:
    def __init__(self):
        self.brain = Brain()
        self.imu = Inertial()
        self.left = Motor(smart_port(LEFT_DRIVE_PORT), GearSetting.RATIO_18_1,
                          LEFT_DRIVE_REVERSED)
        self.right = Motor(smart_port(RIGHT_DRIVE_PORT), GearSetting.RATIO_18_1,
                           RIGHT_DRIVE_REVERSED)
        self.arm = Motor(smart_port(ARM_PORT), GearSetting.RATIO_18_1, ARM_REVERSED)
        self.claw = Motor(smart_port(CLAW_PORT), GearSetting.RATIO_18_1, CLAW_REVERSED)
        self.distance = Distance(smart_port(DISTANCE_PORT))
        self.optical = Optical(smart_port(OPTICAL_PORT))
        self.left.set_stopping(BRAKE)
        self.right.set_stopping(BRAKE)
        self.arm.set_stopping(HOLD)
        self.claw.set_stopping(HOLD)

    # ---- time
    def time_ms(self):
        return self.brain.timer.time(MSEC)

    def sleep_ms(self, ms):
        wait(ms, MSEC)

    # ---- drive
    def drive(self, left_pct, right_pct):
        self.left.spin(FORWARD, left_pct, PERCENT)
        self.right.spin(FORWARD, right_pct, PERCENT)

    def stop_drive(self):
        self.left.stop()
        self.right.stop()

    def drive_degrees(self):
        return self.left.position(DEGREES), self.right.position(DEGREES)

    def reset_drive_degrees(self):
        self.left.set_position(0, DEGREES)
        self.right.set_position(0, DEGREES)

    # ---- inertial sensor (inside the Brain)
    def start_imu_calibration(self):
        self.imu.calibrate()

    def imu_calibrating(self):
        return self.imu.is_calibrating()

    def heading(self):
        return self.imu.heading(DEGREES)

    def set_heading(self, heading):
        self.imu.set_heading(heading, DEGREES)

    # ---- arm and claw
    def arm_spin(self, pct):
        self.arm.spin(FORWARD, pct, PERCENT)

    def arm_stop(self):
        self.arm.stop()

    def arm_degrees(self):
        return self.arm.position(DEGREES)

    def reset_arm_degrees(self):
        self.arm.set_position(0, DEGREES)

    def claw_spin(self, pct):
        self.claw.spin(FORWARD, pct, PERCENT)

    def claw_stop(self):
        self.claw.stop()

    def claw_degrees(self):
        return self.claw.position(DEGREES)

    def reset_claw_degrees(self):
        self.claw.set_position(0, DEGREES)

    def claw_current(self):
        return self.claw.current()

    def stop_all(self):
        self.left.stop()
        self.right.stop()
        self.arm.stop()
        self.claw.stop()

    # ---- sensors
    def distance_raw(self):
        """Distance in mm to the nearest object, or None if nothing is seen."""
        if not self.distance.is_object_detected():
            return None
        return self.distance.object_distance(MM)

    def optical_hue(self):
        return self.optical.hue()

    def optical_brightness(self):
        return self.optical.brightness()

    def optical_near(self):
        return self.optical.is_near_object()

    def optical_light(self, pct):
        """LED on at pct percent, or off when pct is 0."""
        if pct > 0:
            self.optical.set_light(LEDStateType.ON)
            self.optical.set_light_power(pct, PERCENT)
        else:
            self.optical.set_light(LEDStateType.OFF)

    # ---- Brain buttons, screen and console
    def start_pressed(self):
        return self.brain.buttonCheck.pressing()

    def stop_pressed(self):
        return self.brain.buttonLeft.pressing() or self.brain.buttonRight.pressing()

    def show(self, lines):
        self.brain.screen.clear_screen()
        row = 1
        for text in lines:
            self.brain.screen.set_cursor(row, 1)
            self.brain.screen.print(text)
            row += 1

    def log(self, text):
        print(text)

    def beep(self):
        self.brain.play_sound(SoundType.TADA)
