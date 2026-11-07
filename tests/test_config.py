import ast
import glob
import os

import settings
from settings import *
from colour import overlaps
from main import MODES
from paths import path_names

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MOTOR_PORTS = [LEFT_DRIVE_PORT, RIGHT_DRIVE_PORT, ARM_PORT, CLAW_PORT]
SENSOR_PORTS = [DISTANCE_PORT, OPTICAL_PORT]


def test_ports_are_smart_ports():
    for port in MOTOR_PORTS + SENSOR_PORTS:
        assert isinstance(port, int) and 1 <= port <= 10


def test_no_two_devices_share_a_port():
    ports = MOTOR_PORTS + SENSOR_PORTS
    assert len(set(ports)) == len(ports)


def test_default_speeds_are_slow():
    assert DRIVE_MAX_PCT <= 35
    assert TURN_MAX_PCT <= 30
    assert STEER_MAX_PCT <= 15
    assert MOTOR_CHECK_PCT <= 25
    assert DRIVE_MIN_PCT < DRIVE_MAX_PCT
    assert TURN_MIN_PCT < TURN_MAX_PCT
    assert ARM_MAX_PCT <= 50 and ARM_MIN_PCT < ARM_MAX_PCT
    assert CLAW_CLOSE_PCT <= 40 and CLAW_OPEN_PCT <= 40
    assert ARM_HOME_PCT <= 20 and CLAW_HOME_PCT <= 20
    assert CREEP_PCT <= APPROACH_PCT <= DRIVE_MAX_PCT


def test_every_timeout_is_positive():
    names = [name for name in dir(settings) if "TIMEOUT" in name]
    assert len(names) >= 5
    for name in names:
        assert getattr(settings, name) > 0, name


def test_selected_mode_and_path_exist():
    assert RUN_MODE in MODES
    assert SELECTED_PATH in path_names()
    assert SORT_PATH in path_names()
    assert UNKNOWN_COLOUR_ACTION in ("reject", "stop")


def test_claw_and_arm_settings_make_sense():
    # front to back along the robot: sensor, palm, claw tips
    assert SENSOR_OFFSET_MM <= CLAW_PALM_MM < FRONT_MM
    assert CHASSIS_FRONT_MM <= CLAW_PALM_MM
    assert 0 <= ARM_SEARCH_DEG <= ARM_CARRY_DEG < ARM_DROP_DEG
    assert 0 <= ARM_GRAB_DEG < ARM_CARRY_DEG
    assert 0 < CLAW_GRIP_MARGIN_DEG < CLAW_EMPTY_CLOSED_DEG
    # the ball fits inside a box at the drop point
    assert BALL_DIAMETER_MM / 2.0 <= DROP_INSET_MM <= BOX_SIZE_MM - BALL_DIAMETER_MM / 2.0
    # the chassis stays out of the box while the ball is over it
    assert DROP_REACH_MM - DROP_INSET_MM > CHASSIS_FRONT_MM
    # the approach stops before the claw would push the ball away
    assert APPROACH_STOP_MM < OBJECT_RANGE_MM
    assert OBSTACLE_STOP_MM < OBJECT_RANGE_MM


def test_colour_settings_make_sense():
    assert sorted(COLOUR_REFERENCES) == sorted(COLOURS)
    for hue, tolerance in COLOUR_REFERENCES.values():
        assert 0 <= hue < 360
        assert COLOUR_MIN_TOLERANCE_DEG <= tolerance <= COLOUR_MAX_TOLERANCE_DEG
    assert overlaps(COLOUR_REFERENCES) == []
    assert 0 <= COLOUR_GATE_BRIGHTNESS <= 100
    # the Optical Sensor page asks for a whole number of percent
    assert isinstance(OPTICAL_LIGHT_PCT, int) and 0 < OPTICAL_LIGHT_PCT <= 100
    # a strict majority, so two answers can never both win the vote
    assert COLOUR_READS / 2.0 < COLOUR_MIN_VOTES <= COLOUR_READS
    assert COLOUR_CAL_MIN_GOOD <= COLOUR_CAL_SAMPLES
    assert COLOUR_MIN_TOLERANCE_DEG < COLOUR_MAX_TOLERANCE_DEG


def test_distance_settings_make_sense():
    # most of the window must be valid, so one bad reading cannot set the median
    assert DISTANCE_WINDOW / 2.0 < DISTANCE_MIN_VALID <= DISTANCE_WINDOW
    assert DISTANCE_MIN_MM < OBJECT_RANGE_MM <= DISTANCE_MAX_MM
    assert DISTANCE_SAMPLE_MS >= LOOP_MS


def test_sd_card_files_are_in_the_root_folder_with_an_extension():
    # the SD Card page: root folder only, and the name must include the extension
    for name in (COLOUR_FILE, COLOUR_LOG_FILE):
        assert "/" not in name and "\\" not in name
        assert "." in name


def test_every_colour_has_a_box():
    assert sorted(BOX_POSITIONS) == sorted(COLOURS)


def test_boxes_do_not_overlap():
    spots = list(BOX_POSITIONS.values()) + [REJECT_POSITION]
    for i, a in enumerate(spots):
        for b in spots[i + 1:]:
            assert abs(a[0] - b[0]) >= BOX_SIZE_MM or abs(a[1] - b[1]) >= BOX_SIZE_MM


def test_src_has_no_tuning_numbers():
    """Tuning values belong in config/settings.py.

    Code in src/ may only use numbers that are part of the maths: 0, 1 and 2,
    90, 180, 270 and 360 for compass directions and turns, and 1000 for
    milliseconds per second.
    """
    allowed = {0, 1, 2, 90, 180, 270, 360, 1000}
    for path in sorted(glob.glob(os.path.join(ROOT, "src", "*.py"))):
        with open(path) as handle:
            tree = ast.parse(handle.read())
        for node in ast.walk(tree):
            if (isinstance(node, ast.Constant) and not isinstance(node.value, bool)
                    and isinstance(node.value, (int, float))):
                assert abs(node.value) in allowed, (
                    "%s line %d uses %r; move it to config/settings.py"
                    % (os.path.basename(path), node.lineno, node.value))
