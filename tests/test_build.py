import ast
import os
import sys

import pytest

import build_brain
import fake_vex
from settings import *

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BRAIN_FILE = build_brain.OUTPUT
BRAIN_FILES = [build_brain.OUTPUT, build_brain.COMPACT_OUTPUT]
both_files = pytest.mark.parametrize("path", BRAIN_FILES, ids=["full", "compact"])


def brain_source(path=BRAIN_FILE):
    with open(path) as handle:
        return handle.read()


# ---------------------------------------------------------------- build
def test_brain_files_are_up_to_date():
    text = build_brain.build()
    assert text == brain_source(build_brain.OUTPUT), "run: python3 tools/build_brain.py"
    assert build_brain.compact(text) == brain_source(build_brain.COMPACT_OUTPUT)


@both_files
def test_brain_file_imports_only_vex_and_math(path):
    imported = set()
    for node in ast.walk(ast.parse(brain_source(path))):
        if isinstance(node, ast.Import):
            imported.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imported.add(node.module)
    assert imported == {"vex", "math"}


@both_files
def test_brain_file_does_not_hide_the_vex_names_it_uses(path):
    # everything ends up in one file after "from vex import *"
    defined = set()
    for node in ast.parse(brain_source(path)).body:
        if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
            defined.add(node.name)
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                for item in ast.walk(target):
                    if isinstance(item, ast.Name):
                        defined.add(item.id)
    assert not defined & set(fake_vex.__all__)


@both_files
def test_brain_file_uses_only_python_3_4_syntax(path):
    assert build_brain.micropython_problems(brain_source(path)) == []


def test_sources_use_only_python_3_4_syntax():
    for part in build_brain.PARTS:
        with open(os.path.join(ROOT, part)) as handle:
            assert build_brain.micropython_problems(handle.read(), part) == [], part


def test_compact_file_is_smaller_and_has_no_docstrings():
    full = brain_source(build_brain.OUTPUT)
    small = brain_source(build_brain.COMPACT_OUTPUT)
    assert len(small) < 0.8 * len(full)
    for node in ast.walk(ast.parse(small)):
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef)):
            assert ast.get_docstring(node) is None


@pytest.mark.parametrize("code", [
    'x = f"{y}"',
    "x: int = 1",
    "if (n := 1):\n    pass",
    "async def f():\n    pass",
    "x = a @ b",
    "x = [*a, *b]",
    "x = {**a}",
    "f(*a, *b)",
    "f(*a, b)",
    "f(**a, b=1)",
    "x = 1_000",
    "def f(x: int):\n    pass",
    "def f() -> int:\n    pass",
    "def f(a, /):\n    pass",
])
def test_syntax_check_catches_newer_python(code):
    assert build_brain.micropython_problems(code) != []


@pytest.mark.parametrize("code", [
    "first, *rest = items",
    "f(*args)",
    "f(x, *args, **kwargs)",
    "f(x, key=1, *args)",
    "def f(a, b=1, *args, c, **kwargs):\n    pass",
    "x = '%d %s' % (1, 'a')",
    "g = lambda a, b=2: a + b",
])
def test_syntax_check_allows_python_3_4(code):
    assert build_brain.micropython_problems(code) == []


def test_build_refuses_imports_the_brain_does_not_have():
    with pytest.raises(build_brain.BuildError):
        build_brain._strip_imports("x.py", "import os\n")
    with pytest.raises(build_brain.BuildError):
        build_brain._strip_imports("x.py", "from collections import deque\n")


# ------------------------------------- the Brain file on a fake vex module
def run_brain_file(monkeypatch, path=BRAIN_FILE, **script):
    """Run a Brain file, main() and all, on the fake vex module."""
    fake_vex.reset(**script)
    monkeypatch.setitem(sys.modules, "vex", fake_vex)
    names = {"__name__": "__main__"}
    exec(compile(brain_source(path), path, "exec"), names)
    return names


def brain_names(monkeypatch, path=BRAIN_FILE, **script):
    """Load a Brain file on the fake vex module without running main()."""
    fake_vex.reset(**script)
    monkeypatch.setitem(sys.modules, "vex", fake_vex)
    names = {"__name__": "brain_without_main"}
    source = brain_source(path)
    assert source.endswith("\nmain()\n")
    exec(compile(source[:-len("main()\n")], path, "exec"), names)
    return names


def screen():
    return [fake_vex.state.rows[row] for row in sorted(fake_vex.state.rows)]


def motors():
    return [device for device in fake_vex.state.devices.values()
            if isinstance(device, fake_vex.Motor)]


def test_brain_file_sets_up_every_device_on_its_port(monkeypatch):
    names = brain_names(monkeypatch)
    names["VexHardware"]()
    devices = fake_vex.state.devices
    expected = {
        LEFT_DRIVE_PORT: (fake_vex.Motor, LEFT_DRIVE_REVERSED, fake_vex.BRAKE),
        RIGHT_DRIVE_PORT: (fake_vex.Motor, RIGHT_DRIVE_REVERSED, fake_vex.BRAKE),
        ARM_PORT: (fake_vex.Motor, ARM_REVERSED, fake_vex.HOLD),
        CLAW_PORT: (fake_vex.Motor, CLAW_REVERSED, fake_vex.HOLD),
    }
    assert sorted(devices) == sorted(list(expected) + [DISTANCE_PORT, OPTICAL_PORT])
    for port, (kind, reverse, stopping) in expected.items():
        assert isinstance(devices[port], kind)
        assert devices[port].reverse == reverse
        assert devices[port].stopping is stopping
    assert isinstance(devices[DISTANCE_PORT], fake_vex.Distance)
    assert isinstance(devices[OPTICAL_PORT], fake_vex.Optical)


@pytest.mark.skipif(RUN_MODE != "sensor_check", reason="the shipped RUN_MODE has been changed")
def test_shipped_settings_never_move_a_motor(monkeypatch):
    # a fresh copy runs the sensor check: CHECK does nothing, L/R stops it
    run_brain_file(monkeypatch, check_press_ms=3000, left_press_ms=9000)
    assert screen() == ["STOPPED", "Stop pressed"]
    assert [motor.peak for motor in motors()] == [0.0, 0.0, 0.0, 0.0]


@pytest.mark.parametrize("button", ["left_press_ms", "right_press_ms"])
def test_brain_file_stops_on_either_stop_button(monkeypatch, button):
    script = {"check_press_ms": 3000, button: 6000}
    run_brain_file(monkeypatch, **script)
    assert screen() == ["STOPPED", "Stop pressed"]
    assert all(motor.command == 0 for motor in motors())


def test_brain_file_ends_if_check_is_never_pressed(monkeypatch):
    names = brain_names(monkeypatch)
    assert names["run"](names["VexHardware"](), "path", "original") == "no_start"
    assert screen() == ["Not started.", "Program ended."]
    assert fake_vex.state.now_ms >= START_WAIT_TIMEOUT_MS
    assert all(motor.peak == 0 for motor in motors())


def test_brain_file_gives_up_when_the_wheels_never_turn(monkeypatch, capsys):
    # the fake motors never move, so the first drive finds itself stuck
    names = brain_names(monkeypatch, check_press_ms=3000)
    assert names["run"](names["VexHardware"](), "path", "original") == "stuck"
    assert screen() == ["PATH STOPPED", "Reason: stuck", "At segment 2"]
    assert all(motor.command == 0 for motor in motors())
    assert "path original stuck segment 1" in capsys.readouterr().out


@both_files
def test_brain_file_sort_stops_when_the_wheels_never_turn(monkeypatch, path):
    # homing passes (the fake arm and claw never move, so they count as
    # stalled at once), then the first drive of the search path is stuck
    names = brain_names(monkeypatch, path, check_press_ms=3000)
    assert names["run"](names["VexHardware"](), "sort") == "failed"
    assert screen()[:3] == ["SORT STOPPED", "drive blocked", "FOLLOW_PATH"]
    assert all(motor.command == 0 for motor in motors())


def calibration_view(now_ms):
    """What the fake Optical Sensor sees during the four calibration steps."""
    if now_ms < 5000:
        return 120.0, 3.0      # claw empty
    if now_ms < 8000:
        return 5.0, 40.0       # red
    if now_ms < 11000:
        return 118.0, 35.0     # green
    return 215.0, 28.0         # blue


def test_brain_file_colour_calibration_saves_to_the_sd_card(monkeypatch, capsys):
    names = brain_names(monkeypatch, check_press_ms=[3000, 6000, 9000, 12000],
                        sd_inserted=True, optical_at=calibration_view)
    assert names["run"](names["VexHardware"](), "colour_calibrate") == "done"
    assert screen()[0] == "Saved to SD"
    saved = fake_vex.state.sd_files[COLOUR_FILE].decode("utf-8")
    references, gate = names["parse_calibration"](saved)
    assert references["red"][0] == pytest.approx(5.0)
    assert references["blue"][0] == pytest.approx(215.0)
    assert 3.0 < gate < 28.0
    assert "COLOUR_REFERENCES = {" in capsys.readouterr().out
    log = fake_vex.state.sd_files[COLOUR_LOG_FILE].decode("utf-8")
    assert log.startswith("label,hue,brightness\nempty,120.0,3.0\n")


def test_brain_file_reads_the_calibration_back(monkeypatch):
    text = "gate 15.5\nred 5.0 8.0\ngreen 118.0 8.0\nblue 215.0 8.0\n"
    names = brain_names(monkeypatch, sd_inserted=True,
                        sd_files={COLOUR_FILE: text.encode("utf-8")})
    references, gate, source = names["load_colour_calibration"](names["VexHardware"]())
    assert source == "SD card" and gate == pytest.approx(15.5)


@both_files
@pytest.mark.parametrize("mode, script, result, first_line", [
    ("sensor_check", {"left_press_ms": 6000}, "stopped", "STOPPED"),
    ("motor_check", {"check_press_ms": 3000}, "done", "MOTOR CHECK DONE"),
    ("colour_calibrate", {"right_press_ms": 4000}, "stopped", "STOPPED"),
    ("sort", {"check_press_ms": 3000, "left_press_ms": 4500}, "stopped", "STOPPED"),
])
def test_brain_file_runs_every_mode(monkeypatch, path, mode, script, result, first_line):
    names = brain_names(monkeypatch, path, **script)
    assert names["run"](names["VexHardware"](), mode) == result
    assert screen()[0] == first_line
    assert all(motor.command == 0 for motor in motors())


def test_every_vex_call_in_hardware_is_in_the_fake_api(monkeypatch):
    """Each self.<device>.<call> in hardware.py must exist on the fake vex
    objects, and fake_vex.py only has calls copied from the VEX API pages."""
    names = brain_names(monkeypatch)
    hw = names["VexHardware"]()

    with open(os.path.join(ROOT, "src", "hardware.py")) as handle:
        tree = ast.parse(handle.read())
    chains = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute):
            chain = []
            current = node
            while isinstance(current, ast.Attribute):
                chain.append(current.attr)
                current = current.value
            if isinstance(current, ast.Name) and current.id == "self" and len(chain) >= 2:
                chains.add(tuple(reversed(chain)))
    assert len(chains) > 20
    for chain in sorted(chains):
        target = hw
        for name in chain:
            assert hasattr(target, name), "self." + ".".join(chain)
            target = getattr(target, name)
