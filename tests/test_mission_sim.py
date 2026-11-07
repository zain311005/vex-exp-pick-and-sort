"""Sorting runs in the simulator, with the shipped settings.

The balls sit where the comment on "sort_loop" in config/settings.py says
to put them. If you move the boxes or change the path, move them here too.
"""

import pytest

import main as main_module
import mission
from geometry import distance_between, wrap_180
from main import run
from mission import box_poses, on_board, point_ahead
from settings import *
from sim_hardware import (DEMO_BALLS, SimHardware, _polygons_overlap, _rect_polygon,
                          rectangle, robot_outline)

FOUR_BALLS = DEMO_BALLS     # red, orange (never calibrated), blue, green
ONE_PASS = ["APPROACH", "GRAB", "CLASSIFY", "GO_TO_BOX", "RELEASE", "RETURN", "FOLLOW_PATH"]


def record_screens(hw, react=None):
    """Keep every screen the program shows. react(hw, lines) is called too."""
    shown = []
    show = hw.show

    def record(lines):
        shown.append(list(lines))
        if react is not None:
            react(hw, lines)
        show(lines)

    hw.show = record
    return shown


def sort(balls, path="sort_loop", react=None, **options):
    hw = SimHardware(balls=balls, **options)
    shown = record_screens(hw, react)
    result = run(hw, "sort", path)
    return result, hw, shown


def states(hw):
    return [line[len("state "):] for line in hw.console if line.startswith("state ")]


def motors_stopped(hw):
    return all(motor.command == 0 for motor in (hw.left, hw.right, hw.arm, hw.claw))


@pytest.fixture(scope="module")
def full_sort():
    # the arm and claw start part way, so homing has to find their stops
    return sort(FOUR_BALLS, arm_start_deg=80.0, claw_start_deg=40.0)


# --------------------------------------------------------- a normal sort
def test_every_ball_ends_up_in_the_right_box(full_sort):
    result, hw, shown = full_sort
    assert result == "done"
    assert hw.box_contents == {"red": ["red"], "green": ["green"], "blue": ["blue"],
                               "reject": ["orange"]}
    assert hw.balls == [] and hw.held_ball is None
    assert hw.collisions == 0


def test_states_run_in_the_expected_order(full_sort):
    result, hw, shown = full_sort
    assert states(hw) == ["FOLLOW_PATH"] + ONE_PASS * 4


def test_robot_comes_back_to_where_it_started(full_sort):
    result, hw, shown = full_sort
    assert distance_between(hw.x, hw.y, START_X, START_Y) < 50.0
    assert abs(wrap_180(hw.theta - START_HEADING)) < 3.0


def test_screen_shows_the_state_and_the_colour(full_sort):
    result, hw, shown = full_sort
    first_lines = set(lines[0] for lines in shown)
    assert set(ONE_PASS) <= first_lines
    assert ["GO_TO_BOX", "Colour red"] in [lines[:2] for lines in shown]
    assert ["GO_TO_BOX", "Colour unknown"] in [lines[:2] for lines in shown]
    assert shown[-1] == ["SORT DONE", "R1 G1 B1 Rej 1", "Gave up 0",
                         shown[-1][3], "Position drifts"]


def test_no_balls_means_one_lap_and_no_detours():
    result, hw, shown = sort([])
    assert result == "done"
    assert states(hw) == ["FOLLOW_PATH"]
    assert hw.collisions == 0


def test_boxes_seen_from_the_board_are_not_taken_for_balls():
    # on the original path the Distance Sensor sees the colour boxes from
    # column D, about 320 mm away, but they are off the board
    seen = []
    hw = SimHardware()
    raw = hw.distance_raw

    def distance_and_note():
        reading = raw()
        if reading is not None and reading <= OBJECT_RANGE_MM:
            seen.append(reading)
        return reading

    hw.distance_raw = distance_and_note
    assert run(hw, "sort", "original") == "done"
    assert seen
    assert states(hw) == ["FOLLOW_PATH"]


# ------------------------------------------------- known limits of the sort
def test_gyro_drift_can_make_a_drop_miss_without_the_robot_knowing():
    """Dead reckoning drifts, and nothing checks what lands in a box.

    With the gyro drifting 0.02 degrees a second (about 1 degree a minute)
    the robot still counts every ball as sorted, but one of them lands
    beside its box instead of in it.
    """
    result, hw, shown = sort(FOUR_BALLS, imu_drift_dps=0.02)
    assert result == "done"
    assert shown[-1][1] == "R1 G1 B1 Rej 1"          # what the robot believes
    landed = sum(len(balls) for balls in hw.box_contents.values())
    assert landed < 4                                # what really happened
    assert len(hw.balls) == 4 - landed


# --------------------------------------------------------- failure paths
def test_unknown_colour_can_stop_the_sort_instead(monkeypatch):
    monkeypatch.setattr(mission, "UNKNOWN_COLOUR_ACTION", "stop")
    result, hw, shown = sort([{"x": 0.0, "y": 300.0, "colour": "orange"}])
    assert result == "failed"
    assert hw.screen[:3] == ["SORT STOPPED", "unknown colour", "CLASSIFY"]
    assert motors_stopped(hw)


def clear_when_blocked(hw, lines):
    """Act like a person: take the balls away and press CHECK."""
    if lines[0] == "BLOCKED" and not getattr(hw, "cleared", False):
        hw.cleared = True
        hw.balls = []
        hw.obstacles = hw.obstacles[:4]          # just the boxes
        hw.check_presses.append(hw.t_ms + 500.0)


def test_ball_that_slips_out_is_given_up_then_cleared_by_hand():
    slippery = {"x": 0.0, "y": 300.0, "colour": "red", "grabbable": False}
    result, hw, shown = sort([slippery], react=clear_when_blocked)
    assert result == "done"
    assert states(hw)[:5] == ["FOLLOW_PATH", "APPROACH", "GRAB", "APPROACH", "GRAB"]
    assert any("grip failed" in line for line in hw.console)
    assert "blocked in FOLLOW_PATH" in hw.console
    assert shown[-1][2] == "Gave up 1"
    assert hw.box_contents["red"] == []


def take_it_away_on_approach(hw, lines):
    if lines[0] == "APPROACH" and hw.balls:
        hw.balls = []


def test_ball_that_disappears_during_the_approach_is_given_up():
    result, hw, shown = sort([{"x": 0.0, "y": 300.0, "colour": "red"}],
                             react=take_it_away_on_approach)
    assert result == "done"
    assert any("approach lost" in line for line in hw.console)
    assert states(hw) == ["FOLLOW_PATH", "APPROACH", "RETURN", "FOLLOW_PATH"]


def test_ball_stuck_in_the_claw_stops_with_a_message():
    sticky = {"x": 0.0, "y": 300.0, "colour": "red", "sticky": True}
    result, hw, shown = sort([sticky])
    assert result == "failed"
    assert hw.screen[:3] == ["SORT STOPPED", "ball stuck", "RELEASE"]
    assert motors_stopped(hw)


def test_something_in_the_way_that_nobody_clears(monkeypatch):
    monkeypatch.setattr(mission, "BLOCKED_TIMEOUT_MS", 2000)
    block = (-100.0, 400.0, 100.0, 450.0)    # not a ball, on the first side
    result, hw, shown = sort([], obstacles=[block])
    assert result == "failed"
    assert hw.screen[:2] == ["SORT STOPPED", "path blocked"]
    # it was taken for a ball first; the claw hit it before the Distance
    # Sensor read APPROACH_STOP_MM, so the approach found itself stuck
    assert any("approach stuck" in line for line in hw.console)
    assert hw.collisions > 0      # touching it is how the robot found out
    assert motors_stopped(hw)


def test_stop_button_during_the_sort():
    result, hw, shown = sort(FOUR_BALLS, stop_press_ms=20000.0)
    assert result == "stopped"
    assert hw.screen[0] == "STOPPED"
    assert motors_stopped(hw)


def test_arm_that_never_reaches_a_stop_ends_the_sort():
    result, hw, shown = sort(FOUR_BALLS, arm_stops=False)
    assert result == "failed"
    assert hw.screen[:2] == ["SORT STOPPED", "arm not homed"]
    assert motors_stopped(hw)


def test_whole_sort_has_a_time_limit(monkeypatch):
    monkeypatch.setattr(mission, "MISSION_TIMEOUT_MS", 30000)
    result, hw, shown = sort(FOUR_BALLS)
    assert result == "failed"
    assert hw.screen[:2] == ["SORT STOPPED", "took too long"]


def test_sort_refuses_a_box_on_the_board(monkeypatch):
    monkeypatch.setattr(main_module, "REJECT_POSITION", (450.0, 600.0))
    hw = SimHardware()
    assert run(hw, "sort") == "bad_setting"
    assert hw.screen[0] == "Box on the board"


def test_sort_refuses_an_unknown_rule_it_does_not_know(monkeypatch):
    monkeypatch.setattr(main_module, "UNKNOWN_COLOUR_ACTION", "keep")
    hw = SimHardware()
    assert run(hw, "sort") == "bad_setting"
    assert hw.screen[0] == "Bad unknown rule"


# ------------------------------------------------------- drop geometry
@pytest.mark.parametrize("name", sorted(BOX_POSITIONS) + ["reject"])
def test_drop_geometry(name):
    cx, cy = REJECT_POSITION if name == "reject" else BOX_POSITIONS[name]
    line_x, line_y, drop_x, drop_y, heading = box_poses(cx, cy)
    box = _rect_polygon(rectangle(cx, cy, BOX_SIZE_MM, BOX_SIZE_MM))
    assert on_board(line_x, line_y, 0.0)
    # with the arm up, the held ball is over the box with room all round it
    bx, by = point_ahead(drop_x, drop_y, heading, DROP_REACH_MM)
    room = BOX_SIZE_MM / 2.0 - BALL_DIAMETER_MM / 2.0
    assert abs(bx - cx) <= room + 1e-6 and abs(by - cy) <= room + 1e-6
    # the chassis stays outside the box at the drop point
    assert not _polygons_overlap(robot_outline(drop_x, drop_y, heading, CHASSIS_FRONT_MM), box)
    # and the whole robot, claw included, is clear of it at the line-up point
    assert not _polygons_overlap(robot_outline(line_x, line_y, heading), box)
