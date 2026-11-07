# distance.py
#
# Turns raw Distance Sensor readings into a distance the robot can act on.
#
# The rules:
#   1. A reading is valid only if the sensor says it sees an object and the
#      value is inside DISTANCE_MIN_MM to DISTANCE_MAX_MM, the range the VEX
#      API page gives. Anything else is kept as "invalid".
#   2. The filter keeps the last DISTANCE_WINDOW readings, valid or not, and
#      takes a new one at most every DISTANCE_SAMPLE_MS.
#   3. The distance is the median of the valid readings in the window, but
#      only when there are at least DISTANCE_MIN_VALID of them. Otherwise
#      the distance is None, meaning "nothing seen".
#   4. An object is IN RANGE when that distance is OBJECT_RANGE_MM or less.
#
# With 5 readings and at least 3 valid, one wild reading cannot move the
# median past the good ones, and one missed reading does not lose the object.

from settings import *


def valid_distance(raw):
    """raw as a float in mm if it is a usable reading, otherwise None."""
    if raw is None:
        return None
    try:
        value = float(raw)
    except (TypeError, ValueError):
        return None
    if value != value:
        return None   # NaN
    if value < DISTANCE_MIN_MM or value > DISTANCE_MAX_MM:
        return None
    return value


def median(values):
    """Median of a non-empty list of numbers."""
    ordered = sorted(values)
    middle = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[middle]
    return (ordered[middle - 1] + ordered[middle]) / 2.0


class DistanceFilter:
    def __init__(self):
        self.readings = []
        self.last_ms = None

    def reset(self):
        self.readings = []
        self.last_ms = None

    def add(self, raw):
        """Put one raw reading (mm, or None for nothing seen) in the window."""
        self.readings.append(valid_distance(raw))
        if len(self.readings) > DISTANCE_WINDOW:
            self.readings.pop(0)

    def update(self, hw):
        """Read the sensor if DISTANCE_SAMPLE_MS has passed since last time."""
        now = hw.time_ms()
        if self.last_ms is None or now - self.last_ms >= DISTANCE_SAMPLE_MS:
            self.last_ms = now
            self.add(hw.distance_raw())

    def distance(self):
        """Median of the valid readings in mm, or None if too few are valid."""
        valid = [reading for reading in self.readings if reading is not None]
        if len(valid) < DISTANCE_MIN_VALID:
            return None
        return median(valid)

    def in_range(self):
        """True when an object is at OBJECT_RANGE_MM or nearer."""
        found = self.distance()
        return found is not None and found <= OBJECT_RANGE_MM

    def fill(self, robot):
        """Start again and take a full window of readings, then distance().

        The robot keeps ticking in between, so the stop button still works.
        Takes about DISTANCE_WINDOW times DISTANCE_SAMPLE_MS.
        """
        self.reset()
        while len(self.readings) < DISTANCE_WINDOW:
            self.update(robot.hw)
            robot.tick()
        return self.distance()
