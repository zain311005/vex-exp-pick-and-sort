# clawbot.py
#
# GENERATED FILE - do not edit by hand.
# Built by tools/build_brain.py from config/settings.py and src/*.py.
# To change a setting, edit config/settings.py and run the build again.
#
# To use: create a new VEXcode EXP Python project, delete the template
# code, paste in this whole file, and download it to the Brain.
#
# UNTESTED ON HARDWARE. This file has only been run in the simulator and
# against a fake vex module. Work through docs/BRINGUP.md before trusting
# it on a robot, and keep a hand near the Brain's stop buttons.

from vex import *
import math


# ========================================================================
# from config/settings.py
# ========================================================================

# settings.py
#
# Every number the robot uses lives in this file: Smart Ports, speeds,
# thresholds, timeouts, paths and box positions. Code in src/ reads these
# names and never contains its own tuning values.
#
# Values marked MEASURE are estimates. Check them on your robot before
# you trust them. docs/ASSUMPTIONS.md lists where every value came from.


# ----------------------------------------------------------- Smart Ports
# Motor ports follow the official EXP Clawbot build instructions (rev 3):
# step 14 wires the drive motors, step 41 wires the arm and the claw.
LEFT_DRIVE_PORT = 6
RIGHT_DRIVE_PORT = 10
ARM_PORT = 3
CLAW_PORT = 4

# The stock Clawbot has no sensors. These two are added for this project.
DISTANCE_PORT = 5   # same port the Distance Sensor used in the earlier program
OPTICAL_PORT = 1    # a free port chosen for the Optical Sensor

LEFT_DRIVE_REVERSED = False
RIGHT_DRIVE_REVERSED = True   # the right motor is mounted facing the other way
ARM_REVERSED = False          # MEASURE: positive power must raise the arm
CLAW_REVERSED = False         # MEASURE: positive power must close the claw


# -------------------------------------------------------- Drive geometry
# The drive motors turn the two 3.25 in traction wheels directly. The omni
# wheels at the claw end spin freely, so the robot pivots about the middle
# of the traction wheel axle. That point is the "turning centre" that the
# position tracking follows.
WHEEL_TRAVEL_MM = 260.0   # 3.25 in wheel, 260 mm per turn (build parts list)
DRIVE_GEAR_RATIO = 1.0    # wheel turns per motor turn
TRACK_WIDTH_MM = 240.0    # MEASURE: left wheel centre to right wheel centre

# Robot outline, measured from the turning centre.
FRONT_MM = 330.0          # MEASURE: turning centre to the claw tips
REAR_MM = 80.0            # MEASURE: turning centre to the back of the robot
ROBOT_WIDTH_MM = 290.0    # MEASURE: widest point
SENSOR_OFFSET_MM = 200.0  # MEASURE: turning centre to the Distance Sensor face


# -------------------------------------------------------------- The field
# The 300 mm grid board. The origin is where line A crosses line 1.
# +x points east towards column D, +y points north towards row 6.
GRID_MM = 300.0
BOARD_MIN_X = -300.0
BOARD_MAX_X = 1200.0
BOARD_MIN_Y = -300.0
BOARD_MAX_Y = 1500.0

BALL_DIAMETER_MM = 150.0  # the balls being sorted are about 15 cm across
BOX_SIZE_MM = 254.0       # the boxes are 10 in by 10 in

# Box centres in mm. The original path uses almost the whole board, so the
# boxes sit off its edges: the colour boxes to the east, the reject spot to
# the west. Move them to suit your room. tests/test_paths.py checks that the
# robot outline on the original path stays BOX_CLEARANCE_MM away from every
# box, including while the claw swings round in a turn.
COLOURS = ["red", "green", "blue"]
BOX_POSITIONS = {
    "red": (1550.0, 1200.0),
    "green": (1550.0, 600.0),
    "blue": (1550.0, 0.0),
}
REJECT_POSITION = (-600.0, 600.0)  # where a ball of unknown colour is left
BOX_CLEARANCE_MM = 100.0


# ------------------------------------------------------------------ Paths
# The robot starts with its turning centre here, facing north.
START_X = 0.0
START_Y = -150.0
START_HEADING = 0.0

# "original" is the route from the assignment program, copied exactly.
# Each point is (x, y) in mm. The robot turns to face the next point and
# then drives straight to it. At the end it turns back to face north.
ORIGINAL_WAYPOINTS = [
    (0, 300), (600, 300), (600, 0), (900, 0), (900, 600), (300, 600),
    (300, 900), (0, 900), (0, 1200), (900, 1200),
    (900, 1350), (-150, 1350), (-150, -150), (0, -150),
]
ORIGINAL_FINAL_HEADING = 0.0

# Paths written directly as segments:
#   ("turn", h)  turn on the spot to compass heading h, in degrees
#   ("drive", d) drive d mm straight along the current heading
# A negative d drives backwards.
SEGMENT_PATHS = {
    "bringup_line": [("drive", 300), ("turn", 180), ("drive", 300), ("turn", 0)],
}

SELECTED_PATH = "original"


# --------------------------------------------------------------- Run mode
# What the program does once the gyro has calibrated. The first time the
# code runs on a robot, go through the modes in the order docs/BRINGUP.md
# gives:
#   "sensor_check"      show live sensor readings; no motor ever moves
#   "colour_calibrate"  record the Optical Sensor with the claw empty and
#                       with each ball in turn, then save the colour references
#   "motor_check"       after CHECK, spin each motor slowly, one at a time
#   "path"              after CHECK, drive SELECTED_PATH
RUN_MODE = "path"

START_DELAY_MS = 1000     # pause after CHECK so your hand is clear of the robot


# --------------------------------------------------------- Speeds (slow)
# Motor power is in percent. Defaults are deliberately slow.
LOOP_MS = 10              # every control loop runs once per LOOP_MS

DRIVE_MAX_PCT = 30.0
DRIVE_MIN_PCT = 7.0       # MEASURE: lowest power that still moves the robot
DRIVE_RAMP_PCT = 2.0      # speed added per loop while speeding up
DRIVE_KP = 0.3            # percent per mm of distance still to go
DRIVE_TOLERANCE_MM = 5.0
STEER_KP = 1.0            # percent per degree of heading error
STEER_MAX_PCT = 10.0

TURN_MAX_PCT = 25.0
TURN_MIN_PCT = 6.0        # MEASURE: lowest power that still turns the robot
TURN_KP = 0.8             # percent per degree of heading error
TURN_KD = 2.0             # percent per degree of change since the last loop
TURN_TOLERANCE_DEG = 1.5
TURN_SETTLE_LOOPS = 4     # loops in a row inside the tolerance before a turn ends

STOP_SETTLE_MS = 150      # time allowed for the robot to come to rest

MOTOR_CHECK_PCT = 20.0    # power for each motor in the motor check
MOTOR_CHECK_MS = 1000     # how long each motor spins in the motor check
MOTOR_CHECK_GAP_MS = 500  # pause after each motor in the motor check


# --------------------------------------------------------------- Timeouts
IMU_CALIBRATION_TIMEOUT_MS = 5000
START_WAIT_TIMEOUT_MS = 120000   # program ends if CHECK is not pressed in 2 minutes
TURN_TIMEOUT_MS = 6000
DRIVE_TIMEOUT_BASE_MS = 2000
DRIVE_TIMEOUT_MS_PER_MM = 15
SENSOR_CHECK_TIMEOUT_MS = 300000  # the sensor check ends after 5 minutes


# ---------------------------------------------------------------- Sensors
# Distance Sensor. object_distance() covers 20 mm to 2000 mm (VEX EXP Python
# API, Distance Sensor page). A reading outside that range, or one taken while
# the sensor says it sees nothing, is thrown away. src/distance.py explains
# the median and the "in range" rule.
DISTANCE_MIN_MM = 20.0
DISTANCE_MAX_MM = 2000.0
DISTANCE_SAMPLE_MS = 50   # VERIFY: take a new reading at most this often
DISTANCE_WINDOW = 5       # the median uses the last this-many readings
DISTANCE_MIN_VALID = 3    # valid readings the window needs before it counts
OBJECT_RANGE_MM = 400.0   # an object at this distance or nearer is "in range"

# Optical Sensor. src/colour.py explains the colour rule. hue() is 0 to 359
# degrees and brightness() is a percent (VEX EXP Python API, Optical Sensor).
OPTICAL_LIGHT_PCT = 50    # MEASURE: LED power, a whole number of percent
COLOUR_READS = 7          # readings taken for one colour decision
COLOUR_MIN_VOTES = 5      # how many of them must agree, or the answer is "unknown"
COLOUR_READ_MS = 30       # gap between those readings

# Reference hues used until you run the colour calibration, as
# (hue, tolerance) in degrees. These starting values are the middles of the
# hue ranges the Optical Sensor page gives for its own color() method:
# red 340 to 20, green 80 to 140, blue 200 to 240.
COLOUR_REFERENCES = {
    "red": (0.0, 20.0),
    "green": (110.0, 30.0),
    "blue": (220.0, 20.0),
}
COLOUR_GATE_BRIGHTNESS = 10.0  # MEASURE: a reading darker than this means nothing is there

# Colour calibration (RUN_MODE "colour_calibrate").
COLOUR_CAL_SAMPLES = 20        # readings for the empty claw and for each colour
COLOUR_CAL_MIN_GOOD = 15       # bright enough readings each colour needs
COLOUR_CAL_READ_MS = 50        # gap between calibration readings
COLOUR_MIN_BRIGHTNESS_GAP = 5.0  # a ball reading must beat the empty claw by this much
COLOUR_SPREAD_FACTOR = 3.0     # tolerance = this many times the spread of the readings
COLOUR_MIN_TOLERANCE_DEG = 8.0
COLOUR_MAX_TOLERANCE_DEG = 30.0
COLOUR_FILE = "colours.txt"          # the calibration, in the SD card's root folder
COLOUR_LOG_FILE = "colour_log.csv"   # every calibration reading, for tools/fit_colours.py


# ------------------------------------------------------------ Brain screen
# The assignment program showed five lines of up to 16 characters, so the
# messages are kept that short.
SCREEN_PERIOD_MS = 250    # how often the status lines are redrawn
SCREEN_ROWS = 5


# ========================================================================
# from src/geometry.py
# ========================================================================

# geometry.py
#
# Plain maths used by the robot and the simulator. Nothing in here talks to
# hardware, so it runs the same on the EXP Brain and on a laptop.
#
# Headings are compass degrees: 0 points north (+y), 90 points east (+x),
# and they increase clockwise, which matches the EXP Brain's inertial sensor.



def clamp(value, low, high):
    """Limit value to the range low..high."""
    if value < low:
        return low
    if value > high:
        return high
    return value


def wrap_180(angle):
    """Wrap an angle in degrees into the range -180 (inclusive) to 180."""
    return (angle + 180.0) % 360.0 - 180.0


def wrap_360(angle):
    """Wrap an angle in degrees into the range 0 (inclusive) to 360."""
    return angle % 360.0


def compass_vector(heading):
    """Unit vector (dx, dy) pointing along a compass heading."""
    rad = math.radians(heading)
    return math.sin(rad), math.cos(rad)


def bearing(x0, y0, x1, y1):
    """Compass heading from point 0 to point 1."""
    return wrap_360(math.degrees(math.atan2(x1 - x0, y1 - y0)))


def distance_between(x0, y0, x1, y1):
    """Straight-line distance between two points."""
    dx = x1 - x0
    dy = y1 - y0
    return math.sqrt(dx * dx + dy * dy)


def waypoints_to_segments(start_x, start_y, waypoints, final_heading):
    """Turn a list of (x, y) points into turn and drive segments.

    For each point the robot turns to face it, then drives straight to it.
    Points that repeat the previous point are skipped. After the last point
    the robot turns to final_heading.
    """
    segments = []
    x = start_x
    y = start_y
    for point in waypoints:
        px = float(point[0])
        py = float(point[1])
        length = distance_between(x, y, px, py)
        if length > 0.0:
            segments.append(("turn", bearing(x, y, px, py)))
            segments.append(("drive", length))
        x = px
        y = py
    segments.append(("turn", wrap_360(final_heading)))
    return segments


def trace_segments(start_x, start_y, start_heading, segments):
    """Where perfect segments would take the robot, as a list of (x, y).

    Used to check that a path really visits the points it should.
    """
    x = start_x
    y = start_y
    heading = start_heading
    points = []
    for kind, value in segments:
        if kind == "turn":
            heading = wrap_360(value)
        elif kind == "drive":
            dx, dy = compass_vector(heading)
            x += value * dx
            y += value * dy
            points.append((x, y))
        else:
            raise ValueError("unknown segment type: %s" % kind)
    return points


# ========================================================================
# from src/paths.py
# ========================================================================

# paths.py
#
# Paths are lists of segments:
#   ("turn", h)  turn on the spot to compass heading h (degrees)
#   ("drive", d) drive d mm along the current heading (negative = backwards)
#
# "original" is built from ORIGINAL_WAYPOINTS, the route copied exactly from
# the assignment program. Other paths are written as segments in settings.py.



def path_names():
    """Every path that can be selected, original first."""
    names = ["original"]
    for name in sorted(SEGMENT_PATHS):
        names.append(name)
    return names


def get_path(name):
    """The segments for the path called name."""
    if name == "original":
        return waypoints_to_segments(START_X, START_Y, ORIGINAL_WAYPOINTS,
                                     ORIGINAL_FINAL_HEADING)
    if name in SEGMENT_PATHS:
        segments = []
        for kind, value in SEGMENT_PATHS[name]:
            if kind not in ("turn", "drive"):
                raise ValueError("path %s has an unknown segment: %s" % (name, kind))
            segments.append((kind, float(value)))
        return segments
    raise ValueError("unknown path: %s" % name)


# ========================================================================
# from src/hardware.py
# ========================================================================

# hardware.py
#
# The only code that talks to the VEX EXP API. Everything else in src/ calls
# the methods of this class, and sim/sim_hardware.py provides a class with
# the same methods, so the same robot logic runs on the Brain and in the
# simulator.
#
# Each method is a thin wrapper around one documented VEX EXP Python call
# (https://api.vex.com/exp/home/python/index.html). Keep logic out of here.




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
        """LED power in whole percent. Above 0 turns it on, 0 turns it off."""
        self.optical.set_light_power(int(pct), PERCENT)

    # ---- Brain buttons, screen and console
    def check_pressed(self):
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

    # ---- SD card (FAT32, files in the root folder only)
    def sd_load(self, name):
        """Text of a file on the SD card, or None if there is no card or file."""
        if not self.brain.sdcard.is_inserted():
            return None
        try:
            return self.brain.sdcard.loadfile(name).decode("utf-8")
        except Exception:
            return None

    def sd_save(self, name, text):
        """Write text to a file on the SD card. Returns True if it was written."""
        if not self.brain.sdcard.is_inserted():
            return False
        try:
            self.brain.sdcard.savefile(name, bytearray(text, "utf-8"))
        except Exception:
            return False
        return True


# ========================================================================
# from src/robot.py
# ========================================================================

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

    def wait_for_check(self, timeout_ms):
        """Wait for a new press of CHECK. Returns False if none comes in time.

        A press only counts after CHECK has been seen released, so one long
        press (or the press that started the program) is never taken twice.
        """
        start = self.hw.time_ms()
        released = False
        while True:
            if self.hw.stop_pressed():
                self.hw.stop_all()
                raise StopRequested()
            pressing = self.hw.check_pressed()
            if pressing and released:
                return True
            if not pressing:
                released = True
            if self.hw.time_ms() - start > timeout_ms:
                return False
            self.hw.sleep_ms(LOOP_MS)

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


# ========================================================================
# from src/distance.py
# ========================================================================

# distance.py
#
# Turns raw Distance Sensor readings into a distance the robot can act on.
#
# The rules:
#   1. A reading is valid only if the sensor says it sees an object and the
#      value is inside DISTANCE_MIN_MM to DISTANCE_MAX_MM, the range the VEX
#      API page gives. Anything else is kept as "invalid".
#   2. The filter keeps the last DISTANCE_WINDOW readings, valid or not, and
#      takes a new one at most every DISTANCE_SAMPLE_MS.
#   3. The distance is the median of the valid readings in the window, but
#      only when there are at least DISTANCE_MIN_VALID of them. Otherwise
#      the distance is None, meaning "nothing seen".
#   4. An object is IN RANGE when that distance is OBJECT_RANGE_MM or less.
#
# With 5 readings and at least 3 valid, one wild reading cannot move the
# median past the good ones, and one missed reading does not lose the object.



def valid_distance(raw):
    """raw as a float in mm if it is a usable reading, otherwise None."""
    if raw is None:
        return None
    try:
        value = float(raw)
    except (TypeError, ValueError):
        return None
    if value != value:
        return None   # NaN
    if value < DISTANCE_MIN_MM or value > DISTANCE_MAX_MM:
        return None
    return value


def median(values):
    """Median of a non-empty list of numbers."""
    ordered = sorted(values)
    middle = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[middle]
    return (ordered[middle - 1] + ordered[middle]) / 2.0


class DistanceFilter:
    def __init__(self):
        self.readings = []
        self.last_ms = None

    def reset(self):
        self.readings = []
        self.last_ms = None

    def add(self, raw):
        """Put one raw reading (mm, or None for nothing seen) in the window."""
        self.readings.append(valid_distance(raw))
        if len(self.readings) > DISTANCE_WINDOW:
            self.readings.pop(0)

    def update(self, hw):
        """Read the sensor if DISTANCE_SAMPLE_MS has passed since last time."""
        now = hw.time_ms()
        if self.last_ms is None or now - self.last_ms >= DISTANCE_SAMPLE_MS:
            self.last_ms = now
            self.add(hw.distance_raw())

    def distance(self):
        """Median of the valid readings in mm, or None if too few are valid."""
        valid = [reading for reading in self.readings if reading is not None]
        if len(valid) < DISTANCE_MIN_VALID:
            return None
        return median(valid)

    def in_range(self):
        """True when an object is at OBJECT_RANGE_MM or nearer."""
        found = self.distance()
        return found is not None and found <= OBJECT_RANGE_MM

    def fill(self, robot):
        """Start again and take a full window of readings, then distance().

        The robot keeps ticking in between, so the stop button still works.
        Takes about DISTANCE_WINDOW times DISTANCE_SAMPLE_MS.
        """
        self.reset()
        while len(self.readings) < DISTANCE_WINDOW:
            self.update(robot.hw)
            robot.tick()
        return self.distance()


# ========================================================================
# from src/colour.py
# ========================================================================

# colour.py
#
# Works out the colour of the ball in the claw from the Optical Sensor.
# This is a calibrated rule, not machine learning: it compares the hue with
# reference hues that you record yourself in the calibration step, and it
# does not change itself while it runs.
#
# The rule for one reading:
#   1. Brightness gate. A reading darker than the gate means nothing is in
#      front of the sensor, so the answer is "none".
#   2. Nearest match. Otherwise find the reference hue nearest to the
#      reading's hue, going round the colour wheel (359 is next to 0).
#   3. Tolerance. If the reading is further from that hue than the colour's
#      tolerance, the answer is "unknown".
# read_colour() then takes COLOUR_READS readings and gives a colour only if
# at least COLOUR_MIN_VOTES of them agree. Otherwise it says "unknown".
#
# Calibration (RUN_MODE "colour_calibrate") records COLOUR_CAL_SAMPLES
# readings with the claw empty and with each ball in turn. A colour's
# reference hue is the average of its hues round the colour wheel, and its
# tolerance is COLOUR_SPREAD_FACTOR times how far the hues spread, kept
# between COLOUR_MIN_TOLERANCE_DEG and COLOUR_MAX_TOLERANCE_DEG. The gate
# sits halfway between the empty claw and the darkest ball.



NONE = "none"
UNKNOWN = "unknown"


# ------------------------------------------------------------------ maths
def average(values):
    """Plain mean of a non-empty list."""
    return sum(values) / float(len(values))


def circular_mean(angles):
    """Mean of angles in degrees, going round the circle.

    The plain mean of 350 and 10 is 180, which is the wrong side of the
    wheel. This gives 0.
    """
    s = 0.0
    c = 0.0
    for angle in angles:
        s += math.sin(math.radians(angle))
        c += math.cos(math.radians(angle))
    return wrap_360(math.degrees(math.atan2(s, c)))


def circular_spread(angles, centre):
    """Root mean square distance of the angles from centre, in degrees."""
    total = 0.0
    for angle in angles:
        error = wrap_180(angle - centre)
        total += error * error
    return math.sqrt(total / len(angles))


def fit_reference(hues):
    """(reference hue, tolerance) from one colour's calibration hues."""
    centre = circular_mean(hues)
    tolerance = clamp(COLOUR_SPREAD_FACTOR * circular_spread(hues, centre),
                      COLOUR_MIN_TOLERANCE_DEG, COLOUR_MAX_TOLERANCE_DEG)
    return (centre, tolerance)


def fit_calibration(empty, balls):
    """References and gate from calibration readings.

    empty is a list of (hue, brightness) taken with the claw empty. balls
    maps each colour name to its list of (hue, brightness). Returns
    (references, gate, problem). problem is None when it worked, or a short
    message naming the colour that had too few readings bright enough to use.
    """
    empty_brightness = average([b for h, b in empty])
    floor = empty_brightness + COLOUR_MIN_BRIGHTNESS_GAP
    references = {}
    darkest = None
    for name in COLOURS:
        good = [(h, b) for h, b in balls.get(name, []) if b >= floor]
        if len(good) < COLOUR_CAL_MIN_GOOD:
            return None, None, name + " too dark"
        references[name] = fit_reference([h for h, b in good])
        brightness = average([b for h, b in good])
        if darkest is None or brightness < darkest:
            darkest = brightness
    return references, (empty_brightness + darkest) / 2.0, None


def overlaps(references):
    """Pairs of colours whose hue ranges overlap, such as "red/blue"."""
    found = []
    for i in range(len(COLOURS)):
        for j in range(i + 1, len(COLOURS)):
            a = references[COLOURS[i]]
            b = references[COLOURS[j]]
            if abs(wrap_180(a[0] - b[0])) < a[1] + b[1]:
                found.append(COLOURS[i] + "/" + COLOURS[j])
    return found


# -------------------------------------------------------- classification
def nearest_colour(hue, references):
    """(name, error in degrees) of the reference hue nearest to hue."""
    best = None
    best_error = None
    for name in COLOURS:
        if name in references:
            error = abs(wrap_180(hue - references[name][0]))
            if best_error is None or error < best_error:
                best = name
                best_error = error
    return best, best_error


def classify(hue, brightness, references, gate):
    """One reading: a colour name, NONE or UNKNOWN."""
    if brightness < gate:
        return NONE
    name, error = nearest_colour(hue, references)
    if name is None or error > references[name][1]:
        return UNKNOWN
    return name


def vote(labels):
    """The label that at least COLOUR_MIN_VOTES readings agree on, else UNKNOWN."""
    best = UNKNOWN
    best_count = 0
    for label in labels:
        count = labels.count(label)
        if count > best_count:
            best = label
            best_count = count
    if best_count >= COLOUR_MIN_VOTES:
        return best
    return UNKNOWN


def read_colour(robot, references, gate):
    """Take COLOUR_READS readings and vote. Returns (answer, labels)."""
    hw = robot.hw
    labels = []
    while len(labels) < COLOUR_READS:
        labels.append(classify(hw.optical_hue(), hw.optical_brightness(), references, gate))
        robot.pause(COLOUR_READ_MS)
    return vote(labels), labels


# ---------------------------------------------------- saving and loading
def calibration_text(references, gate):
    """The calibration as the text stored in COLOUR_FILE."""
    lines = ["# colour calibration: name hue tolerance", "gate %.1f" % gate]
    for name in COLOURS:
        lines.append("%s %.1f %.1f" % (name, references[name][0], references[name][1]))
    return "\n".join(lines) + "\n"


def settings_text(references, gate):
    """The same calibration written as lines for config/settings.py."""
    lines = ["COLOUR_REFERENCES = {"]
    for name in COLOURS:
        lines.append('    "%s": (%.1f, %.1f),' % (name, references[name][0], references[name][1]))
    lines.append("}")
    lines.append("COLOUR_GATE_BRIGHTNESS = %.1f" % gate)
    return "\n".join(lines)


def parse_calibration(text):
    """(references, gate) from calibration_text(), or None if the text does
    not hold a sensible value for the gate and every colour."""
    references = {}
    gate = None
    for line in text.split("\n"):
        parts = line.split()
        if not parts or parts[0].startswith("#"):
            continue
        try:
            if parts[0] == "gate":
                key, value = parts
                gate = float(value)
            elif parts[0] in COLOURS:
                name, hue, tolerance = parts
                references[name] = (wrap_360(float(hue)), float(tolerance))
            else:
                return None
        except ValueError:
            return None
    if gate is None or gate < 0:
        return None
    for name in COLOURS:
        if name not in references:
            return None
        tolerance = references[name][1]
        if tolerance < COLOUR_MIN_TOLERANCE_DEG or tolerance > COLOUR_MAX_TOLERANCE_DEG:
            return None
    return references, gate


def load_colour_calibration(hw):
    """(references, gate, source). source is "SD card" when COLOUR_FILE on
    the SD card holds a good calibration, otherwise "settings"."""
    text = hw.sd_load(COLOUR_FILE)
    if text is not None:
        parsed = parse_calibration(text)
        if parsed is not None:
            return parsed[0], parsed[1], "SD card"
        hw.log("%s on the SD card is not usable, so settings.py is used" % COLOUR_FILE)
    return COLOUR_REFERENCES, COLOUR_GATE_BRIGHTNESS, "settings"


# ------------------------------------------------------------ calibration
def _collect(robot, prompt):
    """Wait for CHECK, then record COLOUR_CAL_SAMPLES (hue, brightness)
    readings. Returns None if CHECK is not pressed in time."""
    robot.set_lines(["COLOUR CALIBRATE", prompt, "then press CHECK", "L/R = stop"])
    if not robot.wait_for_check(START_WAIT_TIMEOUT_MS):
        return None
    robot.set_lines(["COLOUR CALIBRATE", prompt, "Reading...", "Keep it still"])
    samples = []
    while len(samples) < COLOUR_CAL_SAMPLES:
        samples.append((robot.hw.optical_hue(), robot.hw.optical_brightness()))
        robot.pause(COLOUR_CAL_READ_MS)
    return samples


def colour_calibrate(robot):
    """RUN_MODE "colour_calibrate". Returns "done", "failed" or "no_start".

    The readings go to the console as label,hue,brightness lines and to
    COLOUR_LOG_FILE on the SD card, so tools/fit_colours.py can check them.
    A good calibration is saved to COLOUR_FILE on the SD card and printed as
    lines you can paste into config/settings.py.
    """
    hw = robot.hw
    hw.optical_light(OPTICAL_LIGHT_PCT)
    empty = _collect(robot, "Claw empty")
    if empty is None:
        hw.optical_light(0)
        robot.set_lines(["Not started.", "Program ended."])
        return "no_start"
    balls = {}
    for name in COLOURS:
        samples = _collect(robot, name + " in claw")
        if samples is None:
            hw.optical_light(0)
            robot.set_lines(["Not finished.", "Program ended."])
            return "no_start"
        balls[name] = samples

    lines = ["label,hue,brightness"]
    for hue, brightness in empty:
        lines.append("empty,%.1f,%.1f" % (hue, brightness))
    for name in COLOURS:
        for hue, brightness in balls[name]:
            lines.append("%s,%.1f,%.1f" % (name, hue, brightness))
    for line in lines:
        hw.log(line)
    hw.sd_save(COLOUR_LOG_FILE, "\n".join(lines) + "\n")

    references, gate, problem = fit_calibration(empty, balls)
    if problem is not None:
        hw.log("colour calibration failed: " + problem)
        robot.set_lines(["CALIBRATE FAILED", problem, "Ball in claw?", "LED on?"])
        hw.optical_light(0)
        return "failed"

    saved = hw.sd_save(COLOUR_FILE, calibration_text(references, gate))
    hw.log("colour calibration for config/settings.py:")
    hw.log(settings_text(references, gate))
    close = overlaps(references)
    if close:
        hw.log("these colours look alike: " + ", ".join(close))
    result = ["Saved to SD" if saved else "No SD: console"]
    for name in COLOURS:
        result.append("%s %.0f +-%.0f" % (name, references[name][0], references[name][1]))
    result.append("Gate %.0f%s" % (gate, " CLOSE!" if close else ""))
    robot.set_lines(result)
    hw.optical_light(0)
    return "done"


# ========================================================================
# from src/bringup.py
# ========================================================================

# bringup.py
#
# Two short programs for the first runs on a real robot. docs/BRINGUP.md
# says when to use each one.
#
#   sensor_check  shows live sensor readings and never moves a motor
#   motor_check   spins each motor slowly, one at a time, so you can see
#                 which way it turns while the wheels are off the ground



def sensor_check(robot):
    """Show live sensor readings until a stop button or the timeout.

    The screen shows the heading, the filtered distance (IN when an object
    is in range), the raw hue and brightness, and the colour the rule in
    colour.py gives for the last COLOUR_READS readings.
    Returns "timeout". A stop button raises StopRequested as usual.
    """
    hw = robot.hw
    references, gate, source = load_colour_calibration(hw)
    hw.log("sensor check: colour references from " + source)
    hw.optical_light(OPTICAL_LIGHT_PCT)
    distance = DistanceFilter()
    labels = []
    start = hw.time_ms()
    while hw.time_ms() - start < SENSOR_CHECK_TIMEOUT_MS:
        distance.update(hw)
        found = distance.distance()
        if found is None:
            distance_text = "Dist none"
        elif distance.in_range():
            distance_text = "Dist %.0f IN" % found
        else:
            distance_text = "Dist %.0f mm" % found
        hue = hw.optical_hue()
        brightness = hw.optical_brightness()
        labels.append(classify(hue, brightness, references, gate))
        if len(labels) > COLOUR_READS:
            labels.pop(0)
        robot.set_lines(["SENSORS L/R=stop",
                         "Head %.1f" % hw.heading(),
                         distance_text,
                         "Hue %.0f Br %.0f" % (hue, brightness),
                         "Colour " + vote(labels)], False)
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


# ========================================================================
# from src/main.py
# ========================================================================

# main.py
#
# What runs when the program starts on the Brain. run() takes any hardware
# object, so the simulator and the tests call it with SimHardware instead.
#
# Calibrate the gyro, then do RUN_MODE (see settings.py). Milestone 2 added
# the colour calibration. The pick-and-sort behaviour comes in milestone 3.


MODES = ["sensor_check", "colour_calibrate", "motor_check", "path"]


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
        if mode == "colour_calibrate":
            return colour_calibrate(robot)

        if mode == "motor_check":
            hint = "Lift wheels!"
        else:
            hint = "Path " + path_name
        robot.set_lines(["Clawbot sorter", hint, "CHECK = start", "L/R = stop"])
        if not robot.wait_for_check(START_WAIT_TIMEOUT_MS):
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


main()
