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
#   "sensor_check"  show live sensor readings; no motor ever moves
#   "motor_check"   after CHECK, spin each motor slowly, one at a time
#   "path"          after CHECK, drive SELECTED_PATH
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
# Distance Sensor range from the VEX EXP Python API page for the sensor.
DISTANCE_MIN_MM = 20.0
DISTANCE_MAX_MM = 2000.0

OPTICAL_LIGHT_PCT = 50.0  # MEASURE: brightness of the Optical Sensor's LED


# ------------------------------------------------------------ Brain screen
# The assignment program showed five lines of up to 16 characters, so the
# messages are kept that short.
SCREEN_PERIOD_MS = 250    # how often the status lines are redrawn
SCREEN_ROWS = 5
