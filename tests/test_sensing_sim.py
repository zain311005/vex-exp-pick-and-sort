import pytest

import colour
from colour import (NONE, UNKNOWN, calibration_text, load_colour_calibration,
                    parse_calibration, read_colour)
from geometry import wrap_180
from main import run
from robot import Robot
from settings import *
from sim_hardware import SIM_BALL_LOOKS, SIM_EMPTY_BRIGHTNESS, SimHardware

# CHECK presses for the four calibration steps, and which ball is in the claw
# when. Each step reads for COLOUR_CAL_SAMPLES * COLOUR_CAL_READ_MS = 1 s.
PRESSES = [3000.0, 6000.0, 9000.0, 12000.0]
BALLS = [(0.0, None), (5000.0, "red"), (8000.0, "green"), (11000.0, "blue")]


def calibrated_sim(**options):
    hw = SimHardware(check_presses=PRESSES, held=BALLS, **options)
    return hw, run(hw, "colour_calibrate")


def screens_of(hw):
    """Record every screen the program shows."""
    shown = []
    show = hw.show

    def record(lines):
        shown.append(list(lines))
        show(lines)

    hw.show = record
    return shown


# ------------------------------------------------------- calibration
def test_calibration_saves_references_close_to_the_balls():
    hw, result = calibrated_sim()
    assert result == "done"
    references, gate = parse_calibration(hw.sd_files[COLOUR_FILE])
    for name in COLOURS:
        assert abs(wrap_180(references[name][0] - SIM_BALL_LOOKS[name][0])) < 3.0, name
    darkest = min(SIM_BALL_LOOKS[name][1] for name in COLOURS)
    assert SIM_EMPTY_BRIGHTNESS < gate < darkest
    assert hw.screen[0] == "Saved to SD"
    assert hw.light_pct == 0


def test_calibration_logs_every_reading():
    hw, result = calibrated_sim()
    log = hw.sd_files[COLOUR_LOG_FILE].strip().split("\n")
    assert log[0] == "label,hue,brightness"
    assert len(log) == 1 + COLOUR_CAL_SAMPLES * (1 + len(COLOURS))
    first_red = log[1 + COLOUR_CAL_SAMPLES]
    assert first_red.startswith(COLOURS[0] + ",")
    assert first_red in hw.console


def test_calibration_without_an_sd_card_prints_the_settings():
    hw, result = calibrated_sim(sd_card=False)
    assert result == "done"
    assert hw.screen[0] == "No SD: console"
    assert "COLOUR_REFERENCES = {" in "\n".join(hw.console)


def test_calibration_with_no_balls_fails_and_keeps_the_old_file():
    old = calibration_text(COLOUR_REFERENCES, COLOUR_GATE_BRIGHTNESS)
    hw = SimHardware(check_presses=PRESSES, held=None, sd_files={COLOUR_FILE: old})
    assert run(hw, "colour_calibrate") == "failed"
    assert hw.sd_files[COLOUR_FILE] == old
    assert hw.screen[0] == "CALIBRATE FAILED"
    assert hw.screen[1] == "%s too dark" % COLOURS[0]


def test_calibration_gives_up_if_check_is_not_pressed(monkeypatch):
    # a shorter wait than the real two minutes keeps the test quick
    monkeypatch.setattr(colour, "START_WAIT_TIMEOUT_MS", 3000)
    hw = SimHardware(check_presses=None)
    assert run(hw, "colour_calibrate") == "no_start"
    assert COLOUR_FILE not in hw.sd_files


def test_one_long_press_counts_for_one_step_only(monkeypatch):
    # CHECK held down from 3 s to 9 s. The empty-claw step may start, but the
    # next step has to wait for CHECK to be let go and pressed again.
    monkeypatch.setattr(colour, "START_WAIT_TIMEOUT_MS", 4000)
    hw = SimHardware(check_presses=[3000.0 + 100.0 * i for i in range(60)], held=BALLS)
    shown = screens_of(hw)
    assert run(hw, "colour_calibrate") == "no_start"
    # the screen is redrawn while reading, so a step can appear more than once
    reading = set(lines[1] for lines in shown
                  if lines[0] == "COLOUR CALIBRATE" and lines[2] == "Reading...")
    assert reading == {"Claw empty"}


# ---------------------------------------------------- loading and reading
def test_load_prefers_a_good_file_on_the_sd_card():
    text = calibration_text({"red": (5.0, 9.0), "green": (120.0, 9.0), "blue": (210.0, 9.0)}, 12.0)
    references, gate, source = load_colour_calibration(SimHardware(sd_files={COLOUR_FILE: text}))
    assert source == "SD card" and gate == pytest.approx(12.0)
    assert references["green"][0] == pytest.approx(120.0)


@pytest.mark.parametrize("options", [{"sd_card": False}, {"sd_files": {}},
                                     {"sd_files": {COLOUR_FILE: "rubbish"}}])
def test_load_falls_back_to_settings(options):
    references, gate, source = load_colour_calibration(SimHardware(**options))
    assert source == "settings"
    assert references == COLOUR_REFERENCES and gate == COLOUR_GATE_BRIGHTNESS


@pytest.mark.parametrize("held, want", [
    ("red", "red"), ("green", "green"), ("blue", "blue"),
    ("orange", UNKNOWN), ("white", UNKNOWN), (None, NONE),
])
def test_read_colour_with_the_shipped_references(held, want):
    hw = SimHardware(held=held, seed=5)
    hw.optical_light(OPTICAL_LIGHT_PCT)
    answer, labels = read_colour(Robot(hw), COLOUR_REFERENCES, COLOUR_GATE_BRIGHTNESS)
    assert answer == want, labels
    assert len(labels) == COLOUR_READS


def test_sensor_check_shows_the_colour_from_the_sd_card_calibration():
    hw, result = calibrated_sim()
    saved = dict(hw.sd_files)
    hw = SimHardware(held="green", sd_files=saved, stop_press_ms=8000.0)
    shown = screens_of(hw)
    assert run(hw, "sensor_check") == "stopped"
    assert "sensor check: colour references from SD card" in hw.console
    assert ["Colour green"] == list(set(lines[4] for lines in shown[-10:-1]))
