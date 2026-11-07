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
CHASSIS_FRONT_MM = 200.0  # MEASURE: turning centre to the front of the chassis, under the claw
CLAW_PALM_MM = 230.0      # MEASURE: turning centre to the back of the claw's opening


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
# the south. Move them to suit your room. tests/test_paths.py checks that the
# robot outline on every path stays BOX_CLEARANCE_MM away from every box,
# including while the claw swings round in a turn.
COLOURS = ["red", "green", "blue"]
BOX_POSITIONS = {
    "red": (1550.0, 1200.0),
    "green": (1550.0, 600.0),
    "blue": (1550.0, 0.0),
}
REJECT_POSITION = (450.0, -650.0)  # where a ball of unknown colour is left
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
    # A loop round the board for sorting: north up line A, east along row 6,
    # south down column D and back west. Put the balls on the west and north
    # sides, on the line, at least 450 mm from a corner. Keep the east and
    # south sides clear: the robot crosses them on its way to the boxes.
    # It only sees straight ahead, so a ball beside its path is not seen,
    # and one within about 22 cm of where it drives can be clipped.
    "sort_loop": [("drive", 1500), ("turn", 90), ("drive", 900), ("turn", 180),
                  ("drive", 1500), ("turn", 270), ("drive", 900), ("turn", 0)],
}

SELECTED_PATH = "original"    # the path RUN_MODE "path" drives
SORT_PATH = "sort_loop"       # the path RUN_MODE "sort" searches along


# --------------------------------------------------------------- Run mode
# What the program does once the gyro has calibrated. The first time the
# code runs on a robot, go through the modes in the order docs/BRINGUP.md
# gives:
#   "sensor_check"      show live sensor readings; no motor ever moves
#   "colour_calibrate"  record the Optical Sensor with the claw empty and
#                       with each ball in turn, then save the colour references
#   "motor_check"       after CHECK, spin each motor slowly, one at a time
#   "path"              after CHECK, drive SELECTED_PATH
#   "sort"              after CHECK, search along SELECTED_PATH and sort the balls
# The default is "sensor_check", so a fresh copy never drives off by itself.
RUN_MODE = "sensor_check"

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
DRIVE_STALL_MM = 5.0      # a drive that moves less than this ...
DRIVE_STALL_MS = 500      # ... in this long is stuck against something, so it stops

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
HOME_TIMEOUT_MS = 4000
ARM_TIMEOUT_MS = 4000
CLAW_TIMEOUT_MS = 2500
APPROACH_TIMEOUT_MS = 10000
CREEP_TIMEOUT_MS = 6000
BLOCKED_TIMEOUT_MS = 120000   # how long "clear the way" waits for CHECK
MISSION_TIMEOUT_MS = 900000   # a whole sort may take at most 15 minutes


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


# ----------------------------------------------------------- Arm and claw
# Positions are motor degrees, counted from where the arm and claw stop when
# they are homed at the start of a sort: the arm all the way down and the
# claw wide open. The arm motor drives a 12 tooth gear into the 60 tooth gear
# on the arm (EXP Clawbot build instructions), so 5 motor degrees lift the
# arm about 1 degree. The sensor check shows both positions while you move
# them by hand, which is how to find your values.
ARM_SEARCH_DEG = 0.0      # MEASURE: arm while looking for balls (claw down and open)
ARM_GRAB_DEG = 0.0        # MEASURE: arm when the claw closes on a ball
ARM_CARRY_DEG = 150.0     # MEASURE: ball clear of the floor and of the Distance Sensor
ARM_DROP_DEG = 400.0      # MEASURE: bottom of the ball above the box rim
ARM_KP = 0.5              # percent per degree of arm error
ARM_MAX_PCT = 40.0
ARM_MIN_PCT = 8.0         # MEASURE: lowest power that still moves the arm
ARM_TOLERANCE_DEG = 10.0
ARM_HOME_PCT = 15.0       # gentle push down onto the arm's lowest point
CLAW_HOME_PCT = 15.0      # gentle push open onto the claw's open stop
CLAW_CLOSE_PCT = 25.0     # grip power; the claw stops when it meets the ball
CLAW_OPEN_PCT = 25.0
CLAW_EMPTY_CLOSED_DEG = 120.0  # MEASURE: where the claw stops when it closes on nothing
CLAW_GRIP_MARGIN_DEG = 20.0    # stopping this far short of that means a ball is held
STALL_DEG = 3.0           # a motor that turns less than this ...
STALL_MS = 300            # ... in this long has reached a stop


# ---------------------------------------------------------------- Sorting
# RUN_MODE "sort". src/mission.py describes the states and what happens when
# something goes wrong. The robot searches along SELECTED_PATH.
APPROACH_PCT = 15.0       # slow drive up to a ball
APPROACH_STOP_MM = 100.0  # stop when the ball is this close to the Distance Sensor
APPROACH_MAX_MM = 700.0   # give up if the ball is not reached within this distance
OBJECT_LOST_MS = 1000     # no valid distance for this long means the object has gone
CREEP_PCT = 8.0           # then creep forward until the Optical Sensor sees the ball
CREEP_MAX_MM = 150.0
IN_CLAW_READS = 3         # bright readings in a row that mean the ball is in the claw
GRAB_TRIES = 2
GRAB_RETRY_BACKUP_MM = 100.0
OBSTACLE_STOP_MM = 150.0  # anything this close that is not a ball to fetch stops the robot
IGNORE_RADIUS_MM = 200.0  # after giving up on an object, ignore anything this near it
BOARD_MARGIN_MM = 0.0     # an object only counts as a ball if it is on the board
UNKNOWN_COLOUR_ACTION = "reject"  # "reject": take it to REJECT_POSITION; "stop": stop there
BOX_STAGING_MM = 400.0    # line up this far back from the drop point, and back out to it
DROP_REACH_MM = 310.0     # MEASURE: turning centre to the held ball's centre, arm at ARM_DROP_DEG
DROP_INSET_MM = 90.0      # put the ball's centre this far inside the box's near edge
RELEASE_WAIT_MS = 800
RELEASE_TRIES = 2
NAV_TRIES = 3             # times to ask for the way to be cleared before giving up
ARRIVE_TOLERANCE_MM = 30.0  # this near a point counts as being there already


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
        self.screen_source = None   # if set, called for fresh lines at each redraw
        self.last_found = None
        self.last_driven_mm = 0.0

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
            if self.screen_source is not None:
                self.lines = list(self.screen_source())[:SCREEN_ROWS]
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

        If the wheels move less than DRIVE_STALL_MM in DRIVE_STALL_MS the
        robot is pushing against something, so it stops and says "stuck".

        Returns ("done", None), ("timeout", None), ("stuck", None) or
        ("object", value). Afterwards last_driven_mm says how far it went.
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
        stall_ms = start
        stall_mm = start_mm
        while True:
            remaining = target - (self.wheel_mm() - start_mm) * direction
            if remaining <= DRIVE_TOLERANCE_MM:
                self.stop_drive()
                self.last_driven_mm = (self.wheel_mm() - start_mm) * direction
                return ("done", None)
            now = self.hw.time_ms()
            if now - start > limit:
                self.stop_drive()
                self.last_driven_mm = (self.wheel_mm() - start_mm) * direction
                return ("timeout", None)
            if now - stall_ms >= DRIVE_STALL_MS:
                if abs(self.wheel_mm() - stall_mm) < DRIVE_STALL_MM:
                    self.stop_drive()
                    self.last_driven_mm = (self.wheel_mm() - start_mm) * direction
                    return ("stuck", None)
                stall_ms = now
                stall_mm = self.wheel_mm()
            if watch is not None and direction > 0:
                found = watch(remaining)
                if found is not None:
                    self.stop_drive()
                    self.last_driven_mm = (self.wheel_mm() - start_mm) * direction
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

    def drive_until(self, pct, heading, check, max_mm, timeout_ms):
        """Drive straight at a steady pct power along heading until check()
        returns something other than None. Negative pct drives backwards.

        Returns what check() returned, or "too_far" after max_mm,
        "timeout" after timeout_ms, or "stuck" if the wheels stop moving as
        in drive(). The robot is stopped either way.
        """
        start_mm = self.wheel_mm()
        start = self.hw.time_ms()
        stall_ms = start
        stall_mm = start_mm
        while True:
            outcome = check()
            if outcome is not None:
                self.stop_drive()
                return outcome
            if abs(self.wheel_mm() - start_mm) >= max_mm:
                self.stop_drive()
                return "too_far"
            now = self.hw.time_ms()
            if now - start > timeout_ms:
                self.stop_drive()
                return "timeout"
            if now - stall_ms >= DRIVE_STALL_MS:
                if abs(self.wheel_mm() - stall_mm) < DRIVE_STALL_MM:
                    self.stop_drive()
                    return "stuck"
                stall_ms = now
                stall_mm = self.wheel_mm()
            steer = clamp(STEER_KP * wrap_180(heading - self.hw.heading()),
                          -STEER_MAX_PCT, STEER_MAX_PCT)
            self.hw.drive(pct + steer, pct - steer)
            self.tick()

    def follow_segments(self, segments, watch=None, first=0):
        """Run segments in order, starting at index first.

        Returns (result, index): result is "done", "timeout", "stuck" or
        "object", index is the segment that ended the run (len(segments)
        when done). For "object" the found value is kept in self.last_found.
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
                if result == "object":
                    self.last_found = found
                    return ("object", index)
                if result != "done":
                    return (result, index)
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
# from src/arm.py
# ========================================================================

# arm.py
#
# Moving the arm and the claw. Positions are motor degrees counted from the
# homed position: the arm all the way down and the claw wide open.
#
# There are no limit switches, so the code finds the ends of travel by
# stalling: it pushes gently and waits until the motor stops turning. A
# motor that turns less than STALL_DEG in STALL_MS has reached a stop. Every
# move has a time limit and the stop button works throughout.



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


# ========================================================================
# from src/mission.py
# ========================================================================

# mission.py
#
# RUN_MODE "sort": search along SELECTED_PATH, and whenever a ball turns up,
# fetch it, read its colour and drop it in that colour's box.
#
# The states, in the order they normally run:
#   FOLLOW_PATH  drive the path, watching the Distance Sensor while driving
#   APPROACH     drive slowly up to the ball, then creep until the Optical
#                Sensor in the claw sees it
#   GRAB         close the claw and check that it holds something
#   CLASSIFY     read the colour with the rule in colour.py
#   GO_TO_BOX    drive to a point in line with the box, raise the arm, and
#                move in until the ball is over the box
#   RELEASE      open the claw and check that the ball has gone
#   RETURN       back out to where it lined up, lower the arm, go back to
#                where the path was left and carry on along it
#
# Failure paths. Every state has a time limit, and:
#   - object not found (lost from view, too far, never in the claw): give up
#     on that spot, go back to the path, and ignore anything near the spot
#   - grip failed: open, back off and try again, GRAB_TRIES times in all,
#     then give up on the spot as above
#   - colour unknown: take it to REJECT_POSITION, or stop with a message
#     when UNKNOWN_COLOUR_ACTION is "stop"
#   - something in the way (nearer than OBSTACLE_STOP_MM and not a ball to
#     fetch): stop and ask for the way to be cleared, carry on after CHECK
#   - anything else, such as a turn that times out or a ball stuck in the
#     claw: stop every motor and say why on the screen
# The Brain's Left and Right buttons stop everything at any time.
#
# A detection only counts as a ball if the point where the Distance Sensor
# says the object is lies on the board. That is what stops the robot from
# driving at the boxes, which sit off the board. That point, like every
# position here, comes from dead reckoning (robot.py), which drifts: the
# further the robot has driven, the less exact the drops and the return to
# the path become.


STOPPED = "STOPPED"
DONE = "DONE"


def point_ahead(x, y, heading, distance):
    """The point distance mm from (x, y) along a compass heading."""
    dx, dy = compass_vector(heading)
    return x + distance * dx, y + distance * dy


def on_board(x, y, margin):
    """True if (x, y) is on the board, at least margin mm inside its edges."""
    return (BOARD_MIN_X + margin <= x <= BOARD_MAX_X - margin
            and BOARD_MIN_Y + margin <= y <= BOARD_MAX_Y - margin)


def box_heading(cx, cy):
    """Compass heading pointing from the board towards a box beside it."""
    sides = [(cx - BOARD_MAX_X, 90.0), (BOARD_MIN_X - cx, 270.0),
             (cy - BOARD_MAX_Y, 0.0), (BOARD_MIN_Y - cy, 180.0)]
    best = sides[0]
    for side in sides:
        if side[0] > best[0]:
            best = side
    return best[1]


def box_poses(cx, cy):
    """Where to line up, and where to stop, to drop a ball in the box at (cx, cy).

    Returns (line-up x, line-up y, drop x, drop y, heading). At the drop
    point, with the arm at ARM_DROP_DEG, the held ball's centre is
    DROP_INSET_MM inside the box's near edge.
    """
    heading = box_heading(cx, cy)
    back = BOX_SIZE_MM / 2.0 - DROP_INSET_MM + DROP_REACH_MM
    drop_x, drop_y = point_ahead(cx, cy, heading, -back)
    line_x, line_y = point_ahead(drop_x, drop_y, heading, -BOX_STAGING_MM)
    return line_x, line_y, drop_x, drop_y, heading


class Mission:
    def __init__(self, robot, references, gate, path_name):
        self.robot = robot
        self.hw = robot.hw
        self.references = references
        self.gate = gate
        self.segments = get_path(path_name)
        self.index = 0             # path segment being driven
        self.remaining = None      # mm left of that segment after a stop
        self.state = "HOME"
        self.colour = "-"
        self.message = ""
        self.resume = None         # (x, y, heading) where the path was left
        self.spot = None           # where the object being fetched seems to be
        self.target = None         # centre of the box being driven to
        self.line_up = None        # where the robot lined up for that box
        self.tries = 0
        self.bright_reads = 0
        self.last_seen_ms = 0
        self.reverse_to_path = False
        self.ignored = []          # spots given up on
        self.sorted = {}
        for name in COLOURS:
            self.sorted[name] = 0
        self.rejected = 0
        self.given_up = 0
        self.distance = DistanceFilter()
        self.start_ms = 0

    # ------------------------------------------------------------------ run
    def run(self):
        """Sort until the path is finished or something stops it.

        Returns "done", or "failed" with the reason in self.message.
        """
        robot = self.robot
        hw = self.hw
        self.start_ms = hw.time_ms()
        robot.screen_source = self.screen_lines
        robot.refresh_screen(True)
        problem = home(robot)
        if problem is not None:
            return self.result(self.stop_with(problem))
        if not move_arm(robot, ARM_SEARCH_DEG):
            return self.result(self.stop_with("arm timed out"))
        steps = {
            "FOLLOW_PATH": self.follow_path,
            "APPROACH": self.approach,
            "GRAB": self.grab,
            "CLASSIFY": self.classify,
            "GO_TO_BOX": self.go_to_box,
            "RELEASE": self.release,
            "RETURN": self.go_back,
        }
        self.state = "FOLLOW_PATH"
        while self.state in steps:
            if hw.time_ms() - self.start_ms > MISSION_TIMEOUT_MS:
                self.state = self.stop_with("took too long")
                break
            hw.log("state " + self.state)
            robot.refresh_screen(True)
            self.state = steps[self.state]()
        return self.result(self.state)

    def result(self, state):
        if state == DONE:
            self.finish()
            return "done"
        return "failed"

    # --------------------------------------------------------------- screen
    def screen_lines(self):
        return [self.state,
                "Colour " + self.colour,
                "Sorted %d Rej %d" % (self.sorted_total(), self.rejected),
                "X %.0f Y %.0f" % (self.robot.x, self.robot.y),
                "L/R = stop"]

    def sorted_total(self):
        total = 0
        for name in COLOURS:
            total += self.sorted[name]
        return total

    def stop_with(self, message):
        """Stop every motor and say why on the screen. Returns STOPPED."""
        self.hw.stop_all()
        self.message = message
        self.robot.screen_source = None
        self.hw.log("sort stopped in %s: %s" % (self.state, message))
        self.robot.set_lines(["SORT STOPPED", message, self.state, "Colour " + self.colour])
        return STOPPED

    def finish(self):
        hw = self.hw
        seconds = (hw.time_ms() - self.start_ms) / 1000.0
        counts = ""
        for name in COLOURS:
            counts += "%s%d " % (name[0].upper(), self.sorted[name])
        hw.log("sort done in %.0f s: %srejected %d, gave up on %d"
               % (seconds, counts, self.rejected, self.given_up))
        hw.log("Positions are dead reckoning estimates from the wheels and the "
               "gyro. They drift over a run.")
        self.robot.screen_source = None
        self.robot.set_lines(["SORT DONE", counts + "Rej %d" % self.rejected,
                              "Gave up %d" % self.given_up, "Time %.0f s" % seconds,
                              "Position drifts"])
        hw.beep()

    # ------------------------------------------------------------- watching
    def read_distance(self):
        self.distance.update(self.hw)
        return self.distance.distance()

    def near_ignored(self, spot):
        for old in self.ignored:
            if distance_between(spot[0], spot[1], old[0], old[1]) <= IGNORE_RADIUS_MM:
                return True
        return False

    def watch_path(self, remaining):
        """While following the path: ("ball", (x, y)) for something on the
        board worth fetching, ("blocked", mm) for anything else too near,
        otherwise None."""
        found = self.read_distance()
        if found is None or found > OBJECT_RANGE_MM:
            return None
        spot = point_ahead(self.robot.x, self.robot.y, self.hw.heading(),
                           SENSOR_OFFSET_MM + found)
        if on_board(spot[0], spot[1], BOARD_MARGIN_MM) and not self.near_ignored(spot):
            return ("ball", spot)
        if found <= OBSTACLE_STOP_MM:
            return ("blocked", found)
        return None

    def watch_blocked(self, remaining):
        """While driving anywhere else: ("blocked", mm) if anything is too near."""
        found = self.read_distance()
        if found is not None and found <= OBSTACLE_STOP_MM:
            return ("blocked", found)
        return None

    def wait_until_clear(self):
        """Ask for the way to be cleared. True once CHECK is pressed."""
        robot = self.robot
        robot.screen_source = None
        robot.set_lines(["BLOCKED", "Clear the way,", "then press CHECK", "L/R = stop"])
        self.hw.log("blocked in " + self.state)
        pressed = robot.wait_for_check(BLOCKED_TIMEOUT_MS)
        robot.screen_source = self.screen_lines
        if pressed:
            robot.pause(START_DELAY_MS)
        return pressed

    def navigate(self, x, y):
        """Turn to face (x, y) and drive straight to it, asking for the way to
        be cleared when something is in it. Returns None when there, or
        STOPPED. Nothing watches the sides while it turns on the spot."""
        robot = self.robot
        tries = 0
        while True:
            if distance_between(robot.x, robot.y, x, y) <= ARRIVE_TOLERANCE_MM:
                return None
            if robot.turn_to(bearing(robot.x, robot.y, x, y)) == "timeout":
                return self.stop_with("turn timed out")
            self.distance.reset()
            length = distance_between(robot.x, robot.y, x, y)
            result, found = robot.drive(length, robot.target_heading, self.watch_blocked)
            if result == "done":
                return None
            if result == "timeout":
                return self.stop_with("drive timed out")
            if result == "stuck":
                return self.stop_with("drive blocked")
            tries += 1
            if tries >= NAV_TRIES or not self.wait_until_clear():
                return self.stop_with("way blocked")

    # --------------------------------------------------------------- states
    def follow_path(self):
        robot = self.robot
        while self.index < len(self.segments):
            kind, value = self.segments[self.index]
            if kind == "turn":
                if robot.turn_to(value) == "timeout":
                    return self.stop_with("turn timed out")
                self.index += 1
                continue
            if self.remaining is None:
                length = value
            else:
                length = self.remaining
            self.distance.reset()
            result, found = robot.drive(length, robot.target_heading, self.watch_path)
            if result == "timeout":
                return self.stop_with("drive timed out")
            if result == "stuck":
                return self.stop_with("drive blocked")
            if result == "object":
                self.remaining = length - robot.last_driven_mm
                if found[0] == "ball":
                    self.resume = (robot.x, robot.y, robot.target_heading)
                    self.spot = found[1]
                    self.tries = 0
                    self.hw.log("object ahead at %.0f, %.0f" % self.spot)
                    return "APPROACH"
                if not self.wait_until_clear():
                    return self.stop_with("path blocked")
                continue
            self.remaining = None
            self.index += 1
        return DONE

    def approach(self):
        robot = self.robot
        heading = robot.target_heading
        self.distance.reset()
        self.last_seen_ms = self.hw.time_ms()
        outcome = robot.drive_until(APPROACH_PCT, heading, self.close_enough,
                                    APPROACH_MAX_MM, APPROACH_TIMEOUT_MS)
        if outcome != "close":
            return self.give_up("approach " + outcome)
        self.bright_reads = 0
        outcome = robot.drive_until(CREEP_PCT, heading, self.ball_in_claw,
                                    CREEP_MAX_MM, CREEP_TIMEOUT_MS)
        if outcome != "in claw":
            return self.give_up("not in claw: " + outcome)
        return "GRAB"

    def close_enough(self):
        found = self.read_distance()
        now = self.hw.time_ms()
        if found is not None:
            self.last_seen_ms = now
            if found <= APPROACH_STOP_MM:
                return "close"
        elif now - self.last_seen_ms > OBJECT_LOST_MS:
            return "lost"
        return None

    def ball_in_claw(self):
        if self.hw.optical_brightness() >= self.gate:
            self.bright_reads += 1
        else:
            self.bright_reads = 0
        if self.bright_reads >= IN_CLAW_READS:
            return "in claw"
        return None

    def grab(self):
        robot = self.robot
        if not move_arm(robot, ARM_GRAB_DEG):
            return self.stop_with("arm timed out")
        stopped_at = close_claw(robot)
        holding = holding_ball(stopped_at, self.hw.optical_brightness(), self.gate)
        if holding:
            self.hw.log("grab: claw stopped at %.0f degrees, holding a ball" % stopped_at)
        else:
            self.hw.log("grab: no ball in the claw")
            return self.grab_failed()
        if not move_arm(robot, ARM_CARRY_DEG):
            return self.stop_with("arm timed out")
        return "CLASSIFY"

    def grab_failed(self):
        """Open up and try again, or give up on the spot after GRAB_TRIES."""
        robot = self.robot
        if not open_claw(robot):
            return self.stop_with("claw timed out")
        if not move_arm(robot, ARM_SEARCH_DEG):
            return self.stop_with("arm timed out")
        self.tries += 1
        if self.tries >= GRAB_TRIES:
            return self.give_up("grip failed")
        if robot.drive(-GRAB_RETRY_BACKUP_MM, robot.target_heading)[0] != "done":
            return self.stop_with("backup timed out")
        return "APPROACH"

    def give_up(self, reason):
        """Leave this object alone from now on and go back to the path."""
        self.hw.log("giving up on the object at %.0f, %.0f: %s"
                    % (self.spot[0], self.spot[1], reason))
        self.ignored.append(self.spot)
        self.given_up += 1
        self.colour = "-"
        self.reverse_to_path = True
        return "RETURN"

    def classify(self):
        answer, labels = read_colour(self.robot, self.references, self.gate)
        self.hw.log("colour %s from %s" % (answer, " ".join(labels)))
        if answer == NONE:
            return self.grab_failed()   # the ball slipped out
        self.colour = answer
        if answer != UNKNOWN:
            self.target = BOX_POSITIONS[answer]
        elif UNKNOWN_COLOUR_ACTION == "stop":
            return self.stop_with("unknown colour")
        else:
            self.target = REJECT_POSITION
        return "GO_TO_BOX"

    def go_to_box(self):
        robot = self.robot
        line_x, line_y, drop_x, drop_y, heading = box_poses(self.target[0], self.target[1])
        self.line_up = (line_x, line_y)
        stopped = self.navigate(line_x, line_y)
        if stopped is not None:
            return stopped
        if robot.turn_to(heading) == "timeout":
            return self.stop_with("turn timed out")
        if not move_arm(robot, ARM_DROP_DEG):
            return self.stop_with("arm timed out")
        if robot.drive(distance_between(robot.x, robot.y, drop_x, drop_y), heading)[0] != "done":
            return self.stop_with("box not reached")
        return "RELEASE"

    def release(self):
        robot = self.robot
        for attempt in range(RELEASE_TRIES):
            if not open_claw(robot):
                return self.stop_with("claw timed out")
            robot.pause(RELEASE_WAIT_MS)
            if self.hw.optical_brightness() < self.gate:
                if self.target == REJECT_POSITION:
                    self.rejected += 1
                else:
                    self.sorted[self.colour] += 1
                # the claw is empty, but nothing can tell whether the ball
                # landed in the box or next to it
                self.hw.log("let go of the %s ball" % self.colour)
                self.reverse_to_path = False
                return "RETURN"
            close_claw(robot)
        return self.stop_with("ball stuck")

    def go_back(self):
        robot = self.robot
        x, y, heading = self.resume
        if self.reverse_to_path:
            # straight back along the line the approach came in on
            back = distance_between(robot.x, robot.y, x, y)
            result = robot.drive(-back, heading)[0]
        else:
            # straight back out from the box to where it lined up, so the
            # claw is clear of the box before the arm comes down
            back = distance_between(robot.x, robot.y, self.line_up[0], self.line_up[1])
            result = robot.drive(-back, robot.target_heading)[0]
        if result != "done":
            return self.stop_with("backup timed out")
        if not move_arm(robot, ARM_SEARCH_DEG):
            return self.stop_with("arm timed out")
        stopped = self.navigate(x, y)
        if stopped is not None:
            return stopped
        if robot.turn_to(heading) == "timeout":
            return self.stop_with("turn timed out")
        self.colour = "-"
        return "FOLLOW_PATH"


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

    The screen shows the arm and claw positions, the heading, the filtered
    distance (IN when an object is in range), the raw hue and brightness,
    and the colour the rule in colour.py gives for the last COLOUR_READS
    readings. Start with the arm all the way down and the claw wide open:
    those positions read 0, so moving them by hand shows the values for the
    ARM_* and CLAW_* settings.
    Returns "timeout". A stop button raises StopRequested as usual.
    """
    hw = robot.hw
    hw.reset_arm_degrees()
    hw.reset_claw_degrees()
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
        robot.set_lines(["Arm %.0f Claw %.0f" % (hw.arm_degrees(), hw.claw_degrees()),
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
# Calibrate the gyro, then do RUN_MODE (see settings.py): a bring-up check,
# the colour calibration, a plain drive along a path, or the sort itself.


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


main()
