# fake_vex.py
#
# A stand-in for the vex module so tests/test_build.py can run
# brain/clawbot.py on a laptop. It is not a simulator: motors do not move
# anything and sensors see nothing. It has a fake clock and scripted Brain
# button presses, and it complains about arguments the real API would not
# take (a wrong unit, two devices on one port, power over 100 percent).
#
# Each class and method copies the name and arguments of a call in the
# VEX EXP Python API (https://api.vex.com/exp/home/python/index.html), and
# only the calls this project uses are here. A call that is missing from
# this file has not been checked against the API, so the tests fail on it.
# docs/REFERENCES.md links each API page.

BUTTON_HOLD_MS = 200
MAX_FAKE_MS = 1000000   # a run longer than this is treated as stuck
SMART_PORTS = 10        # the EXP Brain has Smart Ports 1 to 10

__all__ = [
    "Brain", "Inertial", "Motor", "Distance", "Optical", "Ports", "GearSetting",
    "SoundType", "wait", "MSEC", "SECONDS", "DEGREES", "PERCENT",
    "MM", "FORWARD", "REVERSE", "BRAKE", "HOLD", "COAST",
]


class FakeStuck(Exception):
    """The fake clock ran past MAX_FAKE_MS, so the program never ended."""
    pass


class _State:
    pass


state = _State()


def reset(check_press_ms=None, left_press_ms=None, right_press_ms=None,
          calibration_ms=2000, sd_inserted=False, sd_files=None, optical_at=None):
    """Start a new fake run. Press times are in fake ms; None = never.

    check_press_ms may also be a list of press times.
    calibration_ms=None makes the gyro calibrate forever.
    optical_at, if given, is called with the fake time in ms and returns the
    (hue, brightness) the Optical Sensor sees then.
    """
    state.now_ms = 0.0
    if check_press_ms is None or isinstance(check_press_ms, (int, float)):
        check_press_ms = [check_press_ms]
    state.check_press_ms = list(check_press_ms)
    state.left_press_ms = [left_press_ms]
    state.right_press_ms = [right_press_ms]
    state.calibration_ms = calibration_ms
    state.sd_inserted = sd_inserted
    state.sd_files = dict(sd_files or {})
    state.optical_at = optical_at
    state.devices = {}
    state.rows = {}
    state.sounds = []


reset()


class _Token:
    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return self.name


MSEC = _Token("MSEC")
SECONDS = _Token("SECONDS")
DEGREES = _Token("DEGREES")
PERCENT = _Token("PERCENT")
MM = _Token("MM")
FORWARD = _Token("FORWARD")
REVERSE = _Token("REVERSE")
BRAKE = _Token("BRAKE")
HOLD = _Token("HOLD")
COAST = _Token("COAST")


class Ports:
    pass


for _number in range(1, SMART_PORTS + 1):
    setattr(Ports, "PORT%d" % _number, _number)


class GearSetting:
    RATIO_36_1 = _Token("RATIO_36_1")
    RATIO_18_1 = _Token("RATIO_18_1")
    RATIO_6_1 = _Token("RATIO_6_1")


class SoundType:
    TADA = _Token("TADA")


def _need(value, *allowed):
    if not any(value is choice for choice in allowed):
        raise ValueError("unexpected argument %r, expected one of %r" % (value, allowed))


def _register(device, port):
    if not isinstance(port, int) or not 1 <= port <= SMART_PORTS:
        raise ValueError("%r is not a Smart Port" % (port,))
    if port in state.devices:
        raise ValueError("two devices on port %d" % port)
    state.devices[port] = device


def wait(time, units):
    """VEX EXP Python API, Logic: wait"""
    _need(units, MSEC, SECONDS)
    state.now_ms += time if units is MSEC else time * 1000.0
    if state.now_ms > MAX_FAKE_MS:
        raise FakeStuck("fake clock passed %d ms" % MAX_FAKE_MS)


# ------------------------------------------------------------------ Brain
class _Button:
    def __init__(self, press_attr):
        self.press_attr = press_attr

    def pressing(self):
        for press in getattr(state, self.press_attr):
            if press is not None and press <= state.now_ms < press + BUTTON_HOLD_MS:
                return True
        return False


class _Timer:
    def time(self, units):
        _need(units, MSEC, SECONDS)
        return state.now_ms if units is MSEC else state.now_ms / 1000.0


class _Screen:
    def __init__(self):
        self.row = 1

    def clear_screen(self):
        state.rows = {}

    def set_cursor(self, row, column):
        self.row = row

    def print(self, text):
        state.rows[self.row] = str(text)


class _SDCard:
    """https://api.vex.com/exp/home/python/SDcard.html"""

    def is_inserted(self):
        return state.sd_inserted

    def savefile(self, filename, buffer):
        if not isinstance(buffer, bytearray):
            raise TypeError("savefile takes a bytearray")
        state.sd_files[filename] = bytes(buffer)
        return len(buffer)

    def loadfile(self, filename):
        return bytearray(state.sd_files.get(filename, b""))


class Brain:
    """Buttons: https://api.vex.com/exp/home/python/Sensing/Brain.html
    (the Screen and Sound pages cover the rest)"""

    def __init__(self):
        self.screen = _Screen()
        self.timer = _Timer()
        self.sdcard = _SDCard()
        self.buttonCheck = _Button("check_press_ms")
        self.buttonLeft = _Button("left_press_ms")
        self.buttonRight = _Button("right_press_ms")

    def play_sound(self, sound):
        _need(sound, SoundType.TADA)
        state.sounds.append(sound)


# --------------------------------------------------------------- Inertial
class Inertial:
    """https://api.vex.com/exp/home/python/Inertial.html (built into the Brain)"""

    def __init__(self):
        self._heading = 0.0
        self._calibration_start = None

    def calibrate(self):
        self._calibration_start = state.now_ms

    def is_calibrating(self):
        if self._calibration_start is None:
            return False
        if state.calibration_ms is None:
            return True
        return state.now_ms - self._calibration_start < state.calibration_ms

    def heading(self, units):
        _need(units, DEGREES)
        return self._heading

    def set_heading(self, value, units):
        _need(units, DEGREES)
        self._heading = value % 360.0


# ------------------------------------------------------------------ Motor
class Motor:
    """https://api.vex.com/exp/home/python/Motion/motor_and_motor_group.html"""

    def __init__(self, port, gears, reverse):
        _register(self, port)
        _need(gears, GearSetting.RATIO_36_1, GearSetting.RATIO_18_1, GearSetting.RATIO_6_1)
        self.port = port
        self.reverse = reverse
        self.command = 0.0
        self.stopping = None
        self._degrees = 0.0

    def spin(self, direction, velocity, units):
        _need(direction, FORWARD, REVERSE)
        _need(units, PERCENT)
        if not -100.0 <= velocity <= 100.0:
            raise ValueError("velocity %r is outside -100..100 percent" % velocity)
        self.command = velocity if direction is FORWARD else -velocity

    def stop(self):
        self.command = 0.0

    def set_stopping(self, mode):
        _need(mode, BRAKE, HOLD, COAST)
        self.stopping = mode

    def position(self, units):
        _need(units, DEGREES)
        return self._degrees

    def set_position(self, value, units):
        _need(units, DEGREES)
        self._degrees = float(value)

    def current(self):
        return 0.0


# ---------------------------------------------------------------- sensors
class Distance:
    """https://api.vex.com/exp/home/python/Sensing/distance-sensor.html"""

    def __init__(self, port):
        _register(self, port)

    def is_object_detected(self):
        return False

    def object_distance(self, units):
        _need(units, MM)
        return 0.0


class Optical:
    """https://api.vex.com/exp/home/python/Sensing/optical-sensor.html"""

    def __init__(self, port):
        _register(self, port)
        self.light_power = 0

    def _reading(self):
        if state.optical_at is None:
            return 0.0, 0.0
        return state.optical_at(state.now_ms)

    def hue(self):
        return float(self._reading()[0])

    def brightness(self):
        return float(self._reading()[1])

    def is_near_object(self):
        return False

    def set_light_power(self, value, units):
        # the API page asks for a whole number of percent
        _need(units, PERCENT)
        if not isinstance(value, int) or not 0 <= value <= 100:
            raise ValueError("light power %r is not a whole number 0..100" % value)
        self.light_power = value
