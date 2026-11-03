# conftest.py
#
# Puts config/, src/, sim/, tools/ and tests/ on the import path so the
# tests can import the robot code module by module, the same modules that
# tools/build_brain.py joins into brain/clawbot.py.

import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for folder in ("config", "src", "sim", "tools", "tests"):
    path = os.path.join(ROOT, folder)
    if path not in sys.path:
        sys.path.insert(0, path)


@pytest.fixture(scope="session")
def original_run():
    """The original path, run once in the simulator with perfect wheels."""
    from main import run
    from sim_hardware import SimHardware
    hw = SimHardware()
    result = run(hw, "path", "original")
    return result, hw
