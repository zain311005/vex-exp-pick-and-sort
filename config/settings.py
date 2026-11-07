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
