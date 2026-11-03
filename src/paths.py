# paths.py
#
# Paths are lists of segments:
#   ("turn", h)  turn on the spot to compass heading h (degrees)
#   ("drive", d) drive d mm along the current heading (negative = backwards)
#
# "original" is built from ORIGINAL_WAYPOINTS, the route copied exactly from
# the assignment program. Other paths are written as segments in settings.py.

from settings import *
from geometry import waypoints_to_segments


def path_names():
    """Every path that can be selected, original first."""
    names = ["original"]
    for name in sorted(SEGMENT_PATHS):
        names.append(name)
    return names


def get_path(name):
    """The segments for the path called name."""
    if name == "original":
        return waypoints_to_segments(START_X, START_Y, ORIGINAL_WAYPOINTS,
                                     ORIGINAL_FINAL_HEADING)
    if name in SEGMENT_PATHS:
        segments = []
        for kind, value in SEGMENT_PATHS[name]:
            if kind not in ("turn", "drive"):
                raise ValueError("path %s has an unknown segment: %s" % (name, kind))
            segments.append((kind, float(value)))
        return segments
    raise ValueError("unknown path: %s" % name)
