import ast
import os
import sys

import pytest

import build_brain
import fake_vex
from settings import *

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BRAIN_FILE = build_brain.OUTPUT

shipped_defaults = pytest.mark.skipif(
    RUN_MODE != "path" or SELECTED_PATH != "original",
    reason="checks the shipped settings: RUN_MODE 'path', SELECTED_PATH 'original'")


def brain_source():
    with open(BRAIN_FILE) as handle:
        return handle.read()


# ---------------------------------------------------------------- build
def test_brain_file_is_up_to_date():
    assert build_brain.build() == brain_source(), "run: python3 tools/build_brain.py"


def test_brain_file_imports_only_vex_and_math():
    imported = set()
    for node in ast.walk(ast.parse(brain_source())):
        if isinstance(node, ast.Import):
            imported.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imported.add(node.module)
    assert imported == {"vex", "math"}


def test_brain_file_and_sources_use_only_python_3_4_syntax():
    assert build_brain.micropython_problems(brain_source()) == []
    for part in build_brain.PARTS:
        with open(os.path.join(ROOT, part)) as handle:
            assert build_brain.micropython_problems(handle.read(), part) == [], part


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
def run_brain_file(monkeypatch, **script):
    """Run brain/clawbot.py on the fake vex module. Returns its names."""
    fake_vex.reset(**script)
    monkeypatch.setitem(sys.modules, "vex", fake_vex)
    names = {"__name__": "__main__"}
    exec(compile(brain_source(), BRAIN_FILE, "exec"), names)
    return names


def screen():
    return [fake_vex.state.rows[row] for row in sorted(fake_vex.state.rows)]


def motors():
    return [device for device in fake_vex.state.devices.values()
            if isinstance(device, fake_vex.Motor)]


def test_brain_file_sets_up_every_device_on_its_port(monkeypatch):
    run_brain_file(monkeypatch)
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


@pytest.mark.skipif(RUN_MODE == "sensor_check", reason="sensor_check does not wait for CHECK")
def test_brain_file_ends_if_check_is_never_pressed(monkeypatch):
    run_brain_file(monkeypatch)
    assert screen() == ["Not started.", "Program ended."]
    assert fake_vex.state.now_ms >= START_WAIT_TIMEOUT_MS
    assert all(motor.command == 0 for motor in motors())


@pytest.mark.parametrize("button", ["left_press_ms", "right_press_ms"])
def test_brain_file_stops_on_either_stop_button(monkeypatch, button):
    script = {"check_press_ms": 3000, button: 6000}
    run_brain_file(monkeypatch, **script)
    assert screen() == ["STOPPED", "Stop pressed"]
    assert all(motor.command == 0 for motor in motors())


@shipped_defaults
def test_brain_file_gives_up_when_the_wheels_never_turn(monkeypatch, capsys):
    # the fake motors never move, so the first drive has to time out
    run_brain_file(monkeypatch, check_press_ms=3000)
    assert screen() == ["PATH STOPPED", "Reason: timeout", "At segment 2"]
    assert all(motor.command == 0 for motor in motors())
    assert "path original timeout segment 1" in capsys.readouterr().out


def test_every_vex_call_in_hardware_is_in_the_fake_api(monkeypatch):
    """Each self.<device>.<call> in hardware.py must exist on the fake vex
    objects, and fake_vex.py only has calls copied from the VEX API pages."""
    fake_vex.reset()
    monkeypatch.setitem(sys.modules, "vex", fake_vex)
    names = {"__name__": "brain_without_main"}
    source = brain_source()
    assert source.endswith("\nmain()\n")
    exec(compile(source[:-len("main()\n")], BRAIN_FILE, "exec"), names)
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
