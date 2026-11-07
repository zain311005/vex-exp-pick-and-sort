import os

import pytest

import distance
from distance import DistanceFilter, median, valid_distance
from robot import Robot
from settings import START_X, START_Y, SENSOR_OFFSET_MM, BALL_DIAMETER_MM
from sim_hardware import SimHardware

DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")

# Pin the rule's settings so these tests check the rule, not your tuning.
RULE = dict(DISTANCE_MIN_MM=20.0, DISTANCE_MAX_MM=2000.0, DISTANCE_SAMPLE_MS=50,
            DISTANCE_WINDOW=5, DISTANCE_MIN_VALID=3, OBJECT_RANGE_MM=400.0)


@pytest.fixture(autouse=True)
def fixed_rule(monkeypatch):
    for name, value in RULE.items():
        monkeypatch.setattr(distance, name, value)


def load_scenarios(path):
    """scenario -> list of readings, None where the sensor saw nothing."""
    scenarios = {}
    with open(path) as handle:
        for line in handle:
            line = line.strip()
            if not line or line.startswith("#") or line == "scenario,reading":
                continue
            name, reading = line.split(",")
            scenarios.setdefault(name, []).append(None if reading == "none" else float(reading))
    return scenarios


SCENARIOS = load_scenarios(os.path.join(DATA, "distance_samples_synthetic.csv"))

# (distance the filter should give, in range?) after all of a scenario's readings
EXPECTED = {
    "steady": (300.2, True),
    "one_spike": (301.0, True),
    "two_missed": (350.0, True),
    "three_missed": (None, False),
    "out_of_range": (None, False),
    "four_valid": (325.0, True),
    "far": (800.0, False),
    "at_the_limit": (400.0, True),
    "approaching": (400.0, True),
}


def test_every_scenario_has_an_expected_answer():
    assert sorted(SCENARIOS) == sorted(EXPECTED)


@pytest.mark.parametrize("name", sorted(EXPECTED))
def test_sample_scenarios(name):
    found = DistanceFilter()
    for reading in SCENARIOS[name]:
        found.add(reading)
    want_distance, want_in_range = EXPECTED[name]
    if want_distance is None:
        assert found.distance() is None
    else:
        assert found.distance() == pytest.approx(want_distance)
    assert found.in_range() == want_in_range


def test_approaching_object_comes_into_range_on_the_right_reading():
    found = DistanceFilter()
    states = []
    for reading in SCENARIOS["approaching"]:
        found.add(reading)
        states.append(found.in_range())
    # the median of the last five only reaches 400 mm on the seventh reading
    assert states == [False] * 6 + [True]


@pytest.mark.parametrize("raw, want", [
    (None, None), ("abc", None), (float("nan"), None), (19.9, None), (20, 20.0),
    (2000, 2000.0), (2000.1, None), (-5, None), (735.5, 735.5),
])
def test_valid_distance(raw, want):
    assert valid_distance(raw) == want


def test_median():
    assert median([3, 1, 2]) == 2
    assert median([4, 1, 3, 2]) == 2.5
    assert median([7]) == 7


class ClockOnly:
    """Just enough hardware for DistanceFilter.update()."""

    def __init__(self):
        self.now = 0.0
        self.reads = 0

    def time_ms(self):
        return self.now

    def distance_raw(self):
        self.reads += 1
        return 500.0


def test_update_reads_no_faster_than_the_sample_time():
    hw = ClockOnly()
    found = DistanceFilter()
    for _ in range(100):          # one second of 10 ms loops
        found.update(hw)
        hw.now += 10
    assert hw.reads == 20         # one reading every 50 ms
    assert len(found.readings) == RULE["DISTANCE_WINDOW"]


def ball_ahead(gap_mm, **options):
    """A simulated robot at the start with a ball gap_mm in front of its sensor."""
    sensor_y = START_Y + SENSOR_OFFSET_MM
    ball = {"x": START_X, "y": sensor_y + gap_mm + BALL_DIAMETER_MM / 2.0}
    hw = SimHardware(balls=[ball], **options)
    return hw, Robot(hw)


def test_fill_measures_a_ball_in_the_simulator():
    hw, robot = ball_ahead(300.0)
    assert DistanceFilter().fill(robot) == pytest.approx(300.0, abs=0.5)


def test_filter_copes_with_missed_and_wild_readings_in_the_simulator():
    hw, robot = ball_ahead(300.0, seed=3, distance_dropout=0.2, distance_spike=0.05)
    found = DistanceFilter()
    results = [found.fill(robot) for _ in range(50)]
    good = [r for r in results if r is not None and abs(r - 300.0) <= 15.0]
    assert len(good) >= 45
