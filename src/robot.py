# robot.py
#
# Robot behaviour that only needs a hardware object with the methods in
# hardware.py. It keeps track of where the robot is, turns, drives and
# follows paths. Every loop checks the stop button and has a timeout.
#
# Position tracking is dead reckoning: the average wheel distance is added
# along the gyro heading every loop. Nothing ever corrects it from outside,
# so small errors (wheel slip, a bump) build up over a run. Expect the
# robot to be a little off after a long path.

from settings import *
from geometry import clamp, wrap_180, wrap_360, compass_vector


class StopRequested(Exception):
    """Raised from any loop when a stop button is pressed."""
    pass


class Robot:
    def __init__(self, hw):
        self.hw = hw
        self.x = START_X
        self.y = START_Y
        self.target_heading = START_HEADING
        self.last_wheel_mm = 0.0
        self.lines = []
        self.last_screen_ms = None
        self.last_found = None

    # ---------------------------------------------------- position tracking
    def wheel_mm(self):
        """Average distance the two drive wheels have rolled, in mm."""
        left, right = self.hw.drive_degrees()
        return (left + right) / 2.0 * WHEEL_TRAVEL_MM * DRIVE_GEAR_RATIO / 360.0

    def reset_pose(self, x, y, heading):
        self.hw.reset_drive_degrees()
        self.hw.set_heading(heading)
        self.x = x
        self.y = y
        self.target_heading = heading
        self.last_wheel_mm = 0.0

    def update(self):
        """Check the stop button, update the position, refresh the screen."""
        if self.hw.stop_pressed():
            self.hw.stop_all()
            raise StopRequested()
        travelled = self.wheel_mm()
        step = travelled - self.last_wheel_mm
        self.last_wheel_mm = travelled
        dx, dy = compass_vector(self.hw.heading())
        self.x += step * dx
        self.y += step * dy
        self.refresh_screen(False)

    def tick(self):
        """One pass of the control loop."""
        self.update()
        self.hw.sleep_ms(LOOP_MS)

    def pause(self, ms):
        """Wait while still tracking position and watching the stop button."""
        end = self.hw.time_ms() + ms
        while self.hw.time_ms() < end:
            self.tick()

    # --------------------------------------------------------------- screen
    def set_lines(self, lines, force=True):
        """Choose the lines shown on the Brain screen.

        force=True redraws at once. A loop that changes the lines on every
        pass uses force=False, so the screen is redrawn only every
        SCREEN_PERIOD_MS.
        """
        self.lines = list(lines)[:SCREEN_ROWS]
        self.refresh_screen(force)

    def refresh_screen(self, force):
        now = self.hw.time_ms()
        if force or self.last_screen_ms is None or now - self.last_screen_ms >= SCREEN_PERIOD_MS:
            self.last_screen_ms = now
            self.hw.show(self.lines)

    # ------------------------------------------------------- start and stop
    def calibrate(self):
        """Calibrate the gyro. Returns False if it does not finish in time."""
        self.hw.start_imu_calibration()
        start = self.hw.time_ms()
        while self.hw.imu_calibrating():
            if self.hw.time_ms() - start > IMU_CALIBRATION_TIMEOUT_MS:
                return False
            if self.hw.stop_pressed():
                self.hw.stop_all()
                raise StopRequested()
            self.hw.sleep_ms(LOOP_MS)
        return True

    def wait_for_start(self):
        """Wait for CHECK. Returns False if nobody presses it in time."""
        start = self.hw.time_ms()
        while not self.hw.start_pressed():
            if self.hw.time_ms() - start > START_WAIT_TIMEOUT_MS:
                return False
            if self.hw.stop_pressed():
                self.hw.stop_all()
                raise StopRequested()
            self.hw.sleep_ms(LOOP_MS)
        return True

    def stop_drive(self):
        """Stop the wheels and give the robot time to come to rest."""
        self.hw.stop_drive()
        self.pause(STOP_SETTLE_MS)

    # --------------------------------------------------------------- motion
    def turn_to(self, target):
        """Turn on the spot to a compass heading. Returns "done" or "timeout"."""
        target = wrap_360(target)
        self.target_heading = target
        start = self.hw.time_ms()
        previous = wrap_180(target - self.hw.heading())
        settled = 0
        while settled < TURN_SETTLE_LOOPS:
            if self.hw.time_ms() - start > TURN_TIMEOUT_MS:
                self.stop_drive()
                return "timeout"
            error = wrap_180(target - self.hw.heading())
            if abs(error) <= TURN_TOLERANCE_DEG:
                settled += 1
                power = 0.0
            else:
                settled = 0
                power = TURN_KP * error + TURN_KD * (error - previous)
                power = clamp(power, -TURN_MAX_PCT, TURN_MAX_PCT)
                if abs(power) < TURN_MIN_PCT:
                    if error > 0:
                        power = TURN_MIN_PCT
                    else:
                        power = -TURN_MIN_PCT
            previous = error
            self.hw.drive(power, -power)
            self.tick()
        self.stop_drive()
        return "done"

    def drive(self, distance_mm, heading, watch=None):
        """Drive distance_mm along a compass heading. Negative drives backwards.

        Speed ramps up, then slows in proportion to the distance left, and a
        heading-hold term keeps the robot on its line.

        watch, if given, is called every loop (only when driving forwards)
        with the distance still to go. If it returns anything other than
        None the robot stops and drive returns ("object", that value).

        Returns ("done", None), ("timeout", None) or ("object", value).
        """
        if distance_mm >= 0:
            direction = 1.0
        else:
            direction = -1.0
        target = abs(distance_mm)
        start_mm = self.wheel_mm()
        start = self.hw.time_ms()
        limit = DRIVE_TIMEOUT_BASE_MS + target * DRIVE_TIMEOUT_MS_PER_MM
        speed = 0.0
        while True:
            remaining = target - (self.wheel_mm() - start_mm) * direction
            if remaining <= DRIVE_TOLERANCE_MM:
                self.stop_drive()
                return ("done", None)
            if self.hw.time_ms() - start > limit:
                self.stop_drive()
                return ("timeout", None)
            if watch is not None and direction > 0:
                found = watch(remaining)
                if found is not None:
                    self.stop_drive()
                    return ("object", found)
            want = clamp(DRIVE_MIN_PCT + DRIVE_KP * remaining, DRIVE_MIN_PCT, DRIVE_MAX_PCT)
            if want < speed:
                speed = want
            else:
                speed = min(want, speed + DRIVE_RAMP_PCT)
            steer = clamp(STEER_KP * wrap_180(heading - self.hw.heading()),
                          -STEER_MAX_PCT, STEER_MAX_PCT)
            self.hw.drive(direction * speed + steer, direction * speed - steer)
            self.tick()

    def follow_segments(self, segments, watch=None, first=0):
        """Run segments in order, starting at index first.

        Returns (result, index): result is "done", "timeout" or "object",
        index is the segment that ended the run (len(segments) when done).
        For "object" the found value is kept in self.last_found.
        """
        self.last_found = None
        index = first
        while index < len(segments):
            kind, value = segments[index]
            self.set_lines(["Segment %d/%d" % (index + 1, len(segments)),
                            "%s %.0f" % (kind, value),
                            "X %.0f Y %.0f" % (self.x, self.y),
                            "L/R = stop"])
            if kind == "turn":
                if self.turn_to(value) == "timeout":
                    return ("timeout", index)
            elif kind == "drive":
                result, found = self.drive(value, self.target_heading, watch)
                if result == "timeout":
                    return ("timeout", index)
                if result == "object":
                    self.last_found = found
                    return ("object", index)
            else:
                raise ValueError("unknown segment type: %s" % kind)
            index += 1
        return ("done", index)
