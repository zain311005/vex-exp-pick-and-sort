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

## Step 1: sensors alone

Setting: `RUN_MODE = "sensor_check"`. No motor moves in this mode.

1. Put the robot on the board and start the program. Keep it still while
   the screen says "Calibrating gyro".
2. The screen then shows the heading, the Distance Sensor reading, and the
   Optical Sensor hue and brightness.

- [ ] Turn the robot by hand about a quarter turn clockwise. The heading
      goes up by about 90.
- [ ] Hold a hand about 300 mm in front of the Distance Sensor. The
      reading is roughly 300 mm. Take the hand away and it says "none" or
      a much bigger number.
- [ ] Hold a ball against the claw. The Optical Sensor brightness goes up
      and the hue changes with the ball's colour.
- [ ] Press Left or Right. The screen shows STOPPED.

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
