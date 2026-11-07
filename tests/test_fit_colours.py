import io
import os

import pytest

import colour
from fit_colours import main, read_log, report

DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
SYNTHETIC = os.path.join(DATA, "colour_samples_synthetic.csv")


@pytest.fixture(autouse=True)
def fixed_colours(monkeypatch):
    monkeypatch.setattr(colour, "COLOURS", ["red", "green", "blue"])


def test_read_log_skips_lines_that_are_not_readings():
    console = [
        "Clawbot sorter",
        "label,hue,brightness",
        "empty,120.5,3.9",
        "red,4.0,41.2",
        "# a comment, with, commas",
        "path original done segment 29 time 82.8 s x 0 y -150",
        "RED,6.0,40.0",
    ]
    assert read_log(console) == {"empty": [(120.5, 3.9)], "red": [(4.0, 41.2), (6.0, 40.0)]}


def test_report_on_the_synthetic_samples():
    with open(SYNTHETIC) as handle:
        readings = read_log(handle)
    out = io.StringIO()
    assert report(readings, out) == 0
    text = out.getvalue()
    names = {}
    exec(text.split("\n\n")[0], names)    # the pasteable settings run as Python
    assert sorted(names["COLOUR_REFERENCES"]) == ["blue", "green", "red"]
    for label in ("empty", "red", "green", "blue", "orange", "white"):
        assert "\n" + label + " " in text


def test_report_needs_every_colour():
    out = io.StringIO()
    assert report({"empty": [(0.0, 4.0)], "red": [(3.0, 40.0)]}, out) == 1
    assert "missing readings for: green, blue" in out.getvalue()


def test_report_says_when_balls_are_too_dark():
    dark = [(10.0, 4.0)] * 20
    out = io.StringIO()
    readings = {"empty": dark, "red": dark, "green": dark, "blue": dark}
    assert report(readings, out) == 1
    assert "calibration failed: red too dark" in out.getvalue()


def test_main_without_a_file_prints_the_help(capsys):
    assert main([]) == 2
    assert "fit_colours.py colour_log.csv" in capsys.readouterr().out
