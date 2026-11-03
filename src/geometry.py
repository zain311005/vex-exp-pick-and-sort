# geometry.py
#
# Plain maths used by the robot and the simulator. Nothing in here talks to
# hardware, so it runs the same on the EXP Brain and on a laptop.
#
# Headings are compass degrees: 0 points north (+y), 90 points east (+x),
# and they increase clockwise, which matches the EXP Brain's inertial sensor.

import math


def clamp(value, low, high):
    """Limit value to the range low..high."""
    if value < low:
        return low
    if value > high:
        return high
    return value


def wrap_180(angle):
    """Wrap an angle in degrees into the range -180 (inclusive) to 180."""
    return (angle + 180.0) % 360.0 - 180.0


def wrap_360(angle):
    """Wrap an angle in degrees into the range 0 (inclusive) to 360."""
    return angle % 360.0


def compass_vector(heading):
    """Unit vector (dx, dy) pointing along a compass heading."""
    rad = math.radians(heading)
    return math.sin(rad), math.cos(rad)


def bearing(x0, y0, x1, y1):
    """Compass heading from point 0 to point 1."""
    return wrap_360(math.degrees(math.atan2(x1 - x0, y1 - y0)))


def distance_between(x0, y0, x1, y1):
    """Straight-line distance between two points."""
    dx = x1 - x0
    dy = y1 - y0
    return math.sqrt(dx * dx + dy * dy)


def waypoints_to_segments(start_x, start_y, waypoints, final_heading):
    """Turn a list of (x, y) points into turn and drive segments.

    For each point the robot turns to face it, then drives straight to it.
    Points that repeat the previous point are skipped. After the last point
    the robot turns to final_heading.
    """
    segments = []
    x = start_x
    y = start_y
    for point in waypoints:
        px = float(point[0])
        py = float(point[1])
        length = distance_between(x, y, px, py)
        if length > 0.0:
            segments.append(("turn", bearing(x, y, px, py)))
            segments.append(("drive", length))
        x = px
        y = py
    segments.append(("turn", wrap_360(final_heading)))
    return segments


def trace_segments(start_x, start_y, start_heading, segments):
    """Where perfect segments would take the robot, as a list of (x, y).

    Used to check that a path really visits the points it should.
    """
    x = start_x
    y = start_y
    heading = start_heading
    points = []
    for kind, value in segments:
        if kind == "turn":
            heading = wrap_360(value)
        elif kind == "drive":
            dx, dy = compass_vector(heading)
            x += value * dx
            y += value * dy
            points.append((x, y))
        else:
            raise ValueError("unknown segment type: %s" % kind)
    return points
