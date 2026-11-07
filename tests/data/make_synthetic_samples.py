"""Write tests/data/colour_samples_synthetic.csv.

    python3 tests/data/make_synthetic_samples.py

The readings are invented with a fixed random seed. They were NOT recorded
from a real Optical Sensor. They give the tests something shaped like a
calibration log until real logs exist. The centres and spreads below are
guesses, not measurements. Laptop only.
"""

import os
import random

SEED = 7
HERE = os.path.dirname(os.path.abspath(__file__))
OUTPUT = os.path.join(HERE, "colour_samples_synthetic.csv")

# label, hue centre (None = no clear hue), hue spread,
# brightness centre, brightness spread, number of readings
LOOKS = [
    ("empty", None, 0.0, 4.0, 1.0, 30),
    ("red", 3.0, 4.0, 42.0, 4.0, 30),
    ("green", 118.0, 5.0, 35.0, 4.0, 30),
    ("blue", 215.0, 5.0, 28.0, 3.0, 30),
    ("orange", 32.0, 4.0, 45.0, 4.0, 14),
    ("white", None, 0.0, 70.0, 5.0, 14),
]

HEADER = [
    "# SYNTHETIC SAMPLE READINGS. These were not recorded from a real sensor.",
    "# Made by tests/data/make_synthetic_samples.py (seed %d) so the colour" % SEED,
    "# tests have something to run on until real calibration logs exist.",
    "# Same format as the colour_calibrate log: label,hue,brightness.",
    "# Hue in degrees, brightness in percent, LED assumed at 50 percent.",
    "label,hue,brightness",
]


def main():
    rng = random.Random(SEED)
    lines = list(HEADER)
    for label, hue, hue_spread, light, light_spread, count in LOOKS:
        for _ in range(count):
            if hue is None:
                reading = rng.uniform(0.0, 360.0)
            else:
                reading = rng.gauss(hue, hue_spread)
            brightness = max(0.0, min(100.0, rng.gauss(light, light_spread)))
            lines.append("%s,%.1f,%.1f" % (label, reading % 360.0, brightness))
    with open(OUTPUT, "w") as handle:
        handle.write("\n".join(lines) + "\n")
    print("wrote %s (%d readings)" % (os.path.basename(OUTPUT), len(lines) - len(HEADER)))


if __name__ == "__main__":
    main()
