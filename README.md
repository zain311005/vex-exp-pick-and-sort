# vex-exp-pick-and-sort

A VEX EXP Clawbot program that I am building up, one milestone at a time,
into a pick-and-sort demo. When it is finished the robot should follow a
path on a 300 mm grid board, find a ball with a Distance Sensor, pick it up
with the claw, read its colour with an Optical Sensor, and drop it in the
box for that colour.

**UNTESTED ON HARDWARE.** So far everything has only run in the laptop
simulator and the unit tests. Before running it on a robot, work through
[docs/BRINGUP.md](docs/BRINGUP.md).

## Status

| Milestone | What | State |
|---|---|---|
| M1 | Project layout, settings file, hardware interface, path following, simulator, tests | Done, simulator only |
| M2 | Distance and colour sensing, colour calibration | Done, simulator only |
| M3 | Pick-and-sort behaviour with timeouts and recovery | Not started |
| M4 | Full guide, wiring diagram, PDF | Not started |

Right now the program can calibrate the gyro, follow a path made of turns
and straight drives, filter the Distance Sensor, calibrate and read ball
colours with the Optical Sensor, and run bring-up checks (sensors only,
and motors one at a time). It does not pick anything up yet.

The colour sorting is a calibrated rule, not machine learning. You record
the Optical Sensor with the claw empty and with each ball, and the robot
then picks the nearest recorded hue, or says "unknown" when nothing is
close or the readings disagree. [src/colour.py](src/colour.py) explains it.

## Quick start

On the robot (VEXcode EXP, Python):

1. Open [brain/clawbot.py](brain/clawbot.py), copy all of it, paste it into
   a new VEXcode EXP Python project and download it to the Brain.
2. Follow [docs/BRINGUP.md](docs/BRINGUP.md) step by step.

On a laptop (Python 3.8 or newer):

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

After changing anything in `config/` or `src/`, rebuild the Brain file:

```bash
python3 tools/build_brain.py
```

## Layout

| Folder | What is in it | Runs on |
|---|---|---|
| `config/settings.py` | Every port, speed, threshold, timeout, path and box position | Brain and laptop |
| `src/` | The robot code. Only `src/hardware.py` calls the VEX API | Brain and laptop |
| `brain/clawbot.py` | `config/` and `src/` joined into the single file VEXcode needs. Generated, do not edit | Brain |
| `sim/` | A simple simulator with the same methods as the real hardware | Laptop only |
| `tests/` | Unit tests and simulator tests | Laptop only |
| `tools/` | The script that builds `brain/clawbot.py`, and the colour log checker | Laptop only |
| `docs/` | [Assumptions](docs/ASSUMPTIONS.md) and the [bring-up checklist](docs/BRINGUP.md) | |

## Known limits

The robot works out where it is by dead reckoning: wheel encoders for
distance and the Brain's gyro for heading. Nothing outside the robot ever
corrects that estimate, so wheel slip and gyro drift build up over a run.
In the simulator, a gyro drifting 3 degrees a minute leaves the robot about
60 mm from where it started after the full path, while its own estimate
still says it is back at the start.

A ball of a colour that was never calibrated can still be read as one of
the calibrated colours if its hue happens to be close. Asking several
readings to agree makes that less likely, not impossible.

## The original assignment version

The program this project started from is kept unchanged on the
`submission-v1` branch and tag.

## Not affiliated with VEX

This is a personal student project. It is not affiliated with or endorsed
by VEX Robotics. VEX, VEX EXP and VEXcode are trademarks of their owner.

The licence will be added before the repository is made public.
