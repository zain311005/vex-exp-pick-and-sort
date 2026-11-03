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
| Turning centre | middle of the traction wheel axle | From VEX | The omni wheels at the claw end are not driven [1] |
| Sensor mounting | Distance Sensor low at the front centre, Optical Sensor on the claw facing in | Chosen | Fixed properly in milestone 2 |

## Field and boxes

| Setting | Value | Status | Where it comes from |
|---|---|---|---|
| `GRID_MM` | 300 | Given | Each board square is 300 mm by 300 mm |
| Board edges | x -300 to 1200 mm, y -300 to 1500 mm | Given | Same board as the assignment |
| `BALL_DIAMETER_MM` | 150 | Given | The balls are about 15 cm |
| `BOX_SIZE_MM` | 254 | Given | The boxes are 10 in by 10 in |
| `BOX_POSITIONS` | x 1550 mm, at y 1200, 600 and 0 | Chosen | Off the east edge. The original path uses almost the whole board |
| `REJECT_POSITION` | x -600, y 600 | Chosen | Off the west edge |
| `BOX_CLEARANCE_MM` | 100 | Chosen | A test checks the robot outline stays this far from every box on the original path. The closest point in the simulator is 143 mm |
| `START_X`, `START_Y`, `START_HEADING` | 0, -150, 0 | Given | The start of the assignment route |
| `ORIGINAL_WAYPOINTS` | 14 points | Given | Copied exactly from the assignment program. A test compares them with the `submission-v1` tag |

## Software and API

| Item | Status | Where it comes from |
|---|---|---|
| The EXP Brain runs MicroPython 1.13, based on Python 3.4 | From VEX | MicroPython Libraries page [2]. The build script rejects newer syntax |
| A VEXcode EXP Python project is a single file | VERIFY | The reason `tools/build_brain.py` joins everything into `brain/clawbot.py` |
| Brain buttons a program can read: Check, Left, Right | From VEX | Brain buttons page [3] |
| Distance Sensor range 20 to 2000 mm | From VEX | EXP Python Distance Sensor page [4] |
| The gyro is built into the EXP Brain and needs no port | From VEX | EXP Python Inertial page [5] |
| Optical Sensor LED: `set_light` and `set_light_power` | From VEX | EXP Python Optical Sensor page [6] |
| The Brain screen fits five lines of about 16 characters | VERIFY | The assignment program's screen used five lines of up to 16 characters |
| Motor, Distance, Screen and wait calls used in `src/hardware.py` | VERIFY | Checked on the EXP Python API pages during the audit. Exact page links get added in milestone 4 |

## Speeds and control

| Setting | Value | Status | Notes |
|---|---|---|---|
| `DRIVE_MAX_PCT` | 30 | Chosen | Kept slow on purpose. A test fails if it goes above 35 |
| `TURN_MAX_PCT` | 25 | Chosen | Kept slow on purpose. A test fails if it goes above 30 |
| `DRIVE_MIN_PCT`, `TURN_MIN_PCT` | 7, 6 | MEASURE | The lowest power that still moves the robot |
| `DRIVE_KP`, `STEER_KP`, `TURN_KP`, `TURN_KD` | 0.3, 1.0, 0.8, 2.0 | Chosen | Only tried in the simulator. Expect to retune on the robot |
| `START_DELAY_MS` | 1000 | Chosen | Same one-second pause as the assignment program |
| Timeouts | see `settings.py` | Chosen | Every wait has one. A test fails if any is 0 or less |
| `OPTICAL_LIGHT_PCT` | 50 | MEASURE | LED power for the colour readings. Settled in milestone 2 |

## Simulator only

These describe the simulator's model, not the robot. They live in
`sim/sim_hardware.py` and never go onto the Brain.

| Value | Status | Notes |
|---|---|---|
| Motor speed at 100 % power: 127 rpm | VERIFY | Only changes how long simulated runs take |
| Motor response lag: 60 ms | Chosen | A rough guess |
| Gyro calibration: 2 s | Chosen | The real calibration time may differ. The program allows 5 s |
| Wheel slip and gyro drift | Chosen per test | Off by default. Tests turn them on to show the drift |

## Open risks

1. **Will a 15 cm ball fit in the claw?** Not checked. Before milestone 3,
   open the claw fully and try a ball by hand. If it does not fit, the
   pick-up step has to change (smaller balls, or a different grip).
2. **Dead reckoning drifts.** See the README. The robot cannot notice its
   own position error.
3. **Gains tuned only in the simulator.** The real robot will behave
   differently. The bring-up checklist says what to change first.

## Links

1. EXP Clawbot build instructions, rev 3:
   <https://content.vexrobotics.com/vexexp/pdf/builds/exp-clawbot-rev3.pdf>
   (listed on <https://www.vexrobotics.com/exp/downloads/build-instructions>)
2. MicroPython Libraries: <https://api.vex.com/exp/home/python/Micropython_libraries.html>
3. Brain (buttons): <https://api.vex.com/exp/home/python/Sensing/Brain.html>
4. Distance Sensor: VEX EXP Python API, Distance Sensor page (link checked in milestone 4)
5. Inertial: <https://api.vex.com/exp/home/python/Inertial.html>
6. Optical Sensor: <https://api.vex.com/exp/home/python/Sensing/optical-sensor.html>

The VEX documents are linked, not copied into this repository.
