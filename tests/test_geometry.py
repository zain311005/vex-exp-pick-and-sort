import math

import pytest

from geometry import (bearing, clamp, compass_vector, distance_between,
                      trace_segments, waypoints_to_segments, wrap_180, wrap_360)


def test_clamp():
    assert clamp(5, 0, 10) == 5
    assert clamp(-1, 0, 10) == 0
    assert clamp(11, 0, 10) == 10


@pytest.mark.parametrize("angle, wrapped", [
    (0, 0), (90, 90), (180, -180), (190, -170), (-190, 170), (360, 0), (540, -180), (-90, -90),
])
def test_wrap_180(angle, wrapped):
    assert wrap_180(angle) == pytest.approx(wrapped)


@pytest.mark.parametrize("angle, wrapped", [(0, 0), (-10, 350), (370, 10), (720, 0), (359.5, 359.5)])
def test_wrap_360(angle, wrapped):
    assert wrap_360(angle) == pytest.approx(wrapped)


@pytest.mark.parametrize("heading, vector", [(0, (0, 1)), (90, (1, 0)), (180, (0, -1)), (270, (-1, 0))])
def test_compass_vector_points_the_right_way(heading, vector):
    dx, dy = compass_vector(heading)
    assert dx == pytest.approx(vector[0], abs=1e-9)
    assert dy == pytest.approx(vector[1], abs=1e-9)


@pytest.mark.parametrize("target, heading", [((0, 1), 0), ((1, 0), 90), ((0, -1), 180), ((-1, 0), 270), ((1, 1), 45)])
def test_bearing_is_a_compass_heading(target, heading):
    assert bearing(0, 0, target[0], target[1]) == pytest.approx(heading)


def test_distance_between():
    assert distance_between(0, 0, 3, 4) == pytest.approx(5)


def test_waypoints_become_turn_then_drive():
    segments = waypoints_to_segments(0, 0, [(0, 300), (300, 300)], 0)
    assert segments == [("turn", 0.0), ("drive", 300.0),
                        ("turn", 90.0), ("drive", 300.0),
                        ("turn", 0.0)]


def test_repeated_waypoints_are_skipped():
    segments = waypoints_to_segments(0, 0, [(0, 300), (0, 300), (0, 600)], 90)
    assert segments == [("turn", 0.0), ("drive", 300.0),
                        ("turn", 0.0), ("drive", 300.0),
                        ("turn", 90.0)]


def test_trace_follows_the_segments():
    points = trace_segments(0, 0, 0, [("drive", 100), ("turn", 90), ("drive", 50), ("drive", -20)])
    expected = [(0, 100), (50, 100), (30, 100)]
    for (x, y), (ex, ey) in zip(points, expected):
        assert x == pytest.approx(ex, abs=1e-9)
        assert y == pytest.approx(ey, abs=1e-9)


def test_trace_rejects_unknown_segments():
    with pytest.raises(ValueError):
        trace_segments(0, 0, 0, [("jump", 100)])


def test_diagonal_waypoint():
    segments = waypoints_to_segments(0, 0, [(300, 300)], 0)
    assert segments[0] == ("turn", pytest.approx(45.0))
    assert segments[1] == ("drive", pytest.approx(300 * math.sqrt(2)))
