import ast
import math
import os
import subprocess

import pytest

import paths
from settings import *
from geometry import distance_between, trace_segments
from paths import get_path, path_names
from sim_hardware import rectangle, robot_outline

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def submitted_route():
    """START and ROUTE from the assignment program on the submission-v1 tag."""
    try:
        source = subprocess.run(
            ["git", "show", "refs/tags/submission-v1:catapultbot.py"],
            cwd=ROOT, capture_output=True, text=True, check=True).stdout
    except (OSError, subprocess.CalledProcessError):
        pytest.skip("the submission-v1 tag is not in this copy of the repository")
    values = {}
    for node in ast.parse(source).body:
        if (isinstance(node, ast.Assign) and len(node.targets) == 1
                and isinstance(node.targets[0], ast.Name)
                and node.targets[0].id in ("START", "ROUTE")):
            values[node.targets[0].id] = ast.literal_eval(node.value)
    return values["START"], values["ROUTE"]


def test_original_waypoints_match_the_submission():
    start, route = submitted_route()
    assert (START_X, START_Y) == tuple(start)
    assert [tuple(point) for point in ORIGINAL_WAYPOINTS] == [tuple(point) for point in route]


def test_original_path_visits_every_waypoint():
    segments = get_path("original")
    points = trace_segments(START_X, START_Y, START_HEADING, segments)
    assert len(points) == len(ORIGINAL_WAYPOINTS)
    for (x, y), (wx, wy) in zip(points, ORIGINAL_WAYPOINTS):
        assert distance_between(x, y, wx, wy) < 1e-6
    assert segments[-1] == ("turn", ORIGINAL_FINAL_HEADING)


def test_every_path_builds():
    for name in path_names():
        segments = get_path(name)
        assert segments, name
        for kind, value in segments:
            assert kind in ("turn", "drive")
            assert isinstance(value, float)


def test_unknown_path_name_is_an_error():
    with pytest.raises(ValueError):
        get_path("no_such_path")


def test_unknown_segment_type_is_an_error(monkeypatch):
    monkeypatch.setitem(paths.SEGMENT_PATHS, "broken", [("jump", 100)])
    with pytest.raises(ValueError):
        get_path("broken")


def test_original_path_never_touches_a_box(original_run):
    result, hw = original_run
    assert result == "done"
    assert hw.collisions == 0


def test_original_path_keeps_the_turning_centre_on_the_board(original_run):
    result, hw = original_run
    for t_ms, x, y, heading in hw.trace:
        assert BOARD_MIN_X <= x <= BOARD_MAX_X
        assert BOARD_MIN_Y <= y <= BOARD_MAX_Y


def point_to_segment(px, py, ax, ay, bx, by):
    dx, dy = bx - ax, by - ay
    length_sq = dx * dx + dy * dy
    t = 0.0
    if length_sq > 0:
        t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / length_sq))
    return math.hypot(px - (ax + t * dx), py - (ay + t * dy))


def gap_between(a, b):
    """Shortest distance between two convex polygons that do not overlap."""
    best = float("inf")
    for corners, edges in ((a, b), (b, a)):
        for px, py in corners:
            for i in range(len(edges)):
                ax, ay = edges[i]
                bx, by = edges[(i + 1) % len(edges)]
                best = min(best, point_to_segment(px, py, ax, ay, bx, by))
    return best


@pytest.mark.parametrize("name", path_names())
def test_every_path_keeps_clear_of_every_box(name):
    from main import run
    from sim_hardware import SimHardware
    hw = SimHardware()
    assert run(hw, "path", name) == "done"
    boxes = []
    for cx, cy in list(BOX_POSITIONS.values()) + [REJECT_POSITION]:
        x0, y0, x1, y1 = rectangle(cx, cy, BOX_SIZE_MM, BOX_SIZE_MM)
        boxes.append([(x0, y0), (x1, y0), (x1, y1), (x0, y1)])
    closest = float("inf")
    for t_ms, x, y, heading in hw.trace:
        outline = robot_outline(x, y, heading)
        for box in boxes:
            closest = min(closest, gap_between(outline, box))
    assert closest >= BOX_CLEARANCE_MM, "closest approach %.0f mm" % closest
