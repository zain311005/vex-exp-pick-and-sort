# References

The official VEX pages this project relies on. They are linked, not
copied: there are no VEX PDFs, knowledge base articles, images, diagrams or
library code in this repository. Every link below was opened on
7 November 2026.

## VEX EXP Python API

These pages describe the `vex` module that VEXcode EXP and the EXP Brain
provide. [src/hardware.py](../src/hardware.py) only makes calls listed on
them.

| Page | What this project takes from it |
|---|---|
| [Python API home](https://api.vex.com/exp/home/python/index.html) | The list of API pages |
| [MicroPython Libraries](https://api.vex.com/exp/home/python/Micropython_libraries.html) | The EXP Brain runs MicroPython 1.13, based on Python 3.4, so the build rejects newer Python syntax |
| [Motor and Motor Group](https://api.vex.com/exp/home/python/Motion/motor_and_motor_group.html) | `Motor(port, GearSetting.RATIO_18_1, reversed)`, `spin`, `stop`, `set_stopping` with `BRAKE` and `HOLD`, `position`, `set_position`, `current` |
| [Inertial](https://api.vex.com/exp/home/python/Inertial.html) | The gyro inside the Brain: `calibrate`, `is_calibrating`, `heading`, `set_heading` |
| [Distance Sensor](https://api.vex.com/exp/home/python/Sensing/distance-sensor.html) | `is_object_detected`, `object_distance` in mm, and its range of 20 mm to 2000 mm |
| [Optical Sensor](https://api.vex.com/exp/home/python/Sensing/optical-sensor.html) | `hue` from 0 to 359, `brightness` as a percent, `is_near_object`, `set_light_power` in whole percent, and the `color()` hue ranges the default `COLOUR_REFERENCES` come from |
| [Brain buttons](https://api.vex.com/exp/home/python/Sensing/Brain.html) | `buttonCheck`, `buttonLeft` and `buttonRight` with `pressing()` |
| [Screen](https://api.vex.com/exp/home/python/Screen.html) | `clear_screen`, `set_cursor`, `print` |
| [Sound](https://api.vex.com/exp/home/python/Sound.html) | `play_sound(SoundType.TADA)` |
| [Control](https://api.vex.com/exp/home/python/Logic/Control.html) | `wait(time, MSEC)` |
| [Timer](https://api.vex.com/exp/home/python/Logic/Timer.html) | `brain.timer.time(MSEC)`, which starts from 0 when a project starts |
| [SD Card](https://api.vex.com/exp/home/python/SDcard.html) | `is_inserted`, `loadfile` and `savefile` with a `bytearray`, and the card rules: FAT32, 32 GB or smaller, files in the root folder |
| [Console](https://api.vex.com/exp/home/python/Console.html) | `print()` output appears in the VEXcode console |

## Building the robot and the software

| Page | What this project takes from it |
|---|---|
| [EXP build instructions](https://www.vexrobotics.com/exp/downloads/build-instructions) | The EXP Clawbot build, revision 3: the motor ports (6, 10, 3 and 4), the 3.25 in wheels and the 12 tooth to 60 tooth arm gear |
| [EXP Clawbot build](https://link.vex.com/exp/builds/clawbot) | VEX's own link to the Clawbot instructions, from the page above |
| [Install VEXcode for VEX EXP](https://www.vexrobotics.com/vexcode/install/exp) | Getting VEXcode EXP, which downloads the program to the Brain |

## Copyright and licences

| Page | What it says, in short |
|---|---|
| [VEX copyright notice](https://www.vexrobotics.com/copyright-notice) | Innovation First, Inc. (VEX Robotics) owns all content and intellectual property relating to VEX Robotics and its materials, with all rights reserved |
| [VEX terms of use](https://www.vexrobotics.com/terms-of-use) | Content on VEX's site may not be copied, shared, published or turned into derivative works, except where VEX says so explicitly, and then only for personal, non-commercial use with VEX's attributions. Statutory copyright exceptions still apply |
| [VEXcode software licence](https://www.vexrobotics.com/software-eula) | VEXcode, its firmware and related materials stay VEX's property. The licence does not allow redistributing, publishing or reverse engineering them |

## Where this project touches VEX code

- [src/hardware.py](../src/hardware.py), and so `brain/clawbot.py`, imports
  the `vex` module that VEXcode and the Brain provide. That module is
  VEX's software under the VEXcode licence above. It is not in this
  repository.
- [tests/fake_vex.py](../tests/fake_vex.py) is a stand-in for the tests,
  written from the API pages above. It repeats the names and arguments of
  the calls this project uses, and none of VEX's code.

This project is not affiliated with or endorsed by VEX Robotics.
