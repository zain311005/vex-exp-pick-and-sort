# Bring-up checklist

**UNTESTED ON HARDWARE.** This code has not been run on a real robot yet.
This checklist is the order to try it in the first time, so that a wrong
setting shows up while the robot cannot hurt itself or anyone.

The order is: sensors alone, then motors with the wheels off the ground,
then slow driving, then the full path. Do not skip ahead. Later milestones
will add steps for the claw and the ball.

## How to stop the robot

- Press the **Left** or **Right** button on the Brain. The program stops
  every motor and shows STOPPED.
- Pick the robot up if it is about to hit something.
- [VERIFY] Find out how VEXos ends a running program on your Brain (for
  example the X button) before step 3, so you have a second way to stop it.

## Changing a setting

Each step changes `RUN_MODE` (and in step 3, `SELECTED_PATH`). Either:

- change it in `config/settings.py`, run `python3 tools/build_brain.py` and
  paste the new `brain/clawbot.py` into VEXcode (this keeps the repository
  correct), or
- change the same line near the top of the pasted file in VEXcode, which is
  quicker while testing. Copy the change back to `config/settings.py`
  afterwards.

## Before switching on

- [ ] The robot is built as in the EXP Clawbot build instructions (rev 3).
- [ ] Left drive motor in port 6, right drive motor in port 10, arm motor
      in port 3, claw motor in port 4.
- [ ] Distance Sensor in port 5, low at the front centre, facing forward.
- [ ] Optical Sensor in port 1, on the claw, facing into the claw.
- [ ] Battery charged.
- [ ] Optional: an SD card in the Brain, FAT32 and 32 GB or smaller, to
      keep the colour calibration between runs.

## Step 1: sensors alone

No motor moves in either part of this step.

### 1a. Live readings

Setting: `RUN_MODE = "sensor_check"`.

1. Put the robot on the board and start the program. Keep it still while
   the screen says "Calibrating gyro".
2. The screen then shows:
   - `Head`: the gyro heading
   - `Dist`: the filtered distance in mm, with `IN` instead of `mm` when
     something is within `OBJECT_RANGE_MM` (400 mm), or `none`
   - `Hue` and `Br`: the raw Optical Sensor hue and brightness
   - `Colour`: the colour rule's answer for the last few readings:
     a colour, `none` (nothing in the claw) or `unknown`

- [ ] The program starts at all. `brain/clawbot.py` is a big file (about
      48 KB). [VERIFY] If VEXcode or the Brain reports a size or memory
      error, write down the exact message.
- [ ] Turn the robot by hand about a quarter turn clockwise. The heading
      goes up by about 90.
- [ ] Hold a hand about 300 mm in front of the Distance Sensor. It shows
      roughly `Dist 300 IN`. At about 600 mm it shows `Dist 600 mm`. Take
      the hand away and it shows `none` or a much bigger number.
- [ ] Put a ball in the claw. Brightness goes up and the hue changes with
      the ball's colour. Until step 1b is done the colour comes from the
      VEX default hue ranges, so it may be wrong.
- [ ] With the claw empty, `Colour` shows `none`.
- [ ] Press Left or Right. The screen shows STOPPED.

### 1b. Colour calibration

Setting: `RUN_MODE = "colour_calibrate"`. Have the red, green and blue
balls ready. The room light should be the same as when the robot will sort.

1. Start the program and keep the robot still for the gyro.
2. The screen says `Claw empty`, `then press CHECK`. Check the claw is
   empty, press CHECK and keep still for about a second while it reads.
3. It then asks for each ball in turn (`red in claw` and so on). Put the
   ball where it sits when the claw holds it, press CHECK, keep it still.
4. The last screen shows `Saved to SD` (or `No SD: console`), then each
   colour's reference hue and tolerance, then the brightness gate.

- [ ] Every colour shows a hue, and the screen does not say `CLOSE!`.
      `CLOSE!` means two colours look alike to the sensor: check the
      lighting and the balls.
- [ ] If it says `CALIBRATE FAILED` and `red too dark` (or another
      colour), that ball was not in front of the sensor, or the LED is off.
- [ ] Run 1a again. Each ball now shows its colour, and the empty claw
      shows `none`.
- [ ] Keep the readings. They are in the VEXcode console as
      `label,hue,brightness` lines, and in `colour_log.csv` on the SD card.
      On a laptop, `python3 tools/fit_colours.py colour_log.csv` shows how
      each reading would be classified. Copy the file into
      `tests/data/recorded/` and the tests will check real data as well.

Without an SD card the calibration is not kept. Paste the
`COLOUR_REFERENCES` and `COLOUR_GATE_BRIGHTNESS` lines from the console
into `config/settings.py` and rebuild instead. [VERIFY] What `loadfile`
does when the file is missing is not documented. The program treats an
error or an empty file as "no calibration" and uses `settings.py`.

## Step 2: motors with the wheels off the ground

Setting: `RUN_MODE = "motor_check"`.

1. Stand the robot on a box so both drive wheels hang in the air.
2. Move the arm by hand to about halfway up and open the claw halfway, so
   each has room to move either way.
3. Start the program, wait for "CHECK = start", press CHECK and take your
   hand away. After one second each motor spins for one second at 20 %
   power, one at a time.

- [ ] Left wheel rolls forward (towards the claw end).
- [ ] Right wheel rolls forward.
- [ ] Arm goes up.
- [ ] Claw closes.
- [ ] The last screen shows four numbers above 0. A 0 means that motor did
      not turn: check its cable and port.

If a part moved the wrong way, flip its `*_REVERSED` setting and do this
step again before going on.

## Step 3: slow driving

Settings: `RUN_MODE = "path"`, `SELECTED_PATH = "bringup_line"`.

The robot drives 300 mm forward, turns round, drives back and turns to face
the way it started. Leave about 1 m of clear space around it.

1. Mark the start position on the board with tape.
2. Start the program, press CHECK, take your hand away.

- [ ] It drives forward, turns round, comes back and stops.
- [ ] Measure how far the end position is from the tape and write it down.
- [ ] If it turns too far and swings back, lower `TURN_KP`. If it stops
      just short of a heading and hums, raise `TURN_MIN_PCT` a little.
- [ ] If it drives a few percent too far or too short, measure the wheel
      and check `WHEEL_TRAVEL_MM`.

## Step 4: the full path

Settings: `RUN_MODE = "path"`, `SELECTED_PATH = "original"`.

The start point is on line A, 150 mm before line 1, facing along line A
towards row 6 (x 0 mm, y -150 mm in `config/settings.py`).

- [ ] The robot follows the route and comes back to the start.
- [ ] Measure the end error and compare it with what the screen says.
      Expect them to differ: dead reckoning drifts, and the robot cannot
      see its own error.
- [ ] The claw never comes near the boxes.

## Results log

Copy this table into your notes and fill in a row each time.

| Date | Step | Pass or fail | What happened | Settings changed |
|---|---|---|---|---|
| | | | | |
