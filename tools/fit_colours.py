"""Work out colour references from logged Optical Sensor readings.

    python3 tools/fit_colours.py colour_log.csv

The input is the log that RUN_MODE "colour_calibrate" writes: colour_log.csv
from the Brain's SD card, or the same lines copied out of the VEXcode
console. Each line is label,hue,brightness, where label is "empty" or a
colour name. Lines that do not look like that are skipped, so a whole
console dump works.

It uses the same maths as the Brain (src/colour.py), prints settings to
paste into config/settings.py, and then shows how each logged reading would
be classified. This is plain arithmetic (averages and spreads), not machine
learning. Laptop only: this script never goes onto the Brain.
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
for folder in ("config", "src"):
    path = os.path.join(ROOT, folder)
    if path not in sys.path:
        sys.path.insert(0, path)

import colour  # noqa: E402

EMPTY = "empty"


def read_log(lines):
    """label -> list of (hue, brightness), in the order the lines come."""
    readings = {}
    for line in lines:
        parts = line.strip().split(",")
        if len(parts) != 3:
            continue
        label = parts[0].strip().lower()
        try:
            hue = float(parts[1])
            brightness = float(parts[2])
        except ValueError:
            continue
        readings.setdefault(label, []).append((hue, brightness))
    return readings


def report(readings, out):
    """Fit the references, print them and a results table. Returns 0 or 1."""
    missing = [name for name in [EMPTY] + list(colour.COLOURS) if name not in readings]
    if missing:
        out.write("missing readings for: %s\n" % ", ".join(missing))
        return 1
    balls = dict((name, readings[name]) for name in colour.COLOURS)
    references, gate, problem = colour.fit_calibration(readings[EMPTY], balls)
    if problem is not None:
        out.write("calibration failed: %s\n" % problem)
        return 1

    out.write("# Paste into config/settings.py\n")
    out.write(colour.settings_text(references, gate) + "\n\n")
    close = colour.overlaps(references)
    if close:
        out.write("Warning: these colours look alike: %s\n\n" % ", ".join(close))

    answers = [colour.NONE, colour.UNKNOWN] + list(colour.COLOURS)
    out.write("How each logged reading is classified, one reading at a time.\n")
    out.write("The fit used these same readings, so this is an optimistic check.\n")
    out.write("%-10s" % "logged" + "".join("%9s" % answer for answer in answers) + "\n")
    order = [EMPTY] + list(colour.COLOURS)
    order += sorted(label for label in readings if label not in order)
    for label in order:
        counts = dict((answer, 0) for answer in answers)
        for hue, brightness in readings[label]:
            counts[colour.classify(hue, brightness, references, gate)] += 1
        out.write("%-10s" % label + "".join("%9d" % counts[answer] for answer in answers) + "\n")
    return 0


def main(argv):
    if len(argv) != 1:
        sys.stdout.write(__doc__)
        return 2
    with open(argv[0]) as handle:
        readings = read_log(handle)
    return report(readings, sys.stdout)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
