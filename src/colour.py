# colour.py
#
# Works out the colour of the ball in the claw from the Optical Sensor.
# This is a calibrated rule, not machine learning: it compares the hue with
# reference hues that you record yourself in the calibration step, and it
# does not change itself while it runs.
#
# The rule for one reading:
#   1. Brightness gate. A reading darker than the gate means nothing is in
#      front of the sensor, so the answer is "none".
#   2. Nearest match. Otherwise find the reference hue nearest to the
#      reading's hue, going round the colour wheel (359 is next to 0).
#   3. Tolerance. If the reading is further from that hue than the colour's
#      tolerance, the answer is "unknown".
# read_colour() then takes COLOUR_READS readings and gives a colour only if
# at least COLOUR_MIN_VOTES of them agree. Otherwise it says "unknown".
#
# Calibration (RUN_MODE "colour_calibrate") records COLOUR_CAL_SAMPLES
# readings with the claw empty and with each ball in turn. A colour's
# reference hue is the average of its hues round the colour wheel, and its
# tolerance is COLOUR_SPREAD_FACTOR times how far the hues spread, kept
# between COLOUR_MIN_TOLERANCE_DEG and COLOUR_MAX_TOLERANCE_DEG. The gate
# sits halfway between the empty claw and the darkest ball.

import math

from settings import *
from geometry import clamp, wrap_180, wrap_360

NONE = "none"
UNKNOWN = "unknown"


# ------------------------------------------------------------------ maths
def average(values):
    """Plain mean of a non-empty list."""
    return sum(values) / float(len(values))


def circular_mean(angles):
    """Mean of angles in degrees, going round the circle.

    The plain mean of 350 and 10 is 180, which is the wrong side of the
    wheel. This gives 0.
    """
    s = 0.0
    c = 0.0
    for angle in angles:
        s += math.sin(math.radians(angle))
        c += math.cos(math.radians(angle))
    return wrap_360(math.degrees(math.atan2(s, c)))


def circular_spread(angles, centre):
    """Root mean square distance of the angles from centre, in degrees."""
    total = 0.0
    for angle in angles:
        error = wrap_180(angle - centre)
        total += error * error
    return math.sqrt(total / len(angles))


def fit_reference(hues):
    """(reference hue, tolerance) from one colour's calibration hues."""
    centre = circular_mean(hues)
    tolerance = clamp(COLOUR_SPREAD_FACTOR * circular_spread(hues, centre),
                      COLOUR_MIN_TOLERANCE_DEG, COLOUR_MAX_TOLERANCE_DEG)
    return (centre, tolerance)


def fit_calibration(empty, balls):
    """References and gate from calibration readings.

    empty is a list of (hue, brightness) taken with the claw empty. balls
    maps each colour name to its list of (hue, brightness). Returns
    (references, gate, problem). problem is None when it worked, or a short
    message naming the colour that had too few readings bright enough to use.
    """
    empty_brightness = average([b for h, b in empty])
    floor = empty_brightness + COLOUR_MIN_BRIGHTNESS_GAP
    references = {}
    darkest = None
    for name in COLOURS:
        good = [(h, b) for h, b in balls.get(name, []) if b >= floor]
        if len(good) < COLOUR_CAL_MIN_GOOD:
            return None, None, name + " too dark"
        references[name] = fit_reference([h for h, b in good])
        brightness = average([b for h, b in good])
        if darkest is None or brightness < darkest:
            darkest = brightness
    return references, (empty_brightness + darkest) / 2.0, None


def overlaps(references):
    """Pairs of colours whose hue ranges overlap, such as "red/blue"."""
    found = []
    for i in range(len(COLOURS)):
        for j in range(i + 1, len(COLOURS)):
            a = references[COLOURS[i]]
            b = references[COLOURS[j]]
            if abs(wrap_180(a[0] - b[0])) < a[1] + b[1]:
                found.append(COLOURS[i] + "/" + COLOURS[j])
    return found


# -------------------------------------------------------- classification
def nearest_colour(hue, references):
    """(name, error in degrees) of the reference hue nearest to hue."""
    best = None
    best_error = None
    for name in COLOURS:
        if name in references:
            error = abs(wrap_180(hue - references[name][0]))
            if best_error is None or error < best_error:
                best = name
                best_error = error
    return best, best_error


def classify(hue, brightness, references, gate):
    """One reading: a colour name, NONE or UNKNOWN."""
    if brightness < gate:
        return NONE
    name, error = nearest_colour(hue, references)
    if name is None or error > references[name][1]:
        return UNKNOWN
    return name


def vote(labels):
    """The label that at least COLOUR_MIN_VOTES readings agree on, else UNKNOWN."""
    best = UNKNOWN
    best_count = 0
    for label in labels:
        count = labels.count(label)
        if count > best_count:
            best = label
            best_count = count
    if best_count >= COLOUR_MIN_VOTES:
        return best
    return UNKNOWN


def read_colour(robot, references, gate):
    """Take COLOUR_READS readings and vote. Returns (answer, labels)."""
    hw = robot.hw
    labels = []
    while len(labels) < COLOUR_READS:
        labels.append(classify(hw.optical_hue(), hw.optical_brightness(), references, gate))
        robot.pause(COLOUR_READ_MS)
    return vote(labels), labels


# ---------------------------------------------------- saving and loading
def calibration_text(references, gate):
    """The calibration as the text stored in COLOUR_FILE."""
    lines = ["# colour calibration: name hue tolerance", "gate %.1f" % gate]
    for name in COLOURS:
        lines.append("%s %.1f %.1f" % (name, references[name][0], references[name][1]))
    return "\n".join(lines) + "\n"


def settings_text(references, gate):
    """The same calibration written as lines for config/settings.py."""
    lines = ["COLOUR_REFERENCES = {"]
    for name in COLOURS:
        lines.append('    "%s": (%.1f, %.1f),' % (name, references[name][0], references[name][1]))
    lines.append("}")
    lines.append("COLOUR_GATE_BRIGHTNESS = %.1f" % gate)
    return "\n".join(lines)


def parse_calibration(text):
    """(references, gate) from calibration_text(), or None if the text does
    not hold a sensible value for the gate and every colour."""
    references = {}
    gate = None
    for line in text.split("\n"):
        parts = line.split()
        if not parts or parts[0].startswith("#"):
            continue
        try:
            if parts[0] == "gate":
                key, value = parts
                gate = float(value)
            elif parts[0] in COLOURS:
                name, hue, tolerance = parts
                references[name] = (wrap_360(float(hue)), float(tolerance))
            else:
                return None
        except ValueError:
            return None
    if gate is None or gate < 0:
        return None
    for name in COLOURS:
        if name not in references:
            return None
        tolerance = references[name][1]
        if tolerance < COLOUR_MIN_TOLERANCE_DEG or tolerance > COLOUR_MAX_TOLERANCE_DEG:
            return None
    return references, gate


def load_colour_calibration(hw):
    """(references, gate, source). source is "SD card" when COLOUR_FILE on
    the SD card holds a good calibration, otherwise "settings"."""
    text = hw.sd_load(COLOUR_FILE)
    if text is not None:
        parsed = parse_calibration(text)
        if parsed is not None:
            return parsed[0], parsed[1], "SD card"
        hw.log("%s on the SD card is not usable, so settings.py is used" % COLOUR_FILE)
    return COLOUR_REFERENCES, COLOUR_GATE_BRIGHTNESS, "settings"


# ------------------------------------------------------------ calibration
def _collect(robot, prompt):
    """Wait for CHECK, then record COLOUR_CAL_SAMPLES (hue, brightness)
    readings. Returns None if CHECK is not pressed in time."""
    robot.set_lines(["COLOUR CALIBRATE", prompt, "then press CHECK", "L/R = stop"])
    if not robot.wait_for_check(START_WAIT_TIMEOUT_MS):
        return None
    robot.set_lines(["COLOUR CALIBRATE", prompt, "Reading...", "Keep it still"])
    samples = []
    while len(samples) < COLOUR_CAL_SAMPLES:
        samples.append((robot.hw.optical_hue(), robot.hw.optical_brightness()))
        robot.pause(COLOUR_CAL_READ_MS)
    return samples


def colour_calibrate(robot):
    """RUN_MODE "colour_calibrate". Returns "done", "failed" or "no_start".

    The readings go to the console as label,hue,brightness lines and to
    COLOUR_LOG_FILE on the SD card, so tools/fit_colours.py can check them.
    A good calibration is saved to COLOUR_FILE on the SD card and printed as
    lines you can paste into config/settings.py.
    """
    hw = robot.hw
    hw.optical_light(OPTICAL_LIGHT_PCT)
    empty = _collect(robot, "Claw empty")
    if empty is None:
        hw.optical_light(0)
        robot.set_lines(["Not started.", "Program ended."])
        return "no_start"
    balls = {}
    for name in COLOURS:
        samples = _collect(robot, name + " in claw")
        if samples is None:
            hw.optical_light(0)
            robot.set_lines(["Not finished.", "Program ended."])
            return "no_start"
        balls[name] = samples

    lines = ["label,hue,brightness"]
    for hue, brightness in empty:
        lines.append("empty,%.1f,%.1f" % (hue, brightness))
    for name in COLOURS:
        for hue, brightness in balls[name]:
            lines.append("%s,%.1f,%.1f" % (name, hue, brightness))
    for line in lines:
        hw.log(line)
    hw.sd_save(COLOUR_LOG_FILE, "\n".join(lines) + "\n")

    references, gate, problem = fit_calibration(empty, balls)
    if problem is not None:
        hw.log("colour calibration failed: " + problem)
        robot.set_lines(["CALIBRATE FAILED", problem, "Ball in claw?", "LED on?"])
        hw.optical_light(0)
        return "failed"

    saved = hw.sd_save(COLOUR_FILE, calibration_text(references, gate))
    hw.log("colour calibration for config/settings.py:")
    hw.log(settings_text(references, gate))
    close = overlaps(references)
    if close:
        hw.log("these colours look alike: " + ", ".join(close))
    result = ["Saved to SD" if saved else "No SD: console"]
    for name in COLOURS:
        result.append("%s %.0f +-%.0f" % (name, references[name][0], references[name][1]))
    result.append("Gate %.0f%s" % (gate, " CLOSE!" if close else ""))
    robot.set_lines(result)
    hw.optical_light(0)
    return "done"
