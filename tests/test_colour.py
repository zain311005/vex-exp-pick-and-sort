import glob
import os

import pytest

import colour
from colour import (NONE, UNKNOWN, calibration_text, circular_mean, circular_spread,
                    classify, fit_calibration, fit_reference, nearest_colour, overlaps,
                    parse_calibration, settings_text, vote)
from fit_colours import read_log
from geometry import wrap_180

DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
SYNTHETIC = os.path.join(DATA, "colour_samples_synthetic.csv")
RECORDED = sorted(glob.glob(os.path.join(DATA, "recorded", "*.csv")))

# Pin the rule's settings so these tests check the rule, not your tuning.
RULE = dict(COLOURS=["red", "green", "blue"], COLOUR_READS=7, COLOUR_MIN_VOTES=5,
            COLOUR_CAL_MIN_GOOD=15, COLOUR_MIN_BRIGHTNESS_GAP=5.0, COLOUR_SPREAD_FACTOR=3.0,
            COLOUR_MIN_TOLERANCE_DEG=8.0, COLOUR_MAX_TOLERANCE_DEG=30.0)
CAL_SAMPLES = 20   # the first 20 readings of each label calibrate, the rest test


@pytest.fixture(autouse=True)
def fixed_rule(monkeypatch):
    for name, value in RULE.items():
        monkeypatch.setattr(colour, name, value)


REFS = {"red": (3.0, 12.0), "green": (118.0, 15.0), "blue": (215.0, 15.0)}
GATE = 16.0


# ------------------------------------------------------------------ maths
def test_circular_mean_goes_round_the_wheel():
    assert abs(wrap_180(circular_mean([350.0, 10.0]))) < 1e-9
    assert circular_mean([90.0, 180.0]) == pytest.approx(135.0)
    assert circular_mean([355.0, 359.0, 3.0]) == pytest.approx(359.0, abs=1e-6)


def test_circular_spread():
    assert circular_spread([350.0, 10.0], 0.0) == pytest.approx(10.0)
    assert circular_spread([20.0, 20.0], 20.0) == 0.0


def test_tolerance_is_kept_between_the_limits():
    assert fit_reference([50.0] * 10) == (pytest.approx(50.0), RULE["COLOUR_MIN_TOLERANCE_DEG"])
    assert fit_reference([0.0, 90.0, 180.0, 270.0, 45.0])[1] == RULE["COLOUR_MAX_TOLERANCE_DEG"]


# -------------------------------------------------------- classification
def test_dark_reading_means_nothing_in_the_claw():
    assert classify(3.0, GATE - 0.1, REFS, GATE) == NONE


def test_close_hue_gives_the_colour():
    assert classify(10.0, 40.0, REFS, GATE) == "red"
    assert classify(125.0, 40.0, REFS, GATE) == "green"


def test_hue_wraps_round_from_359_to_0():
    assert nearest_colour(358.0, REFS) == ("red", pytest.approx(5.0))
    assert classify(358.0, 40.0, REFS, GATE) == "red"


def test_hue_far_from_every_reference_is_unknown():
    assert classify(32.0, 40.0, REFS, GATE) == UNKNOWN    # orange
    assert classify(300.0, 40.0, REFS, GATE) == UNKNOWN   # purple


def test_vote_needs_enough_agreeing_readings():
    assert vote(["red"] * 5 + ["unknown"] * 2) == "red"
    assert vote(["red"] * 4 + ["blue"] * 3) == UNKNOWN
    assert vote([NONE] * 7) == NONE
    assert vote([]) == UNKNOWN


def test_overlaps():
    assert overlaps(REFS) == []
    assert overlaps({"red": (3.0, 20.0), "green": (30.0, 10.0), "blue": (215.0, 15.0)}) == ["red/green"]


# ---------------------------------------------------- saving and loading
def test_calibration_text_round_trip():
    references, gate = parse_calibration(calibration_text(REFS, GATE))
    assert gate == pytest.approx(GATE)
    for name in REFS:
        assert references[name] == (pytest.approx(REFS[name][0]), pytest.approx(REFS[name][1]))


@pytest.mark.parametrize("text", [
    "",
    "gate 16\nred 3 12\ngreen 118 15\n",                     # blue missing
    "red 3 12\ngreen 118 15\nblue 215 15\n",                 # gate missing
    "gate 16\nred 3 12\ngreen 118 15\nblue 215 abc\n",       # not a number
    "gate 16\nred 3 12\ngreen 118 15\nblue 215\n",           # too few values
    "gate 16\nred 3 12\ngreen 118 15\nblue 215 15\npink 300 10\n",  # unknown colour
    "gate 16\nred 3 2\ngreen 118 15\nblue 215 15\n",         # tolerance below the limit
    "gate -1\nred 3 12\ngreen 118 15\nblue 215 15\n",        # negative gate
])
def test_parse_calibration_refuses_bad_files(text):
    assert parse_calibration(text) is None


def test_settings_text_is_python_that_settings_py_can_use():
    names = {}
    exec(settings_text(REFS, GATE), names)
    assert names["COLOUR_GATE_BRIGHTNESS"] == pytest.approx(GATE)
    assert sorted(names["COLOUR_REFERENCES"]) == sorted(REFS)


# --------------------------------------------- synthetic sample readings
def split(readings):
    """First CAL_SAMPLES readings of each label calibrate, the rest test."""
    calibrate = dict((label, values[:CAL_SAMPLES]) for label, values in readings.items())
    check = dict((label, values[CAL_SAMPLES:]) for label, values in readings.items())
    return calibrate, check


def windows(values, size):
    return [values[i:i + size] for i in range(0, len(values) - size + 1, size)]


@pytest.fixture(scope="module")
def synthetic():
    with open(SYNTHETIC) as handle:
        return read_log(handle)


@pytest.fixture
def fitted(synthetic):
    calibrate, check = split(synthetic)
    references, gate, problem = fit_calibration(
        calibrate["empty"], dict((name, calibrate[name]) for name in RULE["COLOURS"]))
    assert problem is None
    return references, gate, check


def test_synthetic_file_has_what_the_tests_need(synthetic):
    for label in ["empty"] + RULE["COLOURS"]:
        assert len(synthetic[label]) > CAL_SAMPLES
    assert "orange" in synthetic and "white" in synthetic


def test_fit_finds_the_colours_in_the_synthetic_samples(fitted):
    references, gate, check = fitted
    # the generator's centres were 3, 118 and 215 degrees
    assert abs(wrap_180(references["red"][0] - 3.0)) < 3.0
    assert abs(wrap_180(references["green"][0] - 118.0)) < 3.0
    assert abs(wrap_180(references["blue"][0] - 215.0)) < 3.0
    assert 4.0 < gate < 28.0
    assert overlaps(references) == []


@pytest.mark.parametrize("name", RULE["COLOURS"])
def test_unseen_synthetic_readings_are_classified(fitted, name):
    references, gate, check = fitted
    answers = [classify(h, b, references, gate) for h, b in check[name]]
    assert answers.count(name) >= 0.9 * len(answers)
    for group in windows(answers, RULE["COLOUR_READS"]):
        assert vote(group) == name


def test_empty_claw_readings_are_none(fitted):
    references, gate, check = fitted
    assert set(classify(h, b, references, gate) for h, b in check["empty"]) == {NONE}


@pytest.mark.parametrize("name", ["orange", "white"])
def test_balls_that_were_not_calibrated_come_out_unknown(fitted, synthetic, name):
    references, gate, check = fitted
    answers = [classify(h, b, references, gate) for h, b in synthetic[name]]
    groups = windows(answers, RULE["COLOUR_READS"])
    assert groups
    for group in groups:
        assert vote(group) == UNKNOWN


def test_fit_fails_when_a_ball_is_as_dark_as_the_empty_claw(synthetic):
    calibrate, check = split(synthetic)
    balls = dict((name, calibrate[name]) for name in RULE["COLOURS"])
    balls["blue"] = calibrate["empty"]
    references, gate, problem = fit_calibration(calibrate["empty"], balls)
    assert references is None and problem == "blue too dark"


# ---------------------------------------------------- real recordings
@pytest.mark.skipif(not RECORDED, reason="no real recordings in tests/data/recorded/ yet")
@pytest.mark.parametrize("path", RECORDED)
def test_real_recording_is_self_consistent(path):
    """A real calibration log, fitted and then classified with itself."""
    with open(path) as handle:
        readings = read_log(handle)
    references, gate, problem = fit_calibration(
        readings["empty"], dict((name, readings[name]) for name in colour.COLOURS))
    assert problem is None, problem
    for name in colour.COLOURS:
        answers = [classify(h, b, references, gate) for h, b in readings[name]]
        assert answers.count(name) >= 0.9 * len(answers), name
