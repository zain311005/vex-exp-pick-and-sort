# Assumptions

Where each value in `config/settings.py` comes from, and what still has to
be checked on the real robot. Nothing in this project has run on a robot
yet, so all of it is **UNTESTED ON HARDWARE** until the steps in
[BRINGUP.md](BRINGUP.md) have been done.

What the status words mean:

| Status | Meaning |
|---|---|
| From VEX | Taken from an official VEX page or build instruction, linked below |
| Given | Told to me by the person who built the robot |
| Chosen | A project decision. Change it if something else suits your setup |
| MEASURE | An estimate. Measure it on your robot and update the setting |
| VERIFY | Believed to be true but not yet confirmed from an official source |

## Robot

| Setting | Value | Status | Where it comes from |
|---|---|---|---|
| Robot | EXP Clawbot | Given | Built from the EXP Clawbot build instructions, rev 3 [1] |
| `LEFT_DRIVE_PORT` | 6 | From VEX | Build instructions, step 14 [1] |
| `RIGHT_DRIVE_PORT` | 10 | From VEX | Build instructions, step 14 [1] |
| `ARM_PORT` | 3 | From VEX | Build instructions, step 41 [1] |
| `CLAW_PORT` | 4 | From VEX | Build instructions, step 41 [1] |
| `DISTANCE_PORT` | 5 | Chosen | The port the Distance Sensor used in the assignment program |
| `OPTICAL_PORT` | 1 | Chosen | A free Smart Port. The stock Clawbot has no sensors |
| `RIGHT_DRIVE_REVERSED` | True | VERIFY | The right motor faces the other way. The motor check confirms it |
| `ARM_REVERSED`, `CLAW_REVERSED` | False | MEASURE | Positive power must raise the arm and close the claw. The motor check confirms it |
| `WHEEL_TRAVEL_MM` | 260 | From VEX | The build uses 3.25 in wheels, listed as 260 mm travel [1] |
| `DRIVE_GEAR_RATIO` | 1.0 | From VEX | The drive motors turn the traction wheels directly [1] |
| `TRACK_WIDTH_MM` | 240 | MEASURE | Left wheel centre to right wheel centre. Only the simulator uses it |
| `FRONT_MM`, `REAR_MM`, `ROBOT_WIDTH_MM` | 330, 80, 290 | MEASURE | Robot outline measured from the turning centre. Used for box clearance |
| `SENSOR_OFFSET_MM` | 200 | MEASURE | Turning centre to the Distance Sensor face |
| `CHASSIS_FRONT_MM` | 200 | MEASURE | Turning centre to the front of the chassis under the claw. Must stay out of a box at the drop point |
| `CLAW_PALM_MM` | 230 | MEASURE | Turning centre to the back of the claw opening. Only the simulator uses it |
| Turning centre | middle of the traction wheel axle | From VEX | The omni wheels at the claw end are not driven [1] |
| Sensor mounting | Distance Sensor low at the front centre, looking out through the open claw. Optical Sensor on the claw palm, facing into the claw | Chosen | With the arm down and nothing in front, the Distance Sensor must not see the claw (bring-up step 1a) |

## Field and boxes

| Setting | Value | Status | Where it comes from |
|---|---|---|---|
| `GRID_MM` | 300 | Given | Each board square is 300 mm by 300 mm |
| Board edges | x -300 to 1200 mm, y -300 to 1500 mm | Given | Same board as the assignment |
| `BALL_DIAMETER_MM` | 150 | Given | The balls are about 15 cm |
| `BOX_SIZE_MM` | 254 | Given | The boxes are 10 in by 10 in |
| `BOX_POSITIONS` | x 1550 mm, at y 1200, 600 and 0 | Chosen | Off the east edge. The original path uses almost the whole board |
| `REJECT_POSITION` | x 450, y -650 | Chosen | Off the south edge, so its approach lane does not cross the sides where balls go |
| `BOX_CLEARANCE_MM` | 100 | Chosen | A test checks the robot outline stays this far from every box on every path. The closest point in the simulator is 164 mm on the original path and 132 mm on `sort_loop` |
| `SORT_PATH` | `sort_loop` | Chosen | A loop round the board with long, well separated sides. The original path's lines are only 150 to 300 mm apart, too close to leave balls beside them |
| `START_X`, `START_Y`, `START_HEADING` | 0, -150, 0 | Given | The start of the assignment route |
| `ORIGINAL_WAYPOINTS` | 14 points | Given | Copied exactly from the assignment program. A test compares them with the `submission-v1` tag |

## Software and API

| Item | Status | Where it comes from |
|---|---|---|
| The EXP Brain runs MicroPython 1.13, based on Python 3.4 | From VEX | MicroPython Libraries page [2]. The build script rejects newer syntax |
| A VEXcode EXP Python project is a single file | VERIFY | The reason `tools/build_brain.py` joins everything into `brain/clawbot.py` |
| Brain buttons a program can read: Check, Left, Right | From VEX | Brain buttons page [3] |
| Distance Sensor range 20 to 2000 mm | From VEX | Distance Sensor page [4] |
| How often the Distance Sensor gives a new reading | VERIFY | Not on the API page. `DISTANCE_SAMPLE_MS` is 50 ms, a guess |
| The gyro is built into the EXP Brain and needs no port | From VEX | Inertial page [5] |
| Optical Sensor: `hue()` is 0 to 359, `brightness()` is a percent, `set_light_power()` takes whole percent and 0 turns the LED off | From VEX | Optical Sensor page [6] |
| Optical Sensor `color()` hue ranges: red 340 to 20, green 80 to 140, blue 200 to 240 | From VEX | Optical Sensor page [6]. The default `COLOUR_REFERENCES` are the middles of these |
| SD card: FAT32, 32 GB or smaller, files in the root folder, names with an extension, `savefile` and `loadfile` take and give a `bytearray` | From VEX | SD Card page [7] |
| What `loadfile` does when the file is missing | VERIFY | Not on the page. The code treats an error or an empty file as "no calibration" |
| The Brain screen fits five lines of about 16 characters | VERIFY | The assignment program's screen used five lines of up to 16 characters |
| Motor calls in `src/hardware.py` | From VEX | Motor page [8] |
| Screen, Sound, `wait` and timer calls | From VEX | Screen [9], Sound [10], Control [11] and Timer [12] pages |

## Sensing

| Setting | Value | Status | Notes |
|---|---|---|---|
| `DISTANCE_WINDOW`, `DISTANCE_MIN_VALID` | 5, 3 | Chosen | The distance is the median of the last 5 readings, and needs at least 3 of them valid |
| `OBJECT_RANGE_MM` | 400 | Chosen | While following the path, an object this near that lies on the board starts an approach |
| `COLOUR_REFERENCES` | red 0 +-20, green 110 +-30, blue 220 +-20 | From VEX | Only a starting point. The calibration replaces them |
| `COLOUR_GATE_BRIGHTNESS` | 10 | MEASURE | The calibration replaces it with a value halfway between the empty claw and the darkest ball |
| `COLOUR_READS`, `COLOUR_MIN_VOTES` | 7, 5 | Chosen | A colour needs 5 of 7 readings to agree, otherwise the answer is "unknown" |
| `COLOUR_SPREAD_FACTOR` and the tolerance limits | 3, 8 to 30 degrees | Chosen | Tolerance is 3 times the spread of the calibration hues, kept between 8 and 30 degrees |
| `COLOUR_CAL_SAMPLES`, `COLOUR_CAL_MIN_GOOD` | 20, 15 | Chosen | 20 readings per step, and at least 15 bright enough for each ball |
| Sample readings in `tests/data/` | | SYNTHETIC | The `*_synthetic.csv` files are made up, not recorded. Real logs go in `tests/data/recorded/` |

## Speeds and control

| Setting | Value | Status | Notes |
|---|---|---|---|
| `DRIVE_MAX_PCT` | 30 | Chosen | Kept slow on purpose. A test fails if it goes above 35 |
| `TURN_MAX_PCT` | 25 | Chosen | Kept slow on purpose. A test fails if it goes above 30 |
| `DRIVE_MIN_PCT`, `TURN_MIN_PCT` | 7, 6 | MEASURE | The lowest power that still moves the robot |
| `DRIVE_KP`, `STEER_KP`, `TURN_KP`, `TURN_KD` | 0.3, 1.0, 0.8, 2.0 | Chosen | Only tried in the simulator. Expect to retune on the robot |
| `START_DELAY_MS` | 1000 | Chosen | Same one-second pause as the assignment program |
| Timeouts | see `settings.py` | Chosen | Every wait has one. A test fails if any is 0 or less |
| `DRIVE_STALL_MM`, `DRIVE_STALL_MS` | 5, 500 | Chosen | A drive that moves less than 5 mm in half a second is pushing on something, so it stops |
| `OPTICAL_LIGHT_PCT` | 50 | MEASURE | LED power for the colour readings, a whole number as the API asks. Calibrate again after changing it |

## Arm, claw and sorting

| Setting | Value | Status | Notes |
|---|---|---|---|
| Homing | arm down, claw open, onto their stops | Chosen | There are no limit switches, so the ends of travel are found by stalling at low power (15 %) |
| `STALL_DEG`, `STALL_MS` | 3, 300 | Chosen | Turning less than 3 degrees in 300 ms counts as reaching a stop |
| `ARM_SEARCH_DEG`, `ARM_GRAB_DEG` | 0, 0 | MEASURE | Claw down at ball height. Bring-up step 1b |
| `ARM_CARRY_DEG` | 150 | MEASURE | High enough that the Distance Sensor no longer sees the held ball |
| `ARM_DROP_DEG` | 400 | MEASURE | The bottom of the ball above the box rim |
| `CLAW_EMPTY_CLOSED_DEG`, `CLAW_GRIP_MARGIN_DEG` | 120, 20 | MEASURE | A claw that stops 20 degrees short of fully shut, while the Optical Sensor sees something, is holding a ball |
| `DROP_REACH_MM` | 310 | MEASURE | Turning centre to the held ball's centre with the arm up |
| `DROP_INSET_MM` | 90 | Chosen | The ball's centre this far inside the box's near edge: 15 mm more than its radius |
| `APPROACH_STOP_MM`, `CREEP_MAX_MM`, `IN_CLAW_READS` | 100, 150, 3 | Chosen | Drive up until the ball is 100 mm from the Distance Sensor, then creep until 3 bright readings in a row |
| `OBSTACLE_STOP_MM` | 150 | Chosen | Anything this near that is not a ball to fetch stops the robot |
| `IGNORE_RADIUS_MM` | 200 | Chosen | After giving up on an object, detections this near it are ignored |
| `BOX_STAGING_MM` | 400 | Chosen | Line up this far from the drop point, and back out to it afterwards |
| `UNKNOWN_COLOUR_ACTION` | `"reject"` | Chosen | Or `"stop"`, which the brief also allows |
| `GRAB_TRIES`, `RELEASE_TRIES`, `NAV_TRIES` | 2, 2, 3 | Chosen | |
| `MISSION_TIMEOUT_MS` | 15 minutes | Chosen | A whole sort in the simulator takes about 3 minutes |

## Simulator only

These describe the simulator's model, not the robot. They live in
`sim/sim_hardware.py` and never go onto the Brain.

| Value | Status | Notes |
|---|---|---|
| Motor speed at 100 % power: 127 rpm | VERIFY | Only changes how long simulated runs take |
| Motor response lag: 60 ms | Chosen | A rough guess |
| Gyro calibration: 2 s | Chosen | The real calibration time may differ. The program allows 5 s |
| Wheel slip and gyro drift | Chosen per test | Off by default. Tests turn them on to show the drift |
| Ball hues: red 3, green 118, blue 215, orange 32 degrees. White has no clear hue | Chosen | Guesses for the model, not measurements |
| Empty-claw brightness 4 %, hue noise 4 degrees, brightness noise 2 % | Chosen | Guesses for the model |
| Distance Sensor misses and wild readings | Chosen per test | Off by default. Tests turn them on to check the filter |
| The claw stops at 60 degrees on a ball and shuts at 120 without one | Chosen | Model values |
| A ball can be gripped if its centre is within 60 mm of the claw's centre line | Chosen | Model value |
| The Optical Sensor sees a floor ball within 10 mm of the palm | Chosen | Model value |
| The arm clears the Distance Sensor above 100 degrees and passes over a box above 300 | Chosen | Model values |
| Balls never roll | Chosen | A real ball may roll away when the claw touches it. The grab retry is there for that, but the simulator never tests it |

## Open risks

1. **Will a 15 cm ball fit in the claw?** Still not checked. Open the claw
   fully and try a ball by hand before any sort. If it does not fit, the
   pick-up has to change (smaller balls, or a different grip). The
   simulator assumes it fits.
2. **Dead reckoning drifts.** See the README. The robot cannot notice its
   own position error.
3. **Gains tuned only in the simulator.** The real robot will behave
   differently. The bring-up checklist says what to change first.
4. **Colours that were not calibrated.** A ball of another colour can be
   read as a calibrated colour if its hue is close enough. In the synthetic
   samples, 3 of 14 single readings of a white ball looked blue. The vote
   (5 of 7 must agree) caught it, but cannot rule it out.
5. **Optical Sensor on the claw.** The LED may reflect off the claw itself.
   The empty-claw calibration step measures that, but only with the claw
   where it was during calibration.
6. **Drops can miss without the robot knowing.** In the simulator a gyro
   drift of about 1 degree a minute is enough for one of four balls to land
   beside its box, while the robot counts it as sorted.
7. **It only sees straight ahead.** A ball beside the path is not seen,
   and one within about 22 cm of where the robot drives can be clipped,
   including while it turns on the spot.
8. **Geometry is guessed.** The arm angles, claw angles and reach are
   placeholders until they are measured in bring-up step 1b.

## Links

1. EXP Clawbot build instructions, rev 3: <https://link.vex.com/exp/builds/clawbot>
   (listed on <https://www.vexrobotics.com/exp/downloads/build-instructions>)
2. MicroPython Libraries: <https://api.vex.com/exp/home/python/Micropython_libraries.html>
3. Brain (buttons): <https://api.vex.com/exp/home/python/Sensing/Brain.html>
4. Distance Sensor: <https://api.vex.com/exp/home/python/Sensing/distance-sensor.html>
5. Inertial: <https://api.vex.com/exp/home/python/Inertial.html>
6. Optical Sensor: <https://api.vex.com/exp/home/python/Sensing/optical-sensor.html>
7. SD Card: <https://api.vex.com/exp/home/python/SDcard.html>
8. Motor: <https://api.vex.com/exp/home/python/Motion/motor_and_motor_group.html>
9. Screen: <https://api.vex.com/exp/home/python/Screen.html>
10. Sound: <https://api.vex.com/exp/home/python/Sound.html>
11. Control (`wait`): <https://api.vex.com/exp/home/python/Logic/Control.html>
12. Timer: <https://api.vex.com/exp/home/python/Logic/Timer.html>

The VEX documents are linked, not copied into this repository.
[REFERENCES.md](REFERENCES.md) lists every VEX page the project uses.
