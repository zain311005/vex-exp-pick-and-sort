import ast
import glob
import os

import settings
from settings import *
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


def test_every_timeout_is_positive():
    names = [name for name in dir(settings) if "TIMEOUT" in name]
    assert len(names) >= 5
    for name in names:
        assert getattr(settings, name) > 0, name


def test_selected_mode_and_path_exist():
    assert RUN_MODE in MODES
    assert SELECTED_PATH in path_names()


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
    180 and 360 for angles, and 1000 for milliseconds per second.
    """
    allowed = {0, 1, 2, 180, 360, 1000}
    for path in sorted(glob.glob(os.path.join(ROOT, "src", "*.py"))):
        with open(path) as handle:
            tree = ast.parse(handle.read())
        for node in ast.walk(tree):
            if (isinstance(node, ast.Constant) and not isinstance(node.value, bool)
                    and isinstance(node.value, (int, float))):
                assert abs(node.value) in allowed, (
                    "%s line %d uses %r; move it to config/settings.py"
                    % (os.path.basename(path), node.lineno, node.value))
