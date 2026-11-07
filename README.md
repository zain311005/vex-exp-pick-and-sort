# vex-exp-pick-and-sort

A VEX EXP Clawbot program that I am building up, one milestone at a time,
into a pick-and-sort demo. The robot drives a path on a 300 mm grid board,
finds a ball with a Distance Sensor, picks it up with the claw, reads its
colour with an Optical Sensor, drops it in the box for that colour, and goes
back to the path to look for the next one.

**UNTESTED ON HARDWARE.** So far everything has only run in the laptop
simulator and the unit tests. Before running it on a robot, work through
[docs/BRINGUP.md](docs/BRINGUP.md).

## Status

| Milestone | What | State |
|---|---|---|
| M1 | Project layout, settings file, hardware interface, path following, simulator, tests | Done, simulator only |
| M2 | Distance and colour sensing, colour calibration | Done, simulator only |
| M3 | Pick-and-sort behaviour with timeouts and recovery | Done, simulator only |
| M4 | Full guide, wiring diagram, PDF | Not started |

## How the sort works

The sort (`RUN_MODE = "sort"`) is a state machine in
[src/mission.py](src/mission.py). The Brain screen shows the state and the
colour all the time.

| State | What the robot does |
|---|---|
| FOLLOW_PATH | Drives `SORT_PATH`, watching the Distance Sensor |
| APPROACH | Drives slowly up to the ball, then creeps until the Optical Sensor in the claw sees it |
| GRAB | Closes the claw and checks it holds something |
| CLASSIFY | Reads the colour |
| GO_TO_BOX | Lines up with that colour's box, raises the arm and moves in |
| RELEASE | Opens the claw and checks the ball has gone |
| RETURN | Backs out, lowers the arm and goes back to where it left the path |

Every state has a time limit. When something goes wrong:

- **Object not found**: if it is lost from view, too far, or never reaches the claw, the
  robot gives up on that spot, goes back to the path and ignores anything near it.
- **Grip failed**: it opens, backs off and tries once more, then gives up as above.
- **Colour unknown**: the ball goes to the reject spot, or the robot stops with a message
  if `UNKNOWN_COLOUR_ACTION` is `"stop"`.
- **Something in the way**: the robot stops, asks for the way to be cleared, and carries
  on after CHECK.
- **Anything else** (a stuck drive, a ball stuck in the claw): every motor stops and the
  screen says why.

The Left and Right buttons on the Brain stop everything at any time.

Only things on the board count as balls. The boxes sit off the board, so
when the Distance Sensor sees one (it does, from column D) the robot
ignores it.

The colour sorting is a calibrated rule, not machine learning. You record
the Optical Sensor with the claw empty and with each ball, and the robot
then picks the nearest recorded hue, or says "unknown" when nothing is
close or the readings disagree. [src/colour.py](src/colour.py) explains it.

## Placing the balls

The sort searches along `sort_loop`: north up line A, east along row 6,
south down column D and back west. Put the balls on the west and north
sides, on the line, at least 450 mm from a corner. Keep the east and south
sides clear, because the robot crosses them on its way to the boxes.

## Quick start

On the robot (VEXcode EXP, Python):

1. Open [brain/clawbot.py](brain/clawbot.py), copy all of it, paste it into
   a new VEXcode EXP Python project and download it to the Brain. If the
   Brain says the program is too big, use
   [brain/clawbot_compact.py](brain/clawbot_compact.py) instead: the same
   program without the comments.
2. Follow [docs/BRINGUP.md](docs/BRINGUP.md) step by step. A fresh copy is
   set to `RUN_MODE = "sensor_check"`, which never moves a motor.

On a laptop (Python 3.9 or newer):

```bash
python3 -m pip install -r requirements-dev.txt
```

```bash
python3 -m pytest
```

```bash
python3 sim/run_sim.py --plot
```

To check a colour calibration log from the Brain on a laptop:

```bash
python3 tools/fit_colours.py colour_log.csv
```

After changing anything in `config/` or `src/`, rebuild the Brain files:

```bash
python3 tools/build_brain.py
```

## Layout

| Folder | What is in it | Runs on |
|---|---|---|
| `config/settings.py` | Every port, speed, threshold, timeout, path and box position | Brain and laptop |
| `src/` | The robot code. Only `src/hardware.py` calls the VEX API | Brain and laptop |
| `brain/` | `config/` and `src/` joined into the single file VEXcode needs, plus a compact copy. Generated, do not edit | Brain |
| `sim/` | A simple simulator with the same methods as the real hardware | Laptop only |
| `tests/` | Unit tests and simulator tests | Laptop only |
| `tools/` | The script that builds the Brain files, and the colour log checker | Laptop only |
| `docs/` | [Assumptions](docs/ASSUMPTIONS.md) and the [bring-up checklist](docs/BRINGUP.md) | |

## Known limits

**Dead reckoning drifts.** The robot works out where it is from the wheel
encoders and the Brain's gyro. Nothing outside the robot ever corrects that
estimate, so wheel slip and gyro drift build up over a run. In the
simulator, with one ball of each colour and one unknown:

| Gyro drift | Result |
|---|---|
| none | all 4 balls land in the right place |
| 0.6 degrees a minute | all 4 land |
| 1.2 degrees a minute | the robot counts all 4 as sorted, but one lands beside its box |
| 3 degrees a minute | the robot hits a box on the way in and stops |

**Nothing checks what lands in a box.** The robot counts a ball as sorted
when the claw is empty after it opens over the box. It cannot see whether
the ball went in.

**It only sees straight ahead.** There is one Distance Sensor, facing
forwards. A ball beside the path is not seen, and one within about 22 cm of
where the robot drives can be clipped. When the robot turns on the spot,
nothing watches the sides at all.

**Anything on the board is taken for a ball first.** A box or a shoe on
the board gets approached. The robot only gives up when the claw meets it
and nothing is in the claw.

**A colour that was never calibrated can pass as one that was**, if its
hue happens to be close. Asking several readings to agree makes that less
likely, not impossible.

**The claw has not been tried with the balls.** Nobody has checked yet
that a 15 cm ball fits in the EXP claw. The arm and claw positions in
`config/settings.py` are guesses until they are measured.

## The original assignment version

The program this project started from is kept unchanged on the
`submission-v1` branch and tag.

## Not affiliated with VEX

This is a personal student project. It is not affiliated with or endorsed
by VEX Robotics. VEX, VEX EXP and VEXcode are trademarks of their owner.

The licence will be added before the repository is made public.
